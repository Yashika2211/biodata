"""Figure package: one module per figure; ``make_all`` regenerates everything."""
from .accuracy import fig_accuracy
from .adaptive_example import fig_adaptive_examples
from .ablations import fig_ablations
from .architecture import fig_architecture
from .convergence import fig_fl_convergence
from .cost import fig_cost
from .latency import fig_latency
from .privacy_utility import fig_privacy_utility
from .style import _load


def make_all():
    fig_architecture()
    fig_adaptive_examples()
    S = _load()
    for ds in S["datasets"]:
        fig_accuracy(S, ds); fig_privacy_utility(S, ds); fig_ablations(S, ds)
    fig_fl_convergence(S); fig_latency(S); fig_cost(S)
