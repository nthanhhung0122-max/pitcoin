"""
TOOL CHUYEN BIET: KHAI THAC MO DAO, XEM ADS BOOST X3.5 & LAM NHIEM VU
- Mini App: @pitbullcoinbot (https://play.pitcoindrop.com/)
- Khi bat dau chay: Tu dong buff Overclock x3.5 lien tiep 10 lan (stack max 12h)
- Thu hoach mo dao: Tu dong gia lap xem quang cao de nhan x1.5 lan PTC
- Tu dong nhan hoa hong gioi thieu + quet nhiem vu moi
- Chay lien tuc theo chu ky 24/7 (Nghi 30 phut giua cac chu ky)
"""

import os
import sys
import time
import json
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

# Thoi gian nghi giua cac chu ky thu hoach (30 phut = 1800 giay)
CYCLE_SLEEP_SECONDS = 1800

ACCOUNTS = [
    {
        "id": 1,
        "name": "Acc 1 (hungzai22)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC1") or "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoedRNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch5TrrzLXi2Q3N0HorIL1JfV0xoFQlY=",
        "init_data": "",
        "stats": {"mined": 0, "ref": 0, "quests": 0, "balance": 0}
    },
    {
        "id": 2,
        "name": "Acc 2 (gaylobucu)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC2") or "1BVtsOHIBuzoeRtBOmpNGh2sdyxpZ5e0nY4MrFe-6KKbmJPaM0YnCJiKRI0L9mEh1C5rwqLQqucj456LRF7vV1YIPjZNqL6JevLM0Ww3FTml1NoKdwsiPINfsy9MbBlBhKOvha7py44L4pK5aEXjwpjpoNj4LaSmtWaPiQPufJuTwPB86f4gYjSeXM3HtxhnFU7MtHR5vbZPBa9N2HQSlt2BMB47q00DbQVtvYA37R3R-TrtV2MtwixL9ozChADFq38NYcw4eRyRwKrkobVLccvz0_hvqgHXiQbrfcFLLRkRGwGlRCB-Ew4YhLLdnCbG1hjGEfxUrp9MRmF0JvS-u20MfAuvlcgQ=",
        "init_data": "",
        "stats": {"mined": 0, "ref": 0, "quests": 0, "balance": 0}
    },
    {
        "id": 3,
        "name": "Acc 3 (phan hoang)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC3") or "1BVtsOHIBuxrTG6Dt9a8C_J7D3bm1disV_mQiY_mw7AP5Gp-cEVAlKU1cfvOJiDnU6yi7PInfBRG_wJBQ3uNc-1kOa8fM3ITgUcE7YkaCd77FoBTgIFqw6gMYeRfVJOS1U9S_botQyX5764dx94NBfHHm8HuQKejs0PrdAJQq6WUTDS3mkijWRWIvO4SwXSUrM5yNOFoGIrav8Mbuyl5ZFQaDPg_kwa11NT4kiqov8rVx0virTbGbQudyFeG80kP4zW2CxcuL6TObemIPJgR_2-jb8zVQRQMiI4oN829ZCfHU2JCQY2S2clWwI7onZV8AhYP1LoDBiu32dgQPuk4brS-r1DtkySc=",
        "init_data": "",
        "stats": {"mined": 0, "ref": 0, "quests": 0, "balance": 0}
    },
    {
        "id": 4,
        "name": "Acc 4 (Wind_trader)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC4", ""),
        "init_data": os.getenv("INIT_DATA_PITCOIN_ACC4", ""),
        "stats": {"mined": 0, "ref": 0, "quests": 0, "balance": 0}
    },
    {
        "id": 5,
        "name": "Acc 5 (Sy Nguyen)",
        "string_session": os.getenv("TELEGRAM_STRING_SESSION_ACC5", ""),
        "init_data": os.getenv("INIT_DATA_PITCOIN_ACC5", ""),
        "stats": {"mined": 0, "ref": 0, "quests": 0, "balance": 0}
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

def process_farm_account(acc, is_first_run=False):
    name = acc["name"]
    stats = acc["stats"]

    print("\n" + "="*65)
    log("ACCOUNT", f"=== THU HOACH & TANG TOC: {name} ===", Fore.CYAN)
    print("="*65)

    # 1. Lay init_data
    init_data = acc.get("init_data")
    s_str = acc.get("string_session")
    if not init_data and s_str:
        init_data = asyncio.run(fetch_fresh_init(s_str))
        acc["init_data"] = init_data

    if not init_data:
        log("SKIP", f"Chua co Session hoac init_data cho {name}. Bo qua!", Fore.YELLOW)
        return

    headers = get_headers(init_data)

    # 2. Lay thong tin user & mo dao
    try:
        r_user = requests.get(f"{API_BASE}/user", headers=headers, timeout=12)
        u_data = r_user.json()
        if not u_data.get("success"):
            log("ERR", f"Loi API user: {u_data.get('error')}", Fore.RED)
            return
    except Exception as e:
        log("ERR", f"Loi ket noi server Pitcoin: {e}", Fore.RED)
        return

    u = u_data["user"]
    m = u_data.get("miningState", {})
    balance = u.get("claimedPITBalance", 0)
    bucket_val = m.get("currentBucketValue", 0)
    bucket_cap = m.get("bucketCapacity", 0)
    speed = m.get("activeTHs", 0)
    stats["balance"] = balance

    log("PROFILE", f"Ten: {Fore.YELLOW}{u.get('displayName')}{Style.RESET_ALL} (ID: {u.get('telegramId')})")
    log("WALLET", f"So du vi: {Fore.GREEN}{balance:,.4f} PTC{Style.RESET_ALL} | Toc do: {Fore.CYAN}{speed} TH/s{Style.RESET_ALL}")
    log("BUCKET", f"Binh dao: {Fore.YELLOW}{bucket_val:,.4f} / {bucket_cap:,.4f} PTC{Style.RESET_ALL}")

    # 2.5. COI BUFF DAO 10 LAN KHI BAT DAU CHAY THEO YEU CAU
    if is_first_run:
        log("BUFF_10", f"⚡ BAT DAU COI BUFF DAO 10 LAN LIEN TIEP CHO {name}...", Fore.MAGENTA)
        for i in range(1, 11):
            try:
                r_b = requests.post(f"{API_BASE}/boost/overclock", headers=headers, json={}, timeout=10).json()
                if r_b.get("success"):
                    msg = r_b.get("message", "Thanh cong")
                    log("BUFF_OK", f"[{i}/10] {Fore.GREEN}Buff Overclock thanh cong!{Style.RESET_ALL} {msg}", Fore.MAGENTA)
                else:
                    msg = r_b.get("message", r_b.get("error", ""))
                    log("BUFF", f"[{i}/10] Server: {msg}", Fore.YELLOW)
                    if "max" in str(r_b).lower() or "limit" in str(r_b).lower():
                        log("BUFF", "Da dat gioi han toi da 12h stack toc do!", Fore.YELLOW)
                        break
            except Exception as e:
                log("ERR", f"Loi buff lan {i}: {e}", Fore.RED)
            time.sleep(1.2)
        log("BUFF_DONE", f"✅ Hoan thanh buff dao 10 lan cho {name}! Bat dau qua trinh thu hoach.", Fore.GREEN)

    # 3. Thu hoach mo dao (XEM QUANG CAO DE NHAN NHIEU HON x1.5 LAN COIN)
    if bucket_val > 0.005:
        log("MINE", f"Dang thu hoach binh dao ({bucket_val:,.4f} PTC) + COI QC (x1.5)...", Fore.YELLOW)
        try:
            payload_claim = {"multiplier": 1.5, "isAdClaim": True}
            r_c = requests.post(f"{API_BASE}/mine/claim", headers=headers, json=payload_claim, timeout=10).json()
            if r_c.get("success"):
                claimed = r_c.get("claimedAmount", bucket_val * 1.5)
                base_amt = r_c.get("baseAmount", bucket_val)
                bonus_amt = r_c.get("bonusAmount", claimed - base_amt)
                balance = r_c.get("newBalance", balance + claimed)
                stats["mined"] += claimed
                stats["balance"] = balance
                log("MINE_OK", f"Thu hoach thanh cong (Xem QC x1.5): {Fore.GREEN}+{claimed:,.4f} PTC{Style.RESET_ALL} (Goc: {base_amt:,.4f} | Thuong QC: {Fore.GREEN}+{bonus_amt:,.4f}{Style.RESET_ALL})! So du: {balance:,.4f} PTC", Fore.GREEN)
            else:
                r_c2 = requests.post(f"{API_BASE}/mine/claim", headers=headers, json={}, timeout=10).json()
                if r_c2.get("success"):
                    claimed = r_c2.get("claimedAmount", bucket_val)
                    balance = r_c2.get("newBalance", balance + claimed)
                    stats["mined"] += claimed
                    stats["balance"] = balance
                    log("MINE_OK", f"Thu hoach thuong: {Fore.GREEN}+{claimed:,.4f} PTC{Style.RESET_ALL}! So du: {balance:,.4f} PTC", Fore.GREEN)
        except Exception as e:
            log("ERR", f"Loi claim mo: {e}", Fore.RED)

    # 4. Thu hoach hoa hong gioi thieu
    unclaimed_ref = u.get("referralStats", {}).get("unclaimedPIT", 0)
    if unclaimed_ref > 0:
        log("REF", f"Phat hien {unclaimed_ref:,.4f} PTC hoa hong! Dang nhan...", Fore.YELLOW)
        try:
            r_ref = requests.post(f"{API_BASE}/referrals/claim", headers=headers, json={}, timeout=10).json()
            if r_ref.get("success"):
                claimed_ref = r_ref.get("claimedAmount", unclaimed_ref)
                balance += claimed_ref
                stats["ref"] += claimed_ref
                stats["balance"] = balance
                log("REF_OK", f"Nhan hoa hong: {Fore.GREEN}+{claimed_ref:,.4f} PTC{Style.RESET_ALL}! So du: {balance:,.4f} PTC", Fore.GREEN)
        except Exception as e:
            log("ERR", f"Loi claim ref: {e}", Fore.RED)

    # 5. Kich hoat Boost Overclock duy tri (neu khong phai lan dau)
    if not is_first_run:
        try:
            r_boost = requests.post(f"{API_BASE}/boost/overclock", headers=headers, json={}, timeout=10).json()
            if r_boost.get("success"):
                log("BOOST", f"Overclock Speed Boost: {Fore.MAGENTA}{r_boost.get('message', 'Active!')}{Style.RESET_ALL}", Fore.MAGENTA)
        except Exception as e:
            log("ERR", f"Loi boost overclock: {e}", Fore.RED)

    # 6. Tu dong lam Nhiem vu moi
    try:
        r_q = requests.get(f"{API_BASE}/quests", headers=headers, timeout=10).json()
        if r_q.get("success"):
            quests = r_q.get("quests", [])
            completed_ids = set(q["id"] for q in u.get("completedQuests", []))
            for q in quests:
                q_id = q["id"]
                if q_id not in completed_ids:
                    reward = q.get("reward", 0)
                    log("QUEST", f"Dang lam: {q.get('title')} (+{reward} PTC)...", Fore.CYAN)
                    r_done = requests.post(f"{API_BASE}/quests/complete", headers=headers, json={"questId": q_id}, timeout=10).json()
                    if r_done.get("success"):
                        log("QUEST_OK", f"Hoan thanh: {q.get('title')}! {Fore.GREEN}+{reward} PTC{Style.RESET_ALL}", Fore.GREEN)
                        balance += reward
                        stats["quests"] += reward
                        stats["balance"] = balance
                    time.sleep(1)
    except Exception as e:
        log("ERR", f"Loi quet quests: {e}", Fore.RED)

    log("DONE", f"Hoan thanh thu hoach cho {name}. So du cuoi: {Fore.GREEN}{stats['balance']:,.4f} PTC{Style.RESET_ALL}\n", Fore.CYAN)

def main():
    print(f"""
{Fore.CYAN}======================================================================
     TOOL AUTO THU HOACH MO DAO & TANG TOC OVERCLOCK PITCOIN DROP
     - Khi bat dau chay: Tu dong xem buff dao Overclock x3.5 du 10 lan
     - Thu hoach mo dao: Tu dong gia lap xem QC de nhan them x1.5 lan PTC
     - Tu dong Mine Claim + Ref Claim + Quests
     - Vong lap 24/7 (nghi {CYCLE_SLEEP_SECONDS // 60} phut giua cac chu ky)
======================================================================{Style.RESET_ALL}
    """)

    cycle = 0
    while True:
        cycle += 1
        is_first_run = (cycle == 1)
        print(f"\n{Fore.GREEN}>>>>>>>>>> BAT DAU CHU KY #{cycle} ({time.strftime('%Y-%m-%d %H:%M:%S')}) <<<<<<<<<<{Style.RESET_ALL}")
        for a in ACCOUNTS:
            if a.get("string_session") or a.get("init_data"):
                process_farm_account(a, is_first_run=is_first_run)
                time.sleep(2)

        print("\n" + "="*60)
        print(f"{Fore.GREEN}BANG TONG KET SO DU TAT CA TAI KHOAN (CHU KY #{cycle}):{Style.RESET_ALL}")
        for a in ACCOUNTS:
            if a.get("string_session") or a.get("init_data"):
                s = a["stats"]
                print(f"- {a['name']:22s}: So du: {Fore.GREEN}{s['balance']:,.4f} PTC{Style.RESET_ALL} | Mined: +{s['mined']:,.4f} | Quests: +{s['quests']:,.4f}")
        print("="*60 + "\n")

        log("SLEEP", f"Tam nghi {CYCLE_SLEEP_SECONDS // 60} phut cho binh dao tich luy coin... (Nhan Ctrl+C de dung)", Fore.YELLOW)
        try:
            time.sleep(CYCLE_SLEEP_SECONDS)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[EXIT] Da dung chuong trinh.{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    main()
