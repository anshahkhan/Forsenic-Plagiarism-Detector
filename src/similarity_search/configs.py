from dotenv import load_dotenv
import os

load_dotenv()

# ============================================================
# 🔍 Perplexity API (Primary Retrieval)
# ============================================================
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = os.getenv("PERPLEXITY_API_URL", "https://api.perplexity.ai/search")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")   # sonar / sonar-pro
PERPLEXITY_TOP_K = int(os.getenv("PERPLEXITY_TOP_K", 10))


# ============================================================
# 🔎 Google Search API (Fallback)
# ============================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")  # e.g. "44a2f0902c54847e4"
GOOGLE_NUM_RESULTS = int(os.getenv("GOOGLE_NUM_RESULTS", 2))


# ============================================================
# 🔎 Bing Web Search API (Optional Fallback 2)
# ============================================================
BING_API_KEY = os.getenv("BING_API_KEY", None)
BING_ENDPOINT = os.getenv("BING_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")
BING_NUM_RESULTS = int(os.getenv("BING_NUM_RESULTS", 5))


# ============================================================
# 📄 Section chunking
# ============================================================
TARGET_WORDS_PER_CHUNK = int(os.getenv("TARGET_WORDS_PER_CHUNK", 150))
CHUNK_OVERLAP_RATIO = 0.3   # 30%
MAX_SENTENCE_EXPANSION = 40

# ============================================================
# 📦 Block merging for queries
# ============================================================
TARGET_WORDS_PER_BLOCK = int(os.getenv("TARGET_WORDS_PER_BLOCK", 300))
MIN_WORDS_PER_BLOCK = int(os.getenv("MIN_WORDS_PER_BLOCK", 200))
MAX_WORDS_PER_BLOCK = int(os.getenv("MAX_WORDS_PER_BLOCK", 400))


# ============================================================
# 🧠 Similarity Settings
# ============================================================
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 10))

# N-gram settings
NGRAM_N = int(os.getenv("NGRAM_N", 3))

# Weight for combining embedding + ngram
EMBEDDING_SIM_WEIGHT = float(os.getenv("EMBEDDING_SIM_WEIGHT", 0.85))

# Minimum score to consider “meaningful similarity”
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.60))

# Confidence thresholds
CONFIDENCE_LOW = float(os.getenv("CONFIDENCE_LOW", 0.50))
CONFIDENCE_MEDIUM = float(os.getenv("CONFIDENCE_MEDIUM", 0.70))
# > 0.70 = high


# ============================================================
# 🌐 Networking
# ============================================================
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_BACKOFF = float(os.getenv("RETRY_BACKOFF", 1.0))
USER_AGENT = os.getenv("USER_AGENT", "DF-Project-SimilarityBot/1.0")
HTTP_USER_AGENT = os.getenv("HTTP_USER_AGENT", "Mozilla/5.0 (DF-Project/1.0)")
MAX_FETCHED_TEXT_CHARS = int(os.getenv("MAX_FETCHED_TEXT_CHARS", 20000))

# Max number of chunks per section to send to Google Advanced Search
MAX_GOOGLE_CHUNKS = 2  # adjust as needed


# ============================================================
# 🧪 Debugging
# ============================================================
ENABLE_DEBUG_LOGS = os.getenv("ENABLE_DEBUG_LOGS", "false").lower() == "true"

# ============================================================
# 📄 PDF Scraping Toggle for Module 3
# ============================================================
ALLOW_PDF_SCRAPING = os.getenv("ALLOW_PDF_SCRAPING", "false").lower() == "true"
