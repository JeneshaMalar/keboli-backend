import enum
class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class InvitationStatus(str, enum.Enum):
    SENT="sent"
    CLICKED="clicked"
    EXPIRED="expired"

class InterviewSessionStatus(str, enum.Enum):
    IN_PROGRESS="in_progress"
    COMPLETED="completed"
    ABANDONED="abandoned"

class HiringRecommendation(str, enum.Enum):
    STRONG_HIRE="strong_hire"
    HIRE="hire"
    REJECT="reject"
    
       