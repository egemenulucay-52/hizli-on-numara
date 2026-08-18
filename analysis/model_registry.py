M4_VARIANTS = ("M4-A", "M4-B", "M4-C", "M4-D", "M4-E", "M4-F")
RESEARCH_MODEL_NAMES = (
    "M1",
    "M2",
    "M3",
    *M4_VARIANTS,
    "M5",
    "M6",
    "Ensemble",
    "M7",
    "M8",
    "M9",
    "M10",
)

MODEL_DESCRIPTIONS = {
    "M1": "Frequency Momentum",
    "M2": "Frequency Deviation",
    "M3": "Pair Association",
    "M4-A": "Standard Conditional Transition",
    "M4-B": "Time-decayed Conditional Transition",
    "M4-C": "Bayesian-smoothed Transition",
    "M4-D": "Multi-lag Conditional Context",
    "M4-E": "Conservative Significant Transitions",
    "M4-F": "Reliability-weighted Context",
    "M5": "Delay / Recency",
    "M6": "Structural Score",
    "Ensemble": "Fixed-weight M1-M6 Ensemble",
    "M7": "Joint Set Optimizer",
    "M8": "Bayesian Conditional Model",
    "M9": "Pair-Triple Hypergraph Set Model",
    "M10": "Online L2 Logistic Ranking",
}
