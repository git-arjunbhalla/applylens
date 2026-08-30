from enum import Enum


class ApplicationStatus(str, Enum):
    WISHLIST = "Wishlist"
    APPLIED = "Applied"
    OA = "OA"
    INTERVIEWING = "Interviewing"
    OFFER = "Offer"
    REJECTED = "Rejected"


class InterviewOutcome(str, Enum):
    PENDING = "Pending"
    PASSED = "Passed"
    FAILED = "Failed"
