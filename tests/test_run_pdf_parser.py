import sys
import os

# Add the src folder to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ingestion.parsers.pdf_parser import parse_pdf
import json

pdf_path = "../tests/samples/testPDF2.pdf"

result = parse_pdf(pdf_path, ocr_if_no_text=True)

print(json.dumps(result, indent=2))
