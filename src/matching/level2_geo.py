"""
level2_geo.py — level 2: geo distance check

geocodes both addresses and checks how far apart they are.
close together = probably same location, far apart = probably different office.

requires GOOGLE_MAPS_API_KEY in .env
"""

import math
import requests
from src.utils.config import GOOGLE_MAPS_API_KEY, GEO_MATCH_DISTANCE_MILES, GEO_DIFF_OFFICE_MILES
from src.utils.logger import get_logger

logger = get_logger(__name__)


def geocode_address(record: dict) -> tuple | None:
    """
    calls google maps geocoding API to get lat/lng for a record's address.
    returns (lat, lng) or None if it fails.
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.warning("no google maps API key set, skipping geocoding")
        return None

    # build the address string from whatever fields we have
    parts = [
        record.get("address_expanded") or record.get("address_clean", ""),
        record.get("city_clean", ""),
        record.get("state_clean", ""),
        record.get("zip_clean", ""),
        record.get("country_clean", ""),
    ]
    address_str = ", ".join(p for p in parts if p)

    if not address_str.strip():
        logger.warning("empty address string, can't geocode")
        return None

    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address_str, "key": GOOGLE_MAPS_API_KEY},
            timeout=10,
        )
        data = resp.json()

        if data.get("status") != "OK" or not data.get("results"):
            logger.warning(f"geocoding failed for '{address_str[:60]}': {data.get('status')}")
            return None

        location = data["results"][0]["geometry"]["location"]
        return (location["lat"], location["lng"])

    except Exception as e:
        logger.warning(f"geocoding request failed: {e}")
        return None


def haversine_miles(coord_a: tuple, coord_b: tuple) -> float:
    """
    calculates the distance in miles between two (lat, lng) coordinates.
    uses the haversine formula — accurate enough for our purposes.
    """
    lat1, lon1 = math.radians(coord_a[0]), math.radians(coord_a[1])
    lat2, lon2 = math.radians(coord_b[0]), math.radians(coord_b[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    earth_radius_miles = 3956
    return earth_radius_miles * c


def geo_distance_check(record_a: dict, record_b: dict) -> dict:
    """
    level 2 check — geocodes both records and computes distance.

    returns a result dict with:
        - distance_miles: float or None if geocoding failed
        - geo_score: 0-100 contribution to the final score
        - same_location: bool
        - different_office: bool
        - reasoning: plain english explanation
    """
    logger.info(f"geocoding: '{record_a.get('name_clean', '')}' and '{record_b.get('name_clean', '')}'")

    coords_a = geocode_address(record_a)
    coords_b = geocode_address(record_b)

    # if either geocode fails just return a neutral result
    if not coords_a or not coords_b:
        return {
            "distance_miles": None,
            "geo_score": 50,  # neutral, don't penalize if geocoding just failed
            "same_location": False,
            "different_office": False,
            "reasoning": "geocoding failed for one or both addresses, skipping geo check",
        }

    distance = haversine_miles(coords_a, coords_b)
    logger.info(f"distance: {distance:.2f} miles")

    # close together = same location
    if distance <= GEO_MATCH_DISTANCE_MILES:
        return {
            "distance_miles": round(distance, 2),
            "geo_score": 95,
            "same_location": True,
            "different_office": False,
            "reasoning": f"addresses are {distance:.2f} miles apart — effectively the same location",
        }

    # far apart = probably different offices of the same company
    if distance >= GEO_DIFF_OFFICE_MILES:
        return {
            "distance_miles": round(distance, 2),
            "geo_score": 30,
            "same_location": False,
            "different_office": True,
            "reasoning": f"addresses are {distance:.1f} miles apart — likely different offices, not a duplicate",
        }

    # in between — partial score, flag for deeper review
    # score scales down linearly as distance increases
    score = int(95 * (1 - (distance / GEO_DIFF_OFFICE_MILES)))
    return {
        "distance_miles": round(distance, 2),
        "geo_score": max(score, 20),
        "same_location": False,
        "different_office": False,
        "reasoning": f"addresses are {distance:.1f} miles apart — close enough to investigate further",
    }


if __name__ == "__main__":
    # quick test with two boeing records
    a = {"address_clean": "100 north riverside plaza", "city_clean": "chicago", "state_clean": "il", "zip_clean": "60606", "country_clean": "usa"}
    b = {"address_clean": "100 north riverside plaza", "city_clean": "chicago", "state_clean": "il", "zip_clean": "60606", "country_clean": "united states"}

    result = geo_distance_check(a, b)
    for k, v in result.items():
        print(f"  {k}: {v}")