"""
Analysis and scoring logic
"""
from config import SCORING_RULES, DECISION_THRESHOLDS


class StockAnalyzer:
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
    
    def calculate_structure_quality_score(self, trend_label):
        """Score based on chart structure"""
        structure_scores = {
            "uptrend": 8,
            "downtrend": 4,
            "sideways": 6,
            "reversal_setup": 7
        }
        return structure_scores.get(trend_label, 5)
    
    def calculate_volume_score(self, volume_label):
        """Score based on volume confirmation"""
        volume_scores = {
            "high": 8,
            "above_average": 7,
            "average": 5,
            "below_average": 3,
            "low": 2
        }
        return volume_scores.get(volume_label, 5)
    
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
    
    def determine_setup_type(self, trend_label, price, ema_20, rsi):
        """Determine setup type"""
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
        for level in sorted(resistance_levels):
            if level > entry:
                targets.append(level)
                if len(targets) >= 3:
                    break
        
        # If not enough resistance levels, use percentage targets
        if len(targets) < 3:
            targets.extend([
                entry * 1.05,
                entry * 1.10,
                entry * 1.15
            ])
        
        return targets[:3]
    
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
