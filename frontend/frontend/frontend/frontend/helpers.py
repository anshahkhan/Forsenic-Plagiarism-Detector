import random
import colorsys
import re
import pandas as pd
from html import escape

URL_COLOR_CHOICES = ["#FF6B6B", "#FFA94D", "#FFD066"]

def random_full_hex():
    h = random.random()
    s = 0.55 + random.random() * 0.35
    l = 0.45 + random.random() * 0.12
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))

def hex_to_rgba(hex_color, alpha=0.18):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def text_contrast_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    lum = 0.2126*r + 0.7152*g + 0.0722*b
    return '#000' if lum > 0.6 else '#fff'

def url_color_choice():
    return random.choice(URL_COLOR_CHOICES)

def clean_pdf_text(text):
    """Fix PDF junk characters and remove invisible unicode."""
    if not text:
        return ""
    # Remove control characters except newlines
    text = re.sub(r"[\x00-\x08\x0B-\x1F\x7F]", "", text)
    # Replace suspicious unknown chars
    text = text.replace("\u25A1", "")   # white square
    text = text.replace("\uf0b7", "")   # PDF bullet
    text = text.replace("\u2022", "•")  # normalize bullets
    return text

def build_fuzzy_pattern(sentence):
    return r'\s+'.join(re.escape(word) for word in sentence.split())

def highlight_sentence_in_text(page_text, sentence, color, badge_html):
    if not sentence.strip():
        return escape(page_text)

    # Clean and escape entire PDF page
    page_text = clean_pdf_text(page_text)
    safe_page = escape(page_text)

    # Prepare highlight span
    txt_color = text_contrast_color(color)
    safe_sentence = escape(sentence)
    replacement = (
        f"<span style='background:{color}; color:{txt_color}; "
        f"padding:2px 6px; border-radius:6px'>{safe_sentence}{badge_html}</span>"
    )

    # Build regex
    pattern = build_fuzzy_pattern(sentence)

    # Replace inside the escaped page
    highlighted = re.sub(
        pattern,
        replacement,
        safe_page,
        flags=re.IGNORECASE
    )

    return highlighted

def create_match_dataframe(module3_data, sentence_colors):
    chart_data = []
    for idx, item in enumerate(module3_data["results"], start=1):
        scs = [
            s.get("score", 0)
            for s in item.get("sources", [])
            if isinstance(s.get("score", None), (int, float))
        ]
        max_score = max(scs) if scs else 0.0
        max_score_pct = int(round(max_score * 100))

        max_source_url = "N/A"
        if item.get("sources"):
            max_source = max(item["sources"], key=lambda s: s.get("score", 0))
            max_source_url = max_source.get("source_url", "N/A")

        chart_data.append({
            "Match ID": f"Match {idx}",
            "Sentence": item["sentence"],
            "Max Score (%)": max_score_pct,
            "Color": sentence_colors.get(item["sentence"], "#CCCCCC"),
            "Max Source": max_source_url,
        })

    return pd.DataFrame(chart_data)
