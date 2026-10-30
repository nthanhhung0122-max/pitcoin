"""
TOOL MINI GAME MINES CHUYEN BIET:
- Chay xoay vong lien tuc 24/7 qua cac tai khoan.
- Chien thuat o chon:
    + Mac dinh mo O 1 (Hang 1 o dau tien #0)
    + Neu O 1 thua -> Chuyen sang O ben canh (#1)
    + Neu O ben canh thang -> Quay lai O 1
    + Neu O ben canh thua -> KET THUC VAN / DUNG PHIEN
- 5 Bom / 25 O (He so: 1.2125x).
- Muc cuoc co ban: 20 PTC (Dat chuoi 10 win -> cuoc 1 tran 50 PTC roi ve 20 PTC).
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
MINE_COUNT = 5               # 5 Bom / 25 O (He so an: 1.2125x)
PRIMARY_TILE = 0             # O 1: Hang 1 o dau tien tu trai qua phai (Index 0)
ADJACENT_TILE = 1            # O ben canh: Hang 1 o thu hai (Index 1)
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

def play_mines_custom(acc):
    name = acc["name"]
    s_str = acc.get("string_session")
    print("\n" + "="*70)
    log("ACCOUNT", f"=== CHOI MINES: {name} (5 Bom - Chien thuat doi o) ===", Fore.CYAN)
    print("="*70)

    init_data = acc.get("init_data")
    if not init_data and s_str:
        init_data = asyncio.run(fetch_fresh_init(s_str))
        acc["init_data"] = init_data

    if not init_data:
        log("SKIP", f"Chua co session cho {name}. Chuyen acc tiep theo!", Fore.YELLOW)
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
    log("WALLET", f"So du ban dau: {Fore.GREEN}{balance:,.4f} PTC{Style.RESET_ALL} | O 1 (#{PRIMARY_TILE}) -> O ben canh (#{ADJACENT_TILE})")

    # Thu hoi van cu chua ket thuc neu co
    try:
        r_act = requests.get(f"{API_BASE}/games/mines/active", headers=headers, timeout=10).json()
        if r_act.get("success") and r_act.get("game"):
            requests.post(f"{API_BASE}/games/mines/cashout", headers=headers, json={"gameId": r_act["game"]["id"]})
    except Exception:
        pass

    game_count = 0
    wins = 0
    losses = 0
    total_profit = 0
    consecutive_wins = 0
    max_streak = 0
    history = []
    current_tile = PRIMARY_TILE  # Luon bat dau voi O 1

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
        tile_name = f"O 1 (#{PRIMARY_TILE})" if current_tile == PRIMARY_TILE else f"O BEN CANH (#{ADJACENT_TILE})"

        print(f"\n{Fore.LIGHTBLACK_EX}--- [Van #{game_count}] Cuoc: {current_wager} PTC | 5 Bom | Chon: {tile_name} | Chuoi thang: {consecutive_wins} ---{Style.RESET_ALL}")

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

            # Mo o theo trang thai hien tai (O 1 hoac O ben canh)
            log("PICK", f"Dang mo {tile_name}...", Fore.YELLOW)
            r_rev = requests.post(f"{API_BASE}/games/mines/reveal", headers=headers, json={
                "gameId": game_id,
                "tileIndex": current_tile
            }, timeout=10).json()

            if not r_rev.get("success"):
                log("ERR", f"Loi mo o: {r_rev.get('error')}", Fore.RED)
                break

            if r_rev.get("busted"):
                losses += 1
                total_profit -= current_wager
                consecutive_wins = 0
                history.append('L')

                if current_tile == PRIMARY_TILE:
                    # Neu chon O 1 ma thua -> chuyen sang O ben canh de go!
                    log("BOOM", f"O 1 (#{PRIMARY_TILE}) dinh BOM! Mat {current_wager} PTC. So du: {balance:,.4f} PTC", Fore.RED)
                    current_tile = ADJACENT_TILE
                    log("SWITCH", f"🔄 O 1 THUA -> Chuyen sang O BEN CANH (#{ADJACENT_TILE}) cho van tiep theo!", Fore.CYAN)
                else:
                    # O ben canh ma lai THUA -> KET THUC VAN / DUNG PHIEN!
                    log("BOOM", f"O BEN CANH (#{ADJACENT_TILE}) cung dinh BOM! Mat {current_wager} PTC. So du: {balance:,.4f} PTC", Fore.RED)
                    print("\n" + "!"*60)
                    log("STOP_TRIGGERED", f"🛑 O BEN CANH THUA -> KET THUC VAN/PHIEN CHO {name} THEO YEU CAU!", Fore.RED)
                    log("LICH_SU", f"Lich su cac van gan nhat: {history[-5:]}", Fore.YELLOW)
                    print("!"*60)
                    break
            else:
                mult = r_rev["game"].get("currentMultiplier", 1.2125)
                log("GEM", f"{tile_name} la KIM CUONG! He so: {Fore.GREEN}{mult:.4f}x{Style.RESET_ALL} -> Cashout chot loi ngay!", Fore.GREEN)
                time.sleep(0.8)

                # Cashout
                r_cash = requests.post(f"{API_BASE}/games/mines/cashout", headers=headers, json={"gameId": game_id}, timeout=10).json()
                if r_cash.get("success"):
                    payout = r_cash["game"].get("payout", current_wager * mult)
                    profit = payout - current_wager
                    balance = r_cash.get("claimedPITBalance", balance + payout)
                    wins += 1
                    total_profit += profit
                    consecutive_wins += 1
                    max_streak = max(max_streak, consecutive_wins)
                    history.append('W')
                    log("CASHOUT", f"CHOT LOI: {Fore.GREEN}+{payout:,.4f} PTC{Style.RESET_ALL} (Lai: +{profit:,.4f} PTC) | So du: {balance:,.4f} PTC", Fore.GREEN)

                    # Neu dang o O ben canh ma THANG -> QUAY LAI O 1
                    if current_tile == ADJACENT_TILE:
                        log("RECOVER_OK", f"🎉 O BEN CANH THANG! QUAY LAI O 1 (#{PRIMARY_TILE}) CHO VAN TIEP THEO!", Fore.GREEN)
                        current_tile = PRIMARY_TILE
                else:
                    log("ERR", f"Loi cashout: {r_cash.get('error')}", Fore.RED)

            if is_boost_round:
                log("RESET_BOOST", f"Da hoan thanh luot cuoc dac biet {BOOST_WAGER} PTC. Chinh ve {BASE_WAGER} PTC!", Fore.CYAN)
                consecutive_wins = 0

        except Exception as e:
            log("ERR", f"Loi van choi: {e}", Fore.RED)
            break

        time.sleep(DELAY_BETWEEN_GAMES)

    # Tong ket phien
    print("\n" + "="*60)
    log("SUMMARY", f"TONG KET CHO {name}: Thang: {wins} | Thua: {losses} | Lai: {total_profit:+,.4f} PTC | So du: {balance:,.4f} PTC", Fore.CYAN)
    print("="*60 + "\n")

def main():
    print(f"""
{Fore.CYAN}======================================================================
     TOOL MINES 5 BOM - CUOC 20 PTC - CHAY XOAY VONG LIEN TUC 24/7
     - Chien thuat o chon:
         + Mac dinh mo O 1 (Hang 1 o dau tien #{PRIMARY_TILE})
         + Neu O 1 thua -> Chuyen sang O ben canh (#{ADJACENT_TILE})
         + Neu O ben canh thang -> Quay lai O 1
         + Neu O ben canh thua -> KET THUC VAN / DUNG PHIEN
     - So bom: {MINE_COUNT} Bom / 25 O (He so an: 1.2125x)
     - Muc cuoc: {BASE_WAGER} PTC (Streak 10 win -> Cuoc 1 tran {BOOST_WAGER} PTC roi ve {BASE_WAGER} PTC)
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
        log("LOOP", f"Hoan thanh vong #{cycle_count}. Tam nghi {COOLDOWN_BETWEEN_CYCLES}s truoc khi vao vong moi...", Fore.CYAN)
        print("="*60 + "\n")
        time.sleep(COOLDOWN_BETWEEN_CYCLES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[EXIT] Da dung chuong trinh.{Style.RESET_ALL}")
