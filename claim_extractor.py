"""
Claim Extraction Module for the Fact-Checking Web Application.

This module identifies and extracts factual claims from text content,
specifically targeting statistics, dates, financial figures, technical facts,
percentages, and other verifiable statements.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from utils import (
    Claim,
    ClaimType,
    ClaimCategory,
    CLAIM_PATTERNS,
    clean_text,
    logger
)


class ClaimExtractor:
    """
    Extracts factual claims from text content using pattern matching
    and NLP-based entity recognition.
    """

    def __init__(self, use_nlp: bool = True):
        """
        Initialize the claim extractor.

        Args:
            use_nlp: Whether to use spaCy NLP for enhanced extraction
        """
        self.use_nlp = use_nlp
        self.nlp = None

        if self.use_nlp:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy model for enhanced claim extraction")
            except Exception as e:
                logger.warning(f"Could not load spaCy model: {e}. Using pattern-based extraction only.")
                self.use_nlp = False

    def extract_from_text(self, text: str, page_number: int = 1) -> List[Claim]:
        """
        Extract all factual claims from the given text.

        Args:
            text: Text content to extract claims from
            page_number: Page number for reference

        Returns:
            List of extracted Claim objects
        """
        claims = []
        clean_content = clean_text(text)

        # Pattern-based extraction
        pattern_claims = self._extract_with_patterns(clean_content, page_number)
        claims.extend(pattern_claims)

        # NLP-based extraction if available
        if self.nlp:
            nlp_claims = self._extract_with_nlp(clean_content, page_number)
            claims.extend(nlp_claims)

        # Deduplicate claims
        unique_claims = self._deduplicate_claims(claims)

        logger.info(f"Extracted {len(unique_claims)} unique claims from page {page_number}")
        return unique_claims

    def extract_from_pages(self, pages: List[Dict[str, Any]]) -> List[Claim]:
        """
        Extract claims from multiple pages of content.

        Args:
            pages: List of page dictionaries with 'page_number' and 'text' keys

        Returns:
            List of all extracted claims across all pages
        """
        all_claims = []

        for page in pages:
            page_number = page.get("page_number", 1)
            text = page.get("text", "")
            if text.strip():
                claims = self.extract_from_text(text, page_number)
                all_claims.extend(claims)

        logger.info(f"Total claims extracted: {len(all_claims)}")
        return all_claims

    def _extract_with_patterns(self, text: str, page_number: int) -> List[Claim]:
        """
        Extract claims using predefined regex patterns.

        Args:
            text: Text to search
            page_number: Page number for reference

        Returns:
            List of claims found via pattern matching
        """
        claims = []

        for claim_type, patterns in CLAIM_PATTERNS.items():
            for pattern in patterns:
                try:
                    matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        claim_text = match.group().strip()
                        if claim_text:
                            # Extract surrounding context
                            context_start = max(0, match.start() - 100)
                            context_end = min(len(text), match.end() + 100)
                            context = text[context_start:context_end].strip()

                            claim = Claim(
                                text=claim_text,
                                claim_type=claim_type,
                                source_text=context,
                                page_number=page_number,
                                position_start=match.start(),
                                position_end=match.end(),
                                confidence=0.0
                            )
                            claims.append(claim)

                except re.error as e:
                    logger.warning(f"Invalid pattern {pattern}: {e}")

        return claims

    def _extract_with_nlp(self, text: str, page_number: int) -> List[Claim]:
        """
        Extract claims using spaCy NLP for entity recognition.

        Args:
            text: Text to analyze
            page_number: Page number for reference

        Returns:
            List of claims found via NLP
        """
        if not self.nlp:
            return []

        claims = []

        try:
            doc = self.nlp(text)

            # Extract entities that represent factual claims
            for ent in doc.ents:
                claim_type = self._map_entity_to_claim_type(ent.label_)
                if claim_type:
                    # Get sentence context
                    sent = ent.sent if ent.sent else None
                    context = sent.text.strip() if sent else text[max(0, ent.start_char-50):ent.end_char+50]

                    claim = Claim(
                        text=ent.text.strip(),
                        claim_type=claim_type,
                        source_text=context,
                        page_number=page_number,
                        position_start=ent.start_char,
                        position_end=ent.end_char,
                        confidence=0.0
                    )
                    claims.append(claim)

        except Exception as e:
            logger.error(f"NLP extraction error: {e}")

        return claims

    def _map_entity_to_claim_type(self, entity_label: str) -> Optional[ClaimType]:
        """
        Map spaCy entity label to claim type.

        Args:
            entity_label: spaCy entity label (e.g., 'DATE', 'MONEY', 'QUANTITY')

        Returns:
            Corresponding ClaimType or None
        """
        mapping = {
            'DATE': ClaimType.DATE,
            'TIME': ClaimType.DATE,
            'MONEY': ClaimType.FINANCIAL,
            'QUANTITY': ClaimType.STATISTIC,
            'PERCENT': ClaimType.PERCENTAGE,
            'CARDINAL': ClaimType.STATISTIC,
            'ORDINAL': ClaimType.STATISTIC,
        }
        return mapping.get(entity_label)

    def _deduplicate_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Remove duplicate claims based on text similarity.

        Args:
            claims: List of claims to deduplicate

        Returns:
            Deduplicated list of claims
        """
        seen_texts = set()
        unique_claims = []

        for claim in claims:
            normalized = claim.text.lower().strip()
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                unique_claims.append(claim)

        return unique_claims

    def prioritize_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Prioritize claims by importance and verifiability.

        Args:
            claims: List of claims to prioritize

        Returns:
            Sorted list of claims by priority
        """
        priority_order = {
            ClaimType.FINANCIAL: 1,
            ClaimType.STATISTIC: 2,
            ClaimType.PERCENTAGE: 3,
            ClaimType.TECHNICAL: 4,
            ClaimType.DATE: 5,
            ClaimType.GENERAL: 6,
        }

        return sorted(
            claims,
            key=lambda c: (priority_order.get(c.claim_type, 7), -len(c.text))
        )

    def filter_valid_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Filter out invalid or non-claimworthy statements.

        Args:
            claims: List of claims to filter

        Returns:
            Filtered list of valid claims
        """
        invalid_patterns = [
            r'^(a|an|the)\s+',
            r'^[A-Z]\s*$',  # Single letter
            r'^\d+$',  # Just a number
            r'^.{1,2}$',  # Too short
        ]

        valid_claims = []
        for claim in claims:
            is_valid = True
            for pattern in invalid_patterns:
                if re.match(pattern, claim.text, re.IGNORECASE):
                    is_valid = False
                    break

            if is_valid and len(claim.text) >= 3:
                valid_claims.append(claim)

        return valid_claims

    def get_extraction_summary(self, claims: List[Claim]) -> Dict[str, int]:
        """
        Get summary statistics of extracted claims by type.

        Args:
            claims: List of claims

        Returns:
            Dictionary with counts by claim type
        """
        summary = {}
        for claim in claims:
            claim_type_name = claim.claim_type.value
            summary[claim_type_name] = summary.get(claim_type_name, 0) + 1

        return summary


class SentenceClaimExtractor:
    """
    Extracts claim-worthy sentences that contain verifiable facts.
    Uses a different approach focusing on sentence-level analysis.
    """

    def __init__(self):
        """Initialize sentence-level claim extractor."""
        self.claim_indicators = [
            'is', 'are', 'was', 'were', 'has', 'have', 'had',
            'states', 'reported', 'according to', 'estimated',
            'approximately', 'total', 'average', 'increase', 'decrease',
            'million', 'billion', 'percent', 'growth', 'revenue',
        ]

    def extract_claim_sentences(self, text: str, min_words: int = 5) -> List[str]:
        """
        Extract sentences that appear to contain factual claims.

        Args:
            text: Text to analyze
            min_words: Minimum words for a valid claim sentence

        Returns:
            List of sentence-level claims
        """
        sentences = self._split_into_sentences(text)
        claim_sentences = []

        for sentence in sentences:
            if self._is_claim_worthy(sentence, min_words):
                claim_sentences.append(sentence.strip())

        return claim_sentences

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _is_claim_worthy(self, sentence: str, min_words: int) -> bool:
        """
        Determine if a sentence contains a verifiable claim.

        Args:
            sentence: Sentence to analyze
            min_words: Minimum word count

        Returns:
            True if sentence is claim-worthy
        """
        words = sentence.split()
        if len(words) < min_words:
            return False

        has_number = any(c.isdigit() for c in sentence)
        has_indicator = any(indicator in sentence.lower() for indicator in self.claim_indicators)

        return has_number or has_indicator


def main():
    """Test the claim extractor with sample text."""
    sample_text = """
    The company reported revenue of $12.5 billion in 2023,
    representing a 15% increase from the previous year.
    Founded in 1998, the organization now serves over 50 million customers worldwide.
    The new processor runs at 3.2 GHz and supports up to 64 GB of RAM.
    Approximately 75% of users prefer the updated interface.
    """

    extractor = ClaimExtractor(use_nlp=False)
    claims = extractor.extract_from_text(sample_text)

    print(f"Extracted {len(claims)} claims:")
    for i, claim in enumerate(claims, 1):
        print(f"\n{i}. [{claim.claim_type.value}] {claim.text}")

    summary = extractor.get_extraction_summary(claims)
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    main()
