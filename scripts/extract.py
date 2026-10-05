"""Extract bank agency data from the Google Places API into raw JSON."""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
CITIES_PATH = PROJECT_ROOT / "data" / "cities.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "data-of-banks.json"
PLACES_URL = "https://places.googleapis.com/v1/places:searchText"

BANKS = [
    "ARAB BANK",
    "ATTIJARIWAFA BANK",
    "Al Barid Bank",
    "BANQUE POPULAIRE",
    "BANK OF AFRICA",
    "BMCI",
    "credit agricole",
    "CFG BANK",
    "CIH BANK",
    "CREDIT DU MAROC",
    "SOCIETE GENERALE",
    "UMNIA BANK",
    "AL AKHDAR BANK",
    "BANK AL YOUSR",
]

REGIONS = [
    "Tangier-Tetouan-Al Hoceima",
    "L'Oriental",
    "Fez-Meknes",
    "Rabat-Salé-Kénitra",
    "Béni Mellal-Khénifra",
    "Casablanca-Settat",
    "Marrakech-Safi",
    "Drâa-Tafilalet",
    "Souss-Massa",
    "Guelmim-Oued Noun",
    "Laâyoune-Sakia El Hamra",
    "Dakhla-Oued Ed-Dahab",
]


def build_places():
    with open(CITIES_PATH, encoding="utf-8") as file:
        regions_dict = json.load(file)

    cities = list({city for region_cities in regions_dict.values() for city in region_cities})
    places = cities[:-3] + REGIONS[-3:]

    city_to_region = {}
    for region, region_cities in regions_dict.items():
        for city in region_cities:
            city_to_region[city.upper()] = region
    for region in REGIONS:
        city_to_region[region.upper()] = region

    return places, city_to_region


def extract():
    if not API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY is not set in .env")

    places, city_to_region = build_places()
    all_results = []

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.shortFormattedAddress,"
            "places.formattedAddress,places.types,places.primaryType,"
            "places.rating,places.userRatingCount,places.reviews,nextPageToken"
        ),
    }

    for place in places:
        for bank in BANKS:
            print(f"Fetching {bank} near {place}")
            payload = {"textQuery": f"{bank} near {place}, Morocco"}

            while True:
                response = requests.post(PLACES_URL, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                body = response.json()

                for place_data in body.get("places", []):
                    place_data["region"] = city_to_region.get(place.upper(), place)
                    place_data["bank_name"] = bank
                    all_results.append(place_data)

                next_page_token = body.get("nextPageToken")
                if not next_page_token:
                    break

                time.sleep(2)
                payload["pageToken"] = next_page_token

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(all_results, file, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_results)} places to {OUTPUT_PATH}")


if __name__ == "__main__":
    extract()
