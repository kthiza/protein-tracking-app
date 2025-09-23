import os
import json
from datetime import datetime

from food_detection import identify_food_with_google_vision


TEST_DIR = os.path.join(os.path.dirname(__file__), "test pics")
SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "test_summary.md")


def run_tests(min_items: int = 1):
    results = []
    total = 0
    passed = 0

    if not os.path.isdir(TEST_DIR):
        raise SystemExit(f"Test directory not found: {TEST_DIR}")

    image_files = [
        f for f in os.listdir(TEST_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".jfif"))
    ]
    image_files.sort()

    for fname in image_files:
        total += 1
        path = os.path.join(TEST_DIR, fname)

        foods = []
        error = None
        try:
            foods = identify_food_with_google_vision(path)
        except Exception as e:
            error = str(e)

        ok = bool(foods) and len(foods) >= min_items and not error
        if ok:
            passed += 1

        results.append({
            "file": fname,
            "foods": foods,
            "passed": ok,
            "error": error,
        })

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "results": results,
    }


def write_summary(report: dict):
    lines = []
    lines.append(f"## Food detection test report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"- Total: {report['total']}")
    lines.append(f"- Passed: {report['passed']}")
    lines.append(f"- Failed: {report['failed']}")
    lines.append("")
    lines.append("### Details")
    for r in report["results"]:
        foods_str = ", ".join(r["foods"]) if r["foods"] else "-"
        status = "PASS" if r["passed"] else "FAIL"
        err = f" | error: {r['error']}" if r["error"] else ""
        lines.append(f"- {status} — {r['file']} — foods: {foods_str}{err}")

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    report = run_tests()
    write_summary(report)
    # Also dump JSON next to the markdown for debugging
    with open(os.path.splitext(SUMMARY_PATH)[0] + ".json", "w", encoding="utf-8") as jf:
        json.dump(report, jf, indent=2)
    print(f"Done. See summary at: {SUMMARY_PATH}")


