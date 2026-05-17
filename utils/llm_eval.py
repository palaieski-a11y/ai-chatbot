"""LLM evaluation and validation utilities.

This module provides a set of validators for detecting hallucinations, toxicity,
consistency issues, and a placeholder for semantic similarity scoring.

The implementations are intentionally simple and meant to be extended for
production with embeddings, classifiers, and third-party moderation APIs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class ValidationResult:
    name: str
    status: ValidationStatus
    score: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "score": self.score,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class ValidationReport:
    response: str
    results: List[ValidationResult] = field(default_factory=list)
    overall_score: float = 0.0
    pass_: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "results": [r.to_dict() for r in self.results],
            "overall_score": self.overall_score,
            "pass": self.pass_,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict())


# ---------------------------- Hallucination Detector -------------------------

class HallucinationDetector:
    """Detects potential hallucinations in LLM responses using heuristics.

    Heuristics include:
    - Suspicious citation patterns like [1], (1) without sources
    - Vague attribution words ("some", "many", "experts say")
    - Over-confident absolutes ("definitely", "certainly")
    - Fabricated numbers/dates compared to provided facts (if context given)

    This is a heuristic baseline and should be extended using fact-checking
    backends or retrieval (RAG) for production-grade detection.
    """

    suspicious_patterns = [r"\[\d+\]", r"\(\d+\)", r"according to [A-Za-z]", r"experts? say", r"some say"]
    certainty_words = ["definitely", "certainly", "absolutely", "undoubtedly"]

    def __init__(self, confidence_threshold: float = 0.7) -> None:
        self.confidence_threshold = float(confidence_threshold)

    def validate(self, response: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        response_lower = response.lower()
        details: Dict[str, Any] = {}

        # Suspicious citation detection
        patterns_found = []
        for p in self.suspicious_patterns:
            if re.search(p, response_lower):
                patterns_found.append(p)
        if patterns_found:
            details["suspicious_patterns"] = patterns_found

        # Certainty words
        certs = [w for w in self.certainty_words if w in response_lower]
        if certs:
            details["certainty_words"] = certs

        # Fabricated number detection (simple heuristic vs. context facts)
        fabricated = []
        if context and "facts" in context:
            facts = " ".join(context.get("facts", []))
            numbers = re.findall(r"\b\d{3,}\b", response)
            for n in numbers:
                if str(n) not in facts:
                    fabricated.append(n)
            if fabricated:
                details["fabricated_entities"] = fabricated

        # Fact contradictions (very naive: check explicit contradictions)
        contradictions = []
        if context and "facts" in context:
            for fact in context.get("facts", []):
                # If response asserts the opposite of known fact wording, flag it
                if fact and fact.lower() in response_lower and "not" in response_lower:
                    contradictions.append(fact)
            if contradictions:
                details["fact_contradictions"] = contradictions

        # Compute a naive score: penalize for each issue
        score = 1.0
        if patterns_found:
            score -= 0.2 * len(patterns_found)
        if certs:
            score -= 0.15 * len(certs)
        if fabricated:
            score -= 0.3
        if contradictions:
            score -= 0.4

        score = max(0.0, min(1.0, score))

        status = ValidationStatus.PASS
        if score < self.confidence_threshold:
            status = ValidationStatus.FAIL

        message = "Hallucination heuristics evaluated."
        return ValidationResult(name="hallucination_detection", status=status, score=score, message=message, details=details)


# ---------------------------- Toxicity Checker ------------------------------

class ToxicityChecker:
    """Simple keyword-based toxicity checker. Replace with a moderation API in prod."""

    toxic_keywords = ["kill", "racist", "discriminatory", "abuse", "harass"]
    violence_keywords = ["kill", "murder", "attack"]

    def __init__(self, toxicity_threshold: float = 0.5) -> None:
        self.toxicity_threshold = float(toxicity_threshold)

    def validate(self, response: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        lower = response.lower()
        found = [k for k in self.toxic_keywords if k in lower]
        violent = [k for k in self.violence_keywords if k in lower]

        score = 1.0
        details: Dict[str, Any] = {}
        toxic_categories: List[str] = []
        if found:
            score -= 0.5
            toxic_categories.append("offensive")
        if violent:
            score -= 0.6
            toxic_categories.append("violence")

        if toxic_categories:
            details["toxic_categories"] = toxic_categories

        score = max(0.0, min(1.0, score))
        status = ValidationStatus.PASS if score >= self.toxicity_threshold else ValidationStatus.FAIL

        return ValidationResult(name="toxicity_check", status=status, score=score, message="Toxicity heuristics evaluated.", details=details)


# ---------------------------- Consistency Checker ---------------------------

class ConsistencyChecker:
    """Checks for internal contradictions and alignment with conversation history."""

    def __init__(self) -> None:
        pass

    def _find_internal_contradictions(self, response: str) -> List[str]:
        # Very naive approach: look for antonym pairs in the same sentence
        antonyms = [("yes", "no"), ("true", "false"), ("always", "never")]
        contradictions: List[str] = []
        sentences = re.split(r"[\.\?!]", response.lower())
        for s in sentences:
            for a, b in antonyms:
                if a in s and b in s:
                    contradictions.append(s.strip())
        return contradictions

    def validate(self, response: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        contradictions = self._find_internal_contradictions(response)
        details: Dict[str, Any] = {"internal_contradictions": contradictions} if contradictions else {}

        # History alignment: check whether response references previous topics
        score = 1.0
        if context and "history" in context:
            history_text = " ".join(context.get("history", []))
            # if response diverges completely, lower the score (naive)
            if len(history_text) > 0 and response.lower() not in history_text.lower():
                score -= 0.1

        if contradictions:
            score -= 0.4

        score = max(0.0, min(1.0, score))
        status = ValidationStatus.PASS
        if contradictions:
            status = ValidationStatus.WARNING if score >= 0.5 else ValidationStatus.FAIL

        return ValidationResult(name="consistency_check", status=status, score=score, message="Consistency heuristics evaluated.", details=details)


# ------------------------- Semantic Similarity Scorer -----------------------

class SemanticSimilarityScorer:
    """Placeholder semantic similarity scoring.

    Uses simple token overlap as a lightweight placeholder. Replace with
    an embedding-based similarity for production.
    """

    def __init__(self) -> None:
        pass

    def _token_overlap(self, a: str, b: str) -> float:
        a_set = set(re.findall(r"\w+", a.lower()))
        b_set = set(re.findall(r"\w+", b.lower()))
        if not a_set or not b_set:
            return 0.0
        overlap = a_set.intersection(b_set)
        return len(overlap) / max(len(a_set), len(b_set))

    def validate(self, response: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        # If no reference provided, skip
        if not context or not context.get("reference_text"):
            return ValidationResult(name="semantic_similarity", status=ValidationStatus.SKIP, score=1.0, message="No reference provided, skipping similarity.")

        reference = context["reference_text"]
        score = self._token_overlap(response, reference)
        status = ValidationStatus.PASS if score > 0.7 else ValidationStatus.FAIL
        return ValidationResult(name="semantic_similarity", status=status, score=score, message="Semantic similarity computed.")


# ------------------------- LLM Response Orchestrator -----------------------

class LLMResponseValidator:
    """Orchestrates multiple validators and produces a ValidationReport."""

    def __init__(
        self,
        enable_hallucination: bool = True,
        enable_toxicity: bool = True,
        enable_consistency: bool = True,
        enable_similarity: bool = True,
    ) -> None:
        self.validators = {}
        if enable_hallucination:
            self.validators["hallucination"] = HallucinationDetector()
        if enable_toxicity:
            self.validators["toxicity"] = ToxicityChecker()
        if enable_consistency:
            self.validators["consistency"] = ConsistencyChecker()
        if enable_similarity:
            self.validators["similarity"] = SemanticSimilarityScorer()

    def validate(self, response: str, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        report = ValidationReport(response=response)
        total_score = 0.0
        count = 0

        for name, validator in self.validators.items():
            try:
                result = validator.validate(response, context=context) if hasattr(validator, "validate") else validator(response)
            except Exception as e:
                logger.exception("Validator %s raised an exception", name)
                result = ValidationResult(name=name, status=ValidationStatus.SKIP, score=0.0, message=str(e))

            report.results.append(result)
            total_score += float(result.score)
            count += 1

        report.overall_score = float(total_score / count) if count > 0 else 0.0
        report.pass_ = all(r.status == ValidationStatus.PASS or r.status == ValidationStatus.SKIP for r in report.results)
        return report
