"""
Post-analysis QC rules for rejecting weak trade plans.
"""


class AnalysisQualityGate:
    def __init__(self):
        self.minimum_risk_reward = 1.0

    @staticmethod
    def _zone_width(entry_zone):
        if not entry_zone or len(entry_zone) != 2:
            return None
        low, high = entry_zone
        if low is None or high is None:
            return None
        return round(abs(high - low), 2)

    def evaluate(self, decision_data, chart_data):
        findings = []
        status = "pass"

        setup_type = decision_data.get("setup_type")
        entry_zone = decision_data.get("entry_zone") or []
        stop_loss = decision_data.get("stop_loss")
        targets = decision_data.get("targets") or []
        risk_reward_ratio = decision_data.get("risk_reward_ratio")
        structure_confidence = chart_data.get("structure_confidence", "medium")
        structure_label = chart_data.get("structure_label", "")

        if structure_confidence == "low":
            findings.append("structure_confidence_low")
        if structure_label in {"insufficient_structure", "trend_breakdown"}:
            findings.append(f"structure_not_actionable:{structure_label}")

        zone_width = self._zone_width(entry_zone)
        if zone_width == 0:
            findings.append("entry_zone_trivial")

        if entry_zone and stop_loss is None:
            findings.append("entry_without_stop_loss")
        if entry_zone and not targets:
            findings.append("entry_without_targets")

        if risk_reward_ratio is not None and risk_reward_ratio < self.minimum_risk_reward:
            findings.append("risk_reward_below_minimum")

        if setup_type in {"continuation", "breakout_watch", "reversal_watch"}:
            if not entry_zone or stop_loss is None or not targets:
                findings.append("setup_missing_trade_plan")

        if findings:
            status = "fail"

        adjusted = dict(decision_data)
        if status == "fail":
            adjusted["action"] = "avoid"
            if "structure_not_actionable:trend_breakdown" in findings:
                adjusted["setup_type"] = "no_setup"
            if "setup_missing_trade_plan" in findings or "risk_reward_below_minimum" in findings:
                adjusted["entry_zone"] = []
                adjusted["stop_loss"] = None
                adjusted["invalidation_level"] = None
                adjusted["targets"] = []
                adjusted["risk_reward_ratio"] = None

        return {
            "status": status,
            "findings": findings,
            "decision": adjusted
        }
