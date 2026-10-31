import sys
from backend.app.api.routes.evaluation import execute_benchmark

def run_cli_eval():
    print("=" * 74)
    print("  REPORT INTELLIGENCE ASSISTANT - COMPREHENSIVE BENCHMARK EVALUATION")
    print("=" * 74)

    data = execute_benchmark()
    summary = data["summary"]
    cases = data["cases"]

    for c in cases:
        mark = "PASS" if c["passed"] else "FAIL"
        print(f"\n[{c['id']}] {c['family']} | {c['category']}")
        print(f"  Q: '{c['question']}'")
        print(f"  Result: {mark} ({c['latency_ms']}ms) | Status: {c['status'].upper()} | Citations: {c['citations_count']}")
        if c["calculation"]:
            calc = c["calculation"]
            print(f"  Formula: {calc['formula']} => {calc['result']} {calc.get('unit') or ''}")
        if c["notes"]:
            for n in c["notes"]:
                print(f"    - {n}")

    print("\n" + "=" * 74)
    print("  SUMMARY SCORECARD")
    print("=" * 74)
    print(f"  Total Benchmark Cases  : {summary['total_cases']}")
    print(f"  Passed Cases           : {summary['passed_cases']}")
    print(f"  Accuracy Percentage    : {summary['accuracy_percentage']}%")
    print(f"  Retrieval MRR          : {summary['retrieval_mrr']}")
    print(f"  Arithmetic Accuracy    : {summary['arithmetic_accuracy']}%")
    print(f"  Abstention Precision   : {summary['abstention_precision']}%")
    print(f"  Average Latency        : {summary['avg_latency_ms']} ms")
    print("=" * 74)

    return summary["passed_cases"] == summary["total_cases"]

if __name__ == "__main__":
    success = run_cli_eval()
    sys.exit(0 if success else 1)
