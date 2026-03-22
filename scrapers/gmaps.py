"""
scrapers/gmaps.py — Find local business leads via Google Places Text Search API.
Requires GOOGLE_MAPS_API_KEY in .env. Module is skipped if key is absent.
"""
import requests
import config

PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


def scrape_gmaps(queries: list[str] = None, max_per_query: int = 10) -> list[dict]:
    """
    Search Google Maps for business leads.
    Returns normalized lead dicts with type='lead'.
    """
    if not config.GMAPS_ENABLED:
        print("[GMaps] Skipped — GOOGLE_MAPS_API_KEY not set in .env")
        return []

    queries = queries or config.GMAPS_QUERIES
    all_leads = []
    seen_ids = set()

    for query in queries:
        try:
            params = {
                "query": query,
                "key": config.GOOGLE_MAPS_API_KEY,
            }
            resp = requests.get(PLACES_URL, params=params, timeout=15)
            data = resp.json()

            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                print(f"[GMaps] API error for '{query}': {data.get('status')} — {data.get('error_message', '')}")
                if data.get("status") == "REQUEST_DENIED":
                    print("[GMaps] Check your GOOGLE_MAPS_API_KEY — it may be invalid or billing not enabled.")
                continue

            results = data.get("results", [])[:max_per_query]
            for place in results:
                place_id = place.get("place_id", "")
                if not place_id or place_id in seen_ids:
                    continue
                seen_ids.add(place_id)

                name    = place.get("name", "")
                address = place.get("formatted_address", "")
                rating  = place.get("rating", 0)
                reviews = place.get("user_ratings_total", 0)

                lead = {
                    "id": f"gmaps-{place_id}",
                    "platform": "gmaps",
                    "title": name,
                    "company": name,
                    "url": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                    "budget": 0,
                    "proposals": 0,
                    "client_spend": 0,
                    "payment_verified": False,
                    "description": f"{name} — {address} (Rating: {rating}, Reviews: {reviews})",
                    "address": address,
                    "phone": "",
                    "website": "",
                    "rating": rating,
                    "review_count": reviews,
                    "query": query,
                    "niche": _infer_niche(query),
                    "type": "lead",
                }
                all_leads.append(lead)

            print(f"[GMaps] '{query}' → {len(results)} businesses found")

        except Exception as e:
            print(f"[GMaps] Error for query '{query}': {e}")
            continue

    return all_leads


def _infer_niche(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["restaurant", "hotel", "food", "cafe", "bar"]):
        return "hospitality"
    if any(w in q for w in ["real estate", "property", "realty"]):
        return "real estate"
    if any(w in q for w in ["coach", "consult", "advisor"]):
        return "coaching"
    return "business"
