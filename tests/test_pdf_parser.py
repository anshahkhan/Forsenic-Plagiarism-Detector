# tests/test_pdf_parser.py
import sys
import os
import pytest

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ingestion.parsers.pdf_parser import parse_pdf

def test_parse_pdf_basic():
    # Path to a sample PDF for testing
    sample_pdf = os.path.join(os.path.dirname(__file__), 'samples/testPDF2.pdf')
    result = parse_pdf(sample_pdf, ocr_if_no_text=False)

    # Check that required keys exist
    assert "doc_id" in result
    assert "sections" in result
    assert "metadata" in result
    assert "raw_text" in result
    assert "images" in result

    # Metadata sanity checks
    assert result["metadata"]["file_type"] == "pdf"
    assert result["metadata"]["num_pages"] > 0
