# tests/test_html_parser.py
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ingestion.parsers.html_parser import parse_html

def test_parse_html_basic():
    sample_html = os.path.join(os.path.dirname(__file__), 'samples/testHTML.html')
    result = parse_html(sample_html)

    assert "doc_id" in result
    assert "sections" in result
    assert "metadata" in result
    assert "raw_text" in result

    assert result["metadata"]["file_type"] == "html"
