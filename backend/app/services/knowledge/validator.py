from dataclasses import dataclass


@dataclass
class ValidationResult:
    accepted: bool
    confidence: float
    reasons: list[str]


class KnowledgeValidator:

    MIN_CONFIDENCE = 0.90

    def validate(
        self,
        concept: str,
        description: str | None,
        relationships: list,
        sources: list,
        confidence: float,
    ) -> ValidationResult:

        reasons: list[str] = []

        # 1. Concept must exist
        if not concept or not concept.strip():
            reasons.append(
                "Concept is empty."
            )

        # 2. Description must exist
        if not description or not description.strip():
            reasons.append(
                "Concept description is missing."
            )

        # 3. At least one source must exist
        if not sources:
            reasons.append(
                "No supporting sources provided."
            )

        # 4. Confidence must be high enough
        if confidence < self.MIN_CONFIDENCE:
            reasons.append(
                f"Confidence {confidence:.2f} "
                f"is below required threshold "
                f"{self.MIN_CONFIDENCE:.2f}."
            )

        accepted = len(reasons) == 0

        return ValidationResult(
            accepted=accepted,
            confidence=confidence,
            reasons=reasons,
        )