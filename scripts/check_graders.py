import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rl_interview_coach import TaskBank, TaskType
from rl_interview_coach.graders.answer_grader import get_grader


def main() -> None:
    tasks = [
        TaskBank.get_tasks_by_difficulty(TaskType.EASY)[0],
        TaskBank.get_tasks_by_difficulty(TaskType.MEDIUM)[0],
        TaskBank.get_tasks_by_difficulty(TaskType.HARD)[0],
    ]

    print("Checking grader score ranges for representative tasks...")
    for task in tasks:
        grader, grader_type = get_grader(task.question, task.difficulty.value)
        sample = task.examples[0] if task.examples else "Sample answer"

        if grader_type == "behavioral":
            score, _ = grader.grade(sample)
        else:
            score, _ = grader.grade(task.question, sample)

        ok = 0.0 <= score <= 1.0
        print(f"{task.task_id} ({grader_type}): score={score:.4f} in_range={ok}")
        if not ok:
            raise SystemExit(f"Score out of range for task {task.task_id}")

    print("All representative grader checks passed.")


if __name__ == "__main__":
    main()
