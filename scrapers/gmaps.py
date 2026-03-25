"""
scrapers/gmaps.py — Find local business leads via OpenStreetMap Overpass API.
100% free. No API key. No billing. No account needed.
Searches for businesses by type and city, extracts name, address, phone, website.
"""
import time
import requests
import config

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": "SafeModeBot/1.0 (lead-gen automation; contact@example.com)",
    "Accept": "application/json",
}

# Pre-cached bounding boxes (south, west, north, east) for common cities
# Avoids Nominatim rate limits for known locations
CITY_BBOX_CACHE = {
    "lagos":    (6.295, 3.234, 6.615, 3.554),
    "abuja":    (8.832, 7.240, 9.183, 7.622),
    "london":   (51.286, -0.510, 51.692, 0.334),
    "new york": (40.477, -74.259, 40.917, -73.700),
    "toronto":  (43.581, -79.639, 43.855, -79.116),
    "sydney":   (-34.118, 150.520, -33.578, 151.343),
    "nairobi":  (-1.445,  36.651, -1.163,  37.103),
    "accra":    (5.536,  -0.351,  5.703,  -0.088),
    "kano":     (11.946,  8.417, 12.114,  8.639),
}

# Map niche keywords to OSM amenity/shop tags
NICHE_TAGS = {
    "real estate": "office=estate_agent",
    "estate agent": "office=estate_agent",
    "coach": "amenity=training",
    "consultant": "office=consulting",
    "restaurant": "amenity=restaurant",
    "hotel": "tourism=hotel",
    "school": "amenity=school",
    "university": "amenity=university",
}


def _get_city_bbox(city: str):
    """Get bounding box (s, w, n, e) for a city. Uses cache first, then Nominatim."""
    key = city.lower().strip()
    if key in CITY_BBOX_CACHE:
        return CITY_BBOX_CACHE[key]
    # Try Nominatim as fallback
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": city, "format": "json", "limit": 1},
            headers=HEADERS,
            timeout=10,
        )
        results = resp.json()
        if results:
            bb = results[0].get("boundingbox", [])
            if len(bb) == 4:
                return float(bb[0]), float(bb[2]), float(bb[1]), float(bb[3])
    except Exception as e:
        print(f"[GMaps/OSM] Nominatim error for '{city}': {e}")
    return None


def _overpass_query(bbox: tuple, osm_tag: str, limit: int = 10) -> list[dict]:
    """Run an Overpass query for a given tag within a bounding box."""
    s, w, n, e = bbox
    query = f"""
    [out:json][timeout:20];
    (
      node[{osm_tag}]({s},{w},{n},{e});
      way[{osm_tag}]({s},{w},{n},{e});
    );
    out center {limit};
    """
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=25)
        if resp.status_code != 200:
            return []
        return resp.json().get("elements", [])
    except Exception:
        return []


def _parse_element(el: dict, niche: str, query_label: str) -> dict | None:
    """Convert an Overpass element into a normalized lead dict."""
    tags = el.get("tags", {})
    name = tags.get("name", "").strip()
    if not name:
        return None

    # Get coordinates
    if el.get("type") == "node":
        lat, lon = el.get("lat", 0), el.get("lon", 0)
    else:
        center = el.get("center", {})
        lat, lon = center.get("lat", 0), center.get("lon", 0)

    phone   = tags.get("phone") or tags.get("contact:phone") or ""
    website = tags.get("website") or tags.get("contact:website") or ""
    email   = tags.get("email") or tags.get("contact:email") or ""
    city    = tags.get("addr:city") or query_label
    street  = tags.get("addr:street", "")
    housen  = tags.get("addr:housenumber", "")
    address = f"{housen} {street}, {city}".strip(", ")
    maps_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}"

    place_id = str(el.get("id", ""))
    return {
        "id": f"gmaps-{place_id}",
        "platform": "gmaps",
        "title": name,
        "company": name,
        "url": website or maps_url,
        "budget": 0,
        "proposals": 0,
        "client_spend": 0,
        "payment_verified": False,
        "description": f"{name} — {address}. Phone: {phone or 'N/A'}.",
        "address": address,
        "phone": phone,
        "website": website,
        "email": email,
        "rating": 0,
        "review_count": 0,
        "query": query_label,
        "niche": niche,
        "type": "lead",
        "posted_at": "",
    }


def scrape_gmaps(queries: list[str] = None, max_per_query: int = 10) -> list[dict]:
    """
    Search OpenStreetMap for business leads by query type and city.
    queries format: "real estate agents Lagos" or "restaurants Abuja"
    """
    queries = queries or config.GMAPS_QUERIES
    all_leads = []
    seen_ids = set()

    for query in queries:
        try:
            # Split query into niche + city (last word = city)
            parts = query.strip().split()
            city = parts[-1] if parts else "Lagos"
            niche = _infer_niche(query)

            print(f"[GMaps/OSM] Searching: {query}")

            # Get city bounding box
            bbox = _get_city_bbox(city)
            if not bbox:
                print(f"[GMaps/OSM] Could not find bbox for '{city}'")
                continue
            time.sleep(1.0)  # Nominatim rate limit: 1 req/sec

            # Pick OSM tag based on niche
            osm_tag = _pick_osm_tag(query)
            elements = _overpass_query(bbox, osm_tag, limit=max_per_query)

            count = 0
            for el in elements:
                place_id = str(el.get("id", ""))
                if place_id in seen_ids:
                    continue
                seen_ids.add(place_id)

                lead = _parse_element(el, niche, query)
                if not lead:
                    continue

                all_leads.append(lead)
                count += 1
                phone = lead["phone"] or "N/A"
                print(f"  + {lead['title'][:45]} | {lead['address'][:35]} | phone: {phone}")

            print(f"[GMaps/OSM] '{query}' -> {count} businesses")
            time.sleep(2.0)  # Overpass rate limit

        except Exception as e:
            print(f"[GMaps/OSM] Error for '{query}': {e}")
            continue

    return all_leads


def _pick_osm_tag(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["real estate", "estate agent", "property"]):
        return "office=estate_agent"
    if any(w in q for w in ["restaurant", "food", "cafe"]):
        return "amenity=restaurant"
    if any(w in q for w in ["hotel"]):
        return "tourism=hotel"
    if any(w in q for w in ["coach", "training"]):
        return "amenity=training"
    if any(w in q for w in ["school"]):
        return "amenity=school"
    if any(w in q for w in ["consultant", "office", "business"]):
        return "office=company"
    return "office=company"


def _infer_niche(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["restaurant", "hotel", "food", "cafe", "bar"]):
        return "hospitality"
    if any(w in q for w in ["real estate", "property", "realty", "agent"]):
        return "real estate"
    if any(w in q for w in ["coach", "consult", "advisor"]):
        return "coaching"
    if any(w in q for w in ["school", "university", "college"]):
        return "academic"
    return "business"
