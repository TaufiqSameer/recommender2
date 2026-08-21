from enum import Enum


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"