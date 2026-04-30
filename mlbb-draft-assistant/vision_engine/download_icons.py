import os
import sys
import json
import requests
import cv2
import numpy as np
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

ICONS_DIR = os.path.join(os.path.dirname(__file__), "hero_icons")
ICON_SIZE = (80, 80)
HERO_API = "https://mapi.mobilelegends.com/hero/list"


def sanitize_name(name: str) -> str:
    return name.replace(" ", "_").replace("'", "").replace(".", "")


def download_hero_icons() -> int:
    os.makedirs(ICONS_DIR, exist_ok=True)

    print("Fetching hero list from Moonton API...")
    resp = requests.get(HERO_API, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 2000:
        raise RuntimeError(f"API error: {data.get('message')}")

    heroes = data["data"]
    print(f"Found {len(heroes)} heroes in API response")

    success = 0
    for hero in heroes:
        name = hero["name"]
        safe_name = sanitize_name(name)
        url = hero["key"]

        if not url.startswith("http"):
            url = "https:" + url

        img_path = os.path.join(ICONS_DIR, f"{safe_name}.png")
        if os.path.exists(img_path):
            print(f"  Skipping {name} (already exists)")
            success += 1
            continue

        try:
            img_resp = requests.get(url, timeout=15)
            img_resp.raise_for_status()

            img_bytes = np.frombuffer(img_resp.content, np.uint8)
            img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

            if img is None:
                print(f"  WARN: Could not decode {name}")
                continue

            img = cv2.resize(img, ICON_SIZE)
            cv2.imwrite(img_path, img)
            success += 1
            print(f"  Downloaded {name}")
        except Exception as e:
            print(f"  ERROR: {name} - {e}")

    print(f"\nDone! {success}/{len(heroes)} icons saved to {ICONS_DIR}")
    return success


if __name__ == "__main__":
    download_hero_icons()
