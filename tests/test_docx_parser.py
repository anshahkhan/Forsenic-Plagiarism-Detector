# tests/test_docx_parser.py
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ingestion.parsers.docx_parser import parse_docx

def test_parse_docx_basic():
    sample_docx = os.path.join(os.path.dirname(__file__), 'samples/testWord.docx')
    result = parse_docx(sample_docx)

    assert "doc_id" in result
    assert "sections" in result
    assert "metadata" in result
    assert "raw_text" in result

    assert result["metadata"]["file_type"] == "docx"
