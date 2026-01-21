# Plagiarism Detector

A comprehensive plagiarism detection system that analyzes documents for content similarity, provides detailed forensic analysis, and generates similarity reports with highlighted evidence.

## Features

### 📄 Multi-Format Document Support
- **PDF**: Full text extraction with OCR support for scanned documents
- **DOCX**: Microsoft Word document parsing
- **HTML**: Web page content extraction
- **TXT**: Plain text file analysis

### 🔍 Advanced Similarity Analysis
- **Semantic Similarity Engine**: Uses sentence transformers for deep semantic understanding
- **Query-based Analysis**: Generates intelligent queries from source documents
- **Web Search Integration**: Fetches and analyzes content from web sources
- **Evidence Highlighting**: Visually highlights plagiarized sections in original documents

### 🛡️ Forensic Analysis
- Detailed plagiarism forensics with evidence tracking
- Section-based analysis and merging
- Perplexity and Google Search integration for comprehensive source detection
- JSON-based report generation

### 📊 Analysis Features
- Batch processing of multiple documents
- Configurable similarity thresholds
- Document ingestion pipeline
- Detailed offset finding for plagiarized content
- Visualization and analytics support

### 🔐 Security
- Encrypted file handling
- Secure document processing

## Tech Stack

### Backend
- **Python 3.x**: Core language
- **FastAPI / Streamlit**: Web framework and UI
- **Sentence Transformers**: NLP for semantic similarity analysis
- **scikit-learn**: Machine learning utilities

### Document Processing
- **PyMuPDF (fitz)**: Advanced PDF manipulation
- **pdfplumber**: PDF data extraction
- **pdfminer.six**: PDF content mining
- **pytesseract / Pillow**: OCR for scanned documents
- **python-docx / docx2txt**: Word document parsing
- **tafilatura / newspaper3k**: Web content extraction

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **python-magic**: File type detection

### External APIs
- **Google Search API**: Real-time web source detection
- **Perplexity API**: Advanced document analysis

### Utilities
- **pyahocorasick**: Efficient string matching
- **cryptography**: Security and encryption
- **requests**: HTTP client
- **python-multipart**: Multipart form data handling
- **python-dotenv**: Environment configuration

### Visualization
- **Matplotlib**: Static plotting
- **Plotly**: Interactive visualizations

### Testing & Deployment
- **pytest**: Unit and integration testing
- **Docker**: Containerization for consistent deployment

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Docker (optional, for containerized deployment)
- Tesseract OCR (for scanned document processing)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd plagiarism-detector
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys:
   - Google API key and search engine ID
   - Perplexity API key

5. **Install Tesseract OCR** (for scanned document support)
   
   **Windows:**
   - Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
   - Run installer and note installation path
   - Add to environment: `set PYTESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe`
   
   **macOS:**
   ```bash
   brew install tesseract
   ```
   
   **Linux:**
   ```bash
   sudo apt-get install tesseract-ocr
   ```

6. **Run the application**
   
   See the [Running the Application](#running-the-application) section below.

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

2. **Access the application**
   - Web UI: http://localhost:8000
   - API: http://localhost:8000/api

## Running the Application

### Option 1: Backend (Uvicorn) + Frontend (Streamlit) - Recommended for Development

This approach runs the FastAPI backend and Streamlit frontend as separate services, which is ideal for development.

#### Terminal 1 - Start Backend Server (Uvicorn)

```bash
# From project root directory
cd src/api

# Run FastAPI server with Uvicorn on port 8000
uvicorn pipeline_api:app --reload --host 0.0.0.0 --port 8000
```

**Output should show:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Available API endpoints:**
- Base URL: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### Terminal 2 - Start Frontend (Streamlit)

```bash
# From project root directory
streamlit run src/api/main.py
```

**Output should show:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

#### Accessing the Application

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Option 2: Backend Only (For API Development)

If you only need to work with the backend API:

```bash
cd src/api
uvicorn pipeline_api:app --reload --host 0.0.0.0 --port 8000
```

Then access the API at http://localhost:8000/docs

### Option 3: Frontend Only (For UI Development)

If you only need to work with the frontend:

```bash
streamlit run src/api/main.py
```

Then access the UI at http://localhost:8501

### Option 4: Docker Compose (Full Stack)

To run both backend and frontend in containers:

```bash
docker-compose -f docker/docker-compose.yml up --build
```

Access the application at http://localhost:8000

## Development Workflow

### Running Tests While Developing

In a third terminal, run tests to validate your changes:

```bash
# Run all tests
pytest tests/ -v

# Run tests in watch mode (auto-rerun on file changes)
pytest-watch tests/

# Run specific test file
pytest tests/test_similarity_engine.py -v
```

### Typical Development Setup

```bash
# Terminal 1: Backend
cd src/api
uvicorn pipeline_api:app --reload

# Terminal 2: Frontend
streamlit run src/api/main.py

# Terminal 3: Tests (optional)
pytest-watch tests/
```

The `--reload` flag in Uvicorn automatically restarts the server when you make code changes.

## Project Structure

```
plagiarism-detector/
├── src/
│   ├── api/                    # API endpoints and interfaces
│   │   ├── main.py            # Streamlit application
│   │   ├── pipeline_api.py     # FastAPI pipeline
│   │   ├── similarity_api.py   # Similarity analysis API
│   │   ├── ingestion_api.py    # Document ingestion API
│   │   ├── evidence_api.py     # Evidence extraction API
│   │   └── forsenics_api.py    # Forensic analysis API
│   │
│   ├── ingestion/              # Document parsing and ingestion
│   │   ├── parsers/            # Format-specific parsers
│   │   └── utils.py            # Ingestion utilities
│   │
│   ├── similarity_search/       # Core plagiarism detection
│   │   ├── similarity_engine.py # Similarity computation
│   │   ├── pipeline.py          # Analysis pipeline
│   │   ├── query_generator.py   # Query generation
│   │   ├── web_fetcher.py       # Web content retrieval
│   │   ├── google_client.py     # Google Search integration
│   │   ├── perplexity_client.py # Perplexity API integration
│   │   ├── evidence_algorithm/  # Evidence extraction
│   │   ├── section_merger.py    # Section-based analysis
│   │   ├── highlighter.py       # Content highlighting
│   │   └── configs.py           # Configuration settings
│   │
│   ├── models/                  # Data models and schemas
│   └── RefinedOutput/           # Output formatting
│
├── tests/                        # Unit and integration tests
├── uploads/                      # User uploaded documents
├── docker/                       # Docker configuration
│   ├── Dockerfile.dev          # Development container
│   ├── Dockerfile.prod         # Production container
│   └── docker-compose.yml      # Multi-container setup
│
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Usage

### Command Line Usage

```python
from src.similarity_search.similarity_engine import SimilarityEngine
from src.ingestion.parsers import parse_document

# Load and parse documents
source_doc = parse_document('source.pdf')
suspect_doc = parse_document('suspect.pdf')

# Initialize similarity engine
engine = SimilarityEngine()

# Analyze plagiarism
results = engine.analyze(source_doc, suspect_doc)

# Get detailed report
print(results)
```

### API Usage

```bash
# Upload document for analysis
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"

# Run similarity analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"source_id": "doc1", "suspect_id": "doc2"}'

# Get forensic analysis
curl -X GET http://localhost:8000/api/forensics/doc1
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_similarity_engine.py

# Run with coverage
pytest --cov=src tests/
```

### Test Files
- `test_pdf_parser.py` - PDF parsing tests
- `test_docx_parser.py` - Word document tests
- `test_html_parser.py` - HTML parsing tests
- `test_similarity_engine.py` - Similarity analysis tests
- `test_query_generator.py` - Query generation tests
- `test_section_merger.py` - Section analysis tests

## Configuration

Edit `src/similarity_search/configs.py` to customize:
- Similarity thresholds
- Query generation parameters
- Web search settings
- Evidence extraction parameters

## API Endpoints

### Ingestion
- `POST /api/upload` - Upload document for analysis
- `POST /api/ingest` - Ingest document into database

### Similarity Analysis
- `POST /api/analyze` - Run similarity analysis
- `POST /api/similarity/search` - Search similar content

### Evidence & Forensics
- `GET /api/evidence/{doc_id}` - Extract evidence
- `GET /api/forensics/{doc_id}` - Forensic analysis
- `GET /api/report/{doc_id}` - Generate full report

### Pipeline
- `POST /api/pipeline/run` - Execute full pipeline

## Performance Considerations

- **Large PDFs**: Process may take time depending on document size and OCR requirement
- **Batch Processing**: Use batch endpoints for analyzing multiple documents
- **Caching**: Results are cached to avoid redundant computations
- **Parallelization**: Supports concurrent document processing

## Troubleshooting

### Tesseract Not Found
Ensure Tesseract is installed and path is correctly set in environment variables.

### API Connection Issues
- Check if services are running: `docker ps`
- Verify API keys in `.env` file
- Check logs: `docker-compose logs -f`

### Memory Issues with Large PDFs
- Reduce batch size
- Process documents individually
- Increase available system memory

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Contact

[Add contact information here]
