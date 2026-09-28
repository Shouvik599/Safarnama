"""Unit tests for scripts/fetch_india_places.py."""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.fetch_india_places import (
    fetch_india_states_and_cities,
    fetch_json_with_retries,
    main,
)


@pytest.fixture
def sample_states_response():
    return [
        {
            "id": 4023,
            "name": "Andaman and Nicobar Islands",
            "iso2": "AN",
            "latitude": "12.6112387",
            "longitude": "92.8316541",
        },
        {
            "id": 4025,
            "name": "Rajasthan",
            "iso2": "RJ",
            "latitude": "27.0238",
            "longitude": "74.2179",
        },
    ]


@pytest.fixture
def sample_cities_response():
    return [
        {"id": "1", "name": "Jaipur"},
        {"id": "2", "name": "Udaipur"},
        {"id": "3", "name": "UnknownVillage"},
    ]


def test_fetch_json_with_retries_success():
    """Test successful JSON fetch on first attempt."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({"test": "data"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        data = fetch_json_with_retries("https://example.com/api", "test-key")
        assert data == {"test": "data"}


def test_fetch_json_with_retries_recovers():
    """Test retry recovery on transient network errors."""
    mock_success = MagicMock()
    mock_success.status = 200
    mock_success.read.return_value = json.dumps({"recovered": True}).encode("utf-8")
    mock_success.__enter__.return_value = mock_success

    err = urllib.error.URLError("Connection reset")

    with patch("urllib.request.urlopen", side_effect=[err, mock_success]):
        with patch("time.sleep"):
            data = fetch_json_with_retries("https://example.com/api", "test-key", max_retries=2)
            assert data == {"recovered": True}


def test_fetch_json_with_retries_exhaustion():
    """Test failure when all retries are exhausted."""
    err = urllib.error.URLError("Server unreachable")
    with patch("urllib.request.urlopen", side_effect=[err, err]):
        with patch("time.sleep"):
            with pytest.raises(urllib.error.URLError):
                fetch_json_with_retries("https://example.com/api", "test-key", max_retries=2)


def test_fetch_india_states_and_cities(sample_states_response, sample_cities_response):
    """Test full catalog construction and popular travel tagging."""
    def mock_fetch(url: str, api_key: str, **kwargs):
        if url.endswith("/states"):
            return sample_states_response
        return sample_cities_response

    with patch("scripts.fetch_india_places.fetch_json_with_retries", side_effect=mock_fetch):
        catalog = fetch_india_states_and_cities(api_key="test-key")

        assert catalog["metadata"]["total_states"] == 2
        states = {s["code"]: s for s in catalog["states"]}

        # Check Andaman (UT)
        assert states["AN"]["type"] == "UT"
        # Check Rajasthan (STATE)
        assert states["RJ"]["type"] == "STATE"
        assert states["RJ"]["latitude"] == 27.0238

        # Check popular destination tagging (Jaipur & Udaipur are recognized tourist hubs)
        pop_names = [p["name"] for p in catalog["popular_destinations"]]
        assert "Jaipur" in pop_names
        assert "Udaipur" in pop_names


def test_main_dry_run(capsys):
    """Test CLI main entrypoint with --dry-run flag."""
    sample_cat = {
        "metadata": {"test": "ok"},
        "states": [],
        "popular_destinations": [],
        "cities": [],
    }
    with patch("scripts.fetch_india_places.fetch_india_states_and_cities", return_value=sample_cat):
        with patch("sys.argv", ["fetch_india_places.py", "--dry-run", "--api-key", "dummy"]):
            main()
            captured = capsys.readouterr()
            assert "test" in captured.out
