export interface BoundingBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  coordinate_system?: string;
}

export interface HighlightBox {
  bbox: BoundingBox;
  id: string;
  label?: string;
  pageIndex: number;
}

export interface DocumentItem {
  document_id: string;
  filename: string;
  page_count: number;
  processing_status: "pending" | "processing" | "ready" | "failed" | string;
  metadata?: Record<string, any>;
  updated_at?: string;
}

export interface SampleReport {
  document_id: string;
  title: string;
  filename: string;
  description: string;
  pages: number;
  sample_questions: Array<{
    category: string;
    label: string;
    question: string;
    intent: string;
    expected_answer?: string;
  }>;
}

export interface TableItem {
  table_id: string;
  document_id: string;
  pdf_page_index: number;
  printed_page_number: number | string | null;
  title: string | null;
  headers: string[][];
  rows: any[][];
  units: Record<string, string>;
  footnotes: string[];
  bbox: BoundingBox | null;
  extraction_confidence?: number | null;
}

export interface PageProvenance {
  document_id: string;
  pdf_page_index: number;
  printed_page_number: number | string | null;
  page_width: number;
  page_height: number;
  rotation?: number;
  warnings?: string[];
}

export interface EvidenceItem {
  evidence_id: string;
  document_id: string;
  pdf_page_index: number;
  printed_page_number: number | string | null;
  kind: "paragraph" | "heading" | "table" | "table_cell" | "chart" | "caption" | "footnote" | string;
  text: string;
  normalized_text?: string | null;
  bbox: BoundingBox | null;
  parent_id?: string | null;
  metadata?: Record<string, any>;
}

export interface DocumentEvidenceData {
  document_id: string;
  page_count: number;
  provenances: PageProvenance[];
  evidence_count: number;
  table_count: number;
  evidence: EvidenceItem[];
  tables: TableItem[];
}

export interface CitationItem {
  document_id: string;
  pdf_page_index: number;
  printed_page_number: number | string | null;
  evidence_id: string;
  bbox: BoundingBox | null;
  snippet?: string;
  kind?: string;
}

export interface CalculationRecord {
  operation: string;
  formula: string;
  raw_values: Record<string, any>;
  normalized_values: Record<string, any>;
  result: number | string;
  unit?: string;
  audit_trail?: string;
}

export interface VerificationCheck {
  name: string;
  passed: boolean;
  details: string;
}

export interface QuestionClassification {
  intent: "lookup" | "comparison" | "aggregation" | "trend" | "definition" | "multi_hop" | "unanswerable" | "ambiguous" | string;
  target_entities: string[];
  target_metrics: string[];
  target_periods: string[];
  requires_arithmetic: boolean;
  confidence: number;
  rationale?: string;
}

export interface ClaimItem {
  text: string;
  evidence_ids: string[];
  calculation?: CalculationRecord;
}

export interface PipelineTraceStep {
  stage: string;
  description: string;
  timestamp_ms: number;
  data: Record<string, any>;
}

export interface AnswerResponse {
  status: "answered" | "not_found" | "ambiguous" | "conflicting" | string;
  answer: string | null;
  claims: ClaimItem[];
  citations: CitationItem[];
  warnings: string[];
  classification?: QuestionClassification;
  calculation?: CalculationRecord;
  verification_checks: VerificationCheck[];
  pipeline_trace: PipelineTraceStep[];
}

export interface EvaluationSummary {
  total_cases: number;
  passed_cases: number;
  accuracy_percentage: number;
  retrieval_mrr?: number;
  arithmetic_accuracy?: number;
  abstention_precision?: number;
  avg_latency_ms?: number;
  average_latency_ms?: number;
}

export interface EvaluationCase {
  id: string;
  family: string;
  category: string;
  question: string;
  doc_id?: string;
  status?: string;
  passed: boolean;
  latency_ms: number;
  citations_count?: number;
  notes?: string[];
  calculation?: CalculationRecord;
}

export interface EvaluationData {
  summary: EvaluationSummary;
  cases?: EvaluationCase[];
  test_results?: EvaluationCase[];
}

export interface ActivityEntry {
  id: string;
  timestamp: string;
  title: string;
  details?: string;
  type: "index" | "query" | "upload" | "benchmark";
}

