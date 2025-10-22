import asyncio
import PyPDF2
import json
import datetime
import argparse
import logging
from pathlib import Path
from typing import Dict, Any
from src.loadyaml import load_yaml
from src.config import load_config

from src.llm_client import LLMClient
from src.section_segmenter import SectionSegmenter
from src.extractor import Extractor

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for i, page in enumerate(reader.pages):
            text += f"\n--- PAGE {i + 1} ---\n"
            text += page.extract_text() or ""
    return text

def save_json(output_path: str, data: Dict[str, Any]):
    """Save extracted data to JSON file"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Saved extracted data to %s", output_path)

async def main(pdf_path: str, output_path: str) -> Dict[str, Any]:
    """Main process orchestration"""
    config = load_config()
    logger.info("Starting Financial Statement Extraction Pipeline")
    logger.debug("Initiate LLM client with config keys: %s", list(config))
    llm_client = LLMClient(config['llm'])

    logger.info("Extracting text from PDF: %s", pdf_path)
    text = extract_text_from_pdf(pdf_path)

    logger.info("Segmenting and categorizing financial sections")
    sections = SectionSegmenter(text, chunk_size=config['section_segmenter']['chunk_size'])()

    logger.info("Extracting key metrics per section using LLM model %s", config['llm']['model'])
    extractor = Extractor(llm_client, sections)
    prompt_config = config['prompts']
    prompt_input = load_yaml(prompt_config['file'])[prompt_config['key']]
    key_metrics = await extractor.extract(prompt_input=prompt_input, sections=sections, temperature=prompt_config.get('temperature', 0.1))

    result = {
        "source_file": Path(pdf_path).name,
        "extraction_date": datetime.date.today().isoformat(),
        "sections": list(sections.keys()),
        "key_metrics_by_section": key_metrics
    }

    save_json(output_path, result)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description='Extract financial data from PDF statements')
    parser.add_argument('--pdf', type=str, required=True, help='Path to PDF file')
    parser.add_argument('--output', type=str, default='report.json',
                        help='Output JSON file path (default: report.json)')

    args = parser.parse_args()
    pdf_path = args.pdf
    output_path = args.output

    try:
        result = asyncio.run(main(pdf_path, output_path))
        logger.info("Pipeline finished successfully")
        logger.debug("Result: %s", json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        raise
