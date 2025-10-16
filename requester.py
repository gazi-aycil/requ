#!/usr/bin/env python3
"""
14 dakikada bir belirtilen URL'ye GET isteği atan basit, dayanıklı script.
Kullanım: python3 requester.py
Ayarlar: aşağıdaki CONFIG bölümünü düzenleyin.
"""

import time
import logging
import requests
from requests.exceptions import RequestException
from datetime import datetime

### --- CONFIG --- ###
URL = "https://katalog-2uel.onrender.com/api/health"   # <-- buraya hedef URL'i koy
METHOD = "GET"                         # "GET" veya "POST"
HEADERS = {"User-Agent": "keepalive-bot/1.0 (+you@example.com)"}  # kendine uygun bir user-agent koy
POST_DATA = None                       # POST kullanıyorsan dict koy (ör. {"key":"value"})
INTERVAL_SECONDS = 14 * 60            # 14 dakika
TIMEOUT = 70                           # istek zaman aşımı (s)
MAX_RETRIES = 3                        # geçici hatalarda yeniden deneme
BACKOFF_FACTOR = 2                     # her retry'de bekleme * BACKOFF_FACTOR
LOG_FILE = "/var/log/requester.log"    # Linux'ta çalıştıracaksan log yolu
ENABLE_LOG_FILE = False                # eğer run lokaldeyse True yapabilirsin
### --- /CONFIG --- ###

# setup logging
logger = logging.getLogger("requester")
logger.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
sh = logging.StreamHandler()
sh.setFormatter(fmt)
logger.addHandler(sh)
if ENABLE_LOG_FILE:
    fh = logging.FileHandler(LOG_FILE)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

def do_request():
    session = requests.Session()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ts = datetime.utcnow().isoformat() + "Z"
            logger.info(f"Attempt {attempt}: {METHOD} {URL} (timestamp={ts})")
            if METHOD.upper() == "GET":
                r = session.get(URL, headers=HEADERS, timeout=TIMEOUT)
            else:
                r = session.post(URL, headers=HEADERS, data=POST_DATA, timeout=TIMEOUT)
            logger.info(f"Response: {r.status_code} - {len(r.content)} bytes")
            # opsiyonel: hata say
            if r.status_code >= 500:
                raise RequestException(f"Server error {r.status_code}")
            return True
        except RequestException as e:
            logger.warning(f"Request failed (attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                wait = BACKOFF_FACTOR ** (attempt - 1)
                logger.info(f"Bekleniyor {wait}s ve yeniden deneniyor...")
                time.sleep(wait)
            else:
                logger.error("Maksimum deneme sayısına ulaşıldı, atlanıyor.")
                return False

def main_loop():
    logger.info("Başlıyor. CTRL+C ile durdurulabilir.")
    try:
        while True:
            start = time.time()
            do_request()
            elapsed = time.time() - start
            sleep_for = INTERVAL_SECONDS - elapsed
            if sleep_for <= 0:
                # istek beklenenden uzun sürdüyse hemen döngüye devam et
                logger.warning("İstekler beklenenden uzun sürdü; gecikme oluştu, hemen yenileniyor.")
                continue
            else:
                # daha okunaklı bekleme mesajı
                mins = int(sleep_for // 60)
                secs = int(sleep_for % 60)
                logger.info(f"{mins} dakika {secs} saniye bekleniyor...")
                time.sleep(sleep_for)
    except KeyboardInterrupt:
        logger.info("Kullanıcı tarafından durduruldu. Çıkılıyor.")

if __name__ == "__main__":
    main_loop()
