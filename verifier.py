"""
Claim Verification Module for the Fact-Checking Web Application.

This module provides functionality to verify extracted claims against
live web data using the Tavily API for web search and evidence gathering.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

from utils import (
    Claim,
    ClaimCategory,
    VerificationResult,
    calculate_confidence_score,
    get_env_var,
    logger
)


class WebVerifier:
    """
    Verifies claims against web sources using Tavily search API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the web verifier.

        Args:
            api_key: Tavily API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or get_env_var("TAVILY_API_KEY")
        self.api_url = "https://api.tavily.com/search"
        self.cache: Dict[str, VerificationResult] = {}

        if not self.api_key:
            logger.warning("Tavily API key not set. Verification will be limited.")

    def verify_claim(self, claim: Claim) -> VerificationResult:
        """
        Verify a single claim against web sources.

        Args:
            claim: Claim object to verify

        Returns:
            VerificationResult with verification status
        """
        logger.info(f"Verifying claim: {claim.text}")

        # Check cache first
        cache_key = claim.text.lower().strip()
        if cache_key in self.cache:
            logger.info(f"Using cached result for: {claim.text}")
            return self.cache[cache_key]

        # Handle unverified case
        if not self.api_key:
            return self._create_unverified_result(claim, "API key not configured")

        # Search for evidence
        search_results = self._web_search(claim.text)

        if not search_results:
            return self._create_unverified_result(claim, "No search results found")

        # Analyze search results
        evidence, sources = self._extract_evidence(search_results, claim)
        category, confidence, explanation = self._classify_claim(claim, evidence, sources)

        result = VerificationResult(
            claim=claim,
            category=category,
            confidence_score=confidence,
            evidence=evidence,
            source_urls=sources,
            explanation=explanation
        )

        # Cache the result
        self.cache[cache_key] = result

        return result

    def verify_claims(self, claims: List[Claim]) -> List[VerificationResult]:
        """
        Verify multiple claims.

        Args:
            claims: List of claims to verify

        Returns:
            List of verification results
        """
        results = []
        total = len(claims)

        for i, claim in enumerate(claims, 1):
            logger.info(f"Verifying claim {i}/{total}")
            result = self.verify_claim(claim)
            results.append(result)

        return results

    def _web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform web search using Tavily API.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        if not self.api_key:
            return []

        try:
            payload = {
                "query": self._enhance_search_query(query),
                "max_results": max_results,
                "search_depth": "advanced",
                "include_raw_content": False,
                "include_answer": True,
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            logger.info(f"Found {len(results)} search results for: {query}")
            return results

        except requests.RequestException as e:
            logger.error(f"Search API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return []

    def _enhance_search_query(self, claim_text: str) -> str:
        """
        Enhance claim text for better search results.

        Args:
            claim_text: Original claim text

        Returns:
            Enhanced search query
        """
        # Remove common filler words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'has', 'have'}
        words = claim_text.split()
        filtered_words = [w for w in words if w.lower() not in stop_words]

        # Add fact-checking context
        enhanced = ' '.join(filtered_words[:10])  # Limit query length

        return enhanced.strip()

    def _extract_evidence(
        self,
        search_results: List[Dict[str, Any]],
        claim: Claim
    ) -> tuple[List[str], List[str]]:
        """
        Extract evidence and source URLs from search results.

        Args:
            search_results: Raw search results
            claim: Original claim for context

        Returns:
            Tuple of (evidence_list, source_urls)
        """
        evidence = []
        sources = []

        for result in search_results:
            content = result.get("content", "")
            url = result.get("url", "")

            if content:
                # Extract relevant snippets
                snippets = self._extract_relevant_snippets(content, claim)
                evidence.extend(snippets)

            if url:
                sources.append(url)

        return evidence[:5], sources[:5]  # Limit to top 5

    def _extract_relevant_snippets(self, content: str, claim: Claim) -> List[str]:
        """
        Extract relevant snippets from content.

        Args:
            content: Full content text
            claim: Claim for matching

        Returns:
            List of relevant snippets
        """
        snippets = []
        key_terms = self._extract_key_terms(claim.text)

        sentences = content.split('.')
        scored_sentences = []

        for sentence in sentences:
            if len(sentence.strip()) < 20:
                continue

            score = sum(1 for term in key_terms if term.lower() in sentence.lower())
            if score > 0:
                scored_sentences.append((score, sentence.strip()))

        scored_sentences.sort(reverse=True)
        snippets = [s[1] for s in scored_sentences[:3]]

        return snippets

    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from claim text.

        Args:
            text: Claim text

        Returns:
            List of key terms
        """
        # Extract numbers and percentages
        numbers = re.findall(r'\d+(?:\.\d+)?(?:%| million| billion| trillion)?', text)

        # Extract capitalized words (likely entities)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)

        # Extract years
        years = re.findall(r'\b(?:19|20)\d{2}\b', text)

        return list(set(numbers + entities + years))

    def _classify_claim(
        self,
        claim: Claim,
        evidence: List[str],
        sources: List[str]
    ) -> tuple[ClaimCategory, float, str]:
        """
        Classify the claim based on evidence.

        Args:
            claim: Original claim
            evidence: List of evidence snippets
            sources: List of source URLs

        Returns:
            Tuple of (category, confidence, explanation)
        """
        if not evidence and not sources:
            return ClaimCategory.UNVERIFIABLE, 0.0, "No supporting evidence found"

        # Analyze evidence
        supporting_count, contradicting_count = self._analyze_evidence(claim, evidence)

        total_sources = len(sources)

        if supporting_count >= 2:
            confidence = calculate_confidence_score(
                supporting_count,
                total_sources,
                semantic_similarity=0.85
            )
            return ClaimCategory.VERIFIED, confidence, f"Supported by {supporting_count} source(s)"

        elif supporting_count >= 1 and contradicting_count == 0:
            confidence = calculate_confidence_score(
                supporting_count,
                total_sources,
                semantic_similarity=0.75
            )
            return ClaimCategory.VERIFIED, confidence, "Supported by limited sources"

        elif contradicting_count > supporting_count:
            return ClaimCategory.FALSE, 15.0, f"Contradicted by {contradicting_count} source(s)"

        elif contradicting_count > 0:
            return ClaimCategory.INACCURATE, 35.0, "Partially accurate or contains inaccuracies"

        else:
            return ClaimCategory.INACCURATE, 25.0, "Unable to fully verify with available sources"

    def _analyze_evidence(
        self,
        claim: Claim,
        evidence: List[str]
    ) -> tuple[int, int]:
        """
        Analyze evidence for supporting/contradicting content.

        Args:
            claim: Original claim
            evidence: Evidence snippets

        Returns:
            Tuple of (supporting_count, contradicting_count)
        """
        supporting = 0
        contradicting = 0

        claim_lower = claim.text.lower()

        for snippet in evidence:
            snippet_lower = snippet.lower()

            # Check for numerical match
            claim_numbers = set(re.findall(r'\d+(?:\.\d+)?', claim.text))
            snippet_numbers = set(re.findall(r'\d+(?:\.\d+)?', snippet))

            numerical_match = bool(claim_numbers & snippet_numbers)

            # Check for entity match
            claim_entities = set(self._extract_key_terms(claim.text))
            snippet_entities = set(self._extract_key_terms(snippet))
            entity_match = len(claim_entities & snippet_entities) >= 2

            # Check for contradiction indicators
            contradiction_words = ['however', 'but', 'incorrect', 'false', 'myth', 'debunked', 'wrong']
            has_contradiction = any(word in snippet_lower for word in contradiction_words)

            if has_contradiction:
                contradicting += 1
            elif numerical_match and entity_match:
                supporting += 1
            elif numerical_match:
                supporting += 0.5

        return int(supporting), contradicting

    def _create_unverified_result(
        self,
        claim: Claim,
        reason: str
    ) -> VerificationResult:
        """
        Create result for unverified claim.

        Args:
            claim: Original claim
            reason: Reason for being unverified

        Returns:
            VerificationResult with UNVERIFIABLE status
        """
        return VerificationResult(
            claim=claim,
            category=ClaimCategory.UNVERIFIABLE,
            confidence_score=0.0,
            evidence=[],
            source_urls=[],
            explanation=reason
        )


class MockWebVerifier(WebVerifier):
    """
    Mock verifier for testing without API access.
    Generates simulated verification results.
    """

    def __init__(self):
        """Initialize mock verifier without API key."""
        super().__init__(api_key=None)

    def verify_claim(self, claim: Claim) -> VerificationResult:
        """
        Generate mock verification result for testing.

        Args:
            claim: Claim to mock-verify

        Returns:
            Simulated VerificationResult
        """
        import random

        categories = [
            (ClaimCategory.VERIFIED, 0.6),
            (ClaimCategory.INACCURATE, 0.25),
            (ClaimCategory.FALSE, 0.1),
            (ClaimCategory.UNVERIFIABLE, 0.05)
        ]

        # Random weighted selection
        rand = random.random()
        cumulative = 0.0
        selected_category = ClaimCategory.UNVERIFIABLE

        for category, weight in categories:
            cumulative += weight
            if rand < cumulative:
                selected_category = category
                break

        confidence_map = {
            ClaimCategory.VERIFIED: random.uniform(70, 95),
            ClaimCategory.INACCURATE: random.uniform(30, 55),
            ClaimCategory.FALSE: random.uniform(10, 25),
            ClaimCategory.UNVERIFIABLE: 0.0
        }

        explanations = {
            ClaimCategory.VERIFIED: "Claim is supported by multiple reliable sources.",
            ClaimCategory.INACCURATE: "Claim contains some inaccuracies or outdated information.",
            ClaimCategory.FALSE: "Claim contradicts available evidence from reliable sources.",
            ClaimCategory.UNVERIFIABLE: "Unable to find sufficient sources to verify this claim."
        }

        return VerificationResult(
            claim=claim,
            category=selected_category,
            confidence_score=round(confidence_map[selected_category], 1),
            evidence=["Mock evidence for demonstration purposes."],
            source_urls=["https://example.com/source"],
            explanation=explanations[selected_category]
        )


def create_verifier() -> WebVerifier:
    """
    Create appropriate verifier based on configuration.

    Returns:
        WebVerifier instance (real or mock)
    """
    api_key = get_env_var("TAVILY_API_KEY")

    if api_key:
        logger.info("Using Tavily API for verification")
        return WebVerifier(api_key)
    else:
        logger.warning("TAVILY_API_KEY not set. Using mock verifier for demonstration.")
        return MockWebVerifier()


def main():
    """Test the verifier with a sample claim."""
    from utils import Claim, ClaimType

    # Create sample claim
    test_claim = Claim(
        text="$12.5 billion",
        claim_type=ClaimType.FINANCIAL,
        source_text="The company reported revenue of $12.5 billion in 2023.",
        page_number=1
    )

    verifier = create_verifier()
    result = verifier.verify_claim(test_claim)

    print(f"Claim: {result.claim.text}")
    print(f"Category: {result.category.value}")
    print(f"Confidence: {result.confidence_score}%")
    print(f"Evidence: {result.evidence}")
    print(f"Explanation: {result.explanation}")


if __name__ == "__main__":
    main()
