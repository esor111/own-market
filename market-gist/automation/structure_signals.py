"""
Structure and level derivation helpers.
"""


class StructureSignalEngine:
    MIN_LEVEL_DISTANCE_PCT = 0.015
    SWING_WINDOW = 2
    MIN_BARS_FOR_STRUCTURE = 12
    STRUCTURE_LOOKBACK = 16
    RANGE_LOOKBACK = 8

    @staticmethod
    def round_price(value):
        """Round numeric values for stable output."""
        if value is None:
            return None
        return round(float(value), 2)

    def _normalize_bars(self, bars):
        """Keep only bars with complete OHLC data."""
        normalized = []
        for bar in bars or []:
            if not isinstance(bar, dict):
                continue
            open_price = bar.get("open")
            high = bar.get("high")
            low = bar.get("low")
            close = bar.get("close")
            if None in {open_price, high, low, close}:
                continue
            normalized.append({
                "index": bar.get("index"),
                "time": bar.get("time"),
                "open": float(open_price),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": bar.get("volume")
            })
        return normalized

    def _cluster_levels(self, levels, tolerance_pct=0.0125):
        """Cluster nearby levels so repeated reactions produce cleaner zones."""
        clustered = []
        for raw_level in sorted(level for level in levels if level is not None):
            level = self.round_price(raw_level)
            if level is None or level <= 0:
                continue
            if not clustered:
                clustered.append({"levels": [level]})
                continue

            last_cluster = clustered[-1]["levels"]
            anchor = sum(last_cluster) / len(last_cluster)
            if abs(level - anchor) / anchor <= tolerance_pct:
                last_cluster.append(level)
            else:
                clustered.append({"levels": [level]})

        summarized = []
        for cluster in clustered:
            cluster_levels = cluster["levels"]
            mean_level = sum(cluster_levels) / len(cluster_levels)
            summarized.append({
                "level": self.round_price(mean_level),
                "touches": len(cluster_levels),
                "min": self.round_price(min(cluster_levels)),
                "max": self.round_price(max(cluster_levels))
            })
        return summarized

    def _extract_swings(self, bars):
        """Identify pivot highs and lows from recent bars."""
        swing_highs = []
        swing_lows = []
        if len(bars) < (self.SWING_WINDOW * 2 + 1):
            return swing_highs, swing_lows

        for idx in range(self.SWING_WINDOW, len(bars) - self.SWING_WINDOW):
            current = bars[idx]
            left = bars[idx - self.SWING_WINDOW:idx]
            right = bars[idx + 1:idx + 1 + self.SWING_WINDOW]

            current_high = current["high"]
            current_low = current["low"]

            if all(current_high >= bar["high"] for bar in left + right):
                swing_highs.append(current_high)
            if all(current_low <= bar["low"] for bar in left + right):
                swing_lows.append(current_low)

        return swing_highs, swing_lows

    def _derive_range_boundaries(self, bars):
        """Return local range high/low from the recent structure window."""
        if not bars:
            return None, None, None
        highs = [bar["high"] for bar in bars]
        lows = [bar["low"] for bar in bars]
        range_high = max(highs)
        range_low = min(lows)
        if range_low <= 0:
            return self.round_price(range_high), self.round_price(range_low), None
        width_pct = ((range_high - range_low) / range_low) * 100
        return self.round_price(range_high), self.round_price(range_low), round(width_pct, 2)

    def _classify_structure(self, bars, range_high, range_low, ema_20, ma_50):
        """Classify recent multi-bar behavior using simple, explicit rules."""
        if len(bars) < self.MIN_BARS_FOR_STRUCTURE:
            return "insufficient_structure"

        recent = bars[-10:]
        earlier = bars[-20:-10] if len(bars) >= 20 else bars[:-10]
        if not earlier:
            return "insufficient_structure"

        recent_high = max(bar["high"] for bar in recent)
        recent_low = min(bar["low"] for bar in recent)
        earlier_high = max(bar["high"] for bar in earlier)
        earlier_low = min(bar["low"] for bar in earlier)
        latest_close = recent[-1]["close"]

        if range_high and range_low:
            full_range = range_high - range_low
            recent_range = recent_high - recent_low
            if full_range > 0 and recent_range / full_range <= 0.45:
                return "compression"

        ema_ok = ema_20 is None or latest_close >= ema_20
        ma_ok = ma_50 is None or latest_close <= ma_50

        if recent_high > earlier_high and recent_low > earlier_low and ema_ok:
            return "trend_continuation"
        if recent_high < earlier_high and recent_low < earlier_low and ma_ok:
            return "trend_breakdown"
        return "range"

    def _is_far_enough(self, price, level, direction):
        """Return True when a level is meaningfully separated from current price."""
        if level is None or price is None or price <= 0:
            return False
        distance_pct = abs(level - price) / price
        if direction == "support":
            return level < price and distance_pct >= self.MIN_LEVEL_DISTANCE_PCT
        if direction == "resistance":
            return level > price and distance_pct >= self.MIN_LEVEL_DISTANCE_PCT
        return distance_pct >= self.MIN_LEVEL_DISTANCE_PCT

    def sorted_levels(self, levels, reverse=False):
        """Return unique rounded levels in sorted order."""
        cleaned = []
        seen = set()
        for level in levels:
            if level is None:
                continue
            rounded = self.round_price(level)
            if rounded is None or rounded <= 0:
                continue
            key = f"{rounded:.2f}"
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(rounded)
        return sorted(cleaned, reverse=reverse)

    def levels_to_zones(self, levels):
        """Convert levels into narrow support/resistance zones."""
        zones = []
        for level in levels[:3]:
            width = max(level * 0.01, 1)
            zones.append([
                self.round_price(level - width),
                self.round_price(level + width)
            ])
        return zones

    def derive_price_levels(self, price, chart_data, indicator_data):
        """Derive support, resistance, breakout, and invalidation from chart state."""
        low = chart_data.get("low")
        high = chart_data.get("high")
        open_price = chart_data.get("open")
        ema_20 = indicator_data.get("ema_20")
        ma_50 = indicator_data.get("ma_50")
        recent_bars = self._normalize_bars(chart_data.get("recent_bars", []))
        structure_window = recent_bars[-self.STRUCTURE_LOOKBACK:]
        range_window = structure_window[-self.RANGE_LOOKBACK:] if structure_window else []

        recent_swing_highs, recent_swing_lows = self._extract_swings(structure_window)
        range_high, range_low, range_width_pct = self._derive_range_boundaries(range_window)
        structure_label = self._classify_structure(structure_window, range_high, range_low, ema_20, ma_50)

        support_clusters = self._cluster_levels(recent_swing_lows)
        resistance_clusters = self._cluster_levels(recent_swing_highs)

        support_candidates = list(chart_data.get("swing_lows", []))
        resistance_candidates = list(chart_data.get("swing_highs", []))

        support_candidates.extend(cluster["level"] for cluster in support_clusters)
        resistance_candidates.extend(cluster["level"] for cluster in resistance_clusters)

        if low is not None:
            support_candidates.append(low)
        if open_price is not None:
            support_candidates.append(min(open_price, price))
            resistance_candidates.append(max(open_price, price))
        if high is not None:
            resistance_candidates.append(high)
        if range_low is not None:
            support_candidates.append(range_low)
        if range_high is not None:
            resistance_candidates.append(range_high)
        if ema_20 is not None:
            if ema_20 <= price:
                support_candidates.append(ema_20)
            else:
                resistance_candidates.append(ema_20)
        if ma_50 is not None:
            if ma_50 <= price:
                support_candidates.append(ma_50)
            else:
                resistance_candidates.append(ma_50)

        if not support_candidates:
            support_candidates.append(price * 0.97)
        if not resistance_candidates:
            resistance_candidates.append(price * 1.03)

        all_support_levels = self.sorted_levels(
            [level for level in support_candidates if level < price],
            reverse=True
        )
        all_resistance_levels = self.sorted_levels(
            [level for level in resistance_candidates if level > price]
        )

        support_levels = [
            level for level in all_support_levels
            if self._is_far_enough(price, level, "support")
        ]
        resistance_levels = [
            level for level in all_resistance_levels
            if self._is_far_enough(price, level, "resistance")
        ]

        confidence_reasons = []

        if not support_levels:
            support_levels = self.sorted_levels([price * 0.97, price * 0.94], reverse=True)
            confidence_reasons.append("support_levels_fallback_used")
        if not resistance_levels:
            resistance_levels = self.sorted_levels([price * 1.03, price * 1.06])
            confidence_reasons.append("resistance_levels_fallback_used")

        nearest_support = support_levels[0]
        nearest_resistance = resistance_levels[0]

        deeper_supports = [level for level in support_levels if level < nearest_support]
        if recent_swing_lows:
            swing_supports = self.sorted_levels([level for level in recent_swing_lows if level < nearest_support], reverse=True)
            invalidation = swing_supports[0] if swing_supports else None
        else:
            invalidation = None

        if invalidation is not None:
            invalidation = invalidation
        elif deeper_supports:
            invalidation = deeper_supports[0]
        elif range_low is not None and range_low < nearest_support:
            invalidation = range_low
        elif low is not None and low < nearest_support:
            invalidation = low
        else:
            invalidation = nearest_support * 0.97

        if len(structure_window) < self.MIN_BARS_FOR_STRUCTURE:
            confidence_reasons.append("insufficient_recent_bars")
        if len(support_clusters) < 1 or len(resistance_clusters) < 1:
            confidence_reasons.append("limited_swing_confirmation")
        if len(all_support_levels) < 2 or len(all_resistance_levels) < 2:
            confidence_reasons.append("limited_chart_structure")

        structure_confidence = "high"
        if confidence_reasons:
            structure_confidence = "low" if len(confidence_reasons) >= 2 else "medium"

        return {
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "nearest_support": self.round_price(nearest_support),
            "nearest_resistance": self.round_price(nearest_resistance),
            "breakout_level": self.round_price(nearest_resistance),
            "breakdown_level": self.round_price(nearest_support),
            "invalidation_level": self.round_price(invalidation),
            "local_range_high": self.round_price(range_high),
            "local_range_low": self.round_price(range_low),
            "range_width_pct": range_width_pct,
            "structure_label": structure_label,
            "recent_bar_count": len(structure_window),
            "structure_confidence": structure_confidence,
            "confidence_reasons": confidence_reasons,
            "swing_high_touches": [cluster["touches"] for cluster in resistance_clusters[:3]],
            "swing_low_touches": [cluster["touches"] for cluster in support_clusters[:3]]
        }

    def derive_volume_profile(self, chart_data):
        """Build a conservative volume profile from extracted chart data."""
        current_volume = chart_data.get("volume")
        if current_volume is None:
            return {
                "current_volume": None,
                "volume_vs_average": "unknown",
                "breakout_volume_signal": "unknown",
                "pullback_volume_signal": "unknown",
                "participation_label": "volume_unconfirmed",
                "notes": "Volume not extracted from chart."
            }

        return {
            "current_volume": current_volume,
            "volume_vs_average": "available",
            "breakout_volume_signal": "not_triggered",
            "pullback_volume_signal": "unknown",
            "participation_label": "volume_available",
            "notes": "Current candle volume extracted, but no historical average is available yet."
        }
