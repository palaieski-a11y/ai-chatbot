"""Pytest fixtures for validation tests and factories."""

import pytest
from typing import Dict, List


@pytest.fixture
def validation_context() -> Dict[str, List[str]]:
    """Provide a sample validation context with facts and history."""
    return {
        "facts": [
            "The capital of France is Paris.",
            "Python was first released in 1991.",
            "The Earth revolves around the Sun.",
        ],
        "history": [
            "User asked about machine learning.",
            "Assistant discussed supervised learning." 
        ],
        "reference_text": "Machine learning is a field focused on data-driven model building.",
    }


@pytest.fixture
def valid_response() -> str:
    return "Python is a popular programming language created in 1991. It is widely used for web development and data science."


@pytest.fixture
def hallucination_response() -> str:
    return "According to [1], the capital of France is London. This was discovered in 1234."


@pytest.fixture
def toxic_response() -> str:
    return "We should kill all the bugs in the code. That is a racist idea."


@pytest.fixture
def sample_reference() -> str:
    return "Machine learning is a subfield of artificial intelligence that uses statistical techniques to give computer systems the ability to learn from data."
