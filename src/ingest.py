import os
import time
import json
from datetime import datetime, timezone, timedelta
import requests
from dotenv import load_dotenv

# 1. Ortam değişkenlerini yükle
load_dotenv()
API_KEY = os.getenv("NASA_API_KEY")

if not API_KEY:
    raise ValueError("HATA: NASA_API_KEY bulunamadı! Lütfen .env dosyanızı kontrol edin.")

RAW_DATA_DIR = "data/raw"
os.makedirs(RAW_DATA_DIR, exist_ok=True)

BASE_URL = "https://api.nasa.gov/neo/rest/v1"

def save_json_safely(data, prefix, identifier):
    """UTC zaman damgasıyla ham JSON verisini 'x' modu ile güvenle kaydeder."""
    utc_now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{prefix}_{utc_now}_{identifier}.json"
    filepath = os.path.join(RAW_DATA_DIR, filename)
    
    with open(filepath, "x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"[BAŞARILI] Kaydedildi: {filepath}")
    return filepath

def fetch_with_retry(url, params, max_retries=3):
    """Hata yönetimi ve retry (yeniden deneme) mekanizması."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"[UYARI] API limiti (429). Bekleniyor... (Deneme {attempt+1}/{max_retries})")
                time.sleep(5)
            elif 500 <= response.status_code < 600:
                print(f"[UYARI] Sunucu hatası ({response.status_code}). Bekleniyor... (Deneme {attempt+1}/{max_retries})")
                time.sleep(3)
            else:
                print(f"[HATA] İstek başarısız oldu, Kod: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            print(f"[UYARI] Zaman aşımı (Timeout). Tekrar deneniyor... ({attempt+1}/{max_retries})")
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"[HATA] Bağlantı hatası: {e}")
            return None
    return None

def main():
    print("NASA Veri Toplama (Ingestion) Süreci Başlatıldı...")
    
    browse_count = 0
    feed_count = 0
    lookup_count = 0
    failed_requests = 0
    
    # --- 1. BROWSE KAYNAĞI (Örnek: İlk 2 sayfa) ---
    print("\n--- Browse Kaynağı Çekiliyor ---")
    for page in range(2): # İhtiyaca göre sayfa sayısı artırılabilir
        url = f"{BASE_URL}/neo/browse"
        params = {"api_key": API_KEY, "page": page}
        data = fetch_with_retry(url, params)
        
        if data:
            try:
                save_json_safely(data, prefix="browse", identifier=f"page{page}")
                browse_count += 1
            except Exception as e:
                print(f"[HATA] Dosya kaydedilemedi: {e}")
                failed_requests += 1
        else:
            failed_requests += 1
        time.sleep(1) # API nazik davranmak için kısa bekleme

    # --- 2. FEED KAYNAĞI (Örnek: Son 3 günlük yakın geçişler) ---
    print("\n--- Feed Kaynağı Çekiliyor ---")
    today = datetime.now(timezone.utc).date()
    start_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    
    feed_url = f"{BASE_URL}/feed"
    feed_params = {"api_key": API_KEY, "start_date": start_date, "end_date": end_date}
    feed_data = fetch_with_retry(feed_url, feed_params)
    
    if feed_data:
        try:
            save_json_safely(feed_data, prefix="feed", identifier=f"{start_date}_to_{end_date}")
            feed_count += 1
        except Exception as e:
            print(f"[HATA] Feed dosyası kaydedilemedi: {e}")
            failed_requests += 1
    else:
        failed_requests += 1

    # --- 3. ÇALIŞMA ÖZETİ (SUMMARY) ---
    total_files = browse_count + feed_count + lookup_count
    status = "Completed" if failed_requests == 0 else "Completed with errors"
    
    print("\n" + "="*40)
    print("NASA Data Ingestion Summary")
    print("-" * 40)
    print(f"Browse files saved: {browse_count}")
    print(f"Feed files saved: {feed_count}")
    print(f"Lookup files saved: {lookup_count}")
    print(f"Total files saved: {total_files}")
    print(f"Failed requests: {failed_requests}")
    print(f"Status: {status}")
    print("="*40)

if __name__ == "__main__":
    main()