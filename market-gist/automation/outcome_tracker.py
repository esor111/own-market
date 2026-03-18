"""
Outcome evaluation helpers for previously stored trade decisions.
"""


class OutcomeTracker:
    @staticmethod
    def _find_first_hit(future_bars, stop_level, targets):
        """Return the earliest stop/target event seen in future bars."""
        for bar in future_bars:
            low = bar.get("low")
            high = bar.get("high")
            close_time_ms = bar.get("close_time_ms")

            if stop_level is not None and low is not None and low <= stop_level:
                return {"type": "stop", "level": stop_level, "close_time_ms": close_time_ms}

            for idx, target in enumerate(targets, start=1):
                if high is not None and target is not None and high >= target:
                    return {"type": f"target_{idx}", "level": target, "close_time_ms": close_time_ms}

        return None

    @staticmethod
    def _calculate_excursions(entry_price, future_bars):
        """Calculate max favorable/adverse excursion from the entry reference."""
        if entry_price in (None, 0) or not future_bars:
            return None, None

        highest_high = max((bar.get("high") for bar in future_bars if bar.get("high") is not None), default=None)
        lowest_low = min((bar.get("low") for bar in future_bars if bar.get("low") is not None), default=None)

        mfe = None
        mae = None
        if highest_high is not None:
            mfe = round(((highest_high - entry_price) / entry_price) * 100, 2)
        if lowest_low is not None:
            mae = round(((lowest_low - entry_price) / entry_price) * 100, 2)
        return mfe, mae

    def evaluate(self, decision_record, future_bars, evaluation_date, timeframe):
        """Evaluate a stored decision against bars that occurred afterward."""
        action = decision_record.get("action")
        entry_zone = decision_record.get("entry_zone") or []
        stop_level = decision_record.get("invalidation_level") or decision_record.get("stop_loss")
        targets = decision_record.get("targets") or []
        decision_session_id = decision_record.get("session_id")

        if action == "avoid" or not entry_zone or stop_level is None or not targets:
            return {
                "decision_session_id": decision_session_id,
                "evaluation_date": evaluation_date,
                "time_horizon": timeframe,
                "outcome_label": "not_applicable",
                "target_1_hit": None,
                "target_2_hit": None,
                "target_3_hit": None,
                "stop_hit": None,
                "max_favorable_excursion_pct": None,
                "max_adverse_excursion_pct": None,
                "notes": "Decision did not produce an actionable trade plan."
            }

        if not future_bars:
            return {
                "decision_session_id": decision_session_id,
                "evaluation_date": evaluation_date,
                "time_horizon": timeframe,
                "outcome_label": "pending",
                "target_1_hit": False,
                "target_2_hit": False,
                "target_3_hit": False,
                "stop_hit": False,
                "max_favorable_excursion_pct": None,
                "max_adverse_excursion_pct": None,
                "notes": "No future bars available beyond the decision bar yet."
            }

        entry_price = entry_zone[0]
        mfe, mae = self._calculate_excursions(entry_price, future_bars)
        first_hit = self._find_first_hit(future_bars, stop_level, targets)

        target_hits = []
        for target in targets[:3]:
            target_hits.append(any((bar.get("high") is not None and bar.get("high") >= target) for bar in future_bars))

        stop_hit = any((bar.get("low") is not None and bar.get("low") <= stop_level) for bar in future_bars)

        if first_hit is None:
            outcome_label = "open"
        elif first_hit["type"] == "stop":
            outcome_label = "stopped_out"
        elif first_hit["type"] == "target_3":
            outcome_label = "target_3_hit"
        elif first_hit["type"] == "target_2":
            outcome_label = "target_2_hit"
        else:
            outcome_label = "target_1_hit"

        notes = f"Evaluated against {len(future_bars)} future bars."
        if first_hit:
            notes += f" First event: {first_hit['type']} at {first_hit['level']}."

        return {
            "decision_session_id": decision_session_id,
            "evaluation_date": evaluation_date,
            "time_horizon": timeframe,
            "outcome_label": outcome_label,
            "target_1_hit": target_hits[0] if len(target_hits) > 0 else None,
            "target_2_hit": target_hits[1] if len(target_hits) > 1 else None,
            "target_3_hit": target_hits[2] if len(target_hits) > 2 else None,
            "stop_hit": stop_hit,
            "max_favorable_excursion_pct": mfe,
            "max_adverse_excursion_pct": mae,
            "notes": notes
        }
