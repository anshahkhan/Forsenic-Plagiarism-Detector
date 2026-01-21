import streamlit as st
import pdfplumber
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from io import BytesIO
import tempfile
import os
import requests
import re  # <--- REQUIRED FOR SMART MATCHING

# --- SAFE IMPORTS ---
try:
    from styles import CUSTOM_CSS
    from visuals_page import show_full_visuals
    from helpers import (
        random_full_hex, hex_to_rgba, text_contrast_color
    )
except ImportError:
    CUSTOM_CSS = ""
    def show_full_visuals(*args, **kwargs): pass
    def text_contrast_color(hex): return "#000000"
    def hex_to_rgba(hex, alpha): return hex
    def random_full_hex(): return "#FF0000"

# ---------- Page config ----------
st.set_page_config(
    layout="wide", 
    page_title="Plagiarism Detector", 
    page_icon="📄",
    initial_sidebar_state="collapsed"
)

# ---------- CSS ----------
HIDE_SIDEBAR_CSS = """
<style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    mark {
        border-radius: 3px;
        padding: 2px 0;
        color: transparent; 
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)

# ==========================================
#  SMART HIGHLIGHTING LOGIC
# ==========================================
def clean_text_for_regex(text):
    if not isinstance(text, str): return str(text)
    return text.replace('’', "'").replace('“', '"').replace('”', '"').replace('–', '-')

def smart_highlight(text, sentence_to_find, color, badge_html):
    if not sentence_to_find or len(sentence_to_find) < 5:
        return text
    clean_search = clean_text_for_regex(sentence_to_find).strip()
    pattern_str = re.escape(clean_search)
    pattern_str = pattern_str.replace(r'\ ', r'\s+')
    pattern = re.compile(pattern_str, re.IGNORECASE)
    text_color = text_contrast_color(color)
    replacement = f"{badge_html}<mark style='background-color:{color}; color:{text_color};'>\g<0></mark>"
    return pattern.sub(replacement, text)

# ---------- Backend API URL ----------
API_URL = "http://127.0.0.1:8000/pipeline/full"

def get_pipeline_output(uploaded_file):
    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        files = {
            "file": (
                getattr(uploaded_file, "name", "upload.pdf"),
                file_bytes,
                getattr(uploaded_file, "type", "application/pdf")
            )
        }
        response = requests.post(API_URL, files=files, timeout=120)

        if response.status_code != 200:
            st.error(f"Backend error {response.status_code}: {response.text}")
            return None

        data = response.json()
        if "module3" not in data or "results" not in data["module3"]:
            st.error("Invalid backend response: 'module3.results' missing.")
            return None
        return data

    except Exception as e:
        st.error(f"Request failed: {e}")
        return None

# ==========================================
#  STATE MANAGEMENT
# ==========================================
if "show_visuals_overlay" not in st.session_state:
    st.session_state["show_visuals_overlay"] = False
if "pipeline_data" not in st.session_state:
    st.session_state["pipeline_data"] = None
if "current_file_id" not in st.session_state:
    st.session_state["current_file_id"] = None

# ==========================================
#  PROFESSIONAL PDF CLASS
# ==========================================
class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Only show header on pages after the first one
        if self.page_no() > 1:
            self.set_fill_color(240, 242, 245)
            self.rect(0, 0, 210, 20, 'F')
            self.set_xy(15, 5)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(50, 50, 50)
            self.cell(0, 10, 'PLAGIARISM CHECKER REPORT', 0, 0, 'L')
            self.set_xy(150, 5)
            self.set_font('Arial', '', 9)
            self.set_text_color(100, 100, 100)
            self.cell(45, 10, pd.Timestamp.now().strftime('%b %d, %Y'), 0, 0, 'R')
            self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(33, 37, 41)
        self.cell(0, 8, clean_text_for_regex(label), 0, 1, 'L')
        self.set_draw_color(200, 200, 200)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(8)

# ==========================================
#  MAIN UI CODE
# ==========================================

st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
    <div style="font-size:34px;">📄</div>
    <div>
        <h1 style="margin:0; font-size: 28px;">Plagiarism Detector</h1>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("Upload a PDF. Matched sentences will be highlighted on the left and summarized in the right panel.")

left_col, right_col = st.columns([2.6, 1])

with left_col:
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

# --- PROCESS UPLOAD ---
if uploaded_pdf:
    file_id = uploaded_pdf.name + str(uploaded_pdf.size)
    if st.session_state["current_file_id"] != file_id:
        st.session_state["pipeline_data"] = None
        st.session_state["current_file_id"] = file_id
        st.session_state["show_visuals_overlay"] = False
        
        with st.spinner("Analyzing document..."):
            data = get_pipeline_output(uploaded_pdf)
            if data:
                st.session_state["pipeline_data"] = data
                st.rerun()

# --- LOAD DATA ---
pipeline_output = st.session_state.get("pipeline_data")
pages_html = []
any_match = False
overall_percent = 0
results = []
sentence_colors = {}
badge_numbers = {}

if pipeline_output and uploaded_pdf:
    try:
        module3_output = pipeline_output["module3"]
        results = module3_output["results"]
    except Exception as e:
        st.error(f"Data Error: {e}")
        st.stop()

    try:
        uploaded_pdf.seek(0)
        with pdfplumber.open(uploaded_pdf) as plumber_pdf:
            pages_raw = [p.extract_text() or "" for p in plumber_pdf.pages]
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
        st.stop()

    pastel_colors = ["#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF", "#B5B5FF", "#FFC6FF"]
    sentence_colors = {item["sentence"]: pastel_colors[i % len(pastel_colors)] for i, item in enumerate(results)}
    badge_numbers = {item["sentence"]: idx for idx, item in enumerate(results, start=1)}

    for raw in pages_raw:
        processed_html = clean_text_for_regex(raw)
        sorted_results = sorted(results, key=lambda x: len(x['sentence']), reverse=True)

        for item in sorted_results:
            sentence = item["sentence"]
            color = sentence_colors[sentence]
            badge_html = f"<sup style='display:inline-block;margin:0 2px;background:{color};color:{text_contrast_color(color)};padding:2px 5px;border-radius:4px;font-size:10px;font-weight:700'>{badge_numbers[sentence]}</sup>"
            processed_html = smart_highlight(processed_html, sentence, color, badge_html)
            if "<mark" in processed_html:
                any_match = True
        
        processed_html = processed_html.replace("\n", "<br>")
        pages_html.append(processed_html)

    per_result_max_scores = []
    for item in results:
        scs = [s.get("score", 0) for s in item.get("sources", []) if isinstance(s.get("score", None), (int, float))]
        per_result_max_scores.append(max(scs) if scs else 0.0)

    if per_result_max_scores:
        overall_percent = int(round(min(100.0, (sum(per_result_max_scores) / len(per_result_max_scores)) * 100.0)))

    # --- RIGHT PANEL ---
    with right_col:
        st.markdown(f"<div class='card sticky-panel'>", unsafe_allow_html=True)
        meter_color = "#dc3545" if overall_percent >= 80 else ("#ffc107" if overall_percent >= 50 else "#28a745")

        circle_html = f"""
        <div style="display:flex;align-items:center;justify-content:space-between; margin-bottom: 12px;">
            <div style="font-weight:700; font-size:18px; color: #343a40;">Match Overview</div>
            <div style="text-align:center">
                <div style="width:86px;height:86px;border-radius:50%;background:conic-gradient({meter_color} {overall_percent}%, #e9ecef {overall_percent}%);display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,0,0,0.1)">
                    <div style="background:#fff; width: 72px; height: 72px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <div style="font-size:22px;font-weight:800;color:#212529">{overall_percent}%</div>
                        <div style="font-size:12px;color:#6c757d; font-weight: 500;">Overall</div>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(circle_html, unsafe_allow_html=True)

        st.markdown(f"""
            <div style="height:8px;background:#e9ecef;border-radius:8px;margin-top:10px;margin-bottom:20px">
                <div style="width:{overall_percent}%;height:8px;border-radius:8px;background:linear-gradient(90deg,{meter_color},#e9ecef)"></div>
            </div>
        """, unsafe_allow_html=True)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔍 Visuals"):
                st.session_state.show_visuals_overlay = True
                st.rerun()
        
        with col_btn2:
            generate_pdf = st.button("📄 Report")

        # ==========================================
        # 🔥 UPDATED PDF GENERATION LOGIC
        # ==========================================
        if generate_pdf:
            try:
                pdf = PDFReport()
                pdf.add_page()

                # --- 1. BETTER TITLE PAGE ---
                # Add a border around the page
                pdf.set_draw_color(50, 50, 50)
                pdf.set_line_width(1)
                pdf.rect(10, 10, 190, 277)

                pdf.set_y(60)
                pdf.set_font("Arial", "B", 30)
                pdf.set_text_color(33, 37, 41)
                pdf.cell(0, 15, "Similarity Report", ln=True, align="C")
                
                pdf.set_font("Arial", "", 12)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 10, f"Generated on {pd.Timestamp.now().strftime('%B %d, %Y')}", ln=True, align="C")
                pdf.ln(20)

                # Center the Score Box
                pdf.set_fill_color(248, 249, 250)
                pdf.set_draw_color(220, 220, 220)
                # Calculate center X for a box of width 80
                x_pos = (210 - 80) / 2
                pdf.rect(x_pos, 110, 80, 50, 'FD')
                
                pdf.set_y(120)
                pdf.set_font("Arial", "B", 45)
                # Color logic
                if overall_percent >= 80: pdf.set_text_color(220, 53, 69)
                elif overall_percent >= 50: pdf.set_text_color(255, 193, 7)
                else: pdf.set_text_color(40, 167, 69)

                pdf.cell(0, 15, f"{overall_percent}%", ln=True, align="C")
                
                pdf.set_font("Arial", "B", 10)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 10, "OVERALL SIMILARITY SCORE", ln=True, align="C")

                pdf.ln(40)
                pdf.set_font("Arial", "", 10)
                pdf.set_text_color(50, 50, 50)

                pdf.add_page() # Start content on new page

                # --- 2. EXECUTIVE SUMMARY & GRAPH ---
                pdf.chapter_title("Executive Summary")
                pdf.set_font("Arial", "", 11)
                pdf.set_text_color(50, 50, 50)
                pdf.multi_cell(0, 6, 
                    f"A detailed similarity scan was performed on this document, resulting in {len(results)} detected matches. "
                    f"The analysis below visualizes the strength of each match found in our database."
                )
                pdf.ln(10)

                df_chart = pd.DataFrame([
                    {"Sentence": f"Match {idx+1}", "Max Score": round(max([s.get("score",0) for s in item.get("sources", [])])*100,1)} 
                    for idx, item in enumerate(results)
                ])
                
                # Graph Generation
                try:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=df_chart["Sentence"],
                        y=df_chart["Max Score"],
                        marker_color='#2c3e50',
                        text=df_chart["Max Score"].apply(lambda x: f"{x}%"),
                        textposition='auto',
                    ))
                    fig.update_layout(
                        title={'text': "<b>Similarity Score Distribution</b>", 'y':0.9, 'x':0.5},
                        font=dict(family="Arial, sans-serif", size=12, color="#333"),
                        plot_bgcolor='white'
                    )
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                        fig.write_image(tmp_file.name, scale=2)
                        tmp_name = tmp_file.name
                    pdf.image(tmp_name, x=15, w=180)
                    os.remove(tmp_name)
                except Exception as e:
                    pdf.set_font("Arial", "I", 10)
                    pdf.cell(0, 10, f"Graph unavailable: {e}", ln=True)

                pdf.ln(10)
                pdf.add_page()

                # --- 3. DETAILED MATCHES WITH METADATA ---
                pdf.chapter_title("Detailed Matches & Sources")
                
                for idx, item in enumerate(results, start=1):
                    sentence = item["sentence"]
                    max_score = max([s.get("score",0) for s in item.get("sources", [])])*100 if item.get("sources") else 0
                    
                    # Highlight Box
                    pdf.set_fill_color(240, 245, 255)
                    pdf.set_draw_color(200, 210, 230)
                    pdf.rect(15, pdf.get_y(), 180, 12, 'FD')
                    
                    pdf.set_xy(18, pdf.get_y()+3)
                    pdf.set_font("Arial", "B", 10)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(100, 6, f"Match #{idx}", 0, 0)

                    if max_score > 80: pdf.set_text_color(220, 53, 69)
                    elif max_score > 50: pdf.set_text_color(255, 193, 7)
                    else: pdf.set_text_color(40, 167, 69)
                    
                    pdf.cell(70, 6, f"{int(max_score)}% Similarity", 0, 1, 'R')
                    pdf.ln(6)
                    
                    # Sentence Text
                    pdf.set_font("Arial", "I", 10)
                    pdf.set_text_color(60, 60, 60)
                    pdf.multi_cell(0, 6, f"\"{clean_text_for_regex(sentence)}\"")
                    pdf.ln(4)

                    # SOURCES with METADATA
                    for s in item.get("sources", []):
                        url_txt = s.get("source_url","")
                        metadata = s.get('metadata', {})
                        
                        # Extract Meta
                        author = metadata.get('author', 'Unknown Author')
                        date = metadata.get('publication_date', 'Unknown Date')
                        citation = metadata.get('citation', 'No Citation Available')
                        
                        score_txt = f"{int(s.get('score',0)*100)}%"
                        
                        # URL Line
                        pdf.set_font("Arial", "B", 9)
                        pdf.set_text_color(0, 102, 204) # Blue for URL
                        pdf.cell(145, 5, f"Source URL: {clean_text_for_regex(url_txt[:70])}", 0, 0)
                        pdf.set_text_color(0, 0, 0)
                        pdf.cell(35, 5, score_txt, 0, 1, 'R')
                        
                        # Metadata Line
                        pdf.set_font("Arial", "", 8)
                        pdf.set_text_color(100, 100, 100)
                        meta_str = f"Author: {clean_text_for_regex(str(author))} | Date: {clean_text_for_regex(str(date))} | Ref: {clean_text_for_regex(str(citation))[:40]}..."
                        pdf.cell(0, 5, meta_str, ln=True)
                        pdf.ln(2)
                    
                    pdf.ln(5) # Space between matches

                pdf.add_page()

                # --- 4. INTELLIGENT RECOMMENDATIONS ---
                pdf.chapter_title("Assessment & Recommendations")
                
                # Dynamic Logic based on Overall Score
                if overall_percent >= 80:
                    status = "CRITICAL"
                    status_color = (220, 53, 69) # Red
                    intro_text = "This document contains a very high level of similarity (>80%). It is strongly recommended to rewrite significant portions of the text."
                    recs_list = [
                        ("Immediate Revision", "Major sections appear identical to external sources. Rewrite entirely."),
                        ("Academic Integrity", "Review citations carefully; this level of matching often indicates copy-pasting."),
                        ("Synthesizing", "Try to read sources and write your understanding without looking at the source text.")
                    ]
                elif overall_percent >= 50:
                    status = "WARNING"
                    status_color = (255, 193, 7) # Yellow
                    intro_text = "This document contains moderate similarity (50-80%). Substantial paraphrasing and citation checks are required."
                    recs_list = [
                        ("Paraphrasing", "Change sentence structures and vocabulary while keeping the meaning."),
                        ("Direct Quotes", "Ensure direct quotes are enclosed in quotation marks and cited."),
                        ("Summarization", "Condense long paragraphs from sources into shorter summaries in your own words.")
                    ]
                else:
                    status = "PASSING"
                    status_color = (40, 167, 69) # Green
                    intro_text = "This document has a low similarity score (<50%). Matches found are likely common definitions or properly cited references."
                    recs_list = [
                        ("Standard Check", "Verify that the detected matches are indeed common knowledge or cited."),
                        ("Formatting", "Ensure bibliography follows the required format (APA, MLA, etc.).")
                    ]

                # Status Badge in PDF
                pdf.set_font("Arial", "B", 12)
                pdf.set_text_color(*status_color)
                pdf.cell(0, 10, f"STATUS: {status}", ln=True)
                pdf.ln(5)

                pdf.set_font("Arial", "", 11)
                pdf.set_text_color(50, 50, 50)
                pdf.multi_cell(0, 6, intro_text)
                pdf.ln(10)

                # Loop through Recommendations
                for title, desc in recs_list:
                    pdf.set_font("Arial", "B", 11)
                    pdf.set_text_color(33, 37, 41)
                    pdf.cell(0, 7, f"- {title}", ln=True)
                    
                    pdf.set_font("Arial", "", 10)
                    pdf.set_text_color(80, 80, 80)
                    pdf.multi_cell(0, 6, desc)
                    pdf.ln(4)

                # Output
                pdf_output = pdf.output(dest="S")
                if isinstance(pdf_output, str):
                    pdf_content = pdf_output.encode("latin-1", errors="replace")
                else:
                    pdf_content = pdf_output

                st.success("Report Generated Successfully!")
                st.download_button(
                    label="📥 Download Professional Report",
                    data=BytesIO(pdf_content),
                    file_name="Professional_Similarity_Report.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown("---")

        # --- MATCH CARDS (Original UI) ---
        for item in results:
            sentence = item["sentence"]
            s_color = sentence_colors.get(sentence, "#DDD")
            s_rgba = hex_to_rgba(s_color, alpha=0.08)
            s_text_color = text_contrast_color(s_color)
            scs = [s.get("score", 0) for s in item.get("sources", [])]
            max_pct = int(round(max(scs) * 100)) if scs else 0

            card_html = f"""
            <div style="border-left:6px solid {s_color}; background:{s_rgba}; padding:14px; border-radius:8px; margin-bottom:15px; border:1px solid #f1f3f5;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div style="max-width:72%">
                        <div style="font-weight:600;color:#343a40;margin-bottom:8px; font-size: 14px;">
                            Match {badge_numbers[sentence]} —
                            <span style="background:{s_color}; color:{s_text_color}; padding:4px 8px; border-radius:6px; font-weight: 700;">{clean_text_for_regex(sentence)}</span>
                        </div>
                    </div>
                    <div style="text-align:right">
                        <div class="match-strength-box">{max_pct}%</div>
                        <div style="font-size:11px;color:#6c757d;margin-top:4px;text-align:right">Match Strength</div>
                    </div>
                </div>
                <div style="margin-top:15px">
                    <div style="font-size:14px;color:#495057;font-weight:600;margin-bottom:8px">Sources</div>
            """

            for s in item.get("sources", []):
                u = s.get("source_url")
                score = s.get("score", 0)
                url_pct = int(round(score * 100))
                
                if url_pct > 80: severity_color = "#dc3545"
                elif url_pct >= 50: severity_color = "#fd7e14"
                else: severity_color = "#ffc107"
                
                card_html += f"""
<div style="display:flex;align-items:flex-start;justify-content:space-between;padding:8px 0 8px 12px; border-top:1px solid #e9ecef; border-left: 4px solid {severity_color}; flex-wrap: wrap;">
    <div style="display:flex;flex-direction:column; gap:6px; max-width:75%;">
        <a href="{u}" target="_blank" style="font-size:13px; color:#0d6efd; word-break: break-all;">{u}</a>
        <details style="font-size:13px;">
            <summary style="cursor:pointer; font-weight:600; color:#495057;">Show Metadata</summary>
            <div style="font-size:11px;color:#6c757d; margin-top:4px; padding-left:8px; background: #fff; padding: 5px; border-radius: 4px;">
                <strong>Source:</strong> {clean_text_for_regex(s.get('source_text','N/A'))}<br>
                <strong>Author:</strong> {s['metadata'].get('author','N/A')}<br>
                <strong>Date:</strong> {s['metadata'].get('publication_date','N/A')}<br>
                <strong>Citation:</strong> {s['metadata'].get('citation','N/A')}
            </div>
        </details>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end">
        <div class="match-strength-box" style="font-size:12px; padding: 2px 6px;">{url_pct}%</div>
    </div>
</div>
"""
            card_html += "</div></div>"
            st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# --- LEFT COLUMN (Document Display) ---
with left_col:
    st.header("Document View")
    if uploaded_pdf and pipeline_output:
        if not any_match:
            st.info("No text matches found for this document.")
        for i, html in enumerate(pages_html, start=1):
            with st.expander(f"Page {i}", expanded=True):
                st.markdown(f"<div class='card pdf-text' style='line-height:1.6; font-family:sans-serif;'>{html}</div>", unsafe_allow_html=True)

# --- VISUALS OVERLAY ---
if st.session_state.get("show_visuals_overlay") and pipeline_output:
    overlay = st.container()
    with overlay:
        st.markdown("---")
        col_h1, col_h2 = st.columns([10, 1])
        col_h1.header("Detailed Visual Analytics")
        if col_h2.button("❌ Close"):
            st.session_state.show_visuals_overlay = False
            st.rerun()

        df_chart = pd.DataFrame([
            {
                "Match ID": idx + 1,
                "Sentence": item["sentence"],
                "Max Score (%)": round(max([s.get("score",0) for s in item.get("sources", [])])*100,1) if item.get("sources") else 0,
                "Color": sentence_colors.get(item["sentence"], "#007AFF"),
            }
            for idx, item in enumerate(module3_output["results"])
        ])
        show_full_visuals(df_chart, module3_output)