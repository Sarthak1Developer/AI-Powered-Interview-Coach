"""
Pydantic models for the Interview Coach RL environment.
Follows OpenEnv specification for Observation, Action, and Reward.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# OBSERVATIONS (STATE)
# ============================================================================

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Observation(BaseModel):
    """
    Represents the current state of an interview session.
    The agent observes this state and must decide which feedback strategy to use.
    """
    task_id: str = Field(description="Unique identifier for the task")
    difficulty: DifficultyLevel = Field(description="Task difficulty level")
    
    # Question context
    question: str = Field(description="The interview question")
    
    # User's answer metrics
    user_answer: str = Field(description="User's current answer attempt")
    answer_length: int = Field(description="Number of tokens in answer")
    keywords_found: int = Field(description="Number of required keywords present")
    keyword_recall: float = Field(ge=0, le=1, description="Fraction of keywords found (0.0-1.0)")
    
    # Quality metrics
    sentiment_score: float = Field(ge=-1, le=1, description="Sentiment polarity (-1 to 1)")
    structure_score: float = Field(ge=0, le=1, description="Answer structure quality (0.0-1.0)")
    current_grade: float = Field(ge=0, le=1, description="Current answer grade (0.0-1.0)")
    
    # Episode progress
    attempt_number: int = Field(ge=0, description="Which attempt is this (0-indexed)")
    max_attempts: int = Field(default=5, description="Maximum attempts allowed")
    
    # Historical feedback
    previous_feedback: List[str] = Field(default_factory=list, description="Feedback types used so far")
    improvement_history: List[float] = Field(default_factory=list, description="Grade from each attempt")
    
    def to_dict(self) -> Dict:
        """Convert observation to dictionary for Q-learning."""
        return self.model_dump()


# ============================================================================
# ACTIONS
# ============================================================================

class FeedbackStrategy(str, Enum):
    """The agent can choose one of three feedback strategies."""
    STRICT = "strict"           # Aggressive feedback, point out all issues
    MODERATE = "moderate"       # Balanced feedback
    HINT = "hint"              # Minimal guidance, let user discover


class Action(BaseModel):
    """
    Represents the agent's decision for which feedback strategy to use.
    The agent (policy network) observes the state and selects an action.
    """
    strategy: FeedbackStrategy = Field(description="Chosen feedback strategy")
    confidence: float = Field(ge=0, le=1, description="Agent's confidence in this action (0.0-1.0)")
    response_text: Optional[str] = Field(
        default=None,
        description="Optional user answer attempt to support step(action) style environments"
    )
    
    def to_dict(self) -> Dict:
        return self.model_dump()


# ============================================================================
# REWARDS
# ============================================================================

class Reward(BaseModel):
    """
    Reward signal for the RL algorithm.
    Guide the agent to choose feedback strategies that improve user answers.
    """
    # Primary reward: improvement in answer quality
    improvement_reward: float = Field(
        ge=-10, le=10,
        description="Reward based on answer grade improvement (-10 to +10)"
    )
    
    # Efficiency reward: prefer strategies that work quickly
    efficiency_reward: float = Field(
        ge=-3, le=2,
        description="Penalty for excessive attempts (-3 to +2)"
    )
    
    # Penalty for reaching max attempts without improvement
    max_attempts_penalty: float = Field(
        ge=-5, le=2,
        description="Reward/Penalty at max attempts (-5 if fail, +2 if success)"
    )
    
    # Total reward (for learning)
    total: float = Field(
        ge=-16, le=12,
        description="Total reward = improvement + efficiency + penalty"
    )
    
    # Metadata
    done: bool = Field(default=False, description="Is episode terminal?")
    success: bool = Field(default=False, description="Did user reach target grade?")
    reason: str = Field(default="", description="Why episode ended")
    
    def to_dict(self) -> Dict:
        return self.model_dump()


# ============================================================================
# ENVIRONMENT STEP RETURN
# ============================================================================

class StepReturn(BaseModel):
    """
    Return value from env.step(action).
    Follows standard Gym-like interface.
    """
    observation: Observation = Field(description="Next state")
    reward: Reward = Field(description="Reward for this step")
    done: bool = Field(description="Is episode terminal?")
    info: Dict = Field(default_factory=dict, description="Additional info")
