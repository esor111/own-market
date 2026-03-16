"""
Generate normalized JSON files from templates
"""
import json
import os
from datetime import datetime
from config import TEMPLATES_DIR, NORMALIZED_DIR, FEATURES_DIR, RAW_TABLES_DIR


class FileGenerator:
    def __init__(self, session_id, run_date):
        self.session_id = session_id
        self.run_date = run_date
        self.timestamp = datetime.now().isoformat()
    
    def load_template(self, template_name):
        """Load a JSON template"""
        template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.template.json")
        with open(template_path, 'r') as f:
            return json.load(f)
    
    def save_json(self, data, filepath):
        """Save data as JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Created: {filepath}")
    
    def generate_session_record(self, symbol, stages_completed, stages_skipped, notes):
        """Generate session record"""
        template = self.load_template("session")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "captured_at": self.timestamp,
            "symbol": symbol,
            "status": "completed",
            "stages_completed": stages_completed,
            "stages_skipped": stages_skipped,
            "notes": notes
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "sessions", f"{self.run_date}__{symbol}__session_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_market_record(self, market_data, evidence_refs):
        """Generate market record"""
        template = self.load_template("market")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "captured_at": self.timestamp,
            "close": market_data.get("close"),
            "change_pct": market_data.get("change_pct"),
            "trend_label": market_data.get("trend_label", ""),
            "market_phase": market_data.get("market_phase", ""),
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "market", f"{self.run_date}__NEPSE__1D__market_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_sector_record(self, sector_name, sector_data, evidence_refs):
        """Generate sector record"""
        template = self.load_template("sector")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "captured_at": self.timestamp,
            "sector_name": sector_name,
            "timeframe": sector_data.get("timeframe", "1W"),
            "close": sector_data.get("close"),
            "change_pct": sector_data.get("change_pct"),
            "trend_label": sector_data.get("trend_label", ""),
            "relative_strength_vs_market": sector_data.get("rs_vs_market", ""),
            "notes": sector_data.get("notes"),
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "sectors", f"{self.run_date}__{sector_name}__sector_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_stock_chart_record(self, symbol, timeframe, chart_data, evidence_refs):
        """Generate stock chart record"""
        template = self.load_template("stock_chart")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "captured_at": self.timestamp,
            "symbol": symbol,
            "timeframe": timeframe,
            "close": chart_data.get("close"),
            "open": chart_data.get("open"),
            "high": chart_data.get("high"),
            "low": chart_data.get("low"),
            "volume": chart_data.get("volume"),
            "trend_label": chart_data.get("trend_label", ""),
            "structure_label": chart_data.get("structure_label", ""),
            "swing_highs": chart_data.get("swing_highs", []),
            "swing_lows": chart_data.get("swing_lows", []),
            "support_zones": chart_data.get("support_zones", []),
            "resistance_zones": chart_data.get("resistance_zones", []),
            "location_label": chart_data.get("location_label", ""),
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "stocks", f"{self.run_date}__{symbol}__{timeframe}__stock_chart_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_indicator_record(self, symbol, timeframe, indicator_data, evidence_refs):
        """Generate indicator record"""
        template = self.load_template("indicator")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "captured_at": self.timestamp,
            "symbol": symbol,
            "timeframe": timeframe,
            "ema_20": indicator_data.get("ema_20"),
            "ma_50": indicator_data.get("ma_50"),
            "ma_200": indicator_data.get("ma_200"),
            "rsi": indicator_data.get("rsi"),
            "macd_line": indicator_data.get("macd_line"),
            "signal_line": indicator_data.get("signal_line"),
            "histogram": indicator_data.get("histogram"),
            "price_above_ema_20": indicator_data.get("price_above_ema_20"),
            "price_above_ma_50": indicator_data.get("price_above_ma_50"),
            "momentum_label": indicator_data.get("momentum_label", ""),
            "notes": indicator_data.get("notes"),
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "indicators", f"{self.run_date}__{symbol}__{timeframe}__indicator_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_volume_record(self, symbol, timeframe, volume_data, evidence_refs):
        """Generate volume record"""
        template = self.load_template("volume")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "symbol": symbol,
            "timeframe": timeframe,
            "current_volume": volume_data.get("current_volume"),
            "volume_vs_average": volume_data.get("volume_vs_average", ""),
            "participation_label": volume_data.get("participation_label", ""),
            "notes": volume_data.get("notes"),
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "stocks", f"{self.run_date}__{symbol}__{timeframe}__volume_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_relative_strength_record(self, symbol, rs_data, evidence_refs):
        """Generate relative strength record"""
        template = self.load_template("relative_strength")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "symbol": symbol,
            "benchmark_sector": rs_data.get("benchmark_sector", ""),
            "rs_vs_market_label": rs_data.get("rs_vs_market_label", ""),
            "rs_vs_sector_label": rs_data.get("rs_vs_sector_label", ""),
            "rs_notes": rs_data.get("rs_notes"),
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "relative_strength", f"{self.run_date}__{symbol}__relative_strength_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_feature_score_record(self, symbol, scores, evidence_refs):
        """Generate feature score record"""
        template = self.load_template("feature_score")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "symbol": symbol,
            "scores": scores.get("individual", {}),
            "score_total": scores.get("total"),
            "score_max": scores.get("max"),
            "score_percent": scores.get("percent"),
            "notes": scores.get("notes"),
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(FEATURES_DIR, "setup_scores", f"{self.run_date}__{symbol}__feature_score_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_decision_record(self, symbol, decision_data, evidence_refs):
        """Generate decision record"""
        template = self.load_template("decision")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "captured_at": self.timestamp,
            "symbol": symbol,
            "setup_type": decision_data.get("setup_type", ""),
            "score": decision_data.get("score"),
            "score_max": decision_data.get("score_max", 100),
            "confidence": decision_data.get("confidence"),
            "action": decision_data.get("action", ""),
            "entry_zone": decision_data.get("entry_zone", []),
            "stop_loss": decision_data.get("stop_loss"),
            "invalidation_level": decision_data.get("invalidation_level"),
            "targets": decision_data.get("targets", []),
            "risk_reward_ratio": decision_data.get("risk_reward_ratio"),
            "why": decision_data.get("why", []),
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "decisions", f"{self.run_date}__{symbol}__decision_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_event_record(self, symbol, event_found, evidence_refs, notes=""):
        """Generate event record (or no-event record)"""
        template = self.load_template("event")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "symbol": symbol,
            "event_found": event_found,
            "notes": notes or "No corporate actions or significant events found during chart review.",
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "events", f"{self.run_date}__{symbol}__event_v2.json")
        self.save_json(template, filepath)
        return filepath
    
    def generate_broker_flow_record(self, symbol, data_available, evidence_refs, reason=""):
        """Generate broker flow record (or unavailable record)"""
        template = self.load_template("broker_flow")
        template.update({
            "session_id": self.session_id,
            "run_date": self.run_date,
            "symbol": symbol,
            "data_available": data_available,
            "unavailable_reason": reason or "floorsheet_requires_login",
            "notes": "Floorsheet data requires authentication. Cannot access without login.",
            "evidence_refs": evidence_refs
        })
        
        filepath = os.path.join(NORMALIZED_DIR, "broker_flow", f"{self.run_date}__{symbol}__broker_flow_v2.json")
        self.save_json(template, filepath)
        return filepath
