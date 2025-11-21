# src/ingestion/cli.py
import argparse
import sys
from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .html_parser import parse_html
import json

def main(argv=None):
    parser = argparse.ArgumentParser("df-ingest")
    parser.add_argument("path", help="Path to document to ingest")
    parser.add_argument("--type", choices=["pdf", "docx", "html"], required=True)
    parser.add_argument("--ocr", action="store_true", help="Enable OCR fallback for PDFs")
    args = parser.parse_args(argv)

    if args.type == "pdf":
        res = parse_pdf(args.path, ocr_if_no_text=args.ocr)
    elif args.type == "docx":
        res = parse_docx(args.path)
    elif args.type == "html":
        res = parse_html(args.path)
    else:
        print("Unsupported type", file=sys.stderr)
        sys.exit(2)

    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
