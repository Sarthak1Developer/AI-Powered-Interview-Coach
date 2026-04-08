"""
Deterministic OpenAI baseline for InterviewCoachEnv.

What this script does:
1. Runs one representative task from each level: easy, medium, hard.
2. Uses OpenAI Chat Completions to generate answer attempts.
3. Interacts with environment via OpenEnv-style step(action).
4. Produces reproducible scores and writes JSON report.

Requirements:
- API_KEY environment variable
- pip install openai

Run:
  python baseline.py
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Load env vars from a local .env file when available (MUST be before reading env vars).
if load_dotenv is not None:
    load_dotenv()

from rl_interview_coach import Action, InterviewCoachEnv, TaskBank, TaskType, FeedbackStrategy

try:
    from openai import OpenAI
except ImportError as exc:
    raise RuntimeError("openai package is required. Install with: pip install openai") from exc


MODEL_NAME = "gpt-4o-mini"
MAX_ATTEMPTS = 3
REPORT_PATH = Path("reports/baseline_openai_report.json")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or os.getenv("API_BASE_URL")


@dataclass
class TaskResult:
    task_id: str
    difficulty: str
    question: str
    best_grade: float
    final_grade: float
    total_reward: float
    attempts: int
    success: bool


def _require_api_key() -> str:
    key = os.getenv("API_KEY")
    if not key:
        raise ValueError("API_KEY is not set")
    return key


def _select_three_tasks():
    return [
        TaskBank.get_tasks_by_difficulty(TaskType.EASY)[0],
        TaskBank.get_tasks_by_difficulty(TaskType.MEDIUM)[0],
        TaskBank.get_tasks_by_difficulty(TaskType.HARD)[0],
    ]


def _compose_prompt(question: str, attempt: int, previous_feedback: List[str]) -> str:
    feedback_text = "\n".join(previous_feedback[-2:]) if previous_feedback else "None"
    return (
        "You are answering a real interview question. "
        "Return only the answer text.\n\n"
        f"Question: {question}\n"
        f"Attempt: {attempt}\n"
        "Target: concise but complete, concrete examples, measurable outcomes when possible.\n"
        f"Prior feedback: {feedback_text}\n"
    )


def _pick_strategy(attempt: int) -> FeedbackStrategy:
    # Deterministic strategy schedule for reproducibility.
    if attempt == 1:
        return FeedbackStrategy.HINT
    if attempt == 2:
        return FeedbackStrategy.MODERATE
    return FeedbackStrategy.STRICT


def run_baseline() -> Dict:
    api_key = _require_api_key()
    client = OpenAI(api_key=api_key, base_url=OPENAI_BASE_URL) if OPENAI_BASE_URL else OpenAI(api_key=api_key)
    env = InterviewCoachEnv(seed=42, max_attempts=MAX_ATTEMPTS, target_grade=0.80)

    task_results: List[TaskResult] = []

    for task in _select_three_tasks():
        obs = env.reset(task)
        total_reward = 0.0
        best_grade = 0.0
        feedback_history: List[str] = []
        final_grade = 0.0
        success = False

        for attempt in range(1, MAX_ATTEMPTS + 1):
            strategy = _pick_strategy(attempt)
            prompt = _compose_prompt(task.question, attempt, feedback_history)

            response = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": "You produce interview answers only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=260,
            )
            answer = (response.choices[0].message.content or "").strip()
            action = Action(strategy=strategy, confidence=0.95, response_text=answer)

            step_result = env.step(action)
            total_reward += step_result.reward.total
            final_grade = step_result.observation.current_grade
            best_grade = max(best_grade, final_grade)

            feedback = step_result.info.get("feedback", "")
            if isinstance(feedback, str) and feedback:
                feedback_history.append(feedback)

            if step_result.done:
                success = step_result.reward.success
                break

        task_results.append(
            TaskResult(
                task_id=task.task_id,
                difficulty=task.difficulty.value,
                question=task.question,
                best_grade=best_grade,
                final_grade=final_grade,
                total_reward=total_reward,
                attempts=attempt,
                success=success,
            )
        )

    aggregate_score = sum(t.final_grade for t in task_results) / len(task_results)
    success_rate = sum(1 for t in task_results if t.success) / len(task_results)

    report = {
        "model": MODEL_NAME,
        "base_url": OPENAI_BASE_URL or "https://api.openai.com/v1",
        "seed": 42,
        "max_attempts": MAX_ATTEMPTS,
        "aggregate_score": round(aggregate_score, 4),
        "success_rate": round(success_rate, 4),
        "tasks": [
            {
                "task_id": t.task_id,
                "difficulty": t.difficulty,
                "question": t.question,
                "best_grade": round(t.best_grade, 4),
                "final_grade": round(t.final_grade, 4),
                "total_reward": round(t.total_reward, 4),
                "attempts": t.attempts,
                "success": t.success,
            }
            for t in task_results
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    report = run_baseline()
    print("OpenAI baseline complete")
    print(f"Aggregate score: {report['aggregate_score']:.4f}")
    print(f"Success rate: {report['success_rate']:.2%}")
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
