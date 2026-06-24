export type ClaimCategory = 'Verified' | 'Inaccurate' | 'False' | 'Unverifiable';
export type ClaimType = 'Statistic' | 'Date/Temporal' | 'Financial/Monetary' | 'Technical/Specification' | 'Percentage/Ratio' | 'General Fact';

export interface Claim {
  text: string;
  claim_type: ClaimType;
  source_text: string;
  page_number: number;
}

export interface VerificationResult {
  claim_text: string;
  claim_type: ClaimType;
  category: ClaimCategory;
  confidence_score: number;
  evidence: string[];
  source_urls: string[];
  explanation: string;
  page_number: number;
}

export interface ProcessingSession {
  id: string;
  document_name: string;
  results: VerificationResult[];
  created_at: string;
}

export type SortKey = 'confidence_score' | 'category' | 'page_number';
export type SortDir = 'asc' | 'desc';
