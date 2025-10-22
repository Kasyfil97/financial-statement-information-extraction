import re
import json
from typing import Dict, Any

# === SECTION SEGMENTATION & CATEGORIZATION ===
class SectionSegmenter:
    """
    Segment by statement type and categorize into meaningful financial groups
    (based on Fineksi test requirement)
    """

    def __init__(self, raw_text: str, chunk_size: int = 5000):
        self.raw_text = raw_text
        self.chunk_size = chunk_size

    def _extract_section(self, pattern: str) -> str:
        match = re.search(pattern, self.raw_text, re.IGNORECASE)
        if not match:
            return ""
        start = match.start()
        next_match = re.search(r'\nStatement of|Laporan|Notes to|Catatan|--- PAGE', self.raw_text[start + 100:], re.IGNORECASE)
        end = next_match.start() + start + self.chunk_size if next_match else len(self.raw_text)
        return self.raw_text[start:end]

    def __call__(self) -> Dict[str, str]:
        """
        Segment by statement type and categorize into meaningful financial groups
        (based on Fineksi test requirement)
        """
        sections = {
            "Statement of financial position": self._extract_section("Statement of financial position|Laporan posisi keuangan"),
            "Statement of profit or loss": self._extract_section("Statement of profit or loss|Laporan laba rugi"),
            "Statement of cash flows": self._extract_section("Statement of cash flows|Laporan arus kas"),
            "Statement of changes in equity": self._extract_section("Statement of changes in equity|Laporan perubahan ekuitas"),
        }

        return {k: v for k, v in sections.items() if v.strip()}
