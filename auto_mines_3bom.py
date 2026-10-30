import os, sys, time, json, random, asyncio, urllib.parse, requests
from colorama import Fore, Style, init
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

init(autoreset=True)

API_ID = 39182276
API_HASH = "f02b155d895a3a3fbf8a1cbe810b5338"
API_BASE = "https://api.pitcoindrop.com/api"

# CAU HINH MINES 3 BOM
WAGER = 10                  # Cuoc 10 PTC / van
MINE_COUNT = 3             # 3 Bom / 25 O
DELAY_BETWEEN_GAMES = 2.0  # Nghi giua cac van (giay)
TOTAL_GAMES_TO_PLAY = 0    # 0 = Chay lien tuc khong gioi han

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
    },
    {
        "id": 4,
        "name": "Acc 4 (Wind_trader)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC4", ""),
        "init_data": os.getenv("INIT_DATA_PITCOIN_ACC4", "")
    },
    {
        "id": 5,
        "name": "Acc 5 (Sy Nguyen)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC5", ""),
        "init_data": os.getenv("INIT_DATA_PITCOIN_ACC5", "")
    }
]

def log(tag, msg, color=Fore.WHITE):
    print(f"{Fore.LIGHTBLACK_EX}[{time.strftime('%H:%M:%S')}]{Style.RESET_ALL} {color}[{tag}]{Style.RESET_ALL} {msg}")

async def fetch_fresh_init(session_str):
    if not session_str: return None
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
        log("WARN", f"Loi ket noi Telethon: {e}", Fore.YELLOW)
        return None

def get_headers(init_data):
    return {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://play.pitcoindrop.com",
        "referer": "https://play.pitcoindrop.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-telegram-init-data": init_data
    }

def play_mines_loop(acc):
    name = acc["name"]
    s_str = acc.get("string_session")
    print("\n" + "="*70)
    log("ACCOUNT", f"=== BAT DAU MINES 3 BOM: {name} ===", Fore.CYAN)
    print("="*70)

    init_data = acc.get("init_data")
    if not init_data and s_str:
        init_data = asyncio.run(fetch_fresh_init(s_str))
        acc["init_data"] = init_data

    if not init_data:
        log("SKIP", f"Chua co Session cho {name}. Bo qua!", Fore.YELLOW)
        return

    headers = get_headers(init_data)
    try:
        r_u = requests.get(f"{API_BASE}/user", headers=headers, timeout=10).json()
        if not r_u.get("success"): return
        balance = r_u["user"].get("claimedPITBalance", 0)
    except Exception: return

    start_balance = balance
    log("WALLET", f"So du ban dau: {Fore.GREEN}{balance:,.4f} PTC{Style.RESET_ALL} | Cuoc: {WAGER} PTC | So bom: {MINE_COUNT} Bom")

    game_count, wins, losses, total_profit = 0, 0, 0, 0
    recent_tiles = []

    while True:
        if TOTAL_GAMES_TO_PLAY > 0 and game_count >= TOTAL_GAMES_TO_PLAY: break
        if balance < WAGER:
            log("STOP", f"So du ({balance:,.4f} PTC) khong du cuoc {WAGER} PTC. Tam dung!", Fore.YELLOW)
            break

        game_count += 1
        client_seed = f"seed_{random.randint(100000, 999999)}_{game_count}"
        print(f"\n{Fore.LIGHTBLACK_EX}--- [Van #{game_count}] Cuoc: {WAGER} PTC | 3 Bom / 25 O (Ti le an toan 88%) ---{Style.RESET_ALL}")

        try:
            r_start_raw = requests.post(f"{API_BASE}/games/mines/start", headers=headers, json={
                "wager": WAGER, "mineCount": MINE_COUNT, "clientSeed": client_seed
            }, timeout=10)

            if r_start_raw.status_code == 429:
                wait_sec = r_start_raw.json().get("retryAfterSeconds", 6) + 1
                log("RATE_LIMIT", f"Server bao cho {wait_sec} giay...", Fore.YELLOW)
                time.sleep(wait_sec)
                r_start_raw = requests.post(f"{API_BASE}/games/mines/start", headers=headers, json={
                    "wager": WAGER, "mineCount": MINE_COUNT, "clientSeed": client_seed
                }, timeout=10)

            r_start = r_start_raw.json()
            if not r_start.get("success"): break

            game_id = r_start["game"]["id"]
            balance = r_start.get("claimedPITBalance", balance - WAGER)
            log("START", f"Van khoi tao (ID: {game_id[:8]}...) | Cuoc -{WAGER} PTC")
            time.sleep(random.uniform(1.0, 1.8))

            available = [i for i in range(25) if i not in recent_tiles[-3:]]
            pick_tile = random.choice(available)
            recent_tiles.append(pick_tile)
            log("PICK", f"Dang lat o #{pick_tile}...", Fore.YELLOW)

            r_rev = requests.post(f"{API_BASE}/games/mines/reveal", headers=headers, json={
                "gameId": game_id, "tileIndex": pick_tile
            }, timeout=10).json()

            if not r_rev.get("success"): break

            if r_rev.get("busted"):
                losses += 1
                total_profit -= WAGER
                log("BOOM", f"O #{pick_tile} dinh BOM! Mat {WAGER} PTC. So du: {balance:,.4f} PTC", Fore.RED)
            else:
                mult = r_rev["game"].get("currentMultiplier", 1.1023)
                log("GEM", f"O #{pick_tile} la KIM CUONG! He so: {Fore.GREEN}{mult:.4f}x{Style.RESET_ALL} -> Chot loi ngay!", Fore.GREEN)
                time.sleep(random.uniform(0.8, 1.5))

                r_cash = requests.post(f"{API_BASE}/games/mines/cashout", headers=headers, json={"gameId": game_id}, timeout=10).json()
                if r_cash.get("success"):
                    payout = r_cash["game"].get("payout", WAGER * mult)
                    profit = payout - WAGER
                    balance = r_cash.get("claimedPITBalance", balance + payout)
                    wins += 1
                    total_profit += profit
                    log("CASHOUT", f"CHOT LOI: {Fore.GREEN}+{payout:,.4f} PTC{Style.RESET_ALL} (Lai: {Fore.CYAN}+{profit:,.4f} PTC{Style.RESET_ALL}) | So du moi: {Fore.GREEN}{balance:,.4f} PTC{Style.RESET_ALL}", Fore.GREEN)

        except Exception as e:
            log("ERR", f"Loi van choi: {e}", Fore.RED)
            break

        time.sleep(DELAY_BETWEEN_GAMES)

    print("\n" + "="*55)
    log("SUMMARY", f"TONG KET PHIEN CHO {name}:", Fore.CYAN)
    log("SUMMARY", f"- So van: {game_count} | Thang: {Fore.GREEN}{wins}{Style.RESET_ALL} | Thua: {Fore.RED}{losses}{Style.RESET_ALL}")
    log("SUMMARY", f"- Tong lai rong: {Fore.GREEN if total_profit >= 0 else Fore.RED}{total_profit:+,.4f} PTC{Style.RESET_ALL} | So du cuoi: {Fore.GREEN}{balance:,.4f} PTC{Style.RESET_ALL}")
    print("="*55 + "\n")

def main():
    for a in ACCOUNTS:
        if a.get("string_session") or a.get("init_data"):
            play_mines_loop(a)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print(f"\n[EXIT] Da dung chuong trinh.")
