"""
Shared executable entry-label taxonomy for replay research.

This preserves backward-compatible next-open labels while adding a clearer
execution-aware label set for future entry research.
"""


def next_open_label(simulation):
    status = simulation.get("status")
    if status == "skip_gap_above_first_target":
        return "gap_above_target"
    if status == "skip_gap_below_stop":
        return "gap_below_stop"
    if status == "entered":
        gross_return = simulation.get("gross_return_pct")
        if gross_return is None:
            return "entered_unresolved"
        if gross_return > 0:
            return "tradable_positive_gross"
        return "tradable_negative_gross"
    return "unresolved"


def executable_entry_label(simulation):
    status = simulation.get("status")
    if status == "skip_gap_above_first_target":
        return "untradeable_gap_above_target"
    if status == "skip_gap_below_stop":
        return "untradeable_gap_below_stop"
    if status != "entered":
        return "unresolved"

    net_return = simulation.get("net_return_pct")
    if net_return is None:
        return "entered_unresolved"
    if net_return > 0:
        return "tradable_positive_after_costs"
    return "tradable_negative_after_costs"


def survival_label(original_verdict, simulation):
    label = executable_entry_label(simulation)
    if label in {"untradeable_gap_above_target", "untradeable_gap_below_stop"}:
        return "untradeable_gap"
    if label in {"entered_unresolved", "unresolved"}:
        return "unresolved"
    if original_verdict == "good_call":
        return "good_call_survived" if label == "tradable_positive_after_costs" else "good_call_collapsed"
    return "profitable_after_costs" if label == "tradable_positive_after_costs" else "negative_after_costs"


def is_tradable_positive(simulation):
    return executable_entry_label(simulation) == "tradable_positive_after_costs"
