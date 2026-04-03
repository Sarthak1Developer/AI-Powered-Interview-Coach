"""
Interview Coach RL Environment - OpenEnv Compliant.

Implements a reinforcement learning environment for interview coaching.
The agent observes the current state (user's answer quality) and decides
which feedback strategy to use (strict, moderate, hint) to improve the answer.

OpenEnv Interface:
- reset(): Initialize episode and return initial observation
- step(action): Process action, simulate feedback, get new observation & reward
- state(): Get current observation
"""
import random
import uuid
from typing import Optional, Dict, Tuple
from datetime import datetime

from .models import (
    Observation, Action, Reward, StepReturn, FeedbackStrategy, DifficultyLevel
)
from .tasks import TaskBank, Task, TaskType
from ..graders.answer_grader import get_grader


class InterviewCoachEnv:
    """
    RL Environment for interview coaching.
    
    State Space (Observation):
    - Task difficulty (easy/medium/hard)
    - Answer quality metrics (keywords, length, sentiment, structure)
    - Attempt number and history
    - Previous feedback strategies
    
    Action Space:
    - Three feedback strategies: strict, moderate, hint
    
    Reward:
    - Improvement in answer grade
    - Efficiency (penalty for excessive attempts)
    - Bonus for reaching target grade within attempts
    """
    
    # Feedback templates for each strategy
    FEEDBACK_TEMPLATES = {
        FeedbackStrategy.STRICT: {
            "description": "Detailed critical feedback pointing out all issues",
            "template": """
STRICT FEEDBACK:
Your answer has the following issues that need immediate attention:
- Missing key elements: {missing_keywords}
- Answer too {length_issue}
- Structure could be improved: {structure_feedback}
Please revise and focus on these specific areas.
            """
        },
        FeedbackStrategy.MODERATE: {
            "description": "Balanced feedback with both strengths and areas for improvement",
            "template": """
BALANCED FEEDBACK:
Strengths:
- You covered some good points ({covered_keywords})
Areas for improvement:
- Add more specific examples
- Expand on {structure_feedback}
- Ensure at least {min_length} words
            """
        },
        FeedbackStrategy.HINT: {
            "description": "Minimal guidance that guides discovery",
            "template": """
HINT:
Think about:
- What are the key {domain} concepts your answer should include?
- Can you provide any specific examples or metrics?
- Is your answer structured clearly with beginning, middle, and end?
            """
        }
    }
    
    def __init__(
        self,
        seed: Optional[int] = None,
        max_attempts: int = 5,
        target_grade: float = 0.80
    ):
        """
        Initialize the environment.
        
        Args:
            seed: Random seed for reproducibility
            max_attempts: Maximum number of answer attempts
            target_grade: Target grade to consider episode successful
        """
        if seed is not None:
            random.seed(seed)
        
        self.max_attempts = max_attempts
        self.target_grade = target_grade
        
        # Current episode state
        self.current_task: Optional[Task] = None
        self.episode_id: str = str(uuid.uuid4())[:8]
        self.attempt_number: int = 0
        self.answer_history: list = []
        self.grade_history: list = []
        self.feedback_history: list = []
        self.current_observation: Optional[Observation] = None
        
        # Metrics for learning
        self.improvement_per_attempt: list = []
        self.action_effectiveness: Dict[str, list] = {
            FeedbackStrategy.STRICT: [],
            FeedbackStrategy.MODERATE: [],
            FeedbackStrategy.HINT: []
        }
    
    def reset(self, task: Optional[Task] = None) -> Observation:
        """
        Reset environment and start a new episode.
        
        Args:
            task: Specific task to use. If None, random task is selected.
            
        Returns:
            Initial observation (state)
        """
        # Select task
        if task is None:
            all_tasks = TaskBank.get_all_tasks()
            task = random.choice(all_tasks)
        
        self.current_task = task
        self.episode_id = str(uuid.uuid4())[:8]
        self.attempt_number = 0
        self.answer_history = []
        self.grade_history = []
        self.feedback_history = []
        self.improvement_per_attempt = []
        
        # Initial observation (empty answer)
        self.current_observation = self._create_observation("", 0.0)
        
        return self.current_observation
    
    def step(self, action: Action, user_new_answer: Optional[str] = None) -> StepReturn:
        """
        Execute one environment step.
        
        Process flow:
        1. Score the user's new answer
        2. Provide feedback based on action (strategy)
        3. Calculate reward based on improvement
        4. Update state
        
        Args:
            action: Agent's feedback strategy choice
            user_new_answer: Optional explicit user answer attempt.
                If omitted, action.response_text is used.
            
        Returns:
            StepReturn containing (observation, reward, done, info)
        """
        if self.current_task is None:
            raise RuntimeError("Environment not reset. Call reset() first.")
        
        if self.attempt_number >= self.max_attempts:
            raise RuntimeError("Max attempts exceeded. Call reset() for new episode.")

        if user_new_answer is None:
            user_new_answer = action.response_text

        if not user_new_answer or not user_new_answer.strip():
            raise ValueError("Answer text is required. Pass user_new_answer or set action.response_text.")
        
        # Score the answer
        grader, grader_type = get_grader(
            self.current_task.question,
            self.current_task.difficulty.value
        )
        
        if grader_type == "behavioral":
            new_grade, grade_details = grader.grade(user_new_answer)
        else:
            new_grade, grade_details = grader.grade(
                self.current_task.question,
                user_new_answer
            )
        
        # Store history
        self.answer_history.append(user_new_answer)
        self.grade_history.append(new_grade)
        self.attempt_number += 1
        
        # Generate feedback based on action
        feedback_text = self._generate_feedback(
            action.strategy,
            user_new_answer,
            new_grade,
            grade_details
        )
        self.feedback_history.append({
            'strategy': action.strategy.value,
            'feedback': feedback_text,
            'attempt': self.attempt_number
        })
        
        # Calculate previous grade for improvement calculation
        prev_grade = self.grade_history[-2] if len(self.grade_history) > 1 else 0.0
        improvement = new_grade - prev_grade
        self.improvement_per_attempt.append(improvement)
        
        # Calculate reward
        reward = self._calculate_reward(
            improvement,
            new_grade,
            action.strategy,
            self.attempt_number
        )
        
        # Track action effectiveness
        self.action_effectiveness[action.strategy].append(reward.total)
        
        # Check if episode is done
        done = False
        success = False
        reason = ""
        
        if new_grade >= self.target_grade:
            done = True
            success = True
            reason = "Target grade reached"
        elif self.attempt_number >= self.max_attempts:
            done = True
            success = False
            reason = "Max attempts exceeded"
        
        reward.done = done
        reward.success = success
        reward.reason = reason
        
        # Create new observation
        self.current_observation = self._create_observation(
            user_new_answer,
            new_grade
        )
        
        # Info dict
        info = {
            'attempt': self.attempt_number,
            'grade': new_grade,
            'improvement': improvement,
            'feedback_strategy': action.strategy.value,
            'episode_id': self.episode_id,
            'grader_type': grader_type,
            'grade_details': grade_details
        }
        
        return StepReturn(
            observation=self.current_observation,
            reward=reward,
            done=done,
            info=info
        )
    
    def state(self) -> Observation:
        """Get current observation (state)."""
        if self.current_observation is None:
            raise RuntimeError("Environment not reset. Call reset() first.")
        return self.current_observation
    
    def _create_observation(self, answer: str, grade: float) -> Observation:
        """Create observation from current state."""
        if self.current_task is None:
            raise RuntimeError("No current task")
        
        # Analyze answer
        grader, _ = get_grader(
            self.current_task.question,
            self.current_task.difficulty.value
        )
        
        if answer:
            keywords_found = self._count_keywords(answer, self.current_task.keywords)
            keyword_recall = keywords_found / max(len(self.current_task.keywords), 1)
            sentiment_score = grader.get_sentiment_score(answer)
            answer_length = len(answer.split())
        else:
            keywords_found = 0
            keyword_recall = 0.0
            sentiment_score = 0.0
            answer_length = 0
        
        return Observation(
            task_id=self.current_task.task_id,
            difficulty=DifficultyLevel(self.current_task.difficulty.value),
            question=self.current_task.question,
            user_answer=answer,
            answer_length=answer_length,
            keywords_found=keywords_found,
            keyword_recall=keyword_recall,
            sentiment_score=sentiment_score,
            structure_score=grade,  # Simplified: use overall grade as structure proxy
            current_grade=grade,
            attempt_number=self.attempt_number,
            max_attempts=self.max_attempts,
            previous_feedback=[f['strategy'] for f in self.feedback_history],
            improvement_history=self.grade_history
        )
    
    def _count_keywords(self, answer: str, keywords: list) -> int:
        """Count how many keywords are present in answer."""
        answer_lower = answer.lower()
        return sum(1 for kw in keywords if kw.lower() in answer_lower)
    
    def _generate_feedback(
        self,
        strategy: FeedbackStrategy,
        answer: str,
        grade: float,
        grade_details: Dict
    ) -> str:
        """Generate feedback based on strategy."""
        template_info = self.FEEDBACK_TEMPLATES[strategy]
        
        if strategy == FeedbackStrategy.STRICT:
            missing_kw = self.current_task.keywords[:3]  # Top 3 keywords
            length_issue = "short" if len(answer.split()) < self.current_task.min_length else "verbose"
            structure_feedback = grade_details.get('structure_score', 0.5) < 0.7 and "Consider adding examples" or "Good structure"
            
            feedback = f"""
STRICT FEEDBACK (Grade: {grade:.2f})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Issues to address:
1. Missing keywords: {', '.join(missing_kw)}
2. Answer too {length_issue} ({len(answer.split())} words, target: {self.current_task.min_length}+)
3. Structure: {structure_feedback}

Please revise focusing on these specific areas.
            """
        
        elif strategy == FeedbackStrategy.MODERATE:
            covered = self._count_keywords(answer, self.current_task.keywords)
            covered_keywords = [kw for kw in self.current_task.keywords 
                               if kw.lower() in answer.lower()][:2]
            
            feedback = f"""
BALANCED FEEDBACK (Grade: {grade:.2f})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Strengths:
✓ You covered: {', '.join(covered_keywords)}
✓ Length: {len(answer.split())} words

Areas to improve:
• Add more specific examples
• Include {self.current_task.keywords[-2:]} concepts
• Be more concise if over {self.current_task.max_length} words
            """
        
        else:  # HINT
            feedback = f"""
HINT-BASED GUIDANCE (Grade: {grade:.2f})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reflect on these questions:
? What are the key concepts for this question?
? Can you provide specific examples or numbers?
? Does your answer have a clear structure?
? Consider keywords like: {self.current_task.keywords[0]}, {self.current_task.keywords[1]}

Try again and see if you can improve!
            """
        
        return feedback
    
    def _calculate_reward(
        self,
        improvement: float,
        current_grade: float,
        strategy: FeedbackStrategy,
        attempt_num: int
    ) -> Reward:
        """
        Calculate reward signal.
        
        Reward components:
        1. Improvement reward: +10 for big improvement, -5 if worse
        2. Efficiency: -1 per attempt (encourage quick success)
        3. Bonus: +2 if target reached
        """
        # Improvement reward (30% weight in final)
        if improvement > 0.1:
            improvement_reward = min(10.0, improvement * 50)  # Big improvements = bigger rewards
        elif improvement > 0.0:
            improvement_reward = improvement * 20  # Small improvements = smaller rewards
        elif improvement == 0.0:
            improvement_reward = -1.0  # Slight penalty for no improvement
        else:
            improvement_reward = max(-5.0, improvement * 30)  # Penalty for worse answers
        
        # Efficiency reward (discourage many attempts)
        efficiency_reward = -0.5 * attempt_num  # Small penalty per attempt
        
        # Max attempts penalty
        max_attempts_penalty = 0.0
        if attempt_num >= self.max_attempts:
            max_attempts_penalty = -5.0 if current_grade < self.target_grade else 2.0
        
        # Target reached bonus
        reached_bonus = 0.0
        if current_grade >= self.target_grade:
            reached_bonus = 5.0 - (attempt_num * 0.5)  # More attempts = less bonus
        
        # Total reward
        total = improvement_reward + efficiency_reward + max_attempts_penalty + reached_bonus
        
        return Reward(
            improvement_reward=improvement_reward,
            efficiency_reward=efficiency_reward,
            max_attempts_penalty=max_attempts_penalty,
            total=total,
            done=False,
            success=current_grade >= self.target_grade,
            reason=""
        )
    
    def get_episode_summary(self) -> Dict:
        """Get summary of the current episode."""
        if not self.grade_history:
            return {}
        
        return {
            'episode_id': self.episode_id,
            'task_id': self.current_task.task_id,
            'task_question': self.current_task.question,
            'difficulty': self.current_task.difficulty.value,
            'attempts': len(self.grade_history),
            'max_attempts': self.max_attempts,
            'initial_grade': self.grade_history[0],
            'final_grade': self.grade_history[-1],
            'total_improvement': self.grade_history[-1] - self.grade_history[0],
            'average_improvement_per_attempt': sum(self.improvement_per_attempt) / len(self.improvement_per_attempt) if self.improvement_per_attempt else 0,
            'target_reached': self.grade_history[-1] >= self.target_grade,
            'feedback_strategies_used': [f['strategy'] for f in self.feedback_history],
        }
