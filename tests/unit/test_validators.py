"""Unit tests for LLM validation and scoring system."""

import pytest
from datetime import datetime

from utils.llm_eval import (
    HallucinationDetector,
    ToxicityChecker,
    ConsistencyChecker,
    SemanticSimilarityScorer,
    LLMResponseValidator,
    ValidationStatus,
    ValidationResult,
)


# ============================================================================
# HallucinationDetector Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.validation
class TestHallucinationDetector:
    """Tests for HallucinationDetector class."""
    
    def test_init(self):
        """Test HallucinationDetector initialization."""
        detector = HallucinationDetector(confidence_threshold=0.8)
        assert detector.confidence_threshold == 0.8
        assert "fabricated_citation" in detector.suspicious_patterns
    
    def test_detect_fabricated_citations(self):
        """Test detection of fabricated citations."""
        detector = HallucinationDetector()
        response = "According to [1], the Earth was flat [2]."
        
        result = detector.validate(response)
        
        assert result.name == "hallucination_detection"
        assert result.status == ValidationStatus.FAIL
        assert result.score < 1.0
        assert "suspicious citations" in result.details["suspicious_patterns"][0].lower()
    
    def test_detect_vague_attribution(self):
        """Test detection of vague attribution patterns."""
        detector = HallucinationDetector()
        response = "According to some say, the number is definitely 42."
        
        result = detector.validate(response)
        
        assert result.status == ValidationStatus.FAIL
        assert len(result.details["suspicious_patterns"]) > 0
    
    def test_detect_false_certainty(self):
        """Test detection of false certainty statements."""
        detector = HallucinationDetector()
        response = "Absolutely, it's definitely going to happen certainly."
        
        result = detector.validate(response)
        
        assert result.status == ValidationStatus.FAIL
        assert "false_certainty" in str(result.details)
    
    def test_fact_contradiction_detection(self, validation_context):
        """Test detection of contradictions with known facts."""
        detector = HallucinationDetector()
        response = "The capital of France is London."
        
        result = detector.validate(response, context=validation_context)
        
        assert result.status == ValidationStatus.FAIL
        assert len(result.details["fact_contradictions"]) > 0
    
    def test_fabricated_number_detection(self, validation_context):
        """Test detection of fabricated numbers."""
        detector = HallucinationDetector()
        response = "This was discovered in 1234 by scientists."
        
        result = detector.validate(response, context=validation_context)
        
        assert len(result.details["fabricated_entities"]) > 0
    
    def test_valid_response_passes(self):
        """Test that valid responses pass hallucination check."""
        detector = HallucinationDetector()
        response = "Python is a popular programming language created in 1991."
        
        result = detector.validate(response)
        
        assert result.status == ValidationStatus.PASS
        assert result.score > 0.8


# ============================================================================
# ToxicityChecker Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.validation
class TestToxicityChecker:
    """Tests for ToxicityChecker class."""
    
    def test_init(self):
        """Test ToxicityChecker initialization."""
        checker = ToxicityChecker(toxicity_threshold=0.6)
        assert checker.toxicity_threshold == 0.6
        assert "offensive" in checker.toxic_keywords
    
    def test_detect_offensive_language(self):
        """Test detection of offensive language."""
        checker = ToxicityChecker()
        response = "That is a racist and discriminatory statement."
        
        result = checker.validate(response)
        
        assert result.name == "toxicity_check"
        assert result.status == ValidationStatus.FAIL
        assert result.score < 1.0
    
    def test_detect_violence(self):
        """Test detection of violence-related content."""
        checker = ToxicityChecker()
        response = "We should kill all the bugs in the code."
        
        result = checker.validate(response)
        
        assert result.status == ValidationStatus.FAIL
        assert len(result.details["toxic_categories"]) > 0
    
    def test_detect_abuse(self):
        """Test detection of abuse and harassment."""
        checker = ToxicityChecker()
        response = "This is abuse and harassment."
        
        result = checker.validate(response)
        
        assert result.status == ValidationStatus.FAIL
    
    def test_safe_response_passes(self):
        """Test that safe responses pass toxicity check."""
        checker = ToxicityChecker()
        response = "Machine learning is a fascinating field of study."
        
        result = checker.validate(response)
        
        assert result.status == ValidationStatus.PASS
        assert result.score == 1.0


# ============================================================================
# ConsistencyChecker Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.validation
class TestConsistencyChecker:
    """Tests for ConsistencyChecker class."""
    
    def test_init(self):
        """Test ConsistencyChecker initialization."""
        checker = ConsistencyChecker()
        assert checker is not None
    
    def test_detect_internal_contradictions(self):
        """Test detection of internal contradictions."""
        checker = ConsistencyChecker()
        response = "Yes, the answer is definitely no. It's true but false."
        
        result = checker.validate(response)
        
        assert result.status in [ValidationStatus.WARNING, ValidationStatus.FAIL]
        assert len(result.details["internal_contradictions"]) > 0
    
    def test_history_alignment_check(self, validation_context):
        """Test alignment with conversation history."""
        checker = ConsistencyChecker()
        response = "Machine learning is great for image recognition tasks."
        
        result = checker.validate(response, context=validation_context)
        
        assert result.name == "consistency_check"
        assert result.score >= 0.0
    
    def test_tone_consistency_check(self, validation_context):
        """Test tone consistency checking."""
        checker = ConsistencyChecker()
        response = "Accordingly, the therefore consequence is thus implemented."
        
        result = checker.validate(response, context=validation_context)
        
        assert result.score > 0.5
    
    def test_consistent_response_passes(self):
        """Test that consistent responses pass checks."""
        checker = ConsistencyChecker()
        response = "Python is a programming language. It's used for web development."
        
        result = checker.validate(response)
        
        assert result.status == ValidationStatus.PASS
        assert result.score >= 0.7


# ============================================================================
# SemanticSimilarityScorer Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.validation
class TestSemanticSimilarityScorer:
    """Tests for SemanticSimilarityScorer class."""
    
    def test_init(self):
        """Test SemanticSimilarityScorer initialization."""
        scorer = SemanticSimilarityScorer()
        assert scorer is not None
    
    def test_skip_without_reference(self):
        """Test that scoring is skipped without reference text."""
        scorer = SemanticSimilarityScorer()
        response = "Test response"
        
        result = scorer.validate(response)
        
        assert result.status == ValidationStatus.SKIP
        assert result.score == 1.0
    
    def test_high_similarity_with_reference(self):
        """Test high similarity scoring."""
        scorer = SemanticSimilarityScorer()
        response = "The quick brown fox jumps over the lazy dog"
        context = {"reference_text": "The quick brown fox jumps over the lazy dog"}
        
        result = scorer.validate(response, context=context)
        
        assert result.status == ValidationStatus.PASS
        assert result.score == 1.0
    
    def test_low_similarity_with_reference(self):
        """Test low similarity scoring."""
        scorer = SemanticSimilarityScorer()
        response = "Cats are animals"
        context = {"reference_text": "The quick brown fox jumps over the lazy dog"}
        
        result = scorer.validate(response, context=context)
        
        assert result.score < 1.0


# ============================================================================
# LLMResponseValidator Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.validation
class TestLLMResponseValidator:
    """Tests for LLMResponseValidator orchestrator class."""
    
    def test_init_all_validators(self):
        """Test initialization with all validators enabled."""
        validator = LLMResponseValidator(
            enable_hallucination=True,
            enable_toxicity=True,
            enable_consistency=True,
            enable_similarity=True,
        )
        
        assert len(validator.validators) == 4
        assert "hallucination" in validator.validators
        assert "toxicity" in validator.validators
    
    def test_init_selective_validators(self):
        """Test initialization with selective validators."""
        validator = LLMResponseValidator(
            enable_hallucination=True,
            enable_toxicity=False,
            enable_consistency=False,
            enable_similarity=False,
        )
        
        assert len(validator.validators) == 1
        assert "hallucination" in validator.validators
    
    def test_full_validation_pass(self, valid_response):
        """Test full validation pipeline with valid response."""
        validator = LLMResponseValidator()
        
        report = validator.validate(valid_response)
        
        assert report.overall_score > 0.5
        assert isinstance(report.overall_score, float)
        assert report.timestamp is not None
    
    def test_full_validation_hallucination_fail(self, hallucination_response):
        """Test full validation with hallucination detection failure."""
        validator = LLMResponseValidator()
        
        report = validator.validate(hallucination_response)
        
        assert len(report.results) > 0
        hallucination_result = [
            r for r in report.results if r.name == "hallucination_detection"
        ]
        assert len(hallucination_result) > 0
    
    def test_full_validation_toxicity_fail(self, toxic_response):
        """Test full validation with toxicity detection failure."""
        validator = LLMResponseValidator()
        
        report = validator.validate(toxic_response)
        
        toxicity_result = [r for r in report.results if r.name == "toxicity_check"]
        assert len(toxicity_result) > 0
    
    def test_validation_report_serialization(self, valid_response):
        """Test validation report can be serialized to JSON."""
        validator = LLMResponseValidator()
        report = validator.validate(valid_response)
        
        report_dict = report.to_dict()
        assert "response" in report_dict
        assert "results" in report_dict
        assert "overall_score" in report_dict
        assert "pass" in report_dict
        
        report_json = report.to_json()
        assert isinstance(report_json, str)
        assert "response" in report_json
    
    def test_validation_with_context(self, valid_response, validation_context):
        """Test validation with custom context."""
        validator = LLMResponseValidator()
        
        report = validator.validate(valid_response, context=validation_context)
        
        assert report is not None
        assert len(report.results) > 0
    
    def test_validation_result_structure(self, valid_response):
        """Test structure of validation results."""
        validator = LLMResponseValidator()
        report = validator.validate(valid_response)
        
        for result in report.results:
            assert hasattr(result, "name")
            assert hasattr(result, "status")
            assert hasattr(result, "score")
            assert hasattr(result, "message")
            assert isinstance(result.score, float)
            assert 0.0 <= result.score <= 1.0
    
    def test_validator_error_handling(self):
        """Test that validator errors don't break the pipeline."""
        validator = LLMResponseValidator(enable_similarity=False)
        
        # Very long response that might cause issues
        long_response = "a" * 100000
        
        # Should not raise an exception
        report = validator.validate(long_response)
        
        assert report is not None
        assert len(report.results) >= 0
    
    def test_empty_response_validation(self):
        """Test validation of empty response."""
        validator = LLMResponseValidator()
        
        report = validator.validate("")
        
        assert report is not None
        assert isinstance(report.overall_score, float)
