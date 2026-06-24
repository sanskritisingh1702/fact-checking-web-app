# Fact-Checker Pro

A production-ready web application that automatically extracts factual claims from PDF documents, verifies them against live web sources, and generates comprehensive verification reports.

## Overview

Fact-Checker Pro helps users validate the accuracy of claims made in PDF documents by:

1. **Extracting** factual claims from PDF text content
2. **Identifying** different claim types (statistics, dates, financial figures, percentages, technical specs)
3. **Verifying** claims against live web sources using Tavily AI search
4. **Classifying** verification status (Verified, Inaccurate, False, or Unverifiable)
5. **Generating** detailed PDF reports with confidence scores and supporting evidence

## Features

- PDF document upload and text extraction
- Intelligent claim detection using regex patterns and optional NLP
- Real-time web verification via Tavily API
- Confidence scoring (0-100%)
- Interactive sortable results table
- Multi-format report export (PDF, CSV, JSON)
- Clean, responsive Streamlit interface

## Claim Types Detected

| Type | Examples |
|------|----------|
| **Statistics** | "50 million users", "estimated 5,000 cases" |
| **Dates/Temporal** | "January 2023", "founded in 1998", "Q4 2022" |
| **Financial** | "$12.5 billion revenue", "€500 million valuation" |
| **Technical** | "3.2 GHz processor", "64 GB RAM", "5nm process" |
| **Percentages** | "15% increase", "75% of users" |
| **General Facts** | "headquartered in Seattle", "CEO is John Smith" |

## Verification Categories

| Status | Description |
|--------|-------------|
| **Verified** | Claim is supported by multiple reliable sources |
| **Inaccurate** | Claim contains errors or partial inaccuracies |
| **False** | Claim is contradicted by reliable sources |
| **Unverifiable** | Insufficient sources to verify the claim |

## Project Structure

```
/
├── app.py                    # Main Streamlit application
├── claim_extractor.py        # Claim identification and extraction
├── verifier.py               # Web search and claim verification
├── report_generator.py       # PDF/CSV/JSON report generation
├── utils.py                  # Shared utilities and constants
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation
```

## Prerequisites

- Python 3.9 or higher
- Tavily API key (for web verification)
- Optional: spaCy language model for enhanced NLP extraction

## Local Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fact-checker-pro
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy Model (Optional but Recommended)

```bash
python -m spacy download en_core_web_sm
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
TAVILY_API_KEY=your_tavily_api_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

### 6. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

## Getting API Keys

### Tavily API Key

1. Visit [https://tavily.com](https://tavily.com)
2. Sign up for a free account
3. Navigate to API Keys in your dashboard
4. Create a new API key
5. The free tier includes 1,000 searches per month

### Supabase Configuration (Optional)

Used for storing verification session data:

1. Create a project at [https://supabase.com](https://supabase.com)
2. Copy the Project URL and anon/public key from Settings > API
3. Add to your `.env` file

## Deployment on Streamlit Cloud

### Step 1: Prepare Your Repository

1. Create a new GitHub repository
2. Push all project files to the repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/your-username/fact-checker-pro.git
   git push -u origin main
   ```

3. Ensure your repository includes:
   - `app.py`
   - `requirements.txt`
   - `claim_extractor.py`
   - `verifier.py`
   - `report_generator.py`
   - `utils.py`
   - `README.md`
   - `.gitignore` (exclude `.env`, `__pycache__`, `*.pyc`, `logs/`)

### Step 2: Create Streamlit Cloud Account

1. Visit [https://streamlit.io/cloud](https://streamlit.io/cloud)
2. Sign up using your GitHub account
3. Authorize Streamlit to access your repositories

### Step 3: Deploy the Application

1. Click **"New app"** in your Streamlit Cloud dashboard
2. Select your repository: `your-username/fact-checker-pro`
3. Set the following options:
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (optional): Choose a custom subdomain
4. Click **"Deploy!"**

### Step 4: Configure Secrets

1. In your deployed app dashboard, click **"Settings"**
2. Scroll to **"Secrets"** section
3. Add your API keys in TOML format:
   ```toml
   TAVILY_API_KEY = "tvly-your-api-key-here"
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-anon-key-here"
   ```
4. Click **"Save"**
5. The app will automatically redeploy with the new secrets

### Step 5: Verify Deployment

1. Your app URL will be: `https://your-app-name.streamlit.app`
2. Open the URL in your browser
3. Upload a test PDF to verify functionality
4. Check the sidebar for API connection status

### Deployment Troubleshooting

**Issue: "Module not found" errors**

Solution: Ensure all dependencies are in `requirements.txt` with exact versions. Example:
```
streamlit==1.38.0
pypdf==4.0.1
```

**Issue: "API key not found"**

Solution:
1. Go to app Settings > Secrets
2. Verify key names match exactly (case-sensitive)
3. Check TOML syntax is correct
4. Restart the app after saving secrets

**Issue: "spaCy model not found"**

Solution: The requirements.txt includes a direct download URL for the model. If issues persist:
1. Use the NLP toggle in the sidebar to disable enhanced extraction
2. Pattern-based extraction will still work without the model

**Issue: "PDF extraction failed"**

Solution:
1. Ensure PDF contains selectable text (not scanned images)
2. Check file size is under 10 MB
3. Try a different PDF to isolate the issue

**Issue: Slow verification**

Solution:
1. Reduce "Maximum Claims to Verify" in sidebar settings
2. Disable NLP-enhanced extraction
3. Tavily API typically responds in 2-5 seconds per claim

## Usage Guide

### Uploading a Document

1. Click "Browse files" to select a PDF
2. Verify the file preview shows the document details
3. Adjust settings in the sidebar:
   - Enable/disable NLP extraction
   - Set maximum claims to verify
   - Filter claim types

### Processing

1. Click "Process Document"
2. Watch the progress bar as the app:
   - Extracts text from PDF pages
   - Identifies factual claims
   - Verifies each claim against web sources

### Reviewing Results

1. View the **Summary** section for overall statistics
2. Use the **Results Table** to browse individual claims
3. Sort by confidence, category, or page number
4. Filter by verification status
5. Expand each claim for detailed evidence and sources

### Downloading Reports

1. **PDF Report**: Comprehensive document with all findings
2. **CSV Data**: Spreadsheet format for data analysis
3. **JSON**: Structured data for integration with other tools

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `TAVILY_API_KEY` | Yes* | API key for web search verification |
| `SUPABASE_URL` | No | Supabase project URL for session storage |
| `SUPABASE_KEY` | No | Supabase anon key |

*Without Tavily API key, the app uses mock verification for demonstration.

## File Format Support

- **Input**: PDF documents with selectable text
- **Max File Size**: 10 MB
- **Output Formats**: PDF, CSV, JSON

## Performance Considerations

- Processing time scales with document length and claim count
- Web verification requires API calls (rate limits apply)
- Recommended maximum: 50 claims per document
- Typical processing: 1-2 minutes for 20 claims

## Limitations

- Cannot extract text from scanned PDF images (OCR not included)
- Verification accuracy depends on web source availability
- Some claims may be inherently unverifiable
- Confidence scores are estimates, not guarantees

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Support

For issues and feature requests, please open a GitHub issue.

---

Built with Streamlit, Tavily API, and Python.
