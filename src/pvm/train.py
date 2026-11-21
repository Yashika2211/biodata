"""Train and export the serving model (method D by default, tuned threshold)."""
from __future__ import annotations

import argparse

from . import config as C
from . import methods as MT
from . import models as ML
from . import thresholds as T
from .experiments import Provider


def train_serving_model(patients, m=C.PERSISTENCE_M, alpha=C.ALPHA):
    fa = MT.featurize(patients, "adaptive", alpha)
    sites, mean, sd, cw, std = MT.prepare_global(patients, fa)
    import numpy as np
    Xa = np.vstack([v[0] for v in std.values()]); y = np.concatenate([v[1] for v in std.values()])
    model = ML.Model(ML.fit_central(Xa, y, cw), mean, sd, m=m, alpha=alpha)
    sc = {p.pid: model.score(fa[p.pid]) for p in patients}
    model.tau, _ = T.tune(list(sites.values()), sc, T.LOGIT_GRID, m)
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="synthetic")
    ap.add_argument("--out", default="models/model.json")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    ps = Provider(a.dataset).cohort(a.seed)
    model = train_serving_model(ps)
    with open(a.out, "w") as f:
        f.write(model.to_json())
    print("saved", a.out, "tau=", model.tau)


if __name__ == "__main__":
    main()
