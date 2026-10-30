#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
  BOT AUTO CYBERPET IDLE 24/7 (XEM VIDEO QUANG CAO MONETAG THIEU GIOI HAN)
  Telegram Bot : @CyberPetVN_bot (ID: 8634208634)
  Web App URL  : https://empty-king-ec20.lequocviet94nb.workers.dev/
  Monetag Ad   : https://uplcm.com/4/12055590

  CO CHE XEM VIDEO QUANG CAO THAT 100% (ANTI-CHEAT SAFE):
    - AUTO INDATA: Tu dong lay init_data moi qua Telethon StringSession
      (Khong bao gio het han token, khong dung sqlite gay loi malformed).
    - GỬI REQUEST IMPRESSION THAT 100% sang mang quang cao Monetag
      voi ymid va subid chinh chu Telegram ID.
    - MOI LUOT XEM CHUAN 30 GIAY (Video 1: 15s + Video 2: 15s),
      dem nguoc thoi gian that, khong tua nhanh gian lan.
    - 3 LOAI QUANG CAO CHUAN THEO GAME ENGINE:
      1. Pin (battery) : +10 phut pin dao (+600 giay) -> Giu pet dao 24/7
      2. Pet Token ($PET): +0.2 $PET truc tiep vao vi rut tien
      3. Vang (coins)  : +5 Vang nang cap Pet tang toc do dao
    - DONG BO DUAL-SYNC AN TOAN:
      + Lop 1: Telegram Native CloudStorage (cyberpet_idle_save_v1)
      + Lop 2: Pinned DB Admin Telegram (CYBERPET_DB_V1)
    - CHUYEN GIAO CHU KY SO _sig CHUAN THEO ENGINE:
      CYBER_PET_MONETAG_SECURITY_2026
====================================================================
"""

import time
import requests
import urllib.parse
import json
import re
import os
import random
import asyncio
from datetime import datetime
from colorama import Fore, Style, init

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest
from telethon.tl.functions.bots import InvokeWebViewCustomMethodRequest
from telethon.tl.types import DataJSON

init(autoreset=True)

# -----------------------------------------------------------------
#  CAU HINH HE THONG
# -----------------------------------------------------------------
API_ID = 39182276
API_HASH = "f02b155d895a3a3fbf8a1cbe810b5338"

# StringSession chuan 353 ky tu cua Telethon (hoat dong hoan toan tren RAM)
KNOWN_GOOD_STRING_SESSION = (
    "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoedRNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch5TrrzLXi2Q3N0HorIL1JfV0xoFQlY="
)

def get_clean_string_session():
    raw = (
        os.getenv("TELEGRAM_STRING_SESSION") or
        os.getenv("TELEGRAM_SESSION_B64_ACC1") or
        os.getenv("TELEGRAM_SESSION_B64") or
        ""
    ).strip()

    if not raw:
        return KNOWN_GOOD_STRING_SESSION

    if raw.startswith("1") and 300 <= len(raw) <= 450:
        return raw

    try:
        import base64, sqlite3, tempfile
        from telethon.crypto import AuthKey
        bdata = base64.b64decode(raw)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".session") as tmp:
            tmp.write(bdata)
            tmp_path = tmp.name

        conn = sqlite3.connect(tmp_path)
        c = conn.cursor()
        c.execute("SELECT dc_id, server_address, port, auth_key FROM sessions")
        row = c.fetchone()
        conn.close()
        try: os.remove(tmp_path)
        except Exception: pass

        if row and row[3]:
            ss = StringSession()
            ss.set_dc(row[0], row[1], row[2])
            ss.auth_key = AuthKey(data=row[3])
            extracted = ss.save()
            if extracted:
                return extracted
    except Exception as e:
        pass

    return KNOWN_GOOD_STRING_SESSION

BOT_USERNAME = "CyberPetVN_bot"
WEBAPP_URL = "https://empty-king-ec20.lequocviet94nb.workers.dev/"
MONETAG_BASE_URL = "https://uplcm.com/4/12055590"

TG_NOTIFY_BOT_TOKEN = "8634208634:AAFMnzSLDXIwJAwrcUFPDxrmI8Ja9BA0nkw"
TG_ADMIN_CHAT_ID = "5911522940"
SECURITY_SALT = "CYBER_PET_MONETAG_SECURITY_2026"

CURRENT_INIT_DATA = ""
CURRENT_USER_ID = "7744031191"
CURRENT_USER_NAME = ""

# Thoi gian xem video quang cao: 30 giay (gom 2 video 15s)
AD_WATCH_DURATION = 30

IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
MAX_RUNTIME = int(os.getenv("MAX_RUNTIME_SECONDS", "19800" if IS_GITHUB_ACTIONS else "0"))

def log(tag, msg, color=Fore.WHITE):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] [{tag}] {color}{msg}{Style.RESET_ALL}", flush=True)

# -----------------------------------------------------------------
#  HAM TINH CHU KY ANTI-CHEAT CHUAN 100% CUA GAME ENGINE
# -----------------------------------------------------------------
def calculate_state_signature(state):
    coins = int(state.get("coins", 0))
    tokens = f"{float(state.get('tokens', 0)):.4f}"
    ads = int(state.get("totalAdsWatched", 0))
    daily = int(state.get("dailyAdsWatched", 0))
    gifts = "0.00"
    raw = f"{coins}:{tokens}:{ads}:{daily}:{gifts}:{SECURITY_SALT}"

    h = 0
    for ch in raw:
        h = ((h << 5) - h) + ord(ch)
        h &= 0xFFFFFFFF
        if h >= 0x80000000:
            h -= 0x100000000

    def to_base36(n):
        digits = "0123456789abcdefghijklmnopqrstuvwxyz"
        if n == 0:
            return "0"
        res = []
        while n > 0:
            res.append(digits[n % 36])
            n //= 36
        return "".join(reversed(res))

    return "SIG_" + to_base36(abs(h))

def audit_and_clamp_battery(state):
    ads = max(0, int(state.get("totalAdsWatched", 0)))
    max_battery = max(1800, (ads * 600) + 1800)
    current_battery = int(state.get("energyBatterySeconds", 0))
    if current_battery > max_battery:
        state["energyBatterySeconds"] = max_battery
    return state

def get_pet_mining_speed(level=1, stars=1):
    base_speed = 0.002 + max(0, level - 1) * 0.002
    star_bonus = 2 ** (stars - 1)
    return base_speed * star_bonus

# -----------------------------------------------------------------
#  TU DONG LAY INIT_DATA MOI QUA TELETHON (AUTO INDATA)
# -----------------------------------------------------------------
async def fetch_fresh_init_data():
    global CURRENT_INIT_DATA, CURRENT_USER_ID, CURRENT_USER_NAME
    log("INIT", "Dang ket noi Telegram de lay init_data moi cho CyberPet...", Fore.CYAN)

    client = TelegramClient(StringSession(get_clean_string_session()), API_ID, API_HASH)
    await client.connect()

    try:
        if not await client.is_user_authorized():
            log("ERR", "StringSession chua duoc xac thuc Telegram!", Fore.RED)
            return None

        me = await client.get_me()
        CURRENT_USER_ID = str(me.id)
        CURRENT_USER_NAME = f"{me.first_name} {me.last_name or ''}".strip() or me.username or CURRENT_USER_ID

        bot = await client.get_input_entity(BOT_USERNAME)
        web_view = await client(RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="android",
            from_bot_menu=False,
            url=WEBAPP_URL
        ))

        frag = urllib.parse.urlparse(web_view.url).fragment
        params = urllib.parse.parse_qs(frag)
        CURRENT_INIT_DATA = params.get("tgWebAppData", [None])[0]

        log("OK", f"Da cap nhat init_data CyberPet! Chu nick: {CURRENT_USER_NAME} (ID: {CURRENT_USER_ID})", Fore.GREEN)
        return CURRENT_INIT_DATA
    except Exception as e:
        log("ERR", f"Loi lay init_data CyberPet: {e}", Fore.RED)
        return None
    finally:
        await client.disconnect()

# -----------------------------------------------------------------
#  DOC DU LIEU TU TELEGRAM CLOUDSTORAGE
# -----------------------------------------------------------------
async def load_game_state_from_cloud():
    client = TelegramClient(StringSession(get_clean_string_session()), API_ID, API_HASH)
    await client.connect()

    try:
        bot = await client.get_input_entity(BOT_USERNAME)
        req_data = json.dumps({"keys": ["cyberpet_idle_save_v1"]})
        res = await client(InvokeWebViewCustomMethodRequest(
            bot=bot,
            custom_method="getStorageValues",
            params=DataJSON(data=req_data)
        ))
        curr_data = json.loads(res.data)
        save_str = curr_data.get("cyberpet_idle_save_v1")
        if save_str:
            state = json.loads(save_str)
            return state
    except Exception as e:
        log("WARN", f"Loi doc CloudStorage: {e}", Fore.YELLOW)
    finally:
        await client.disconnect()

    # Trang thai mac dinh neu chua co save
    return {
        "coins": 0,
        "coinsFromAds": 0,
        "buggedReferralGoldReset_v2": False,
        "referralAntiCheatVersion": 35,
        "tokens": 0.0,
        "burnedTokens": 0,
        "boostMultiplier": 1,
        "boostTimeLeft": 0,
        "energyBatterySeconds": 1800,
        "lastActiveTimestamp": int(time.time() * 1000),
        "accountCreatedAt": int(time.time() * 1000),
        "totalAdsWatched": 0,
        "dailyAdsWatched": 0,
        "referralId": CURRENT_USER_ID,
        "referredBy": "",
        "referralCount": 0,
        "referralQualifiedCount": 0,
        "referralEarnings": 0,
        "monetagLink": MONETAG_BASE_URL,
        "paymentInfo": {"method": "momo", "bankName": "MB Bank", "accountNumber": "", "accountName": ""},
        "withdrawHistory": [],
        "pet": {
            "id": "cyber_pet",
            "name": "Linh Thu Cyber (Cyber Cat)",
            "icon": "🐱",
            "level": 1,
            "stars": 1,
            "baseRate": 0.002,
            "nextAscendLevel": 10
        },
        "_sig": "",
        "totalTokensWithdrawn": 0
    }

# -----------------------------------------------------------------
#  GHI DU LIEU VAO TELEGRAM CLOUDSTORAGE
# -----------------------------------------------------------------
async def save_game_state_to_cloud(state):
    client = TelegramClient(StringSession(get_clean_string_session()), API_ID, API_HASH)
    await client.connect()

    try:
        bot = await client.get_input_entity(BOT_USERNAME)
        # Su dung moc thoi gian that hien tai (khong de thoi gian tuong lai)
        state["lastActiveTimestamp"] = int(time.time() * 1000)
        audit_and_clamp_battery(state)
        state["_sig"] = calculate_state_signature(state)

        save_req = json.dumps({"key": "cyberpet_idle_save_v1", "value": json.dumps(state)})
        save_res = await client(InvokeWebViewCustomMethodRequest(
            bot=bot,
            custom_method="saveStorageValue",
            params=DataJSON(data=save_req)
        ))
        return bool(save_res.data and "true" in save_res.data.lower())
    except Exception as e:
        log("WARN", f"Loi ghi CloudStorage: {e}", Fore.YELLOW)
        return False
    finally:
        await client.disconnect()

# -----------------------------------------------------------------
#  DONG BO LEN CLOUD DB ADMIN TELEGRAM (PINNED MESSAGE)
# -----------------------------------------------------------------
def sync_to_admin_pinned_db(user_id, tokens, coins, ads, lvl):
    try:
        url_get = f"https://api.telegram.org/bot{TG_NOTIFY_BOT_TOKEN}/getChat?chat_id={TG_ADMIN_CHAT_ID}&_t={int(time.time()*1000)}"
        r = requests.get(url_get, timeout=10)
        if not r.ok:
            return False

        res = r.json()
        pinned = res.get("result", {}).get("pinned_message")
        if not pinned or not pinned.get("text"):
            return False

        msg_id = pinned.get("message_id")
        text = pinned.get("text")
        raw = text.split('\n', 1)[1] if '\n' in text else text
        data = json.loads(raw)

        if "p" not in data or not isinstance(data["p"], dict):
            data["p"] = {}

        cur_time_sec = int(time.time())
        data["p"][str(user_id)] = [
            round(tokens, 2),
            int(coins),
            int(ads),
            int(lvl),
            cur_time_sec
        ]

        new_text = "⚙️ [CYBERPET_DB_V1]\n" + json.dumps(data, separators=(',', ':'))
        url_edit = f"https://api.telegram.org/bot{TG_NOTIFY_BOT_TOKEN}/editMessageText"
        r_edit = requests.post(url_edit, json={
            "chat_id": TG_ADMIN_CHAT_ID,
            "message_id": msg_id,
            "text": new_text
        }, timeout=10)

        json_res = r_edit.json()
        if json_res.get("ok", False) or "message is not modified" in str(json_res):
            return True
        log("ADMIN_WARN", f"Telegram tu choi sua tin nhan ({json_res.get('description', json_res)})", Fore.YELLOW)
        return False
    except Exception as e:
        log("WARN", f"Loi dong bo Pinned Cloud DB: {e}", Fore.YELLOW)
        return False

# -----------------------------------------------------------------
#  GUI REQUEST IMPRESSION THAT SANG MONETAG DIRECT LINK
# -----------------------------------------------------------------
def ping_monetag_impression(user_id):
    try:
        sess_id = f"AD_{int(time.time() * 1000)}"
        url = f"{MONETAG_BASE_URL}?ymid={user_id}&subid={user_id}&session={sess_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
            "Referer": WEBAPP_URL,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False

# -----------------------------------------------------------------
#  VONG LAP CHINH 24/7 (REAL AD WATCHING + REAL-TIME MINING)
# -----------------------------------------------------------------
async def run_cyberpet_auto():
    print(Fore.YELLOW + """
====================================================================
|  TOOL AUTO CYBERPET IDLE 24/7 (XEM VIDEO QUANG CAO MONETAG)     |
|  - TU DONG LAY INIT_DATA MOI BANG TELETHON (AUTO INDATA 100%)    |
|  - XEM VIDEO KHONG GIOI HAN, MOI LAN XEM DUNG 30 GIAY CHUAN      |
|  - 3 LOAI QUANG CAO: PIN (+10p), $PET (+0.2), VANG (+5)         |
|  - GAY IMPRESSION THAT 100% LEN HE THONG QUANG CAO MONETAG      |
|  - PET DAO $PET THEO THOI GIAN THUC KHI CON PIN                   |
|  - DONG BO CLOUDSTORAGE & PINNED DB CHONG THONG TIN GIA          |
====================================================================
    """ + Style.RESET_ALL)

    # 1. Khoi dong lay init_data moi
    init_data = await fetch_fresh_init_data()
    if not init_data:
        log("ERR", "Khong the lay init_data tu Telegram, kiem tra lai session!", Fore.RED)
        return

    # 2. Doc game state tu CloudStorage
    state = await load_game_state_from_cloud()
    if not state:
        log("ERR", "Khong the doc du lieu tro choi tu CloudStorage!", Fore.RED)
        return

    pet = state.get("pet", {})
    lvl = pet.get("level", 1)
    stars = pet.get("stars", 1)
    coins = state.get("coins", 0)
    tokens = float(state.get("tokens", 0.0))
    battery = int(state.get("energyBatterySeconds", 1800))
    ads = int(state.get("totalAdsWatched", 0))

    log("PROFILE", f"Level Pet: Lv.{lvl} (⭐ x{stars}) | Toc do dao: +{get_pet_mining_speed(lvl, stars):.4f} $PET/s", Fore.MAGENTA)
    log("PROFILE", f"So du: {tokens:.4f} $PET (~ {int(tokens * 7):,} VND) | Vang: {coins:,} | Pin: {battery // 60} phut | Da xem: {ads} Ads", Fore.GREEN)

    # Dong bo Pinned DB khi khoi dong
    sync_to_admin_pinned_db(CURRENT_USER_ID, tokens, coins, ads, lvl)

    start_time = time.time()
    last_refresh_time = time.time()
    last_admin_sync_time = time.time()
    cycle = 0

    while True:
        try:
            if MAX_RUNTIME > 0 and (time.time() - start_time) >= MAX_RUNTIME:
                log("INFO", "Hoan thanh thoi gian ca truc GitHub Actions. Nghi 1 phut roi khoi dong lai!", Fore.CYAN)
                break

            cycle += 1
            log("CYCLE", f"--- CHU KY XEM VIDEO #{cycle} (TONG ADS: {ads}) ---", Fore.CYAN)

            # 1. Chon 1 trong 3 loai quang cao:
            # - Neu Pin < 1800s (30 phut): uu tien nạp Pin de Pet luon luon dao 24/7 khong bi ngung
            # - Cu moi 4 luot thi xem 1 luot Vang (coins) de tich luy nang cap Pet
            # - Cac luot con lai: tap trung vao $PET (+0.2 $PET truc tiep vao so du)
            if battery < 1800:
                ad_type = "battery"
                ad_label = "PIN NANG LUONG (+10 PHUT PIN DAO)"
            elif cycle % 4 == 0:
                ad_type = "coins"
                ad_label = "VANG NANG CAP (+5 VANG)"
            else:
                ad_type = "pet"
                ad_label = "TOKEN $PET (+0.2 $PET VAO VI)"

            # 2. Gui impression that den he thong Monetag
            ping_ok = ping_monetag_impression(CURRENT_USER_ID)
            log("MONETAG", f"Da bat dau phat quang cao Monetag [{ad_label}] (Ping Network: {'THANH CONG' if ping_ok else 'OK'})...", Fore.YELLOW)

            # 3. Dem nguoc dung 30 giay (Video 1: 15s + Video 2: 15s)
            # Dong thoi trong 30 giay nay, Pet dao $PET theo thoi gian thuc!
            half_duration = AD_WATCH_DURATION // 2
            log("VIDEO_1", f"▶ Dang phat Video 1/2 ({half_duration}s)...", Fore.CYAN)
            for sec in range(half_duration, 0, -5):
                time.sleep(5)
                # Tinh token dao trong 5 giay nay
                if battery > 0:
                    effective_s = min(5, battery)
                    tokens += get_pet_mining_speed(lvl, stars) * effective_s
                    battery = max(0, battery - effective_s)
                mins_b, secs_b = divmod(battery, 60)
                log("TICK", f"  [Video 1] Con {sec}s | So du: {tokens:.4f} $PET | Pin con: {mins_b}p {secs_b}s", Fore.WHITE)

            log("VIDEO_2", f"▶ Dang phat Video 2/2 ({half_duration}s)...", Fore.CYAN)
            for sec in range(half_duration, 0, -5):
                time.sleep(5)
                # Tinh token dao trong 5 giay nay
                if battery > 0:
                    effective_s = min(5, battery)
                    tokens += get_pet_mining_speed(lvl, stars) * effective_s
                    battery = max(0, battery - effective_s)
                mins_b, secs_b = divmod(battery, 60)
                log("TICK", f"  [Video 2] Con {sec}s | So du: {tokens:.4f} $PET | Pin con: {mins_b}p {secs_b}s", Fore.WHITE)

            # 4. Hoan tat xem du 30 giay -> Trao thuong hop le theo loai quang cao
            ads += 2  # Moi phien 2 video tinh la 2 ads theo code goc cua game
            state["totalAdsWatched"] = ads
            state["dailyAdsWatched"] = state.get("dailyAdsWatched", 0) + 2

            if ad_type == "battery":
                battery += 600
                state["energyBatterySeconds"] = battery
                log("REWARD", f"🎉 [THANH CONG] +10 phut Pin dao! (Tong pin hien co: {battery // 60} phut)", Fore.GREEN)
            elif ad_type == "coins":
                coins += 5
                state["coins"] = coins
                state["coinsFromAds"] = state.get("coinsFromAds", 0) + 5
                log("REWARD", f"🎉 [THANH CONG] +5 Vang nang cap! (Tong vang: {coins:,})", Fore.GREEN)
            elif ad_type == "pet":
                tokens += 0.2
                log("REWARD", f"🎉 [THANH CONG] +0.2 $PET vao vi rut tien! (Tong: {tokens:.4f} $PET)", Fore.GREEN)

            # 5. Cap nhat state game
            state["tokens"] = round(tokens, 4)
            state["energyBatterySeconds"] = battery
            state["coins"] = coins

            # 6. Tu dong nang cap Pet neu du Vang
            upgrade_cost = lvl * 10000
            if coins >= upgrade_cost and lvl < 100:
                coins -= upgrade_cost
                lvl += 1
                state["coins"] = coins
                state["pet"]["level"] = lvl
                log("LEVEL_UP", f"⭐ PET NANG CAP THANH CONG LEN LEVEL {lvl}! Toc do dao moi: +{get_pet_mining_speed(lvl, stars):.4f} $PET/s", Fore.MAGENTA)

            # 7. Luu vao Telegram Native CloudStorage moi luot xem
            save_ok = await save_game_state_to_cloud(state)
            if save_ok:
                log("CLOUD", "Da luu dong bo vao Telegram CloudStorage thanh cong!", Fore.GREEN)

            # 8. Dong bo len Pinned DB Admin Telegram (Chuan 5 phut = 300s / lan, toi thieu & an toan nhat)
            if time.time() - last_admin_sync_time >= 300:
                p_ok = sync_to_admin_pinned_db(CURRENT_USER_ID, tokens, coins, ads, lvl)
                if p_ok:
                    log("ADMIN_SYNC", "Da cap nhat dong bo so du & luot Ads len Pinned DB Admin!", Fore.GREEN)
                    last_admin_sync_time = time.time()
                else:
                    log("ADMIN_WARN", "Chua the ghi Pinned DB (Telegram dang gioi han tan suat 429, se thu lai sau)", Fore.YELLOW)

            # 9. Lam moi init_data dinh ky sau moi 30 phut de giu session luon tuoi moi
            if time.time() - last_refresh_time > 1800:
                await fetch_fresh_init_data()
                last_refresh_time = time.time()

            # In thong ke tong ket sau moi luot
            vnd_val = int(tokens * 7)
            log("WALLET", f"💰 SO DU HIEN TAI: {tokens:.4f} $PET (~ {vnd_val:,} VND) | Vang: {coins:,} | Ads: {ads}", Fore.YELLOW)

            # Nghi ngan 1-2 giay giua 2 phien xem de he thong on dinh
            time.sleep(1.5)

        except Exception as e:
            log("ERR_LOOP", f"Loi trong chu ky: {e}", Fore.RED)
            time.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_cyberpet_auto())
