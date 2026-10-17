import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NASA_API_KEY")
if not API_KEY:
    raise ValueError(
        "NASA_API_KEY bulunamadı. Proje kök dizinindeki .env dosyasını kontrol edin."
    )

BASE_URL = "https://api.nasa.gov/neo/rest/v1"
RAW_DATA_DIR = Path("data/raw")
TARGET_ASTEROIDS = 5000
LOOKUP_LIMIT = int(os.getenv("LOOKUP_LIMIT", "100"))
MAX_RETRIES = 4
TIMEOUT = 20

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def utc_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def save_raw_response(content, prefix, identifier):
    """API yanıtını değiştirmeden, mevcut dosyaların üzerine yazmadan kaydeder."""
    filename = f"{prefix}_{utc_timestamp()}_{identifier}.json"
    filepath = RAW_DATA_DIR / filename

    with filepath.open("xb") as file:
        file.write(content)

    return filepath


def fetch(url, params):
    """Geçici hatalarda sınırlı yeniden deneme yapar."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT)

            if response.status_code == 200:
                return response

            if response.status_code in (401, 403):
                print(
                    f"[HATA] Yetkilendirme başarısız: HTTP "
                    f"{response.status_code}. API anahtarını kontrol edin."
                )
                return None

            if response.status_code == 429 or 500 <= response.status_code < 600:
                if attempt == MAX_RETRIES - 1:
                    print(
                        f"[HATA] HTTP {response.status_code}; "
                        "yeniden deneme sınırı aşıldı."
                    )
                    return None

                retry_after = response.headers.get("Retry-After")
                try:
                    wait_seconds = float(retry_after)
                except (TypeError, ValueError):
                    wait_seconds = min(2 ** (attempt + 1), 60)

                print(
                    f"[UYARI] HTTP {response.status_code}; "
                    f"{wait_seconds:g} saniye sonra tekrar denenecek."
                )
                time.sleep(wait_seconds)
                continue

            print(f"[HATA] İstek başarısız: HTTP {response.status_code}")
            return None

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as error:
            if attempt == MAX_RETRIES - 1:
                print(f"[HATA] İstek tamamlanamadı: {error}")
                return None

            wait_seconds = min(2 ** (attempt + 1), 60)
            print(
                f"[UYARI] Bağlantı/zaman aşımı. "
                f"{wait_seconds} saniye sonra tekrar denenecek."
            )
            time.sleep(wait_seconds)

        except requests.exceptions.RequestException as error:
            print(f"[HATA] Beklenmeyen istek hatası: {error}")
            return None

    return None


def main():
    asteroid_ids = set()
    files_by_source = {"browse": 0, "feed": 0, "lookup": 0}
    failed_requests = 0
    feed_records = 0
    lookup_attempts = 0
    browse_page = 0
    total_pages = None

    print("NASA Data Ingestion başlatıldı.")
    print(f"Benzersiz asteroid hedefi: {TARGET_ASTEROIDS}")
    print(f"Lookup hedefi: en fazla {LOOKUP_LIMIT} asteroid")

    # 1. BROWSE: Benzersiz asteroid hedefini karşılayana kadar sayfaları çek.
    print("\n--- Browse ---")

    while len(asteroid_ids) < TARGET_ASTEROIDS:
        params = {"api_key": API_KEY, "page": browse_page}
        response = fetch(f"{BASE_URL}/neo/browse", params)

        if response is None:
            failed_requests += 1
            break

        try:
            data = response.json()
            page_info = data["page"]
            asteroids = data["near_earth_objects"]

            if not isinstance(asteroids, list):
                raise ValueError("near_earth_objects bir liste değil.")

            if total_pages is None:
                total_pages = int(page_info["total_pages"])

            save_raw_response(response.content, "browse", f"page{browse_page}")
            files_by_source["browse"] += 1

            previous_count = len(asteroid_ids)

            for asteroid in asteroids:
                asteroid_id = asteroid.get("id")
                if asteroid_id is not None:
                    asteroid_ids.add(str(asteroid_id))

            print(
                f"Browse sayfası {browse_page}: "
                f"{len(asteroids)} kayıt; "
                f"toplam benzersiz asteroid: {len(asteroid_ids)}"
            )

            if not asteroids or len(asteroid_ids) == previous_count:
                print("[UYARI] Yeni asteroid bulunamadı; Browse durduruluyor.")
                break

            browse_page += 1

            if total_pages is not None and browse_page >= total_pages:
                break

            time.sleep(1)

        except (ValueError, KeyError, TypeError) as error:
            print(f"[HATA] Browse yanıtı okunamadı: {error}")
            failed_requests += 1
            break
        except OSError as error:
            print(f"[HATA] Browse dosyası kaydedilemedi: {error}")
            failed_requests += 1
            break

    if len(asteroid_ids) < TARGET_ASTEROIDS:
        print(
            f"[UYARI] Hedefe ulaşılamadı. "
            f"Benzersiz asteroid sayısı: {len(asteroid_ids)}"
        )

    # 2. FEED: Son 7 günlük yakın geçiş verisi.
    print("\n--- Feed ---")

    today = datetime.now(timezone.utc).date()
    start_date = (today - timedelta(days=6)).isoformat()
    end_date = today.isoformat()

    response = fetch(
        f"{BASE_URL}/feed",
        {
            "api_key": API_KEY,
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    if response is not None:
        try:
            data = response.json()
            feed_records = sum(
                len(items)
                for items in data.get("near_earth_objects", {}).values()
                if isinstance(items, list)
            )

            save_raw_response(
                response.content,
                "feed",
                f"{start_date}_to_{end_date}",
            )
            files_by_source["feed"] += 1
            print(f"Feed kaydedildi. Yakın geçiş kayıtları: {feed_records}")

        except (ValueError, TypeError) as error:
            print(f"[HATA] Feed yanıtı okunamadı: {error}")
            failed_requests += 1
        except OSError as error:
            print(f"[HATA] Feed dosyası kaydedilemedi: {error}")
            failed_requests += 1
    else:
        failed_requests += 1

    # 3. LOOKUP: Benzersiz Browse ID'lerinin sınırlı bir alt kümesi.
    print("\n--- Lookup ---")

    selected_ids = sorted(asteroid_ids)[:max(0, LOOKUP_LIMIT)]

    for asteroid_id in selected_ids:
        lookup_attempts += 1
        response = fetch(
            f"{BASE_URL}/neo/{asteroid_id}",
            {"api_key": API_KEY},
        )

        if response is None:
            failed_requests += 1
            continue

        try:
            save_raw_response(response.content, "lookup", asteroid_id)
            files_by_source["lookup"] += 1
            print(f"Lookup kaydedildi: {asteroid_id}")

        except OSError as error:
            print(f"[HATA] Lookup dosyası kaydedilemedi: {error}")
            failed_requests += 1

        time.sleep(1)

    # 4. ÖZET
    total_files = sum(files_by_source.values())
    status = "Completed" if failed_requests == 0 else "Completed with errors"

    print("\n" + "=" * 42)
    print("NASA DATA INGESTION SUMMARY")
    print("=" * 42)
    print(f"Benzersiz asteroid sayısı: {len(asteroid_ids)}")
    print(f"Browse dosyaları: {files_by_source['browse']}")
    print(f"Feed dosyaları: {files_by_source['feed']}")
    print(f"Feed yakın geçiş kayıtları: {feed_records}")
    print(f"Lookup denemeleri: {lookup_attempts}")
    print(f"Lookup dosyaları: {files_by_source['lookup']}")
    print(f"Toplam dosya: {total_files}")
    print(f"Başarısız istek/kayıt işlemi: {failed_requests}")
    print(f"Durum: {status}")
    print("=" * 42)


if __name__ == "__main__":
    main()