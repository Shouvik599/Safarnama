"""Unit tests for the LLM Fallback Estimator tool (src/tools/fallback_estimator.py)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from src.models.fallback_estimator import (
    CostCategory,
    FallbackEstimateResult,
    TravelTier,
)
from src.tools.fallback_estimator import (
    _ESTIMATOR_CACHE,
    InvalidDestinationError,
    estimate_cost,
    get_fallback_estimator_status,
)


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    """Clear in-memory estimator cache before each test."""
    _ESTIMATOR_CACHE.clear()


def test_estimate_cost_empty_destination_raises_error() -> None:
    """Test that empty or whitespace destination raises InvalidDestinationError."""
    with pytest.raises(InvalidDestinationError):
        estimate_cost(destination="")

    with pytest.raises(InvalidDestinationError):
        estimate_cost(destination="   ")


def test_estimate_cost_fixture_mode() -> None:
    """Test estimation using mock fixture mode."""
    res = estimate_cost(
        destination="Tokyo",
        category=CostCategory.HOTEL,
        tier=TravelTier.MID_RANGE,
        duration_days=2,
        num_travelers=1,
        use_fixture=True,
    )

    assert isinstance(res, FallbackEstimateResult)
    assert res.destination == "TOKYO"
    assert res.category == "HOTEL"
    assert res.estimated_cost_inr > 0.0
    assert res.min_cost_inr <= res.estimated_cost_inr <= res.max_cost_inr
    assert res.provider_used == "fixture"
    assert res.is_fallback is True
    assert res.is_estimated is True


def test_estimate_cost_offline_heuristic_fallback() -> None:
    """Test fallback to offline heuristic calculation when no live keys are configured."""
    with patch.dict("os.environ", {}, clear=True):
        res = estimate_cost(
            destination="Paris",
            category=CostCategory.FOOD,
            tier=TravelTier.MID_RANGE,
            duration_days=3,
            num_travelers=2,
            use_fixture=False,
        )

        assert isinstance(res, FallbackEstimateResult)
        assert res.destination == "PARIS"
        assert res.category == "FOOD"
        assert res.estimated_cost_inr > 0.0
        assert res.provider_used == "offline-heuristic"
        assert res.model_used == "rule-baseline-v1"
        assert res.is_estimated is True


def test_estimate_gemini_provider_mock() -> None:
    """Test live Tier 1 Gemini provider estimation using mock HTTP response."""
    mock_gemini_json = json.dumps({
        "estimated_cost_inr": 9200.0,
        "min_cost_inr": 7000.0,
        "max_cost_inr": 12500.0,
        "confidence_score": 0.88,
        "reasoning": "Mocked Gemini AI price estimation for Tokyo hotels.",
    })

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "candidates": [{"content": {"parts": [{"text": mock_gemini_json}]}}]
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake_gemini_key"}, clear=True):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = estimate_cost(
                destination="Tokyo",
                category=CostCategory.HOTEL,
                tier=TravelTier.MID_RANGE,
                use_fixture=False,
            )

            assert res.provider_used == "gemini"
            assert res.estimated_cost_inr == 9200.0
            assert res.min_cost_inr == 7000.0
            assert res.max_cost_inr == 12500.0
            assert res.confidence_score == 0.88
            assert res.is_estimated is True


def test_estimate_groq_provider_mock() -> None:
    """Test live Tier 2 Groq provider estimation using mock HTTP response."""
    mock_groq_json = json.dumps({
        "estimated_cost_inr": 3400.0,
        "min_cost_inr": 2500.0,
        "max_cost_inr": 4800.0,
        "confidence_score": 0.85,
        "reasoning": "Mocked Groq Llama-3.3 price estimation for Mumbai dining.",
    })

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "choices": [{"message": {"content": mock_groq_json}}]
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    # Set GROQ_API_KEY but clear GEMINI_API_KEY so it proceeds to Groq
    with patch.dict("os.environ", {"GROQ_API_KEY": "fake_groq_key"}, clear=True):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = estimate_cost(
                destination="Mumbai",
                category=CostCategory.FOOD,
                tier=TravelTier.MID_RANGE,
                use_fixture=False,
            )

            assert res.provider_used == "groq"
            assert res.estimated_cost_inr == 3400.0
            assert res.min_cost_inr == 2500.0
            assert res.max_cost_inr == 4800.0
            assert res.is_estimated is True


def test_estimate_nvidia_provider_mock() -> None:
    """Test live Tier 3 NVIDIA NIM provider estimation using mock HTTP response."""
    mock_nvidia_json = json.dumps({
        "estimated_cost_inr": 1500.0,
        "min_cost_inr": 1000.0,
        "max_cost_inr": 2200.0,
        "confidence_score": 0.82,
        "reasoning": "Mocked NVIDIA Llama-3.3 price estimation for transport.",
    })

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "choices": [{"message": {"content": mock_nvidia_json}}]
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch.dict("os.environ", {"NVIDIA_API_KEY": "fake_nvidia_key"}, clear=True):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = estimate_cost(
                destination="Delhi",
                category=CostCategory.TRANSPORT,
                tier=TravelTier.BUDGET,
                use_fixture=False,
            )

            assert res.provider_used == "nvidia"
            assert res.estimated_cost_inr == 1500.0
            assert res.is_estimated is True


def test_estimator_cache_retrieval() -> None:
    """Test that repeating an estimate call retrieves from in-memory cache."""
    with patch.dict("os.environ", {}, clear=True):
        first = estimate_cost(destination="Mumbai", category=CostCategory.HOTEL, use_fixture=False)
        second = estimate_cost(destination="Mumbai", category=CostCategory.HOTEL, use_fixture=False)

        assert first is second
        assert _ESTIMATOR_CACHE.count() == 1


def test_get_fallback_estimator_status() -> None:
    """Test diagnostics and status report."""
    status = get_fallback_estimator_status()
    assert status["status"] == "healthy"
    assert "providers" in status
    assert "gemini" in status["providers"]
    assert "groq" in status["providers"]
    assert "nvidia" in status["providers"]
    assert "offline_heuristic" in status["providers"]
