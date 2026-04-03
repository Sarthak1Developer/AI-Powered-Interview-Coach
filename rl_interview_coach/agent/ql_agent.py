"""
Q-Learning Agent for Interview Coach.

Simple, lightweight Q-learning implementation that learns which feedback
strategy (strict, moderate, hint) is most effective for improving answers.

State representation:
- Discrete features: difficulty (3 values), attempt (6 values), grade_level (5 values)
- Action space: 3 feedback strategies
- Q-table: state -> action -> reward
"""
import json
import random
from typing import Dict, Tuple
from pathlib import Path

from ..environment.models import FeedbackStrategy, Observation, DifficultyLevel


class StateKey:
    """Convert observation to discrete state key for Q-learning."""
    
    @staticmethod
    def discretize_grade(grade: float) -> int:
        """Convert continuous grade [0, 1] to discrete levels [0-4]."""
        if grade < 0.2:
            return 0
        elif grade < 0.4:
            return 1
        elif grade < 0.6:
            return 2
        elif grade < 0.8:
            return 3
        else:
            return 4
    
    @staticmethod
    def discretize_keyword_recall(recall: float) -> int:
        """Convert keyword recall [0, 1] to discrete levels [0-2]."""
        if recall < 0.33:
            return 0
        elif recall < 0.67:
            return 1
        else:
            return 2
    
    @staticmethod
    def create_key(obs: Observation) -> str:
        """
        Create a discrete state key from observation.
        
        State features:
        - Difficulty (3): easy, medium, hard
        - Attempt (6): 0-5
        - Grade level (5): 0-4
        - Keyword recall (3): 0-2
        
        Example key: "medium_2_3_1"
        """
        difficulty = obs.difficulty.value  # 'easy', 'medium', 'hard'
        attempt = min(obs.attempt_number, 5)  # Cap at 5
        grade_level = StateKey.discretize_grade(obs.current_grade)
        keyword_recall = StateKey.discretize_keyword_recall(obs.keyword_recall)
        
        return f"{difficulty}_{attempt}_{grade_level}_{keyword_recall}"


class QLearningAgent:
    """
    Q-Learning agent for selecting best feedback strategy.
    
    Learning:
    - Observe state (answer quality)
    - Choose action (feedback strategy)
    - Receive reward (improvement in grade)
    - Update Q-values
    
    Exploration-Exploitation:
    - Epsilon-greedy: random action with probability epsilon, else best action
    - Epsilon decays over time
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        initial_epsilon: float = 1.0,
        final_epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
    ):
        """
        Initialize Q-Learning agent.
        
        Args:
            learning_rate: How much new experience overrides old Q-values [0, 1]
            discount_factor: How much future rewards matter vs immediate [0, 1]
            initial_epsilon: Initial exploration rate
            final_epsilon: Minimum exploration rate during training
            epsilon_decay: Decay rate per episode (multiplied each step)
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.initial_epsilon = initial_epsilon
        self.final_epsilon = final_epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon = initial_epsilon
        
        # Q-table: state -> {action -> Q-value}
        self.q_table: Dict[str, Dict[str, float]] = {}
        
        # Statistics
        self.episodes_trained = 0
        self.total_reward = 0
        
        # Action space
        self.actions = [
            FeedbackStrategy.STRICT,
            FeedbackStrategy.MODERATE,
            FeedbackStrategy.HINT
        ]
    
    def choose_action(self, obs: Observation, use_epsilon_greedy: bool = True) -> FeedbackStrategy:
        """
        Choose feedback strategy based on current observation.
        
        Args:
            obs: Current observation (state)
            use_epsilon_greedy: If False, always choose best action (pure exploitation)
            
        Returns:
            Selected FeedbackStrategy
        """
        state_key = StateKey.create_key(obs)
        
        if use_epsilon_greedy and random.random() < self.epsilon:
            # Exploration: random action
            return random.choice(self.actions)
        else:
            # Exploitation: best action
            return self.get_best_action(state_key)
    
    def get_best_action(self, state_key: str) -> FeedbackStrategy:
        """Get action with highest Q-value for state."""
        if state_key not in self.q_table:
            # Unknown state: return random action
            return random.choice(self.actions)
        
        q_values = self.q_table[state_key]
        action_str = max(q_values, key=q_values.get)
        return FeedbackStrategy(action_str)
    
    def update(
        self,
        state_obs: Observation,
        action: FeedbackStrategy,
        reward: float,
        next_obs: Observation,
        done: bool
    ) -> None:
        """
        Update Q-values based on experience (state, action, reward, next_state).
        
        Q-learning update rule:
        Q(s,a) <- Q(s,a) + lr * [r + γ * max_a' Q(s',a') - Q(s,a)]
        
        Args:
            state_obs: Current state
            action: Action taken
            reward: Reward received
            next_obs: Next state
            done: Whether episode ended
        """
        state_key = StateKey.create_key(state_obs)
        next_state_key = StateKey.create_key(next_obs)
        action_str = action.value
        
        # Initialize Q-values for new states
        if state_key not in self.q_table:
            self.q_table[state_key] = {a.value: 0.0 for a in self.actions}
        
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = {a.value: 0.0 for a in self.actions}
        
        # Current Q-value
        current_q = self.q_table[state_key][action_str]
        
        # Max Q-value for next state
        if done:
            max_next_q = 0.0
        else:
            max_next_q = max(self.q_table[next_state_key].values())
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state_key][action_str] = new_q
        self.total_reward += reward
    
    def episode_complete(self) -> None:
        """Call after episode ends to decay exploration rate."""
        self.episodes_trained += 1
        self.epsilon = max(
            self.final_epsilon,
            self.epsilon * self.epsilon_decay
        )
    
    def save(self, filepath: Path) -> None:
        """Save Q-table to JSON file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'q_table': self.q_table,
            'episodes_trained': self.episodes_trained,
            'epsilon': self.epsilon,
            'total_reward': self.total_reward,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Agent saved to {filepath}")
    
    def load(self, filepath: Path) -> None:
        """Load Q-table from JSON file."""
        if not filepath.exists():
            print(f"No checkpoint found at {filepath}")
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.q_table = data['q_table']
        self.episodes_trained = data['episodes_trained']
        self.epsilon = data['epsilon']
        self.total_reward = data['total_reward']
        print(f"Agent loaded from {filepath}")
    
    def get_stats(self) -> Dict:
        """Get training statistics."""
        if not self.q_table:
            return {'episodes': 0, 'unique_states': 0, 'total_reward': 0}
        
        return {
            'episodes_trained': self.episodes_trained,
            'unique_states': len(self.q_table),
            'total_reward': self.total_reward,
            'epsilon': self.epsilon,
            'avg_reward_per_episode': self.total_reward / max(self.episodes_trained, 1),
        }
    
    def get_q_table_summary(self) -> Dict:
        """Get summary of Q-table for analysis."""
        summary = {}
        
        for state_key, action_qs in self.q_table.items():
            best_action = max(action_qs, key=action_qs.get)
            summary[state_key] = {
                'best_action': best_action,
                'q_values': action_qs,
                'advantage': max(action_qs.values()) - min(action_qs.values())
            }
        
        return summary
    
    def print_policy(self) -> None:
        """Print learned policy (state -> best action)."""
        print("\n" + "="*60)
        print("LEARNED POLICY (Best Action per State)")
        print("="*60)
        
        if not self.q_table:
            print("No Q-table data available. Train the agent first.")
            return
        
        # Group by difficulty
        for difficulty in ['easy', 'medium', 'hard']:
            print(f"\n{difficulty.upper()} Tasks:")
            print("-" * 40)
            
            relevant_states = {
                k: v for k, v in self.q_table.items()
                if k.startswith(difficulty)
            }
            
            if not relevant_states:
                print("  (No data)")
                continue
            
            for state_key in sorted(relevant_states.keys()):
                qs = relevant_states[state_key]
                best_action = max(qs, key=qs.get)
                best_q = qs[best_action]
                
                print(f"  {state_key:30} -> {best_action:10} (Q={best_q:6.2f})")
