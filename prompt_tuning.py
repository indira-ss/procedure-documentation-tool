"""
Day 6 — Prompt Tuning Script
Runs 10 real inputs through each prompt (describe, recommend, generate-report),
scores each output, and prints a summary.

Usage:
    python prompt_tuning.py

Requirements:
    pip install groq python-dotenv
    .env must contain GROQ_API_KEY=...

Scoring rubric (1-5 per output):
    5 — Perfect: all required fields present, responses are specific and accurate
    4 — Good: all fields present, minor vagueness
    3 — Acceptable: missing 1 field or partially vague
    2 — Poor: missing multiple fields or clearly off-topic
    1 — Fail: JSON parse error or is_fallback=True
"""

import os
import json
import sys
import textwrap
from datetime import datetime, timezone

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


# --------------------------------------------------------------------------- #
# Helper                                                                       #
# --------------------------------------------------------------------------- #

def load_prompt(filename: str) -> str:
    with open(os.path.join(PROMPTS_DIR, filename), encoding="utf-8") as fh:
        return fh.read()


def call_groq(prompt: str, temperature: float = 0.3) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=1000,
    )
    return resp.choices[0].message.content


def parse_json(raw: str) -> dict | None:
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    try:
        return json.loads(clean.strip())
    except json.JSONDecodeError:
        return None


def score_report(result: dict | None) -> tuple[int, str]:
    if result is None:
        return 1, "JSON parse failure"
    if result.get("is_fallback"):
        return 1, "Fallback returned"
    required = ["title", "summary", "overview", "key_items", "recommendations", "quality_score"]
    missing = [f for f in required if f not in result]
    if missing:
        return 2, f"Missing fields: {missing}"
    if not result.get("key_items"):
        return 3, "key_items is empty"
    if not result.get("recommendations"):
        return 3, "recommendations is empty"
    overview = result.get("overview", {})
    if not overview.get("purpose") or not overview.get("scope"):
        return 3, "overview.purpose or scope missing"
    if len(result.get("summary", "")) < 60:
        return 3, "summary too short"
    if len(result.get("key_items", [])) < 2:
        return 4, "fewer than 2 key_items"
    return 5, "All fields present and complete"


def score_describe(result: dict | None) -> tuple[int, str]:
    if result is None:
        return 1, "JSON parse failure"
    if result.get("is_fallback"):
        return 1, "Fallback returned"
    required = ["description", "key_steps", "generated_at"]
    missing = [f for f in required if f not in result]
    if missing:
        return 2, f"Missing fields: {missing}"
    if len(result.get("description", "")) < 50:
        return 3, "description too short"
    if not result.get("key_steps"):
        return 3, "key_steps empty"
    return 5, "Complete"


def score_recommend(result) -> tuple[int, str]:
    if result is None:
        return 1, "JSON parse failure"
    if isinstance(result, dict) and result.get("is_fallback"):
        return 1, "Fallback returned"
    if not isinstance(result, list):
        # might be wrapped
        if isinstance(result, dict):
            result = result.get("recommendations", [])
        else:
            return 2, "Not a list"
    if len(result) < 3:
        return 3, f"Only {len(result)} recommendations (need 3)"
    for rec in result:
        if not all(k in rec for k in ("action_type", "description", "priority")):
            return 3, "Recommendation missing required keys"
    return 5, "Complete"


# --------------------------------------------------------------------------- #
# Test inputs                                                                  #
# --------------------------------------------------------------------------- #

REPORT_INPUTS = [
    {
        "title": "Employee Onboarding Process",
        "description": "Standard procedure for integrating new hires into the company systems and culture.",
        "category": "HR",
        "status": "Active",
        "created_by": "HR Team",
        "steps": "1. Send welcome email. 2. Set up accounts. 3. Assign buddy. 4. Schedule orientation.",
        "additional_context": "Applies to all full-time employees starting on a Monday.",
    },
    {
        "title": "Server Deployment Checklist",
        "description": "Steps to safely deploy a new application version to the production server.",
        "category": "DevOps",
        "status": "Active",
        "created_by": "Platform Team",
        "steps": "1. Run tests. 2. Create backup. 3. Push image. 4. Run migrations. 5. Smoke test.",
        "additional_context": "Must be completed during maintenance window 02:00-04:00 UTC.",
    },
    {
        "title": "Customer Refund Policy",
        "description": "Procedure for processing customer refund requests.",
        "category": "Finance",
        "status": "Draft",
        "created_by": "Finance Ops",
        "steps": "1. Verify purchase. 2. Check eligibility. 3. Process in system. 4. Send confirmation.",
        "additional_context": "Refunds within 30 days only.",
    },
    {
        "title": "Incident Response Plan",
        "description": "Steps to follow when a production incident is detected.",
        "category": "Engineering",
        "status": "Active",
        "created_by": "SRE Team",
        "steps": "1. Page on-call. 2. Create war room. 3. Investigate. 4. Mitigate. 5. Post-mortem.",
        "additional_context": "P1 incidents require CEO notification within 30 minutes.",
    },
    {
        "title": "Annual Performance Review",
        "description": "Structured process for conducting yearly employee performance evaluations.",
        "category": "HR",
        "status": "Active",
        "created_by": "People Ops",
        "steps": "1. Self assessment. 2. Manager review. 3. Calibration. 4. Feedback meeting. 5. Goal setting.",
        "additional_context": "Completed in Q4 each year.",
    },
    {
        "title": "Data Backup Procedure",
        "description": "Automated and manual backup process for all company databases.",
        "category": "IT",
        "status": "Active",
        "created_by": "IT Infrastructure",
        "steps": "1. Automated nightly backup. 2. Weekly manual verification. 3. Quarterly restore test.",
        "additional_context": "Backups retained for 90 days.",
    },
    {
        "title": "Vendor Onboarding",
        "description": "Process for approving and setting up new external vendors in company systems.",
        "category": "Procurement",
        "status": "Draft",
        "created_by": "Procurement Team",
        "steps": "1. Legal review. 2. Security assessment. 3. Contract sign. 4. System access setup.",
        "additional_context": "All vendors must complete security questionnaire.",
    },
    {
        "title": "Customer Support Escalation",
        "description": "Process to escalate unresolved customer issues to senior support or engineering.",
        "category": "Support",
        "status": "Active",
        "created_by": "Support Lead",
        "steps": "1. L1 attempts resolution. 2. Document attempts. 3. Escalate to L2. 4. Set SLA timer.",
        "additional_context": "L2 must respond within 4 hours.",
    },
    {
        "title": "Office Security Protocol",
        "description": "Physical security procedure for office entry, visitor management, and after-hours access.",
        "category": "Facilities",
        "status": "Active",
        "created_by": "Facilities Manager",
        "steps": "1. Badge scan entry. 2. Visitor sign-in. 3. Escort required. 4. After-hours alarm procedure.",
        "additional_context": "Applies to all three office locations.",
    },
    {
        "title": "Product Release Workflow",
        "description": "End-to-end process for releasing new product features from development to customers.",
        "category": "Product",
        "status": "Active",
        "created_by": "Product Manager",
        "steps": "1. Feature freeze. 2. QA sign-off. 3. Staging deploy. 4. Go/No-Go meeting. 5. Prod release. 6. Monitor.",
        "additional_context": "Releases happen every two weeks on Wednesdays.",
    },
]


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

def run_suite(name: str, inputs: list, prompt_file: str, score_fn, temperature=0.3):
    print(f"\n{'='*70}")
    print(f"  ENDPOINT: {name}  |  Prompt: {prompt_file}")
    print(f"{'='*70}")

    template = load_prompt(prompt_file)
    scores = []
    generated_at = datetime.now(timezone.utc).isoformat()

    for i, inp in enumerate(inputs, 1):
        try:
            prompt = template.format(**inp, generated_at=generated_at)
            raw = call_groq(prompt, temperature=temperature)
            result = parse_json(raw)
            score, note = score_fn(result)
        except Exception as exc:
            score, note = 1, f"Exception: {exc}"

        scores.append(score)
        bar = "█" * score + "░" * (5 - score)
        status = "✓" if score >= 4 else ("~" if score == 3 else "✗")
        print(f"  [{status}] Input {i:02d} | Score {score}/5 [{bar}] — {note}")

    avg = sum(scores) / len(scores)
    passing = sum(1 for s in scores if s >= 4)
    print(f"\n  Average: {avg:.1f}/5  |  Passing (≥4): {passing}/{len(scores)}")
    if avg < 3.5:
        print("  ⚠ BELOW TARGET — prompt needs rewriting")
    elif avg < 4.0:
        print("  ↗ MARGINAL — review failing cases")
    else:
        print("  ✓ MEETS TARGET")
    return scores


def main():
    print("\n" + "▓"*70)
    print("  DAY 6 — PROMPT TUNING  |  Tool-32 Procedure Documentation Tool")
    print("  AI Developer 1         |  " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("▓"*70)

    all_scores = {}

    # ── /generate-report ─────────────────────────────────────────────────── #
    scores = run_suite(
        name="POST /generate-report",
        inputs=REPORT_INPUTS,
        prompt_file="generate_report_prompt.txt",
        score_fn=score_report,
        temperature=0.3,
    )
    all_scores["generate-report"] = scores

    # ── /describe (if prompt exists) ──────────────────────────────────────── #
    describe_prompt = os.path.join(PROMPTS_DIR, "describe_prompt.txt")
    if os.path.exists(describe_prompt):
        # Re-use same inputs with a subset of fields
        describe_inputs = [
            {"title": inp["title"], "description": inp["description"],
             "category": inp["category"], "generated_at": datetime.now(timezone.utc).isoformat()}
            for inp in REPORT_INPUTS
        ]
        scores = run_suite(
            name="POST /describe",
            inputs=describe_inputs,
            prompt_file="describe_prompt.txt",
            score_fn=score_describe,
            temperature=0.3,
        )
        all_scores["describe"] = scores
    else:
        print("\n  [SKIP] describe_prompt.txt not found — skipping /describe tuning")

    # ── /recommend (if prompt exists) ────────────────────────────────────── #
    recommend_prompt = os.path.join(PROMPTS_DIR, "recommend_prompt.txt")
    if os.path.exists(recommend_prompt):
        recommend_inputs = [
            {"title": inp["title"], "description": inp["description"],
             "category": inp["category"], "generated_at": datetime.now(timezone.utc).isoformat()}
            for inp in REPORT_INPUTS
        ]
        scores = run_suite(
            name="POST /recommend",
            inputs=recommend_inputs,
            prompt_file="recommend_prompt.txt",
            score_fn=score_recommend,
            temperature=0.5,
        )
        all_scores["recommend"] = scores
    else:
        print("\n  [SKIP] recommend_prompt.txt not found — skipping /recommend tuning")

    # ── Overall summary ───────────────────────────────────────────────────── #
    print(f"\n{'='*70}")
    print("  OVERALL SUMMARY")
    print(f"{'='*70}")
    for endpoint, scores in all_scores.items():
        avg = sum(scores) / len(scores)
        label = "✓ PASS" if avg >= 4.0 else ("~ MARGINAL" if avg >= 3.5 else "✗ FAIL — rewrite prompt")
        print(f"  {endpoint:<25} avg={avg:.1f}/5  {label}")
    print()


if __name__ == "__main__":
    main()
