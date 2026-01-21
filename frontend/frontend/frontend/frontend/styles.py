# styles.py

CUSTOM_CSS = """
<style>
/* 1️⃣ General Page Styling */
.stApp { 
    background: #f8f9fa; 
    color: #343a40; 
    font-family: "Segoe UI", Roboto, Arial, sans-serif; 
}
html, body, [class*="css"]  { font-family: "Segoe UI", Roboto, Arial, sans-serif; }

/* 2️⃣ Card Styling */
.card { 
    background: #ffffff; 
    border-radius: 12px; 
    padding: 20px; 
    box-shadow: 0 4px 16px rgba(0,0,0,0.08); 
    border: 1px solid #e9ecef; 
}

/* 3️⃣ Headings */
h1, h2, h3, h4, h5 { 
    color: #343a40; 
    font-weight: 700; 
    margin-top: 0.5em; 
}

/* 4️⃣ PDF Viewer Styling */
.pdf-text { 
    font-family: "Segoe UI", Roboto, Arial, monospace; 
    color: #212529; 
    font-size: 14px; 
    line-height: 1.6; 
    background: #fff; 
    border-radius: 10px; 
    box-shadow: 0 3px 8px rgba(0,0,0,0.05);
    border: 1px solid #e9ecef; 
    padding: 12px;
    margin-bottom: 15px;
}

/* Sticky Panel */
.sticky-panel { 
    position: sticky; 
    top: 20px; 
}

/* 5️⃣ Match Strength Box */
.match-strength-box {
    background: #f8f9fa; 
    border: 1px solid #e9ecef;
    padding: 6px 12px;
    border-radius: 8px;
    font-weight: 800;
    color: #212529;
    font-size: 16px;
    text-align: center;
}

/* Source Link Styling */
.source-link a {
    color: #495057; 
    font-weight: 500;
    text-decoration: none;
}
.source-link a:hover {
    color: #0d6efd; 
    text-decoration: underline;
}

/* 6️⃣ File Uploader Dark Theme */
[data-testid="stFileUploaderDropzone"], 
.stFileUploader div[data-testid="stFileUploaderDropzone"] {
    background: #343a40 !important; 
    border: 1.5px solid #495057 !important;
    border-radius: 10px !important;
    padding: 18px !important; 
}
[data-testid="stFileUploaderDropzone"] *,
[data-testid="stFileUploaderDropzone"] .stMarkdown,
[data-testid="stFileUploaderDropzone"] [data-testid="stTextLabel"] span { 
    color: #f8f9fa !important; 
    fill: #f8f9fa !important; 
    opacity: 1 !important; 
}
[data-testid="stFileUploaderDropzone"] [data-testid="base-icon"],
[data-testid="stFileUploaderDropzone"] [data-testid="base-icon"] > svg {
    background: transparent !important;
    border: none !important;
}
[data-testid="stFileUploaderDropzone"] svg {
    fill: #f8f9fa !important;
}
[data-testid="stFileUploaderBrowseButton"], 
.stFileUploader button {
    background: #495057 !important; 
    border: 1px solid #495057 !important;
    color: #f8f9fa !important; 
    padding: 8px 16px !important; 
    border-radius: 8px !important; 
    font-weight: 600;
}
[data-testid="stFileUploaderBrowseButton"]:hover, 
.stFileUploader button:hover {
    background: #6c757d !important; 
}

/* 7️⃣ PDF Viewer Expander Styling */
.streamlit-expanderHeader { 
    background: #e9ecef; 
    border-radius: 8px;
    padding: 12px;
    font-weight: 700; 
    color: #212529;
    border: 1px solid #dee2e6;
    margin-top: 10px;
}
.streamlit-expanderHeader:hover {
    background: #dee2e6;
}
.streamlit-expanderHeader button[aria-expanded="false"], 
.streamlit-expanderHeader button[aria-expanded="true"] { 
    color: #212529;
}
.streamlit-expanderContent {
    padding: 0; 
    border-bottom: none;
}

/* 8️⃣ Highlighted Sentences and Badges */
.highlighted-sentence {
    padding: 3px 6px;
    border-radius: 6px;
    font-weight: 700;
    color: #fff;
}
.badge {
    display:inline-block;
    margin-left:6px;
    padding:4px 8px;
    border-radius:6px;
    font-size:11px;
    font-weight:700;
    color:#fff;
}

/* Overlay content panel */
.overlay-content {
    width: 80%;
    max-width: 1200px;
    height: 100%;
    background: #fff;
    padding: 20px 30px;
    overflow-y: auto;
    box-shadow: -4px 0 12px rgba(0,0,0,0.1);
    transform: translateX(100%);
    animation: slideIn 0.3s forwards;
    border-radius: 0 8px 8px 0;
}

/* Slide in animation */
@keyframes slideIn {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
}

/* Close button */
.overlay-close {
    position: absolute;
    top: 18px;
    right: 20px;
    font-size: 18px;
    font-weight: 700;
    cursor: pointer;
    color: #212529;
}

/* 🔥 FINAL FIX — Remove white square / default uploader icon */
[data-testid="stFileUploaderDropzone"] [data-testid="fileUploaderIcon"],
[data-testid="stFileUploaderDropzone"] [data-testid="fileUploaderIcon"] svg {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
}
</style>
"""
