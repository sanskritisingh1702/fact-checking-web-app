"""
Utilities and shared constants for the Fact-Checking Web Application.

This module provides common utilities, constants, and helper functions
used across the application components.
"""

import re
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logger
logger.remove()
logger.add(
    "logs/fact_checker_{time}.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)


class ClaimCategory(Enum):
    """Classification categories for verified claims."""
    VERIFIED = "Verified"
    INACCURATE = "Inaccurate"
    FALSE = "False"
    UNVERIFIABLE = "Unverifiable"


class ClaimType(Enum):
    """Types of factual claims that can be extracted."""
    STATISTIC = "Statistic"
    DATE = "Date/Temporal"
    FINANCIAL = "Financial/Monetary"
    TECHNICAL = "Technical/Specification"
    PERCENTAGE = "Percentage/Ratio"
    GENERAL = "General Fact"


@dataclass
class Claim:
    """Represents a single extracted factual claim."""
    text: str
    claim_type: ClaimType
    source_text: str
    page_number: int
    confidence: float = 0.0
    position_start: int = 0
    position_end: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert claim to dictionary representation."""
        return {
            "text": self.text,
            "claim_type": self.claim_type.value,
            "source_text": self.source_text,
            "page_number": self.page_number,
            "confidence": self.confidence,
            "position_start": self.position_start,
            "position_end": self.position_end
        }


@dataclass
class VerificationResult:
    """Represents the verification result for a claim."""
    claim: Claim
    category: ClaimCategory
    confidence_score: float
    evidence: List[str] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)
    explanation: str = ""
    verified_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert verification result to dictionary representation."""
        return {
            "claim_text": self.claim.text,
            "claim_type": self.claim.claim_type.value,
            "category": self.category.value,
            "confidence_score": self.confidence_score,
            "evidence": self.evidence,
            "source_urls": self.source_urls,
            "explanation": self.explanation,
            "verified_at": self.verified_at.isoformat(),
            "page_number": self.claim.page_number
        }


# Regular expression patterns for claim extraction
CLAIM_PATTERNS = {
    ClaimType.STATISTIC: [
        r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion|trillion)?\s*(?:people|users|customers|units|cases|deaths|infections)\b',
        r'\b(?:estimated|approximately|around|about)\s+\d+(?:,\d{3})*(?:\.\d+)?\b',
        r'\b\d+(?:,\d{3})*\s*(?:km|km²|miles|acres|hectares)\b',
        r'\btotal\s+(?:of\s+)?\d+(?:,\d{3})*(?:\.\d+)?\b',
    ],
    ClaimType.DATE: [
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b(?:in|since|from|during)\s+\d{4}\b',
        r'\b(?:Q[1-4]|first|second|third|fourth)\s+(?:quarter|Q)\s+\d{4}\b',
        r'\b(?:last|past|previous)\s+(?:year|month|decade|century)\b',
    ],
    ClaimType.FINANCIAL: [
        r'\$\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b',
        r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:USD|EUR|GBP|dollars|euros|pounds)\b',
        r'\b(?:revenue|profit|loss|earnings)\s+(?:of\s+)?\$?\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b',
        r'\b(?:market cap|valuation|worth)\s+(?:of\s+)?\$?\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b',
    ],
    ClaimType.TECHNICAL: [
        r'\b\d+(?:\.\d+)?(?:\s*)?(?:GHz|MHz|GB|TB|MB|KB|mm|cm|inches|meters|kg|lbs)\b',
        r'\b(?:runs|operates|functions)\s+(?:at|on)\s+\d+(?:\.\d+)?(?:\s*)?(?:GHz|MHz)\b',
        r'\b(?:supports|capacity)\s+(?:of\s+)?\d+(?:\.\d+)?(?:\s*)?(?:GB|TB|MB)\b',
        r'\b\d+(?:\.\d+)?(?:\s*)?(?:nm|nanometer)\s+(?:process|technology|node)\b',
    ],
    ClaimType.PERCENTAGE: [
        r'\b\d+(?:\.\d+)?%\b',
        r'\b\d+(?:\.\d+)?\s+(?:percent|percentage)\b',
        r'\b(?:increase|decrease|growth|decline)\s+(?:of|by)\s+\d+(?:\.\d+)?%?\b',
        r'\b\d+(?:\.\d+)?%?\s*(?:YoY|QoQ|MoM|year-over-year)\b',
    ],
    ClaimType.GENERAL: [
        r'\b(?:founded|established|created|launched|started)\s+(?:in|on)\s+\d{4}\b',
        r'\b(?:headquarters|headquartered)\s+(?:in|located)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
        r'\b(?:CEO|founder|owner|president|chairman)\s+(?:is|was)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
        r'\b(?:acquired|bought|purchased)\s+(?:by|for)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
    ],
}


def extract_text_from_pdf(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract text content from a PDF file using pdfplumber.

    Args:
        file_path: Path to the PDF file

    Returns:
        List of dictionaries containing page number and extracted text
    """
    import pdfplumber

    pages_content = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages_content.append({
                    "page_number": i,
                    "text": text.strip()
                })
        logger.info(f"Successfully extracted text from {len(pages_content)} pages")
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise
    return pages_content


def clean_text(text: str) -> str:
    """Clean and normalize text for processing."""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    text = re.sub(r'\n+', '\n', text)
    return text


def calculate_confidence_score(
    match_count: int,
    source_count: int,
    semantic_similarity: float = 0.8
) -> float:
    """
    Calculate confidence score based on multiple factors.

    Args:
        match_count: Number of supporting sources
        source_count: Total sources checked
        semantic_similarity: Semantic similarity score (0-1)

    Returns:
        Confidence score between 0 and 100
    """
    if source_count == 0:
        return 0.0

    # Weight factors
    source_weight = 0.4
    match_weight = 0.3
    similarity_weight = 0.3

    # Calculate component scores
    source_score = min(match_count / max(source_count, 1), 1.0) * 100
    match_score = min(match_count * 20, 100)
    similarity_score = semantic_similarity * 100

    # Weighted average
    confidence = (
        source_weight * source_score +
        match_weight * match_score +
        similarity_weight * similarity_score
    )

    return round(min(max(confidence, 0), 100), 1)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def validate_pdf_file(file) -> Tuple[bool, str]:
    """
    Validate uploaded PDF file.

    Args:
        file: Uploaded file object from Streamlit

    Returns:
        Tuple of (is_valid, error_message)
    """
    from typing import Tuple

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    if file is None:
        return False, "No file provided"

    if not file.name.lower().endswith('.pdf'):
        return False, "File must be a PDF"

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return False, f"File size ({format_file_size(file_size)}) exceeds maximum allowed (10 MB)"

    if file_size == 0:
        return False, "File is empty"

    return True, ""


def get_category_color(category: ClaimCategory) -> str:
    """Get display color for verification category."""
    colors = {
        ClaimCategory.VERIFIED: "#28a745",
        ClaimCategory.INACCURATE: "#ffc107",
        ClaimCategory.FALSE: "#dc3545",
        ClaimCategory.UNVERIFIABLE: "#6c757d"
    }
    return colors.get(category, "#6c757d")


def get_category_emoji(category: ClaimCategory) -> str:
    """Get emoji for verification category."""
    emojis = {
        ClaimCategory.VERIFIED: "✓",
        ClaimCategory.INACCURATE: "!",
        ClaimCategory.FALSE: "✗",
        ClaimCategory.UNVERIFIABLE: "?"
    }
    return emojis.get(category, "?")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis if longer than max_length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def save_temp_pdf(uploaded_file) -> Path:
    """Save uploaded file to temporary location and return path."""
    import tempfile

    temp_dir = Path(tempfile.gettempdir()) / "fact_checker"
    temp_dir.mkdir(exist_ok=True)

    file_path = temp_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    logger.info(f"Saved temporary PDF to {file_path}")
    return file_path


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    value = os.getenv(key, default)
    if value is None and default is None:
        logger.warning(f"Environment variable {key} not set and no default provided")
    return value


def check_api_keys() -> Dict[str, bool]:
    """Check which API keys are available."""
    return {
        "tavily": bool(get_env_var("TAVILY_API_KEY")),
        "supabase": bool(get_env_var("SUPABASE_URL") or get_env_var("VITE_SUPABASE_URL"))
    }


__all__ = [
    "ClaimCategory",
    "ClaimType",
    "Claim",
    "VerificationResult",
    "CLAIM_PATTERNS",
    "extract_text_from_pdf",
    "clean_text",
    "calculate_confidence_score",
    "format_file_size",
    "validate_pdf_file",
    "get_category_color",
    "get_category_emoji",
    "truncate_text",
    "save_temp_pdf",
    "get_env_var",
    "check_api_keys",
    "logger"
]
