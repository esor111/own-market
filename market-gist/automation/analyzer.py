"""
Analysis and scoring logic
"""
from config import SCORING_RULES, DECISION_THRESHOLDS


class StockAnalyzer:
    MIN_TARGET_DISTANCE_PCT = 0.03
    MIN_TARGET_RISK_REWARD = 1.0
    MIN_WATCHLIST_RISK_REWARD = 1.2

    def __init__(self):
        self.scoring_rules = SCORING_RULES
        self.decision_thresholds = DECISION_THRESHOLDS
    
    def calculate_market_alignment_score(self, market_change_pct):
        """Score based on market trend"""
        if market_change_pct > 1.5:
            return 10
        elif market_change_pct > 0.5:
            return 7
        elif market_change_pct > -0.5:
            return 5
        elif market_change_pct > -1.5:
            return 3
        else:
            return 1
    
    def calculate_sector_alignment_score(self, sector_change_pct, market_change_pct):
        """Score based on sector relative strength"""
        if sector_change_pct > market_change_pct + 1:
            return 10
        elif sector_change_pct > market_change_pct:
            return 7
        elif sector_change_pct > market_change_pct - 0.5:
            return 5
        else:
            return 3
    
    def calculate_trend_filter_score(self, price, ema_20, ma_50):
        """Score based on price position relative to moving averages"""
        if price > ema_20 and price > ma_50:
            return 10
        elif price > ema_20:
            return 7
        elif price > ma_50:
            return 5
        else:
            return 2
    
    def calculate_momentum_score(self, rsi, macd_histogram):
        """Score based on RSI and MACD"""
        score = 5  # Neutral
        
        # RSI component
        if 30 <= rsi <= 40:
            score += 3  # Oversold but not extreme
        elif 40 < rsi <= 60:
            score += 0  # Neutral
        elif rsi > 70:
            score -= 2  # Overbought
        
        # MACD component
        if macd_histogram > 0:
            score += 2
        elif macd_histogram < -50:
            score -= 2
        
        return max(0, min(10, score))
    
    def calculate_relative_strength_score(self, stock_change, market_change, sector_change):
        """Score based on relative strength"""
        vs_market = stock_change - market_change
        vs_sector = stock_change - sector_change
        
        if vs_market > 0 and vs_sector > 0:
            return 10  # Outperforming both
        elif vs_market > 0 or vs_sector > 0:
            return 6   # Outperforming one
        else:
            return 2   # Underperforming both
    
    def calculate_location_score(self, price, support_level, resistance_level):
        """Score based on price location in range"""
        if support_level and resistance_level:
            range_size = resistance_level - support_level
            distance_from_support = price - support_level
            position_pct = (distance_from_support / range_size) * 100
            
            if position_pct < 20:
                return 8  # Near support, good for reversal
            elif position_pct < 40:
                return 6
            elif position_pct < 60:
                return 5
            elif position_pct < 80:
                return 4
            else:
                return 2  # Near resistance
        
        return 5  # Neutral if can't determine
    
    def calculate_structure_quality_score(self, trend_label, structure_label="", structure_confidence="medium"):
        """Score based on chart structure"""
        structure_scores = {
            "uptrend": 8,
            "downtrend": 4,
            "sideways": 6,
            "reversal_setup": 7,
            "transition": 5
        }
        score = structure_scores.get(trend_label, 5)

        structure_bonus = {
            "trend_continuation": 1,
            "compression": 1,
            "range": 0,
            "trend_breakdown": -1,
            "insufficient_structure": -2
        }
        score += structure_bonus.get(structure_label, 0)

        if structure_confidence == "low":
            score -= 2
        elif structure_confidence == "high":
            score += 1

        return max(0, min(10, score))
    
    def calculate_volume_score(self, volume_label):
        """Score based on volume confirmation"""
        volume_scores = {
            "high": 8,
            "above_average": 7,
            "average": 5,
            "below_average": 3,
            "low": 2,
            "available": 5,
            "unknown": 2
        }
        return volume_scores.get(volume_label, 5)

    def classify_trend(self, price, ema_20, ma_50):
        """Classify trend from price and moving average alignment."""
        if price >= ema_20 >= ma_50:
            return "uptrend"
        if price <= ema_20 <= ma_50:
            return "downtrend"
        return "sideways"
    
    def calculate_total_score(self, scores):
        """Calculate total score from individual components"""
        total = sum(scores.values())
        max_score = len(scores) * 10
        percent = int((total / max_score) * 100)
        
        return {
            "total": total,
            "max": max_score,
            "percent": percent
        }
    
    def determine_action(self, score_percent, confidence):
        """Determine trading action based on score"""
        if score_percent >= self.decision_thresholds["strong_buy"] and confidence >= 70:
            return "strong_buy"
        elif score_percent >= self.decision_thresholds["buy"] and confidence >= 60:
            return "buy"
        elif score_percent >= self.decision_thresholds["watch"]:
            return "watch_only"
        else:
            return "avoid"
    
    def determine_setup_type(self, trend_label, price, ema_20, rsi, structure_label=""):
        """Determine setup type"""
        if structure_label == "compression":
            return "breakout_watch"
        if structure_label == "trend_continuation" and trend_label == "uptrend" and price > ema_20:
            return "continuation"
        if structure_label == "range":
            return "breakout_watch"
        if trend_label == "downtrend" and price < ema_20 and rsi < 40:
            return "reversal_watch"
        elif trend_label == "uptrend" and price > ema_20:
            return "continuation"
        elif trend_label == "sideways":
            return "breakout_watch"
        else:
            return "no_setup"
    
    def calculate_support_resistance(self, price, swing_lows, swing_highs):
        """Calculate nearest support and resistance levels"""
        # Find nearest support below current price
        supports_below = [s for s in swing_lows if s < price]
        nearest_support = max(supports_below) if supports_below else price * 0.95
        
        # Find nearest resistance above current price
        resistances_above = [r for r in swing_highs if r > price]
        nearest_resistance = min(resistances_above) if resistances_above else price * 1.05
        
        return nearest_support, nearest_resistance
    
    def calculate_targets(self, entry, resistance_levels):
        """Calculate target levels"""
        targets = []
        minimum_target = entry * (1 + self.MIN_TARGET_DISTANCE_PCT)
        seen = set()

        for level in sorted(resistance_levels):
            rounded = round(level, 2)
            if rounded <= minimum_target:
                continue
            if rounded in seen:
                continue
            seen.add(rounded)
            targets.append(rounded)
            if len(targets) >= 3:
                break

        # If not enough resistance levels, use percentage targets
        if len(targets) < 3:
            for fallback in [entry * 1.05, entry * 1.10, entry * 1.15]:
                rounded = round(fallback, 2)
                if rounded <= minimum_target or rounded in seen:
                    continue
                seen.add(rounded)
                targets.append(rounded)
                if len(targets) >= 3:
                    break
        
        return targets[:3]

    def filter_viable_targets(self, entry, stop, resistance_levels):
        """Keep only targets that provide at least the minimum risk/reward."""
        raw_targets = self.calculate_targets(entry, resistance_levels)
        viable = []
        for target in raw_targets:
            if self.calculate_risk_reward(entry, stop, target) >= self.MIN_TARGET_RISK_REWARD:
                viable.append(target)
        return viable[:3]

    def select_continuation_entry(self, price, nearest_support, ema_20, ma_50, invalidation_level):
        """Prefer dynamic-support pullback entries over current-price chasing."""
        candidates = []
        for level in [ema_20, ma_50]:
            if (
                level is not None
                and price is not None
                and invalidation_level is not None
                and invalidation_level < level < price
            ):
                candidates.append(level)

        if candidates:
            entry = max(candidates)
        elif nearest_support is not None and nearest_support < price:
            entry = nearest_support
        else:
            entry = price

        upper = min(price, round(entry * 1.01, 2))
        return [round(entry, 2), round(max(entry, upper), 2)]
    
    def calculate_risk_reward(self, entry, stop, target):
        """Calculate risk/reward ratio"""
        risk = entry - stop
        reward = target - entry
        
        if risk > 0:
            return round(reward / risk, 2)
        return 0
    
    def calculate_confidence(self, score_percent, data_quality_factors):
        """Calculate confidence level"""
        base_confidence = score_percent
        
        # Adjust based on data quality
        if data_quality_factors.get("has_sector_data"):
            base_confidence += 5
        if data_quality_factors.get("has_volume_data"):
            base_confidence += 5
        if data_quality_factors.get("has_all_indicators"):
            base_confidence += 5
        if data_quality_factors.get("has_broker_flow"):
            base_confidence += 10
        
        # Reduce confidence for missing data
        if not data_quality_factors.get("has_sector_data"):
            base_confidence -= 10
        
        return max(0, min(100, base_confidence))

    def evaluate_timeframe_alignment(self, monthly_context, weekly_context, daily_context, setup_type):
        """Evaluate top-down monthly/weekly/daily alignment for swing setups."""
        monthly_trend = (monthly_context or {}).get("trend_label")
        weekly_trend = (weekly_context or {}).get("trend_label")
        daily_trend = (daily_context or {}).get("trend_label")
        monthly_structure = (monthly_context or {}).get("structure_label")
        weekly_structure = (weekly_context or {}).get("structure_label")
        daily_structure = (daily_context or {}).get("structure_label")

        findings = []
        score = 0

        if monthly_trend == "uptrend":
            score += 2
        elif monthly_trend == "downtrend":
            score -= 2
            findings.append("monthly_trend_against_setup")

        if weekly_trend == "uptrend":
            score += 2
        elif weekly_trend == "downtrend":
            score -= 2
            findings.append("weekly_trend_against_setup")

        if daily_trend == "uptrend":
            score += 1
        elif daily_trend == "downtrend":
            if setup_type == "continuation":
                findings.append("daily_pullback_against_continuation")
            else:
                score -= 1
                findings.append("daily_trigger_not_supportive")

        if monthly_trend and weekly_trend and monthly_trend == weekly_trend:
            score += 1
        elif (
            monthly_trend in {"uptrend", "downtrend"}
            and weekly_trend in {"uptrend", "downtrend"}
            and monthly_trend != weekly_trend
        ):
            score -= 1
            findings.append("monthly_weekly_conflict")

        if weekly_trend and daily_trend and weekly_trend == daily_trend:
            score += 1
        elif (
            weekly_trend in {"uptrend", "downtrend"}
            and daily_trend in {"uptrend", "downtrend"}
            and weekly_trend != daily_trend
        ):
            score -= 1
            findings.append("weekly_daily_conflict")

        if monthly_structure == "trend_breakdown":
            score -= 1
            findings.append("monthly_structure_broken")
        if weekly_structure == "trend_breakdown":
            score -= 1
            findings.append("weekly_structure_broken")
        if setup_type == "breakout_watch" and daily_structure == "trend_breakdown":
            score -= 1
            findings.append("daily_breakout_trigger_weak")

        if score >= 4:
            alignment = "strong"
        elif score >= 1:
            alignment = "mixed_but_acceptable"
        else:
            alignment = "conflicted"

        return {
            "status": alignment,
            "score": score,
            "findings": findings,
            "is_supportive": alignment != "conflicted"
        }

    def rank_watchlist_candidate(
        self,
        action,
        setup_type,
        score,
        confidence,
        risk_reward_ratio,
        structure_confidence,
        location_label
    ):
        """Rank watchlist-quality setups and optionally downgrade weak continuation ideas."""
        if action != "watch_only":
            return {
                "action": action,
                "watchlist_tier": None,
                "watchlist_priority": None,
                "watchlist_score": None,
                "notes": []
            }

        rank_score = 0
        notes = []

        if risk_reward_ratio is not None:
            if risk_reward_ratio < self.MIN_WATCHLIST_RISK_REWARD:
                notes.append("risk_reward_below_watchlist_minimum")
            elif risk_reward_ratio >= 2.0:
                rank_score += 3
            elif risk_reward_ratio >= 1.5:
                rank_score += 2
            elif risk_reward_ratio >= self.MIN_WATCHLIST_RISK_REWARD:
                rank_score += 1
        else:
            notes.append("risk_reward_missing")

        if score >= 58:
            rank_score += 2
        elif score >= 55:
            rank_score += 1

        if confidence >= 68:
            rank_score += 2
        elif confidence >= 65:
            rank_score += 1

        if structure_confidence == "high":
            rank_score += 1

        if setup_type == "breakout_watch":
            rank_score += 1

        if setup_type == "continuation" and location_label == "near_resistance":
            rank_score -= 1
            notes.append("continuation_setup_is_extended")

        if rank_score >= 7:
            tier = "A"
            priority = 1
        elif rank_score >= 5:
            tier = "B"
            priority = 2
        elif rank_score >= 3:
            tier = "C"
            priority = 3
        else:
            tier = None
            priority = None

        adjusted_action = action
        if risk_reward_ratio is None or risk_reward_ratio < self.MIN_WATCHLIST_RISK_REWARD:
            adjusted_action = "avoid"
            tier = None
            priority = None
            notes.append("watchlist_requires_better_risk_reward")
        elif tier == "C":
            adjusted_action = "avoid"
            notes.append("watchlist_rank_too_weak")
        elif tier is None:
            adjusted_action = "avoid"
            notes.append("watchlist_rank_too_weak")

        return {
            "action": adjusted_action,
            "watchlist_tier": tier,
            "watchlist_priority": priority,
            "watchlist_score": rank_score,
            "notes": notes
        }
