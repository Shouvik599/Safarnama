"""Phase 2 — Static Data Access Layer.

Provides high-performance, in-memory indexed query access to all static datasets:
- ``data/static/airports.json``           (3,244 airports)
- ``data/static/visa_rules.json``         (199 baseline rules)
- ``data/static/visa_rules_enriched.json``(199 enriched rules)
- ``data/static/countries.json``          (250 country profiles)

Datasets are loaded once on initialization and indexed into O(1) hash maps.
The application never repeatedly opens JSON files from disk during runtime queries.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from src.models.airport import Airport
from src.models.country import CountryProfile
from src.models.visa import BaseVisaRule, EnrichedVisaRecord

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "data" / "static"

DEFAULT_AIRPORTS_PATH = STATIC_DIR / "airports.json"
DEFAULT_VISA_RULES_PATH = STATIC_DIR / "visa_rules.json"
DEFAULT_ENRICHED_VISA_PATH = STATIC_DIR / "visa_rules_enriched.json"
DEFAULT_COUNTRIES_PATH = STATIC_DIR / "countries.json"

# IST is UTC+05:30 (5.5 hours)
IST_OFFSET_HOURS = 5.5

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class StaticDataError(Exception):
    """Base exception for static data layer errors."""


class InvalidLookupError(StaticDataError, ValueError):
    """Raised when an invalid or empty lookup parameter is provided."""


class RecordNotFoundError(StaticDataError, KeyError):
    """Base exception when a requested static record is not found."""


class AirportNotFoundError(RecordNotFoundError):
    """Raised when an airport cannot be found for the given code or criteria."""


class CountryNotFoundError(RecordNotFoundError):
    """Raised when a country profile cannot be resolved for code or name."""


class VisaRuleNotFoundError(RecordNotFoundError):
    """Raised when visa rules cannot be found for a destination."""


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def parse_utc_offset_hours(tz_str: str) -> float | None:
    """Parse a timezone string (e.g. 'UTC+09:00', 'UTC-03:30', 'UTC') to float hours.

    Returns:
        Offset in hours relative to UTC (e.g. +9.0, -3.5, 0.0), or None if unparseable.
    """
    cleaned = tz_str.strip().upper()
    if cleaned in ("UTC", "GMT", "UTC+00:00", "UTC-00:00", "Z"):
        return 0.0

    match = re.match(r"^UTC([+-])(\d{1,2})(?::(\d{2}))?$", cleaned)
    if not match:
        return None

    sign, hours_str, mins_str = match.groups()
    hours = float(hours_str)
    mins = float(mins_str) if mins_str else 0.0
    total = hours + (mins / 60.0)
    return total if sign == "+" else -total


# ---------------------------------------------------------------------------
# Static Data Store
# ---------------------------------------------------------------------------


class StaticDataStore:
    """In-memory indexed store for airports, visa rules, and country profiles."""

    def __init__(
        self,
        airports_path: Path | str = DEFAULT_AIRPORTS_PATH,
        visa_rules_path: Path | str = DEFAULT_VISA_RULES_PATH,
        enriched_visa_path: Path | str = DEFAULT_ENRICHED_VISA_PATH,
        countries_path: Path | str = DEFAULT_COUNTRIES_PATH,
    ) -> None:
        self.airports_path = Path(airports_path)
        self.visa_rules_path = Path(visa_rules_path)
        self.enriched_visa_path = Path(enriched_visa_path)
        self.countries_path = Path(countries_path)

        # In-memory indexes
        self._airports_by_iata: dict[str, Airport] = {}
        self._airports_by_city: dict[str, list[Airport]] = {}
        self._airports_by_country: dict[str, list[Airport]] = {}

        self._countries_by_code: dict[str, CountryProfile] = {}
        self._countries_by_alpha3: dict[str, CountryProfile] = {}
        self._countries_by_name: dict[str, CountryProfile] = {}

        self._visa_base_by_dest: dict[str, BaseVisaRule] = {}
        self._visa_base_by_code: dict[str, BaseVisaRule] = {}

        self._visa_enriched_by_dest: dict[str, EnrichedVisaRecord] = {}
        self._visa_enriched_by_code: dict[str, EnrichedVisaRecord] = {}

        self.load()

    def _read_json_list(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            log.warning("Static data file does not exist: %s", path)
            return []
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            log.error("Static data file %s does not contain a JSON array", path)
            return []
        except Exception as exc:
            log.error("Failed to read static data file %s: %s", path, exc)
            raise StaticDataError(f"Error reading {path}: {exc}") from exc

    def load(self) -> None:
        """Load JSON files and build in-memory hash indexes."""
        # 1. Airports
        airports_raw = self._read_json_list(self.airports_path)
        airports_by_iata: dict[str, Airport] = {}
        airports_by_city: dict[str, list[Airport]] = {}
        airports_by_country: dict[str, list[Airport]] = {}

        for item in airports_raw:
            try:
                airport = Airport.model_validate(item)
                iata = airport.iata_code.strip().upper()
                airports_by_iata[iata] = airport

                if airport.municipality:
                    city_key = airport.municipality.strip().lower()
                    airports_by_city.setdefault(city_key, []).append(airport)

                country_key = airport.iso_country.strip().upper()
                airports_by_country.setdefault(country_key, []).append(airport)
            except Exception as exc:
                log.warning("Skipping invalid airport item: %s", exc)

        # 2. Countries
        countries_raw = self._read_json_list(self.countries_path)
        countries_by_code: dict[str, CountryProfile] = {}
        countries_by_alpha3: dict[str, CountryProfile] = {}
        countries_by_name: dict[str, CountryProfile] = {}

        for item in countries_raw:
            try:
                country = CountryProfile.model_validate(item)
                code2 = country.country_code.strip().upper()
                code3 = country.country_code_alpha3.strip().upper()
                name_key = country.name.strip().lower()
                official_key = country.official_name.strip().lower()

                countries_by_code[code2] = country
                countries_by_alpha3[code3] = country
                countries_by_name[name_key] = country
                countries_by_name[official_key] = country
            except Exception as exc:
                log.warning("Skipping invalid country item: %s", exc)

        # 3. Base Visa Rules
        visa_base_raw = self._read_json_list(self.visa_rules_path)
        visa_base_by_dest: dict[str, BaseVisaRule] = {}
        visa_base_by_code: dict[str, BaseVisaRule] = {}

        for item in visa_base_raw:
            try:
                rule = BaseVisaRule.model_validate(item)
                dest_key = rule.destination.strip().lower()
                code_key = rule.country_code.strip().upper()
                visa_base_by_dest[dest_key] = rule
                if code_key and code_key != "??":
                    visa_base_by_code[code_key] = rule
            except Exception as exc:
                log.warning("Skipping invalid baseline visa rule item: %s", exc)

        # 4. Enriched Visa Rules
        visa_enriched_raw = self._read_json_list(self.enriched_visa_path)
        visa_enriched_by_dest: dict[str, EnrichedVisaRecord] = {}
        visa_enriched_by_code: dict[str, EnrichedVisaRecord] = {}

        for item in visa_enriched_raw:
            try:
                enriched = EnrichedVisaRecord.model_validate(item)
                dest_key = enriched.destination.strip().lower()
                code_key = enriched.country_code.strip().upper()
                visa_enriched_by_dest[dest_key] = enriched
                if code_key and code_key != "??":
                    visa_enriched_by_code[code_key] = enriched
            except Exception as exc:
                log.warning("Skipping invalid enriched visa rule item: %s", exc)

        # Commit indexes atomically
        self._airports_by_iata = airports_by_iata
        self._airports_by_city = airports_by_city
        self._airports_by_country = airports_by_country

        self._countries_by_code = countries_by_code
        self._countries_by_alpha3 = countries_by_alpha3
        self._countries_by_name = countries_by_name

        self._visa_base_by_dest = visa_base_by_dest
        self._visa_base_by_code = visa_base_by_code

        self._visa_enriched_by_dest = visa_enriched_by_dest
        self._visa_enriched_by_code = visa_enriched_by_code

        log.info(
            "Static data loaded: %d airports, %d countries, %d base rules, %d enriched rules",
            len(self._airports_by_iata),
            len(self._countries_by_code),
            len(self._visa_base_by_dest),
            len(self._visa_enriched_by_dest),
        )

    def reload(self) -> None:
        """Reload static datasets from disk into memory."""
        self.load()

    # -----------------------------------------------------------------------
    # Airport queries
    # -----------------------------------------------------------------------

    def get_airport(self, iata_code: str) -> Airport:
        """Resolve an airport by its 3-letter IATA code (case-insensitive)."""
        if not iata_code or not isinstance(iata_code, str) or not iata_code.strip():
            raise InvalidLookupError("IATA code must be a non-empty string.")

        code = iata_code.strip().upper()
        airport = self._airports_by_iata.get(code)
        if airport is None:
            raise AirportNotFoundError(f"Airport with IATA code {code!r} not found.")
        return airport

    def find_airport(self, iata_code: str) -> Airport | None:
        """Resolve an airport by IATA code, returning None if not found."""
        try:
            return self.get_airport(iata_code)
        except (AirportNotFoundError, InvalidLookupError):
            return None

    def get_airports_by_city(self, city: str) -> list[Airport]:
        """Find all airports serving a given city/municipality (case-insensitive)."""
        if not city or not isinstance(city, str) or not city.strip():
            raise InvalidLookupError("City name must be a non-empty string.")

        city_key = city.strip().lower()
        results = self._airports_by_city.get(city_key, [])
        if not results:
            # Also try substring matching
            results = [
                a
                for c, airports in self._airports_by_city.items()
                if city_key in c
                for a in airports
            ]
        return list(results)

    def get_airports_by_country(self, iso_country: str) -> list[Airport]:
        """Find all airports in a given country by ISO-2 code (case-insensitive)."""
        if not iso_country or not isinstance(iso_country, str) or not iso_country.strip():
            raise InvalidLookupError("Country code must be a non-empty string.")

        country_key = iso_country.strip().upper()
        return list(self._airports_by_country.get(country_key, []))

    def get_airport_coordinates(self, iata_code: str) -> tuple[float, float]:
        """Return (latitude_deg, longitude_deg) for an airport by IATA code."""
        airport = self.get_airport(iata_code)
        return (airport.latitude_deg, airport.longitude_deg)

    # -----------------------------------------------------------------------
    # Country queries
    # -----------------------------------------------------------------------

    def get_country(self, query: str) -> CountryProfile:
        """Resolve a country by ISO-2, ISO-3, or common/official name (case-insensitive)."""
        if not query or not isinstance(query, str) or not query.strip():
            raise InvalidLookupError("Country query must be a non-empty string.")

        q = query.strip()
        q_upper = q.upper()
        q_lower = q.lower()

        # 1. Try ISO-2
        if len(q_upper) == 2 and q_upper in self._countries_by_code:
            return self._countries_by_code[q_upper]

        # 2. Try ISO-3
        if len(q_upper) == 3 and q_upper in self._countries_by_alpha3:
            return self._countries_by_alpha3[q_upper]

        # 3. Try exact name / official name
        if q_lower in self._countries_by_name:
            return self._countries_by_name[q_lower]

        # 4. Partial name match fallback
        for name_key, profile in self._countries_by_name.items():
            if q_lower in name_key or name_key in q_lower:
                return profile

        raise CountryNotFoundError(f"Country matching {query!r} not found in country profiles.")

    def find_country(self, query: str) -> CountryProfile | None:
        """Resolve a country, returning None if not found."""
        try:
            return self.get_country(query)
        except (CountryNotFoundError, InvalidLookupError):
            return None

    def is_schengen_member(self, query: str) -> bool:
        """Return True if the country is a Schengen Area member state."""
        try:
            country = self.get_country(query)
            return country.is_schengen
        except CountryNotFoundError:
            return False

    def get_ist_time_difference_hours(
        self, query: str, timezone: str | None = None
    ) -> float | None:
        """Calculate the time difference in hours between a destination timezone and IST.

        Positive means destination is ahead of IST; negative means behind IST.
        Example: Japan (UTC+09:00) vs IST (UTC+05:30) -> +3.5 hours.

        If `timezone` is provided (e.g. 'UTC+01:00'), that timezone is used.
        Otherwise, if the country has multiple timezones and capital coordinates are known,
        the timezone closest to the capital city's longitude is chosen as the primary timezone.
        """
        country = self.get_country(query)
        if not country.timezones:
            return None

        target_tz: str | None = None
        if timezone is not None:
            target_tz = timezone
        elif len(country.timezones) == 1:
            target_tz = country.timezones[0]
        elif country.capital_coordinates is not None:
            cap_est_offset = country.capital_coordinates.lng / 15.0
            target_tz = min(
                country.timezones,
                key=lambda tz: abs((parse_utc_offset_hours(tz) or 0.0) - cap_est_offset),
            )
        else:
            target_tz = country.timezones[0]

        offset = parse_utc_offset_hours(target_tz)
        if offset is None:
            return None

        return round(offset - IST_OFFSET_HOURS, 2)

    # -----------------------------------------------------------------------
    # Visa rule queries
    # -----------------------------------------------------------------------

    def get_visa_baseline(self, destination_or_code: str) -> BaseVisaRule:
        """Retrieve the static baseline visa rule for a destination name or ISO-2 code."""
        if (
            not destination_or_code
            or not isinstance(destination_or_code, str)
            or not destination_or_code.strip()
        ):
            raise InvalidLookupError("Destination or country code must be a non-empty string.")

        q = destination_or_code.strip()
        dest_key = q.lower()
        code_key = q.upper()

        if dest_key in self._visa_base_by_dest:
            return self._visa_base_by_dest[dest_key]

        if len(code_key) == 2 and code_key in self._visa_base_by_code:
            return self._visa_base_by_code[code_key]

        # Partial destination name match
        for d, rule in self._visa_base_by_dest.items():
            if dest_key in d or d in dest_key:
                return rule

        raise VisaRuleNotFoundError(f"Baseline visa rule for {destination_or_code!r} not found.")

    def get_enriched_visa(self, destination_or_code: str) -> EnrichedVisaRecord | None:
        """Retrieve the enriched multi-option visa record, or None if not enriched yet."""
        if (
            not destination_or_code
            or not isinstance(destination_or_code, str)
            or not destination_or_code.strip()
        ):
            raise InvalidLookupError("Destination or country code must be a non-empty string.")

        q = destination_or_code.strip()
        dest_key = q.lower()
        code_key = q.upper()

        if dest_key in self._visa_enriched_by_dest:
            return self._visa_enriched_by_dest[dest_key]

        if len(code_key) == 2 and code_key in self._visa_enriched_by_code:
            return self._visa_enriched_by_code[code_key]

        # Partial destination name match
        for d, rule in self._visa_enriched_by_dest.items():
            if dest_key in d or d in dest_key:
                return rule

        return None

    def get_visa_rule(self, destination_or_code: str) -> EnrichedVisaRecord | BaseVisaRule:
        """Return the enriched visa record if available, otherwise fallback to baseline rule."""
        enriched = self.get_enriched_visa(destination_or_code)
        if enriched is not None:
            return enriched
        return self.get_visa_baseline(destination_or_code)


# ---------------------------------------------------------------------------
# Module-level singleton and convenience API
# ---------------------------------------------------------------------------

_default_store: StaticDataStore | None = None


def get_store() -> StaticDataStore:
    """Return the global default StaticDataStore instance, initializing on first access."""
    global _default_store
    if _default_store is None:
        _default_store = StaticDataStore()
    return _default_store


def reload_static_data() -> None:
    """Reload all static datasets in the global store."""
    get_store().reload()


def get_airport(iata_code: str) -> Airport:
    """Resolve an airport by its IATA code (e.g. 'DEL', 'BGO')."""
    return get_store().get_airport(iata_code)


def find_airport(iata_code: str) -> Airport | None:
    """Resolve an airport by IATA code, or None if not found."""
    return get_store().find_airport(iata_code)


def get_airports_by_city(city: str) -> list[Airport]:
    """Find all airports serving a given city/municipality."""
    return get_store().get_airports_by_city(city)


def get_airports_by_country(iso_country: str) -> list[Airport]:
    """Find all airports located in a country (e.g. 'IN', 'NO')."""
    return get_store().get_airports_by_country(iso_country)


def get_airport_coordinates(iata_code: str) -> tuple[float, float]:
    """Return (latitude_deg, longitude_deg) for an airport by IATA code."""
    return get_store().get_airport_coordinates(iata_code)


def get_country(query: str) -> CountryProfile:
    """Resolve a country profile by ISO-2, ISO-3, or country name."""
    return get_store().get_country(query)


def find_country(query: str) -> CountryProfile | None:
    """Resolve a country profile, or None if not found."""
    return get_store().find_country(query)


def is_schengen(query: str) -> bool:
    """Check if a country is a member of the Schengen Area."""
    return get_store().is_schengen_member(query)


def get_ist_time_difference_hours(query: str, timezone: str | None = None) -> float | None:
    """Calculate time difference relative to IST in hours."""
    return get_store().get_ist_time_difference_hours(query, timezone=timezone)


def get_visa_baseline(destination_or_code: str) -> BaseVisaRule:
    """Retrieve the baseline visa rule from Passport Index data."""
    return get_store().get_visa_baseline(destination_or_code)


def get_enriched_visa(destination_or_code: str) -> EnrichedVisaRecord | None:
    """Retrieve the multi-option enriched visa record if available."""
    return get_store().get_enriched_visa(destination_or_code)


def get_visa_rule(destination_or_code: str) -> EnrichedVisaRecord | BaseVisaRule:
    """Retrieve the enriched visa record if available, else baseline rule."""
    return get_store().get_visa_rule(destination_or_code)
