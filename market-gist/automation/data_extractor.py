"""
Extract and parse data from screenshots and snapshots
"""
import json
import re
from datetime import datetime


class DataExtractor:
    def __init__(self):
        pass
    
    def parse_ohlcv_from_text(self, text):
        """Parse OHLCV data from text"""
        data = {}
        
        # Pattern: O530.00 H535.00 L515.00 C516.00 −11.00 (−2.09%)
        patterns = {
            "open": r"O([\d,\.]+)",
            "high": r"H([\d,\.]+)",
            "low": r"L([\d,\.]+)",
            "close": r"C([\d,\.]+)",
            "change": r"[−\-]([\d,\.]+)\s*\(",
            "change_pct": r"\((−|-)?([\d,\.]+)%\)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                if key == "change_pct":
                    value = float(match.group(2).replace(",", ""))
                    if match.group(1):  # Negative sign
                        value = -value
                    data[key] = value
                else:
                    value = match.group(1).replace(",", "")
                    data[key] = float(value)
        
        return data
    
    def parse_volume_from_text(self, text):
        """Parse volume from text like '585.772K' or '34.961B'"""
        match = re.search(r"([\d,\.]+)([KMB])", text)
        if match:
            value = float(match.group(1).replace(",", ""))
            unit = match.group(2)
            
            multipliers = {"K": 1000, "M": 1000000, "B": 1000000000}
            return int(value * multipliers.get(unit, 1))
        
        return None
    
    def parse_indicator_from_text(self, text, indicator_type):
        """Parse indicator values from text"""
        data = {}
        
        if indicator_type == "ema" or indicator_type == "ma":
            # Pattern: EMA 20 close 0 "587.52"
            match = re.search(r'"([\d,\.]+)"', text)
            if match:
                data["value"] = float(match.group(1).replace(",", ""))
        
        elif indicator_type == "macd":
            # Pattern: MACD 12 26 close 9 "2.68" −91.92 −94.60
            matches = re.findall(r'"?(−|-)?([\d,\.]+)"?', text)
            if len(matches) >= 3:
                data["macd_line"] = float(matches[0][1].replace(",", ""))
                
                signal = float(matches[1][1].replace(",", ""))
                if matches[1][0]:
                    signal = -signal
                data["signal_line"] = signal
                
                histogram = float(matches[2][1].replace(",", ""))
                if matches[2][0]:
                    histogram = -histogram
                data["histogram"] = histogram
        
        elif indicator_type == "rsi":
            # Pattern: RSI 14 "37.75"
            match = re.search(r'"([\d,\.]+)"', text)
            if match:
                data["value"] = float(match.group(1).replace(",", ""))
        
        return data
    
    def extract_from_screenshot_metadata(self, screenshot_path):
        """
        Extract data from screenshot filename and associated metadata
        This is a placeholder - in practice, you'd use OCR or manual annotation
        """
        # For now, return empty dict
        # In production, you could use pytesseract for OCR
        return {}
    
    def create_extraction_record(self, symbol, timeframe, data, evidence_refs):
        """Create a structured extraction record"""
        return {
            "extraction_metadata": {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "source": "nepsealpha.com",
                "extraction_method": "automated",
                "data_quality": "high_confidence"
            },
            "data": data,
            "evidence_refs": evidence_refs
        }
