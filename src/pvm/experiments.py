"""Run the full study on one dataset and save raw per-seed results as JSON.

    python -m pvm.experiments --dataset synthetic --seeds 5
    python -m pvm.experiments --dataset eicu --seeds 5
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from . import config as C
from . import methods as MT
from . import models as ML
from .data import public as PB
from .data import synthetic as SY

DATASET_LABEL = {"synthetic": "Synthetic cohort", "eicu": "eICU-CRD demo (semi-synthetic episodes)"}


class Provider:
    """Builds a fresh cohort per seed for either dataset."""

    def __init__(self, dataset, data_dir=PB.DEFAULT_DIR, n_patients=160):
        self.dataset = dataset
        self.n_patients = n_patients
        self.series = PB.load_series(data_dir) if dataset == "eicu" else None

    def cohort(self, seed, n_sites=4):
        if self.dataset == "synthetic":
            return SY.make_cohort(self.n_patients, n_sites, seed=seed)
        return PB.make_cohort(self.series, n_sites, seed=seed)


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) and not np.isinf(o) else (
            "inf" if np.isinf(o) else float(o))
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


def run_main(prov, seeds):
    out = []
    for s in seeds:
        t0 = time.time()
        ps = prov.cohort(s)
        res, ex = run_methods_safe(ps, s)
        fed = ex["fed"]
        res["_loss_curve"] = [(r, L) for r, L in fed.loss_history]
        res["_cohort"] = dict(patients=len(ps), days=float(sum(p.days for p in ps)),
                              test_episodes=int(sum(1 for p in ps for e in p.episodes if e[0] >= p.split)),
                              prevalence=float(np.mean([p.y.mean() for p in ps])),
                              samples=int(sum(p.T for p in ps)))
        out.append(res)
        print(f"[{prov.dataset}] seed {s} main done in {time.time()-t0:.0f}s", flush=True)
    return out


def run_methods_safe(ps, seed, **kw):
    return MT.run_methods(ps, seed=seed, **kw)


def run_ablations(prov, seeds):
    abl = {"alpha": {}, "m": {}, "clip": {}, "sites": {}, "rounds": {}}
    for s in seeds:
        ps = prov.cohort(s)
        fs = MT.featurize(ps, "static")
        for a in (0.005, 0.01, 0.02, 0.05, 0.1):
            r, _ = MT.run_methods(ps, alpha=a, which=("C", "D"), seed=s, feats_cache={"static": fs})
            abl["alpha"].setdefault(str(a), []).append({k: r[k] for k in ("C", "D")})
        for m in (1, 2, 3, 5, 8):
            r, _ = MT.run_methods(ps, m=m, which=("A2", "C", "D"), seed=s, feats_cache={"static": fs})
            abl["m"].setdefault(str(m), []).append(r)
        for clip in (1.0, 3.0, 10.0, 30.0):
            r, _ = MT.run_methods(ps, which=("G",), sigmas=(8.0,), clip=clip, seed=s,
                                  feats_cache={"static": fs})
            abl["clip"].setdefault(str(clip), []).append(r["G@8.0"])
        for k in (2, 4, 8):
            psk = prov.cohort(s, n_sites=k)
            r, _ = MT.run_methods(psk, which=("D", "E", "F"), seed=s)
            abl["sites"].setdefault(str(k), []).append(r)
        for R in (2, 5, 10, 25, 50, 100, 400):
            r, ex = MT.run_methods(ps, which=("F",), fed_rounds=R, seed=s, feats_cache={"static": fs})
            r["F"]["final_loss"] = ex["fed"].loss_history[-1][1]
            abl["rounds"].setdefault(str(R), []).append(r["F"])
        print(f"[{prov.dataset}] seed {s} ablations done", flush=True)
    return abl


def _loss_scores(theta, mean, sd, X, y, cw):
    Xa = ML.aug((X - mean) / sd)
    z = Xa @ theta
    wt = np.where(y == 1, cw[1], cw[0])
    return -(wt * (np.logaddexp(0, z) - y * z))       # higher = looks more like a member


def run_mia(prov, seeds, n=3000):
    """Patient-level loss-threshold membership inference (AUROC; 0.5 = no leak).

    Members: training rows of patients used for training.  Non-members: the same
    time range of held-out patients that were never used.
    """
    from sklearn.metrics import roc_auc_score
    from . import federated as FED
    out = []
    for s in seeds:
        rng = np.random.default_rng(1000 + s)
        ps = prov.cohort(s)
        idx = rng.permutation(len(ps)); cut = int(0.7 * len(ps))
        tr = [ps[i] for i in idx[:cut]]; ho = [ps[i] for i in idx[cut:]]
        fa = MT.featurize(ps, "adaptive")
        sites, mean, sd, cw, std = MT.prepare_global(tr, fa)
        sl = list(std.values())
        Xa = np.vstack([v[0] for v in sl]); y = np.concatenate([v[1] for v in sl])
        models = {"D (central, non-private)": ML.fit_central(Xa, y, cw),
                  "F (FedAvg, non-private)": FED.fedavg(sl, cw, rounds=200, seed=s).theta}
        for sg in (0.5, 8.0, 32.0):
            models[f"G sigma={sg}"] = FED.fedavg(sl, cw, rounds=150, dp_sigma=sg, seed=s).theta
        Xm, ym = MT.train_rows(tr, fa); Xn, yn = MT.train_rows(ho, fa)
        im = rng.choice(len(Xm), min(n, len(Xm), len(Xn)), replace=False)
        jn = rng.choice(len(Xn), len(im), replace=False)
        row = {}
        for name, th in models.items():
            sm = _loss_scores(th, mean, sd, Xm[im], ym[im], cw)
            sn = _loss_scores(th, mean, sd, Xn[jn], yn[jn], cw)
            row[name] = float(roc_auc_score(np.r_[np.ones(len(sm)), np.zeros(len(sn))], np.r_[sm, sn]))
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["synthetic", "eicu"], required=True)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--abl-seeds", type=int, default=3)
    ap.add_argument("--out", default="results")
    ap.add_argument("--skip-ablations", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    prov = Provider(a.dataset)
    seeds = list(range(a.seeds))
    t0 = time.time()
    data = {"dataset": a.dataset, "label": DATASET_LABEL[a.dataset], "seeds": seeds,
            "main": run_main(prov, seeds)}
    data["mia"] = run_mia(prov, seeds)
    if not a.skip_ablations:
        data["ablations"] = run_ablations(prov, list(range(a.abl_seeds)))
    data["wall_seconds"] = time.time() - t0
    with open(os.path.join(a.out, f"raw_{a.dataset}.json"), "w") as f:
        json.dump(_clean(data), f)
    print("saved", a.dataset, f"{data['wall_seconds']:.0f}s")


if __name__ == "__main__":
    main()
