"""
Post-analysis QC rules for rejecting weak trade plans.
"""


class AnalysisQualityGate:
    def __init__(self):
        self.minimum_risk_reward = 1.0
        self.truth_close_mismatch_abs = 0.5
        self.truth_close_mismatch_pct = 0.02
        self.minimum_total_traded_value = 5_000_000
        self.minimum_total_trades = 80
        self.high_risk_event_types = {
            "rights_issue",
            "book_closure",
            "prospectus_offer",
            "prospectus_notice",
            "debenture_offer",
        }

    @staticmethod
    def _zone_width(entry_zone):
        if not entry_zone or len(entry_zone) != 2:
            return None
        low, high = entry_zone
        if low is None or high is None:
            return None
        return round(abs(high - low), 2)

    @staticmethod
    def _extract_truth_mismatch(truth_comparison):
        api_vs_browser = (truth_comparison or {}).get("api_vs_browser_daily", {})
        api_close = api_vs_browser.get("api_close")
        browser_close = api_vs_browser.get("browser_close")
        close_diff = api_vs_browser.get("close_diff")

        if api_close in (None, 0) or browser_close is None or close_diff is None:
            return None, None

        close_diff_abs = abs(close_diff)
        close_diff_pct = close_diff_abs / abs(api_close)
        return close_diff_abs, close_diff_pct

    @staticmethod
    def _extract_truth_liquidity(truth_bundle):
        ticker_row = ((truth_bundle or {}).get("ticker") or {}).get("today_price_row") or {}
        traded_value = ticker_row.get("totalTradedValue")
        traded_quantity = ticker_row.get("totalTradedQuantity")
        total_trades = ticker_row.get("totalTrades")
        return traded_value, traded_quantity, total_trades

    def evaluate(self, decision_data, chart_data, truth_comparison=None, truth_bundle=None, event_data=None):
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

        close_diff_abs, close_diff_pct = self._extract_truth_mismatch(truth_comparison)
        if (
            close_diff_abs is not None
            and close_diff_abs > self.truth_close_mismatch_abs
            and close_diff_pct is not None
            and close_diff_pct > self.truth_close_mismatch_pct
        ):
            findings.append("truth_daily_close_mismatch_major")

        event_payload = event_data or {}
        if (
            event_payload.get("event_found")
            and event_payload.get("relevance_now") == "active_window"
            and event_payload.get("event_type") in self.high_risk_event_types
        ):
            findings.append(f"active_event_window:{event_payload.get('event_type')}")

        traded_value, traded_quantity, total_trades = self._extract_truth_liquidity(truth_bundle)
        if entry_zone:
            if (
                traded_value is not None
                and total_trades is not None
                and (
                    traded_value < self.minimum_total_traded_value
                    or total_trades < self.minimum_total_trades
                )
            ):
                findings.append("liquidity_below_minimum")
            elif traded_value is None or total_trades is None or traded_quantity is None:
                findings.append("liquidity_unconfirmed")

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
            if "truth_daily_close_mismatch_major" in findings:
                adjusted["setup_type"] = "incomplete_data"
                adjusted["confidence"] = min(adjusted.get("confidence", 0), 25)
            if "setup_missing_trade_plan" in findings or "risk_reward_below_minimum" in findings:
                adjusted["entry_zone"] = []
                adjusted["stop_loss"] = None
                adjusted["invalidation_level"] = None
                adjusted["targets"] = []
                adjusted["risk_reward_ratio"] = None
            if "truth_daily_close_mismatch_major" in findings:
                adjusted["entry_zone"] = []
                adjusted["stop_loss"] = None
                adjusted["invalidation_level"] = None
                adjusted["targets"] = []
                adjusted["risk_reward_ratio"] = None
            if (
                any(finding.startswith("active_event_window:") for finding in findings)
                or "liquidity_below_minimum" in findings
                or "liquidity_unconfirmed" in findings
            ):
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
