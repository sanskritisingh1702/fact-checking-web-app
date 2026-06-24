"""
Report Generation Module for the Fact-Checking Web Application.

This module provides functionality to generate formatted PDF reports
from verification results, including tables, summaries, and export options.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import io

from utils import (
    VerificationResult,
    ClaimCategory,
    get_category_color,
    truncate_text,
    logger
)

# PDF Generation imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    ListFlowable,
    ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


class ReportGenerator:
    """
    Generates formatted PDF reports from verification results.
    """

    def __init__(self, title: str = "Fact-Checking Report"):
        """
        Initialize the report generator.

        Args:
            title: Title for the report
        """
        self.title = title
        self.styles = self._create_styles()

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """
        Create custom paragraph styles for the report.

        Returns:
            Dictionary of style name to ParagraphStyle
        """
        styles = getSampleStyleSheet()

        # Title style
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1a1a2e'),
            alignment=TA_CENTER
        ))

        # Subtitle style
        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            textColor=colors.HexColor('#4a4a4a'),
            alignment=TA_CENTER
        ))

        # Section header style
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2d3436'),
            borderWidth=0,
            borderColor=colors.HexColor('#0984e3'),
            borderPadding=5
        ))

        # Claim text style
        styles.add(ParagraphStyle(
            name='ClaimText',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=6,
            textColor=colors.HexColor('#2d3436')
        ))

        # Evidence style
        styles.add(ParagraphStyle(
            name='EvidenceText',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            spaceAfter=4,
            textColor=colors.HexColor('#636e72'),
            leftIndent=20
        ))

        # Source link style
        styles.add(ParagraphStyle(
            name='SourceLink',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#0984e3'),
            leftIndent=20
        ))

        return styles

    def generate_pdf_report(
        self,
        results: List[VerificationResult],
        document_name: str = "document.pdf",
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Generate a comprehensive PDF report from verification results.

        Args:
            results: List of verification results
            document_name: Name of the source document
            output_path: Path to save the report (auto-generated if None)

        Returns:
            Path to the generated report
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"fact_check_report_{timestamp}.pdf")

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []

        # Add header
        story.extend(self._create_header(document_name))

        # Add summary section
        story.extend(self._create_summary_section(results))

        # Add detailed results section
        story.extend(self._create_detailed_section(results))

        # Add footer info
        story.extend(self._create_footer())

        doc.build(story)
        logger.info(f"Generated PDF report at {output_path}")

        return output_path

    def generate_bytes(
        self,
        results: List[VerificationResult],
        document_name: str = "document.pdf"
    ) -> bytes:
        """
        Generate PDF report as bytes for download.

        Args:
            results: List of verification results
            document_name: Name of the source document

        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []
        story.extend(self._create_header(document_name))
        story.extend(self._create_summary_section(results))
        story.extend(self._create_detailed_section(results))
        story.extend(self._create_footer())

        doc.build(story)

        buffer.seek(0)
        return buffer.getvalue()

    def _create_header(self, document_name: str) -> List:
        """
        Create report header section.

        Args:
            document_name: Name of the analyzed document

        Returns:
            List of PDF elements
        """
        elements = []

        # Title
        elements.append(Paragraph(
            self.title,
            self.styles['ReportTitle']
        ))

        # Subtitle with document info
        timestamp = datetime.now().strftime("%B %d, %Y at %H:%M")
        subtitle = f"Analysis of: {document_name}<br/>Generated: {timestamp}"
        elements.append(Paragraph(subtitle, self.styles['ReportSubtitle']))

        elements.append(Spacer(1, 20))

        return elements

    def _create_summary_section(self, results: List[VerificationResult]) -> List:
        """
        Create summary statistics section.

        Args:
            results: Verification results

        Returns:
            List of PDF elements
        """
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))

        # Calculate statistics
        stats = self._calculate_statistics(results)

        summary_text = f"""
        Total Claims Analyzed: {stats['total']}<br/><br/>
        <b>Verification Results:</b><br/>
        - Verified: {stats['verified']} ({stats['verified_pct']:.1f}%)<br/>
        - Inaccurate: {stats['inaccurate']} ({stats['inaccurate_pct']:.1f}%)<br/>
        - False: {stats['false']} ({stats['false_pct']:.1f}%)<br/>
        - Unverifiable: {stats['unverifiable']} ({stats['unverifiable_pct']:.1f}%)<br/><br/>
        Average Confidence Score: {stats['avg_confidence']:.1f}%
        """
        elements.append(Paragraph(summary_text, self.styles['ClaimText']))
        elements.append(Spacer(1, 20))

        # Add summary table
        summary_table = self._create_summary_table(stats)
        if summary_table:
            elements.append(summary_table)
            elements.append(Spacer(1, 20))

        return elements

    def _create_summary_table(self, stats: Dict[str, Any]) -> Optional[Table]:
        """
        Create summary statistics table.

        Args:
            stats: Statistics dictionary

        Returns:
            PDF Table or None
        """
        data = [
            ['Category', 'Count', 'Percentage', 'Status'],
            ['Verified', str(stats['verified']), f"{stats['verified_pct']:.1f}%", 'Supported by sources'],
            ['Inaccurate', str(stats['inaccurate']), f"{stats['inaccurate_pct']:.1f}%", 'Contains errors'],
            ['False', str(stats['false']), f"{stats['false_pct']:.1f}%", 'Contradicted by sources'],
            ['Unverifiable', str(stats['unverifiable']), f"{stats['unverifiable_pct']:.1f}%", 'Insufficient data'],
        ]

        table = Table(data, colWidths=[1.5*inch, 0.8*inch, 1*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3436')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3436')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dfe6e9')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        return table

    def _create_detailed_section(self, results: List[VerificationResult]) -> List:
        """
        Create detailed results section with all claims.

        Args:
            results: Verification results

        Returns:
            List of PDF elements
        """
        elements = []

        elements.append(PageBreak())
        elements.append(Paragraph("Detailed Verification Results", self.styles['SectionHeader']))
        elements.append(Spacer(1, 10))

        for i, result in enumerate(results, 1):
            elements.extend(self._create_claim_section(result, i))

            # Add page break every 5 claims to avoid crowding
            if i % 5 == 0 and i < len(results):
                elements.append(PageBreak())

        return elements

    def _create_claim_section(self, result: VerificationResult, index: int) -> List:
        """
        Create section for a single claim.

        Args:
            result: Verification result
            index: Claim index number

        Returns:
            List of PDF elements
        """
        elements = []

        # Claim header with status
        category_color = self._get_category_text_color(result.category)
        header = f"""
        <b>Claim #{index}</b> [{result.category.value}]
        """
        elements.append(Paragraph(header, self.styles['SectionHeader']))

        # Claim text
        claim_text = f"<b>Claim:</b> {result.claim.text}"
        elements.append(Paragraph(claim_text, self.styles['ClaimText']))

        # Claim type
        type_info = f"<b>Type:</b> {result.claim.claim_type.value} | <b>Page:</b> {result.claim.page_number}"
        elements.append(Paragraph(type_info, self.styles['EvidenceText']))

        # Confidence
        confidence_text = f"<b>Confidence Score:</b> {result.confidence_score}%"
        elements.append(Paragraph(confidence_text, self.styles['EvidenceText']))

        # Explanation
        explanation = f"<b>Explanation:</b> {result.explanation}"
        elements.append(Paragraph(explanation, self.styles['EvidenceText']))

        # Evidence
        if result.evidence:
            elements.append(Paragraph("<b>Supporting Evidence:</b>", self.styles['EvidenceText']))
            for evidence in result.evidence[:3]:
                truncated = truncate_text(evidence, 150)
                elements.append(Paragraph(f"- {truncated}", self.styles['EvidenceText']))

        # Sources
        if result.source_urls:
            elements.append(Paragraph("<b>Sources:</b>", self.styles['EvidenceText']))
            for url in result.source_urls[:3]:
                elements.append(Paragraph(f"- {url}", self.styles['SourceLink']))

        elements.append(Spacer(1, 15))

        return elements

    def _create_footer(self) -> List:
        """
        Create report footer.

        Returns:
            List of PDF elements
        """
        elements = []

        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "--- End of Report ---",
            self.styles['ReportSubtitle']
        ))
        elements.append(Paragraph(
            f"Generated by Fact-Checking Application on {datetime.now().strftime('%Y-%m-%d')}",
            self.styles['SourceLink']
        ))

        return elements

    def _calculate_statistics(self, results: List[VerificationResult]) -> Dict[str, Any]:
        """
        Calculate summary statistics from results.

        Args:
            results: Verification results

        Returns:
            Dictionary of statistics
        """
        total = len(results)
        if total == 0:
            return {
                'total': 0,
                'verified': 0, 'verified_pct': 0,
                'inaccurate': 0, 'inaccurate_pct': 0,
                'false': 0, 'false_pct': 0,
                'unverifiable': 0, 'unverifiable_pct': 0,
                'avg_confidence': 0
            }

        verified = sum(1 for r in results if r.category == ClaimCategory.VERIFIED)
        inaccurate = sum(1 for r in results if r.category == ClaimCategory.INACCURATE)
        false = sum(1 for r in results if r.category == ClaimCategory.FALSE)
        unverifiable = sum(1 for r in results if r.category == ClaimCategory.UNVERIFIABLE)

        avg_confidence = sum(r.confidence_score for r in results) / total

        return {
            'total': total,
            'verified': verified,
            'verified_pct': (verified / total) * 100,
            'inaccurate': inaccurate,
            'inaccurate_pct': (inaccurate / total) * 100,
            'false': false,
            'false_pct': (false / total) * 100,
            'unverifiable': unverifiable,
            'unverifiable_pct': (unverifiable / total) * 100,
            'avg_confidence': avg_confidence
        }

    def _get_category_text_color(self, category: ClaimCategory) -> str:
        """Get text description for category color."""
        color_map = {
            ClaimCategory.VERIFIED: 'green',
            ClaimCategory.INACCURATE: 'orange',
            ClaimCategory.FALSE: 'red',
            ClaimCategory.UNVERIFIABLE: 'gray'
        }
        return color_map.get(category, 'gray')

    def generate_csv_export(self, results: List[VerificationResult]) -> str:
        """
        Generate CSV export of results.

        Args:
            results: Verification results

        Returns:
            CSV formatted string
        """
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Claim', 'Type', 'Category', 'Confidence',
            'Page', 'Explanation', 'Evidence', 'Sources'
        ])

        # Data rows
        for result in results:
            writer.writerow([
                result.claim.text,
                result.claim.claim_type.value,
                result.category.value,
                f"{result.confidence_score}%",
                result.claim.page_number,
                result.explanation,
                '; '.join(result.evidence[:3]),
                '; '.join(result.source_urls[:3])
            ])

        return output.getvalue()


def generate_report(results: List[VerificationResult], document_name: str) -> bytes:
    """
    Convenience function to generate PDF report.

    Args:
        results: List of verification results
        document_name: Name of the source document

    Returns:
        PDF content as bytes
    """
    generator = ReportGenerator()
    return generator.generate_bytes(results, document_name)


def generate_csv(results: List[VerificationResult]) -> str:
    """
    Convenience function to generate CSV export.

    Args:
        results: List of verification results

    Returns:
        CSV content as string
    """
    generator = ReportGenerator()
    return generator.generate_csv_export(results)


def main():
    """Test the report generator with sample data."""
    from utils import Claim, ClaimType

    # Create sample results
    sample_claims = [
        Claim(
            text="$12.5 billion",
            claim_type=ClaimType.FINANCIAL,
            source_text="Company reported revenue of $12.5 billion.",
            page_number=1
        ),
        Claim(
            text="50 million customers",
            claim_type=ClaimType.STATISTIC,
            source_text="The company serves over 50 million customers.",
            page_number=2
        )
    ]

    sample_results = [
        VerificationResult(
            claim=sample_claims[0],
            category=ClaimCategory.VERIFIED,
            confidence_score=85.5,
            evidence=["Revenue confirmed by SEC filing."],
            source_urls=["https://sec.gov/filing"],
            explanation="Claim is supported by official SEC filings."
        ),
        VerificationResult(
            claim=sample_claims[1],
            category=ClaimCategory.INACCURATE,
            confidence_score=42.0,
            evidence=["Company reports 47 million customers."],
            source_urls=["https://company.com/about"],
            explanation="Close but not exact - actual number is 47 million."
        )
    ]

    generator = ReportGenerator()
    output_path = generator.generate_pdf_report(sample_results)
    print(f"Generated report at: {output_path}")


if __name__ == "__main__":
    main()
