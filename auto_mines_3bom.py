"""
TOOL MINI GAME MINES CHUYEN BIET:
- Chay xoay vong lien tuc qua tat ca tai khoan (Loop 24/7).
- Luon chon o dau tien hang 1 tu trai qua phai (tile 0).
- So luong bom: 5 bom tren ban 5x5 (He so an: 1.2125x).
- Muc cuoc co ban: 20 PTC.
- Khi thang 10 lan lien tuc: Tang cuoc len 50 PTC dung 1 luot, sau do ve 20 PTC.
- Dieu kien dung moi phien: Thua 2 tran lien tiep [L, L] HOAC thua cach 1 [L, W, L].
"""

import os
import sys
import time
import json
import random
import asyncio
import urllib.parse
import requests
from colorama import Fore, Style, init

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

init(autoreset=True)

API_ID = 39182276
API_HASH = "f02b155d895a3a3fbf8a1cbe810b5338"
API_BASE = "https://api.pitcoindrop.com/api"

# =============================================================================
# CAU HINH CHIEN THUAT TU DONG
# =============================================================================
MINE_COUNT = 5               # 5 Bom / 25 O
FIXED_TILE = 0               # Luon chon o dau tien hang 1 tu trai qua phai (Index 0)
BASE_WAGER = 20              # Muc cuoc mac dinh: 20 PTC
BOOST_WAGER = 50             # Tang cuoc len 50 PTC khi win streak 10
STREAK_TARGET = 10           # 10 lan trung lien tuc de kich hoat boost 50 PTC
DELAY_BETWEEN_GAMES = 1.8    # Nghi giua cac van (giay)
COOLDOWN_BETWEEN_CYCLES = 10 # Nghi giua cac vong xoay tat ca tai khoan (giay)

ACCOUNTS = [
    {
        "id": 1,
        "name": "Acc 1 (hungzai22)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC1") or "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoedRNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch5TrrzLXi2Q3N0HorIL1JfV0xoFQlY=",
        "init_data": ""
    },
    {
        "id": 2,
        "name": "Acc 2 (gaylobucu)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC2") or "1BVtsOHIBuzoeRtBOmpNGh2sdyxpZ5e0nY4MrFe-6KKbmJPaM0YnCJiKRI0L9mEh1C5rwqLQqucj456LRF7vV1YIPjZNqL6JevLM0Ww3FTml1NoKdwsiPINfsy9MbBlBhKOvha7py44L4pK5aEXjwpjpoNj4LaSmtWaPiQPufJuTwPB86f4gYjSeXM3HtxhnFU7MtHR5vbZPBa9N2HQSlt2BMB47q00DbQVtvYA37R3R-TrtV2MtwixL9ozChADFq38NYcw4eRyRwKrkobVLccvz0_hvqgHXiQbrfcFLLRkRGwGlRCB-Ew4YhLLdnCbG1hjGEfxUrp9MRmF0JvS-u20MfAuvlcgQ=",
        "init_data": ""
    },
    {
        "id": 3,
        "name": "Acc 3 (phan hoang)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC3") or "1BVtsOHIBuxrTG6Dt9a8C_J7D3bm1disV_mQiY_mw7AP5Gp-cEVAlKU1cfvOJiDnU6yi7PInfBRG_wJBQ3uNc-1kOa8fM3ITgUcE7YkaCd77FoBTgIFqw6gMYeRfVJOS1U9S_botQyX5764dx94NBfHHm8HuQKejs0PrdAJQq6WUTDS3mkijWRWIvO4SwXSUrM5yNOFoGIrav8Mbuyl5ZFQaDPg_kwa11NT4kiqov8rVx0virTbGbQudyFeG80kP4zW2CxcuL6TObemIPJgR_2-jb8zVQRQMiI4oN829ZCfHU2JCQY2S2clWwI7onZV8AhYP1LoDBiu32dgQPuk4brS-r1DtkySc=",
        "init_data": ""
    }
]

def log(tag, msg, color=Fore.WHITE):
    t_str = time.strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {color}[{tag}]{Style.RESET_ALL} {msg}")

async def fetch_fresh_init(session_str):
    if not session_str:
        return None
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return None
        bot = await client.get_input_entity("pitbullcoinbot")
        app = InputBotAppShortName(bot_id=bot, short_name="app")
        res = await client(RequestAppWebViewRequest(peer=bot, app=app, platform="android"))
        frag = urllib.parse.urlparse(res.url).fragment
        init_data = urllib.parse.parse_qs(frag).get("tgWebAppData", [None])[0]
        await client.disconnect()
        return init_data
    except Exception as e:
        log("WARN", f"Loi Telethon: {e}", Fore.YELLOW)
        return None

def check_stop_conditions(history):
    if len(history) >= 2 and history[-1] == 'L' and history[-2] == 'L':
        return True, "Thua 2 luot lien tiep [L, L]"
    if len(history) >= 3 and history[-1] == 'L' and history[-2] == 'W' and history[-3] == 'L':
        return True, "Thua 2 luot cach nhau 1 tran [L, W, L]"
    return False, ""

def play_mines_custom(acc):
    name = acc["name"]
    s_str = acc.get("string_session")
    print("\n" + "="*70)
    log("ACCOUNT", f"=== CHOI MINES: {name} (5 Bom - O #0 - Cuoc 20 PTC) ===", Fore.CYAN)
    print("="*70)

    init_data = acc.get("init_data")
    if not init_data and s_str:
        init_data = asyncio.run(fetch_fresh_init(s_str))
        acc["init_data"] = init_data

    if not init_data:
        log("SKIP", f"Chua co session cho {name}. Chuyen tai khoan tiep theo!", Fore.YELLOW)
        return

    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://play.pitcoindrop.com",
        "referer": "https://play.pitcoindrop.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-telegram-init-data": init_data
    }

    try:
        r_u = requests.get(f"{API_BASE}/user", headers=headers, timeout=10).json()
        if not r_u.get("success"):
            log("ERR", f"Loi lay so du: {r_u.get('error')}", Fore.RED)
            return
        balance = r_u["user"].get("claimedPITBalance", 0)
    except Exception as e:
        log("ERR", f"Loi ket noi: {e}", Fore.RED)
        return

    start_balance = balance
    log("WALLET", f"So du hien tai: {Fore.GREEN}{balance:,.4f} PTC{Style.RESET_ALL}")

    # Thu hoi van cu chua ket thuc neu co
    try:
        r_act = requests.get(f"{API_BASE}/games/mines/active", headers=headers, timeout=10).json()
        if r_act.get("success") and r_act.get("game"):
            requests.post(f"{API_BASE}/games/mines/cashout", headers=headers, json={"gameId": r_act["game"]["id"]})
    except Exception:
        pass

    game_count = 0
    consecutive_wins = 0
    history = []

    while True:
        if balance < BASE_WAGER:
            log("STOP", f"So du ({balance:,.4f} PTC) khong du cuoc ({BASE_WAGER} PTC). Chuyen acc!", Fore.YELLOW)
            break

        is_boost_round = False
        if consecutive_wins >= STREAK_TARGET:
            if balance >= BOOST_WAGER:
                current_wager = BOOST_WAGER
                is_boost_round = True
                log("BOOST", f"🎉 TRUNG {consecutive_wins} TRAN LIEN TIEP! TANG CUOC LEN {BOOST_WAGER} PTC CHO 1 LUOT NAY!", Fore.MAGENTA)
            else:
                current_wager = BASE_WAGER
                log("WARN", f"Dat chuoi {consecutive_wins} tran nhung so du < {BOOST_WAGER} PTC. Giu cuoc {BASE_WAGER} PTC.", Fore.YELLOW)
        else:
            current_wager = BASE_WAGER

        game_count += 1
        client_seed = f"seed_{random.randint(100000, 999999)}_{game_count}"
        print(f"\n--- [Van #{game_count}] Cuoc: {current_wager} PTC | 5 Bom | O #{FIXED_TILE} | Chuoi thang: {consecutive_wins} ---")

        # 1. Bat dau van
        try:
            r_start_raw = requests.post(f"{API_BASE}/games/mines/start", headers=headers, json={
                "wager": current_wager,
                "mineCount": MINE_COUNT,
                "clientSeed": client_seed
            }, timeout=10)

            if r_start_raw.status_code == 429:
                wait_sec = r_start_raw.json().get("retryAfterSeconds", 6) + 1
                log("RATE_LIMIT", f"Server bao cho {wait_sec} giay...", Fore.YELLOW)
                time.sleep(wait_sec)
                continue

            r_start = r_start_raw.json()
            if not r_start.get("success"):
                log("ERR", f"Loi start: {r_start.get('error')}", Fore.RED)
                break

            game_id = r_start["game"]["id"]
            balance = r_start.get("claimedPITBalance", balance - current_wager)
            time.sleep(1.0)

            # 2. Mo o dau tien hang 1 (o #0)
            log("PICK", f"Dang mo o #{FIXED_TILE} (Hang 1 o dau tien)...", Fore.YELLOW)
            r_rev = requests.post(f"{API_BASE}/games/mines/reveal", headers=headers, json={
                "gameId": game_id,
                "tileIndex": FIXED_TILE
            }, timeout=10).json()

            if not r_rev.get("success"):
                log("ERR", f"Loi mo o: {r_rev.get('error')}", Fore.RED)
                break

            if r_rev.get("busted"):
                consecutive_wins = 0
                history.append('L')
                log("BOOM", f"O #{FIXED_TILE} dinh BOM! Mat {current_wager} PTC. So du: {balance:,.4f} PTC", Fore.RED)
            else:
                mult = r_rev["game"].get("currentMultiplier", 1.2125)
                log("GEM", f"O #{FIXED_TILE} la KIM CUONG ({mult:.4f}x) -> Cashout ngay!", Fore.GREEN)
                time.sleep(0.8)

                # 3. Cashout chot loi
                r_cash = requests.post(f"{API_BASE}/games/mines/cashout", headers=headers, json={"gameId": game_id}, timeout=10).json()
                if r_cash.get("success"):
                    payout = r_cash["game"].get("payout", current_wager * mult)
                    profit = payout - current_wager
                    balance = r_cash.get("claimedPITBalance", balance + payout)
                    consecutive_wins += 1
                    history.append('W')
                    log("CASHOUT", f"CHOT LOI: {Fore.GREEN}+{payout:,.4f} PTC{Style.RESET_ALL} (Lai: +{profit:,.4f} PTC) | So du: {balance:,.4f} PTC", Fore.GREEN)

            # Het 1 luot boost 50 PTC -> chinh lai ve 20 PTC
            if is_boost_round:
                log("RESET", f"Da het luot dac biet. Chinh lai cuoc ve {BASE_WAGER} PTC!", Fore.CYAN)
                consecutive_wins = 0

            # 4. Kiem tra dieu kien dung
            should_stop, stop_reason = check_stop_conditions(history)
            if should_stop:
                print("\n" + "!"*60)
                log("STOP_TRIGGERED", f"DUNG PHIEN CHO {name}: {stop_reason}!", Fore.RED)
                log("HISTORY", f"Lich su 5 van gan nhat: {history[-5:]}", Fore.YELLOW)
                print("!"*60)
                break

        except Exception as e:
            log("ERR", f"Loi van choi: {e}", Fore.RED)
            break

        time.sleep(DELAY_BETWEEN_GAMES)

def main():
    print(f"""
{Fore.CYAN}======================================================================
     TOOL MINES 5 BOM - CUOC 20 PTC - CHAY XOAY VONG LIEN TUC 24/7
     - O chon co dinh: Hang 1 o dau tien tu trai sang (#{FIXED_TILE})
     - So bom: {MINE_COUNT} Bom / 25 O (He so an: 1.2125x)
     - Muc cuoc: {BASE_WAGER} PTC (Streak 10 win -> Cuoc 1 tran {BOOST_WAGER} PTC roi ve {BASE_WAGER} PTC)
     - Dieu kien dung moi phien:
         + Thua 2 luot lien tiep [L, L]
         + Thua 2 luot cach nhau 1 tran [L, W, L]
     - Che do: Chay xoay vong tat ca tai khoan lien tuc!
======================================================================{Style.RESET_ALL}
    """)

    cycle_count = 0
    while True:
        cycle_count += 1
        print(f"\n{Fore.GREEN}>>>>>>>>>> BAT DAU VONG XOAY #{cycle_count} ({time.strftime('%Y-%m-%d %H:%M:%S')}) <<<<<<<<<<{Style.RESET_ALL}")
        
        active_accs = [a for a in ACCOUNTS if a.get("string_session") or a.get("init_data")]
        for a in active_accs:
            play_mines_custom(a)
            time.sleep(2)

        print("\n" + "="*60)
        log("LOOP", f"Hoan thanh vong #{cycle_count}. Tam nghi {COOLDOWN_BETWEEN_CYCLES} giay truoc khi vao vong moi...", Fore.CYAN)
        print("="*60 + "\n")
        time.sleep(COOLDOWN_BETWEEN_CYCLES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[EXIT] Da dung chuong trinh theo yeu cau.{Style.RESET_ALL}")
