import argparse
import json
import sys
import time
from pathlib import Path

from backend.app.pipeline.parser import PyMuPDFDocumentParser
from backend.app.pipeline.qa_service import QAService
from backend.app.pipeline.registry import get_registry

def run_command(args: argparse.Namespace) -> None:
    pdf_path = Path(args.pdf)
    questions_path = Path(args.questions)
    output_path = Path(args.output)

    if not pdf_path.is_file():
        print(f"Error: PDF file '{pdf_path}' not found.", file=sys.stderr)
        sys.exit(1)
    if not questions_path.is_file():
        print(f"Error: Questions file '{questions_path}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing and indexing PDF: {pdf_path.name}...")
    registry = get_registry()
    doc = registry.register_file(pdf_path, pdf_path.name)
    print(f"Document registered: {doc.document_id} ({doc.page_count} pages)")

    qa = QAService(registry)

    # Read questions
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = [json.loads(line) for line in f if line.strip()]

    print(f"Processing {len(questions)} questions...")
    results = []
    start_t = time.time()

    for idx, q_data in enumerate(questions):
        q_id = q_data.get("id", f"Q{idx+1:03d}")
        q_text = q_data.get("question", "")

        ans, page, conf = qa.answer(q_text, doc.document_id)
        res_record = {
            "id": q_id,
            "answer": ans,
            "page": page,
            "confidence": round(conf, 4),
        }
        results.append(res_record)

    # Write output JSONL
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out_f:
        for r in results:
            out_f.write(json.dumps(r) + "\n")

    elapsed = time.time() - start_t
    print(f"Completed {len(results)} questions in {elapsed:.2f}s ({elapsed/len(results)*1000:.1f}ms/query)")
    print(f"Output written to: {output_path}")

def benchmark_command(args: argparse.Namespace) -> None:
    pdf_path = Path(args.pdf)
    questions_path = Path(args.questions)

    if not pdf_path.is_file():
        print(f"Error: PDF file '{pdf_path}' not found.", file=sys.stderr)
        sys.exit(1)
    if not questions_path.is_file():
        print(f"Error: Benchmark questions file '{questions_path}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing and indexing PDF: {pdf_path.name}...")
    registry = get_registry()
    doc = registry.register_file(pdf_path, pdf_path.name)
    print(f"Document registered: {doc.document_id} ({doc.page_count} pages)")

    qa = QAService(registry)

    with open(questions_path, "r", encoding="utf-8") as f:
        gold_questions = [json.loads(line) for line in f if line.strip()]

    total = len(gold_questions)
    print(f"Running benchmark on {total} questions...")

    correct_answers = 0
    page_hits = 0

    # Abstention metrics
    true_unanswerable = 0
    pred_unanswerable = 0
    true_positive_unanswerable = 0

    error_sources: dict[str, int] = {
        "entity_not_found": 0,
        "wrong_column_metric": 0,
        "page_mismatch": 0,
        "false_abstention": 0,
        "missed_abstention": 0,
        "other": 0,
    }

    start_t = time.time()

    print("\n" + "=" * 90)
    print(f"{'ID':<6} | {'PREDICTED':<12} | {'GOLD':<12} | {'PRED_P':<6} | {'GOLD_PAGES':<16} | {'STATUS'}")
    print("=" * 90)

    for q in gold_questions:
        q_id = q.get("id")
        q_text = q.get("question")
        gold_ans = str(q.get("answer", "")).strip()
        gold_pages = q.get("gold_pages", [])

        pred_ans, pred_page, conf = qa.answer(q_text, doc.document_id)

        # Check exact answer match
        is_ans_correct = (pred_ans == gold_ans)
        if is_ans_correct:
            correct_answers += 1

        # Check page hit
        is_page_hit = False
        if gold_ans == "NOT_FOUND":
            true_unanswerable += 1
            if pred_ans == "NOT_FOUND":
                is_page_hit = (pred_page is None)
        else:
            is_page_hit = (pred_page in gold_pages) if pred_page else False

        if is_page_hit:
            page_hits += 1

        # Abstention tracking
        if pred_ans == "NOT_FOUND":
            pred_unanswerable += 1
            if gold_ans == "NOT_FOUND":
                true_positive_unanswerable += 1

        # Categorize error if failed
        status_label = "[PASS]" if (is_ans_correct and is_page_hit) else ("[PARTIAL]" if is_ans_correct else "[FAIL]")

        if not is_ans_correct:
            if gold_ans == "NOT_FOUND" and pred_ans != "NOT_FOUND":
                error_sources["missed_abstention"] += 1
            elif pred_ans == "NOT_FOUND" and gold_ans != "NOT_FOUND":
                error_sources["false_abstention"] += 1
            elif pred_page in gold_pages:
                error_sources["wrong_column_metric"] += 1
            else:
                error_sources["entity_not_found"] += 1

        pages_str = str(gold_pages[:3]) if len(gold_pages) <= 3 else f"{gold_pages[:3]}+"
        print(f"{q_id:<6} | {pred_ans:<12} | {gold_ans:<12} | {str(pred_page):<6} | {pages_str:<16} | {status_label}")

    elapsed = time.time() - start_t
    accuracy = (correct_answers / total) * 100.0
    page_hit_rate = (page_hits / total) * 100.0

    prec_abstain = (true_positive_unanswerable / pred_unanswerable * 100.0) if pred_unanswerable > 0 else 0.0
    rec_abstain = (true_positive_unanswerable / true_unanswerable * 100.0) if true_unanswerable > 0 else 0.0
    f1_abstain = (2 * prec_abstain * rec_abstain / (prec_abstain + rec_abstain)) if (prec_abstain + rec_abstain) > 0 else 0.0

    print("=" * 90)
    print("BENCHMARK EVALUATION SUMMARY")
    print("=" * 90)
    print(f"Total Questions Evaluated:    {total}")
    print(f"Exact Answer Accuracy:        {accuracy:.2f}% ({correct_answers}/{total})")
    print(f"Page Hit Rate:                {page_hit_rate:.2f}% ({page_hits}/{total})")
    print(f"Abstention Precision:         {prec_abstain:.2f}% ({true_positive_unanswerable}/{pred_unanswerable})")
    print(f"Abstention Recall:            {rec_abstain:.2f}% ({true_positive_unanswerable}/{true_unanswerable})")
    print(f"Abstention F1 Score:          {f1_abstain:.2f}%")
    print(f"Average Query Latency:        {elapsed/total*1000:.1f}ms")
    print("\nERROR SOURCE BREAKDOWN:")
    for err_type, count in sorted(error_sources.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  - {err_type.replace('_', ' ').title()}: {count} cases")
    print("=" * 90)

def main():
    parser = argparse.ArgumentParser(description="Report Intelligence Assistant - CLI & Benchmark")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run
    run_parser = subparsers.add_parser("run", help="Run inference on questions JSONL and produce target output JSONL")
    run_parser.add_argument("--pdf", required=True, help="Path to PDF report")
    run_parser.add_argument("--questions", required=True, help="Path to input questions JSONL")
    run_parser.add_argument("--output", required=True, help="Path to write output predictions JSONL")

    # Subcommand: benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmark evaluation against gold questions")
    bench_parser.add_argument("--pdf", required=True, help="Path to PDF report")
    bench_parser.add_argument("--questions", required=True, help="Path to questions_with_answers.jsonl")

    args = parser.parse_args()
    if args.command == "run":
        run_command(args)
    elif args.command == "benchmark":
        benchmark_command(args)

if __name__ == "__main__":
    main()

