import json
from typing import Dict, Any

class FinancialStatementGrouper:
    """
    Group financial items by category_hint and section context.
    - Assets & Liabilities only from Statement of Financial Position
    - Equity from Statement of Changes in Equity
    - Income Statement Items from Statement of Profit or Loss
    - Other Indicators from remaining sections
    """

    def __init__(self, json_path: str):
        self.json_path = json_path
        self.data = self._load_json()

    def _load_json(self) -> Dict[str, Any]:
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def group_items(self) -> Dict[str, Any]:
        grouped = {
            "Assets": {"Current": {}, "Non-current": {}},
            "Liabilities": {"Current": {}, "Non-current": {}},
            "Equity": {},
            "Income Statement Items": {},
            "Other Indicators": {}
        }

        for section, content in self.data["key_metrics_by_section"].items():
            if section == "Statement of financial position":
                self._process_financial_position(content, grouped)
            elif section == "Statement of profit or loss":
                self._process_profit_or_loss(content, grouped)
            elif section == "Statement of changes in equity":
                self._process_equity_section(content, grouped)
            elif section == "Statement of cash flows":
                self._process_cash_flows(content, grouped)
            else:
                self._process_generic(content, grouped)

        return grouped

    # === SECTION HANDLERS ===
    def _process_financial_position(self, section_data: Dict[str, Any], grouped: Dict[str, Any]):
        """Handle balance sheet items (Assets & Liabilities)"""
        for item_name, item_data in section_data.items():
            if not isinstance(item_data, dict):
                continue
            hint = item_data.get("category_hint", "")
            if "Asset" in hint:
                if "Current" in hint:
                    grouped["Assets"]["Current"][item_name] = item_data
                else:
                    grouped["Assets"]["Non-current"][item_name] = item_data
            elif "Liabilit" in hint:
                if "Current" in hint:
                    grouped["Liabilities"]["Current"][item_name] = item_data
                else:
                    grouped["Liabilities"]["Non-current"][item_name] = item_data
            elif "Equity" in hint:
                grouped["Equity"][item_name] = item_data
            else:
                grouped["Other Indicators"][item_name] = item_data

    def _process_profit_or_loss(self, section_data: Dict[str, Any], grouped: Dict[str, Any]):
        """Handle Income Statement items"""
        for key, item_data in section_data.items():
            if isinstance(item_data, dict):
                # handle nested dicts like "statement_of_profit_or_loss_and_other_comprehensive_income"
                for sub_name, sub_item in item_data.items():
                    if isinstance(sub_item, dict) and "current_year" in sub_item:
                        grouped["Income Statement Items"][sub_name] = sub_item
            elif isinstance(item_data, list):
                for sub_item in item_data:
                    if isinstance(sub_item, dict):
                        grouped["Income Statement Items"][sub_item.get("name", key)] = sub_item

    def _process_equity_section(self, section_data: Any, grouped: Dict[str, Any]):
        """Handle equity statement"""
        if isinstance(section_data, dict) and "items" in section_data:
            for item in section_data["items"]:
                if isinstance(item, dict):
                    grouped["Equity"][item["name"]] = item
        elif isinstance(section_data, list):
            for item in section_data:
                if isinstance(item, dict):
                    grouped["Equity"][item["name"]] = item

    def _process_cash_flows(self, section_data: Dict[str, Any], grouped: Dict[str, Any]):
        """Handle Cash Flow items"""
        for key, item_data in section_data.items():
            if isinstance(item_data, dict):
                # if nested (e.g. Arus kas dari aktivitas operasi)
                for sub_name, sub_item in item_data.items():
                    if isinstance(sub_item, dict) and "current_year" in sub_item:
                        grouped["Other Indicators"][sub_name] = sub_item
            elif isinstance(item_data, dict) and "current_year" in item_data:
                grouped["Other Indicators"][key] = item_data

    def _process_generic(self, section_data: Dict[str, Any], grouped: Dict[str, Any]):
        """Fallback handler for any unclassified section"""
        if isinstance(section_data, dict):
            for name, item in section_data.items():
                if isinstance(item, dict):
                    grouped["Other Indicators"][name] = item

    def save_grouped_json(self, output_path: str, data: Dict[str, Any]):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Grouped financial data saved to {output_path}")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    grouper = FinancialStatementGrouper("report_2.json")
    grouped_result = grouper.group_items()
    grouper.save_grouped_json("grouped_report_v3.json", grouped_result)
    print(json.dumps(grouped_result, indent=2, ensure_ascii=False))
