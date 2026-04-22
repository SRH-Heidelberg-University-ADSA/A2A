"""
A2A Coordination Evaluation Script
Evaluates the AI Assistant's ability to correctly route queries
to the right specialized agents using CLEAR-style metrics.

Metrics:
- Routing Accuracy: Did the LLM pick the correct agent or tool?
- Latency: End-to-end time for each query
- Output Completeness: Did the agent return a meaningful response?
- Fallback Accuracy: Did the LLM correctly refuse out-of-scope queries?
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows terminal encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load .env from AI_Assistant root
load_dotenv(Path(__file__).parent.parent / ".env")

COORDINATOR_URL = os.getenv("COORDINATOR_URL", "http://localhost:8000")
API_KEY = os.getenv("APP_API_KEY", "")

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}


def send_query(query: str) -> dict:
    """Send a query to the A2A coordinator and return the full response with timing."""
    payload = {"query": query, "user_id": "eval_user"}
    start = time.time()
    try:
        resp = requests.post(
            f"{COORDINATOR_URL}/api/query",
            headers=HEADERS,
            json=payload,
            timeout=120
        )
        latency = time.time() - start
        resp.raise_for_status()
        data = resp.json()
        return {
            "status": "success",
            "latency": latency,
            "response": data.get("response", ""),
            "trace": data.get("trace", []),
            "enhanced": data.get("enhanced", False),
            "input_tokens": data.get("input_tokens", 0),
            "output_tokens": data.get("output_tokens", 0)
        }
    except Exception as e:
        return {
            "status": "error",
            "latency": time.time() - start,
            "response": str(e),
            "trace": [],
            "enhanced": False,
            "input_tokens": 0,
            "output_tokens": 0
        }


def extract_routed_agent(trace: list) -> str | None:
    """Extract which agent was delegated to from the trace log."""
    for entry in trace:
        if "LLM Decision" in str(entry) and "Matched" in str(entry):
            # Format: "**LLM Decision**: Matched `Agent_Name` for request"
            parts = str(entry).split("`")
            if len(parts) >= 2:
                return parts[1]
    return None


def extract_used_tool(trace: list) -> str | None:
    """Extract which local tool was used from the trace log."""
    for entry in trace:
        if "Local Assistant Tool" in str(entry):
            parts = str(entry).split("`")
            if len(parts) >= 2:
                return parts[1]
    return None


def check_output_completeness(response: str) -> dict:
    """Check if the response has meaningful content (not truncated)."""
    if not response:
        return {"complete": False, "reason": "Empty response"}

    word_count = len(response.split())
    has_content = word_count > 10

    # Check for truncation indicators
    truncation_markers = [
        "here's the", "here is the", "here are the",
        "below is", "as follows"
    ]
    ends_abruptly = any(
        response.strip().lower().endswith(marker)
        for marker in truncation_markers
    )

    if ends_abruptly and word_count < 50:
        return {"complete": False, "reason": "Response appears truncated"}

    return {"complete": has_content, "reason": "OK" if has_content else "Too short"}


def evaluate_task(task: dict) -> dict:
    """Evaluate a single benchmark task."""
    query = task["query"]
    expected_agent = task.get("expected_agent")
    expected_action = task["expected_action"]
    expected_tool = task.get("expected_tool")

    print(f"\n  Testing: {task['id']} — \"{query[:60]}...\"")

    result = send_query(query)

    if result["status"] == "error":
        print(f"    ❌ Error: {result['response'][:80]}")
        return {
            "task_id": task["id"],
            "category": task["category"],
            "routing_correct": False,
            "latency": result["latency"],
            "output_complete": False,
            "input_tokens": 0,
            "output_tokens": 0,
            "error": result["response"]
        }

    routed_agent = extract_routed_agent(result["trace"])
    used_tool = extract_used_tool(result["trace"])
    completeness = check_output_completeness(result["response"])

    # Determine routing correctness
    if expected_action == "delegate":
        routing_correct = (routed_agent == expected_agent)
        action_taken = f"Delegated to {routed_agent}" if routed_agent else "No delegation"
    elif expected_action == "local_tool":
        routing_correct = (used_tool is not None) and (routed_agent is None)
        action_taken = f"Used tool: {used_tool}" if used_tool else "No tool used"
    elif expected_action == "fallback":
        routing_correct = (routed_agent is None) and (used_tool is None)
        action_taken = "Fallback (no delegation)" if routing_correct else f"Wrongly delegated to {routed_agent or used_tool}"
    else:
        routing_correct = False
        action_taken = "Unknown"

    status = "✅" if routing_correct else "❌"
    in_tok = result.get("input_tokens", 0)
    out_tok = result.get("output_tokens", 0)
    print(f"    {status} {action_taken} | Latency: {result['latency']:.2f}s | Tokens: {in_tok}in/{out_tok}out | Complete: {completeness['complete']}")

    return {
        "task_id": task["id"],
        "category": task["category"],
        "query": query,
        "expected_action": expected_action,
        "expected_agent": expected_agent,
        "actual_agent": routed_agent,
        "actual_tool": used_tool,
        "routing_correct": routing_correct,
        "latency": result["latency"],
        "output_complete": completeness["complete"],
        "output_reason": completeness["reason"],
        "input_tokens": result.get("input_tokens", 0),
        "output_tokens": result.get("output_tokens", 0),
        "response_preview": result["response"][:200],
        "trace": result["trace"]
    }


def run_evaluation(benchmark_file: str = None, output_file: str = None):
    """Run the full A2A evaluation suite."""
    if benchmark_file is None:
        benchmark_file = Path(__file__).parent / "a2a_benchmark_tasks.json"
    if output_file is None:
        output_file = Path(__file__).parent / "a2a_eval_results.json"

    with open(benchmark_file, "r") as f:
        tasks = json.load(f)

    print("=" * 60)
    print("A2A COORDINATION EVALUATION")
    print(f"Target: {COORDINATOR_URL}")
    print(f"Tasks: {len(tasks)}")
    print("=" * 60)

    results = []
    for task in tasks:
        result = evaluate_task(task)
        results.append(result)

    # --- Per-Category Metrics ---
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"correct": 0, "total": 0, "latencies": [], "complete": 0, "input_tokens": 0, "output_tokens": 0}
        categories[cat]["total"] += 1
        if r["routing_correct"]:
            categories[cat]["correct"] += 1
        categories[cat]["latencies"].append(r["latency"])
        if r.get("output_complete"):
            categories[cat]["complete"] += 1
        categories[cat]["input_tokens"] += r.get("input_tokens", 0)
        categories[cat]["output_tokens"] += r.get("output_tokens", 0)

    # --- Overall Metrics ---
    total = len(results)
    correct = sum(1 for r in results if r["routing_correct"])
    avg_latency = sum(r["latency"] for r in results) / total if total else 0
    complete = sum(1 for r in results if r.get("output_complete"))
    total_input_tokens = sum(r.get("input_tokens", 0) for r in results)
    total_output_tokens = sum(r.get("output_tokens", 0) for r in results)

    print("\n" + "=" * 60)
    print("PER-AGENT / CATEGORY RESULTS")
    print("=" * 60)
    for cat, stats in categories.items():
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] else 0
        avg_lat = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
        comp = (stats["complete"] / stats["total"]) * 100 if stats["total"] else 0
        print(f"  {cat:20s} | Routing: {acc:5.1f}% | Avg Latency: {avg_lat:.2f}s | Output Complete: {comp:.1f}%")

    print("\n" + "=" * 60)
    print("OVERALL A2A COORDINATION METRICS")
    print("=" * 60)
    print(f"  Routing Accuracy : {(correct/total)*100:.1f}% ({correct}/{total})")
    print(f"  Average Latency  : {avg_latency:.2f}s")
    print(f"  Output Complete  : {(complete/total)*100:.1f}% ({complete}/{total})")
    print(f"  Total Input Tok  : {total_input_tokens}")
    print(f"  Total Output Tok : {total_output_tokens}")
    print("=" * 60)

    # Save results
    summary = {
        "overall": {
            "routing_accuracy": (correct / total) * 100 if total else 0,
            "average_latency": avg_latency,
            "output_completeness": (complete / total) * 100 if total else 0,
            "total_tasks": total,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens
        },
        "per_category": {
            cat: {
                "routing_accuracy": (s["correct"] / s["total"]) * 100 if s["total"] else 0,
                "avg_latency": sum(s["latencies"]) / len(s["latencies"]) if s["latencies"] else 0,
                "output_completeness": (s["complete"] / s["total"]) * 100 if s["total"] else 0,
                "total": s["total"],
                "input_tokens": s["input_tokens"],
                "output_tokens": s["output_tokens"]
            }
            for cat, s in categories.items()
        },
        "individual_results": results
    }

    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")

    return summary


if __name__ == "__main__":
    run_evaluation()
