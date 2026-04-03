"""
Task definitions for the Interview Coach RL environment.
Three difficulty levels: Easy, Medium, Hard
"""
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


class TaskType(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Task:
    """Represents an interview task."""
    task_id: str
    difficulty: TaskType
    question: str
    description: str
    keywords: List[str]
    target_grade: float
    min_length: int
    max_attempts: int
    grader_type: str  # "general", "behavioral", "technical"
    examples: List[str]
    max_length: int = 300  # Maximum recommended word count


class TaskBank:
    """Collection of predefined tasks."""
    
    EASY_TASKS = [
        Task(
            task_id="easy_001",
            difficulty=TaskType.EASY,
            question="Tell me about yourself in one minute.",
            description="Provide a brief personal and professional background.",
            keywords=[
                "experience", "skills", "background", "interested",
                "currently", "working"
            ],
            target_grade=0.75,
            min_length=30,
            max_attempts=5,
            grader_type="general",
            examples=[
                "I have 5 years of experience in software development with expertise in Python and JavaScript. I'm currently working as a senior developer at TechCorp. I'm passionate about building scalable solutions and mentoring junior developers.",
                "I'm a product manager with background in computer science and 3 years of experience. I've successfully launched 4 products. I'm interested in joining your company because of your innovative approach.",
            ]
        ),
        Task(
            task_id="easy_002",
            difficulty=TaskType.EASY,
            question="What is your greatest strength?",
            description="Identify and describe one key strength with a brief example.",
            keywords=[
                "strength", "excel", "naturally", "skill", "proficient",
                "effective"
            ],
            target_grade=0.80,
            min_length=25,
            max_attempts=5,
            grader_type="general",
            examples=[
                "My greatest strength is problem-solving. I naturally break down complex issues into manageable parts and find efficient solutions. In my current role, this has helped reduce deployment time by 40%.",
                "I excel at communication and team collaboration. I can articulate technical concepts to non-technical stakeholders effectively, which has improved our product roadmap discussions significantly.",
            ]
        ),
        Task(
            task_id="easy_003",
            difficulty=TaskType.EASY,
            question="What is your greatest weakness?",
            description="Describe a weakness and show how you're addressing it.",
            keywords=[
                "weakness", "challenge", "working on", "improve", "learning",
                "tackled"
            ],
            target_grade=0.75,
            min_length=30,
            max_attempts=5,
            grader_type="general",
            examples=[
                "Previously, I struggled with perfectionism which slowed down my output. I recognized this and started using time-boxing techniques. Now I focus on delivering good solutions within reasonable timeframes.",
                "I used to avoid public speaking, but I've been actively addressing this by presenting at team meetings and taking a public speaking course. I'm now more confident and enjoy sharing ideas.",
            ]
        ),
    ]
    
    MEDIUM_TASKS = [
        Task(
            task_id="medium_001",
            difficulty=TaskType.MEDIUM,
            question="Describe a challenging technical problem you solved recently.",
            description="Explain a technical challenge using the STAR method with specific details and outcomes.",
            keywords=[
                "implemented", "algorithm", "optimized", "performance", "testing",
                "result", "improved", "achieved"
            ],
            target_grade=0.80,
            min_length=80,
            max_attempts=5,
            grader_type="technical",
            examples=[
                "We faced a critical performance issue where our API response time was 5+ seconds. The situation: 100K concurrent users during peak hours. The task: I was assigned to optimize the database queries. My approach: I profiled the queries, identified N+1 problems, implemented caching with Redis, and parallelized non-blocking operations. The result: Response time dropped to 200ms, 25x improvement, and we eliminated 99% of timeout errors.",
                "I had to redesign the authentication system for scalability. The challenge was balancing security with performance for 10M+ users. My solution involved implementing JWT tokens, session caching, and implementing a circuit breaker. The result: Reduced auth latency by 70% and increased throughput by 3x.",
            ]
        ),
        Task(
            task_id="medium_002",
            difficulty=TaskType.MEDIUM,
            question="Tell me about a time you worked in a team to achieve a goal.",
            description="Describe team collaboration using STAR format with emphasis on working with diverse perspectives.",
            keywords=[
                "team", "collaborated", "communicated", "consensus", "delivered",
                "stakeholders", "worked with", "achieved"
            ],
            target_grade=0.78,
            min_length=80,
            max_attempts=5,
            grader_type="behavioral",
            examples=[
                "Our team had to deliver a major feature in 6 weeks with three different departments involved. The situation: Three teams with different priorities. The task: I was the technical lead to coordinate. My action: I organized weekly syncs, created clear documentation, and established agreed-upon definitions. We resolved conflicts by prioritizing customer impact. The result: Delivered on time with zero critical bugs, and customer satisfaction increased by 35%.",
                "We needed to implement a new payment system across our platform. The challenge: Different teams had conflicting requirements. I facilitated workshops to understand each team's constraints, documented trade-offs, and helped reach consensus. We launched successfully with all teams aligned and positive feedback.",
            ]
        ),
        Task(
            task_id="medium_003",
            difficulty=TaskType.MEDIUM,
            question="Why do you want to work for our company?",
            description="Show research and genuine interest with specific reasons aligned to your goals.",
            keywords=[
                "company", "mission", "values", "culture", "interested",
                "aligned", "opportunity", "grow", "product"
            ],
            target_grade=0.75,
            min_length=60,
            max_attempts=5,
            grader_type="general",
            examples=[
                "I'm impressed by your company's commitment to accessibility and social impact. Your product helps underserved communities in real ways. I've been following your engineering blog and your approach to scalable architecture aligns with my interests. I'm excited by the opportunity to contribute to meaningful work while growing my expertise in distributed systems.",
                "Your company stands out for its innovation in AI and commitment to ethical practices. I've used your API and built a project with it - the documentation is excellent and the community is welcoming. This aligns with my passion for building responsible AI solutions.",
            ]
        ),
    ]
    
    HARD_TASKS = [
        Task(
            task_id="hard_001",
            difficulty=TaskType.HARD,
            question="Tell me about a time you had to handle conflict or disagreement with a colleague.",
            description="STAR format - emphasize problem-solving, empathy, and professional resolution.",
            keywords=[
                "conflict", "disagreement", "understood", "perspective", "resolved",
                "solution", "learned", "respect"
            ],
            target_grade=0.82,
            min_length=100,
            max_attempts=6,
            grader_type="behavioral",
            examples=[
                "Situation: I disagreed with my manager's architectural decision which I believed would cause scalability issues. Task: I needed to address this without creating team friction. Action: I spent time understanding their perspective and business constraints. I gathered technical evidence, created a detailed analysis with trade-offs, and proposed an alternative that met their constraints while addressing scalability. We discussed for an hour, I walked through the benchmarks I ran, and they appreciated the thorough analysis. Even though we didn't fully adopt my approach, we implemented a hybrid solution that addressed most concerns. Result: The system scaled to 3x current load, and I learned the value of understanding context before pushing back.",
                "Hard situation: Two of our team members had fundamentally different approaches to code review - one very strict, one very lenient. Task: Maintain team harmony while improving code quality. My approach: I facilitated a discussion with both parties to understand their reasoning. The strict reviewer wanted to prevent bugs, the lenient one wanted to maintain velocity. I suggested using automation-first approach with linting and unit tests, followed by focused review. Result: Team adopted the new process, code quality improved by 25%, and both reviewers felt heard.",
            ]
        ),
        Task(
            task_id="hard_002",
            difficulty=TaskType.HARD,
            question="Describe your biggest professional failure and what you learned.",
            description="Honest reflection using STAR - show growth, accountability, and lessons learned.",
            keywords=[
                "failure", "mistake", "learned", "accountability", "improved",
                "approach", "grew", "differently"
            ],
            target_grade=0.80,
            min_length=100,
            max_attempts=6,
            grader_type="behavioral",
            examples=[
                "Situation: I released a feature to production without adequate testing, causing 2 hours of downtime affecting 10K users. Task: I was responsible for end-to-end delivery. Action: After the incident, I took full accountability in the post-mortem rather than blaming others. I analyzed the root cause: skipping the integration test phase due to time pressure. I implemented three key changes: automated integration testing, mandatory staging verification, and a feature review checklist. More importantly, I learned to communicate timeline constraints earlier so we make conscious decisions about trade-offs rather than skipping steps. Result: Zero production incidents in the next 12 months. The team adopted my checklist as standard practice.",
                "Big failure: I spent 4 weeks building the perfect feature only to have the product team say it wasn't aligned with user needs. Task: Deliver this feature on schedule. My mistake: I didn't involve the product team early enough because I was trying to impress them. Lessons: I now enforce weekly alignment meetings, do user research before implementation, and focus on small iterative deliveries. The revised approach reduced delivery time and increased actual user satisfaction by 40%.",
            ]
        ),
        Task(
            task_id="hard_003",
            difficulty=TaskType.HARD,
            question="Where do you see yourself in 5 years and how does this role help you get there?",
            description="Clear vision demonstrating growth mindset and alignment with company values.",
            keywords=[
                "growth", "leadership", "expertise", "impact", "lead", "architect",
                "mentor", "strategic", "vision"
            ],
            target_grade=0.78,
            min_length=80,
            max_attempts=6,
            grader_type="general",
            examples=[
                "In 5 years, I see myself as a technical leader architecting large-scale systems that impact millions of users. I want to have grown from individual contributor to someone who influences technical strategy and mentors a team. This role is perfect because it provides exposure to distributed systems at scale, a strong engineering culture, and opportunities to lead projects. I'm attracted to your company's focus on innovation and mentorship, which aligns with wanting to develop leadership skills. I want to reach the level where I can drive architectural decisions and eventually move into staff engineer or engineering manager roles.",
                "I envision myself as a technical architect with deep expertise in cloud-native systems and AI integration. I want to contribute to open-source projects and speak at conferences about best practices. This company aligns perfectly because of your investment in cutting-edge technologies and your culture of internal mobility. I see myself potentially moving from senior engineer to architect to technical leadership, while always staying hands-on with critical projects.",
            ]
        ),
    ]
    
    @classmethod
    def get_task(cls, task_id: str) -> Task:
        """Retrieve a task by ID."""
        all_tasks = cls.EASY_TASKS + cls.MEDIUM_TASKS + cls.HARD_TASKS
        for task in all_tasks:
            if task.task_id == task_id:
                return task
        raise ValueError(f"Task {task_id} not found")
    
    @classmethod
    def get_tasks_by_difficulty(cls, difficulty: TaskType) -> List[Task]:
        """Get all tasks of a specific difficulty."""
        if difficulty == TaskType.EASY:
            return cls.EASY_TASKS
        elif difficulty == TaskType.MEDIUM:
            return cls.MEDIUM_TASKS
        elif difficulty == TaskType.HARD:
            return cls.HARD_TASKS
        return []
    
    @classmethod
    def get_all_tasks(cls) -> List[Task]:
        """Get all tasks."""
        return cls.EASY_TASKS + cls.MEDIUM_TASKS + cls.HARD_TASKS
