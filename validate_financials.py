import json
from typing import Dict, Any

class FinancialReportValidator:
    """
    Perform validation and sanity checks for extracted financial statement JSON.
    """

    def __init__(self, json_path: str):
        self.json_path = json_path
        self.data = self._load_json()

    def _load_json(self) -> Dict[str, Any]:
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _safe_sum(self, items: Dict[str, Any]) -> float:
        """Safely sum numeric values, ignoring None or invalid data."""
        total = 0.0
        for item in items.values():
            if isinstance(item, dict):
                val = item.get("current_year")
                if isinstance(val, (int, float)):
                    total += val
        return total

    def validate(self) -> Dict[str, Any]:
        report = self.data
        result = {
            "missing_values": [],
            "negative_values": [],
            "balance_check": {},
            "summary": {}
        }

        # === 1️⃣ Check missing or negative values ===
        for category, sections in report.items():
            if not isinstance(sections, dict):
                continue
            for subcat, items in sections.items():
                if not isinstance(items, dict):
                    continue
                for name, entry in items.items():
                    if not isinstance(entry, dict):
                        result["missing_values"].append(name)
                        continue
                    cy = entry.get("current_year")
                    if cy is None:
                        result["missing_values"].append(name)
                    elif isinstance(cy, (int, float)) and cy < 0:
                        result["negative_values"].append(name)

        # === 2️⃣ Compute total Assets / Liabilities / Equity ===
        total_assets = (
            self._safe_sum(report["Assets"].get("Current", {})) +
            self._safe_sum(report["Assets"].get("Non-current", {}))
        )
        total_liabilities = (
            self._safe_sum(report["Liabilities"].get("Current", {})) +
            self._safe_sum(report["Liabilities"].get("Non-current", {}))
        )
        total_equity = self._safe_sum(report.get("Equity", {}))

        # === 3️⃣ Balance sanity check ===
        if total_assets > 0:
            diff = abs(total_assets - (total_liabilities + total_equity))
            tolerance = 0.05 * total_assets  # ±5%
            balance_ok = diff <= tolerance
        else:
            balance_ok = False
            diff = None

        result["balance_check"] = {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "difference": diff,
            "tolerance_5pct": 0.05 * total_assets if total_assets else None,
            "is_balanced": balance_ok
        }

        # === 4️⃣ Summary ===
        result["summary"] = {
            "missing_count": len(result["missing_values"]),
            "negative_count": len(result["negative_values"]),
            "balance_ok": balance_ok
        }

        return result

    def save_validation_report(self, output_path: str, validation_result: Dict[str, Any]):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(validation_result, f, indent=2, ensure_ascii=False)
        print(f"✅ Validation report saved to {output_path}")


# === MAIN ===
if __name__ == "__main__":
    validator = FinancialReportValidator("grouped_report.json")
    result = validator.validate()
    validator.save_validation_report("validation_financial_report.json", result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
