"""The compared methods A, A2, B, C, D, E, F, G(sigma) on one cohort."""
from __future__ import annotations

import time

import numpy as np

from . import config as C
from . import features as F
from . import federated as FED
from . import metrics as M
from . import models as ML
from . import thresholds as T


def featurize(patients, mode="adaptive", alpha=C.ALPHA):
    """pid -> (T, 15) features, via the shared streaming code path."""
    out = {}
    for p in patients:
        feats, _ = F.process_series(p.X, mode=mode, alpha=alpha)
        out[p.pid] = np.asarray(feats, dtype=float)
    return out


def static_scores(patients):
    """Method A/A2 score: max normalised exceedance over the ward limits (>0 = alarm)."""
    out = {}
    for p in patients:
        s = np.full((p.T, C.NV), -np.inf)
        for j, v in enumerate(C.VITALS):
            lo, hi = C.WARD_THRESHOLDS[v]
            x = np.array([F.clean_value(j, a) for a in p.X[:, j]])
            sd = C.PRIOR_SD[v]
            if lo is not None:
                s[:, j] = np.maximum(s[:, j], (lo - x) / sd)
            if hi is not None:
                s[:, j] = np.maximum(s[:, j], (x - hi) / sd)
            s[np.isnan(x), j] = -np.inf
        mx = s.max(1)
        mx[np.isneginf(mx)] = np.nan
        out[p.pid] = mx
    return out


def adaptive_z_scores(patients, feats):
    """Method C score: max over vitals of |current z| (feature block 0:5)."""
    return {p.pid: np.abs(feats[p.pid][:, :C.NV]).max(1) for p in patients}


def by_site(patients):
    d = {}
    for p in patients:
        d.setdefault(p.site, []).append(p)
    return d


def train_rows(patients, feats):
    Xs, ys = [], []
    for p in patients:
        Xs.append(feats[p.pid][T.BURN_IN:p.split]); ys.append(p.y[T.BURN_IN:p.split])
    return np.vstack(Xs), np.concatenate(ys).astype(float)


def _score_patients(model, patients, feats):
    return {p.pid: model.score(feats[p.pid]) for p in patients}


def _eval(patients, scores, tau, m, tol_min):
    r, _ = M.evaluate_alarms(patients, scores, tau, m, "test", tol_min)
    r.update(M.sample_metrics(patients, scores, "test"))
    r["tau"] = float(tau)
    return r


def prepare_global(patients, feats):
    """Aggregate-only quantities: standardiser and class weights."""
    sites = by_site(patients)
    mom, rows, pos, n = [], {}, 0, 0
    for s, ps in sites.items():
        X, y = train_rows(ps, feats)
        rows[s] = (X, y)
        mom.append(ML.moments(X)); pos += int(y.sum()); n += len(y)
    mean, sd = ML.standardiser(mom)
    cw = ML.class_weights(pos, n)
    std_sites = {s: (ML.aug((X - mean) / sd), y) for s, (X, y) in rows.items()}
    return sites, mean, sd, cw, std_sites


def run_methods(patients, m=C.PERSISTENCE_M, alpha=C.ALPHA, tol_min=30.0,
                fed_rounds=400, local_steps=3, lr=0.3, sigmas=(0.5, 2.0, 8.0, 32.0, 128.0),
                clip=10.0, q=0.02, dp_rounds=150, seed=0, which=("A", "A2", "B", "C", "D", "E", "F", "G"),
                feats_cache=None):
    res, extras = {}, {}
    sites_static = by_site(patients)
    site_list = list(sites_static.values())
    fa = (feats_cache or {}).get("adaptive") or featurize(patients, "adaptive", alpha)
    fs = (feats_cache or {}).get("static") or featurize(patients, "static")

    sc_static = static_scores(patients)
    if "A" in which:
        res["A"] = _eval(patients, sc_static, 0.0, 1, tol_min)
    if "A2" in which:
        res["A2"] = _eval(patients, sc_static, 0.0, m, tol_min)

    if "C" in which:
        sc = adaptive_z_scores(patients, fa)
        tau, _ = T.tune(site_list, sc, T.Z_GRID, m, tol_min)
        res["C"] = _eval(patients, sc, tau, m, tol_min)

    def central(feats, name):
        sites, mean, sd, cw, std = prepare_global(patients, feats)
        Xa = np.vstack([v[0] for v in std.values()]); y = np.concatenate([v[1] for v in std.values()])
        t0 = time.process_time()
        th = ML.fit_central(Xa, y, cw)
        dt = time.process_time() - t0
        model = ML.Model(th, mean, sd, m=m, mode="adaptive" if feats is fa else "static", alpha=alpha)
        sc = _score_patients(model, patients, feats)
        tau, _ = T.tune(site_list, sc, T.LOGIT_GRID, m, tol_min)
        model.tau = tau
        r = _eval(patients, sc, tau, m, tol_min)
        r["train_seconds"] = dt
        res[name] = r
        return model, (Xa, y, cw), th

    if "B" in which:
        central(fs, "B")
    cen = None
    if any(k in which for k in ("D", "F", "G")):
        model_d, (Xa, y, cw), th_c = central(fa, "D")
        extras["model_D"] = model_d
        cen = (Xa, y, cw, ML.objective(th_c, Xa, y, cw))

    if "E" in which:
        tot = dict(M.ZERO_COUNTS); delays = []; scs = {}; taus = []
        for s, ps in sites_static.items():
            X, yy = train_rows(ps, fa)
            mean, sd = ML.standardiser([ML.moments(X)])
            cw_s = ML.class_weights(int(yy.sum()), len(yy))
            th = ML.fit_central(ML.aug((X - mean) / sd), yy, cw_s)
            mod = ML.Model(th, mean, sd, m=m)
            sc = _score_patients(mod, ps, fa)
            tau, _ = T.tune([ps], sc, T.LOGIT_GRID, m, tol_min)
            taus.append(tau)
            _, c = M.evaluate_alarms(ps, sc, tau, m, "test", tol_min)
            tot = M.add_counts(tot, c)
            for p in ps:
                _, d = M.patient_counts(sc[p.pid], p.episodes, p.split, p.T, p.dt_min, tau, m, tol_min)
                delays += d
            scs.update(sc)
        r = M.summarise(tot, delays); r.update(M.sample_metrics(patients, scs, "test"))
        r["tau"] = float(np.mean(taus)); res["E"] = r

    if "F" in which or "G" in which:
        sites, mean, sd, cw, std = prepare_global(patients, fa)
        std_list = list(std.values())
        Xa, y, cw_, cen_loss = cen
        fed = FED.fedavg(std_list, cw, rounds=fed_rounds, local_steps=local_steps, lr=lr,
                         central_loss=cen_loss, seed=seed)
        extras["fed"] = fed
        model = ML.Model(fed.theta, mean, sd, m=m, alpha=alpha, tag=C.MODEL_TAG + "-fed")
        sc = _score_patients(model, patients, fa)
        tau, _ = T.tune(site_list, sc, T.LOGIT_GRID, m, tol_min)
        model.tau = tau
        r = _eval(patients, sc, tau, m, tol_min)
        r.update(rounds=fed.rounds, rounds_to_converge=fed.rounds_to_converge,
                 train_seconds=fed.train_seconds, bytes_exchanged=fed.bytes_exchanged,
                 loss_gap=fed.loss_history[-1][1] - cen_loss)
        if "F" in which:
            res["F"] = r
            extras["model_F"] = model
        if "G" in which:
            for sg in sigmas:
                g = FED.fedavg(std_list, cw, rounds=dp_rounds, local_steps=local_steps, lr=lr,
                               dp_sigma=sg, clip=clip, q=q, seed=seed + 1, central_loss=cen_loss)
                mg = ML.Model(g.theta, mean, sd, m=m, alpha=alpha, tag=C.MODEL_TAG + "-fed-dp")
                scg = _score_patients(mg, patients, fa)
                tg, _ = T.tune(site_list, scg, T.LOGIT_GRID, m, tol_min)
                mg.tau = tg
                rg = _eval(patients, scg, tg, m, tol_min)
                rg.update(epsilon=g.epsilon, sigma=sg, clip=clip, rounds=g.rounds,
                          train_seconds=g.train_seconds, loss_gap=g.loss_history[-1][1] - cen_loss)
                res[f"G@{sg}"] = rg
    return res, extras
