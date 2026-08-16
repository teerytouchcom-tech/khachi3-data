#!/usr/bin/env python3
"""
Khachi3 — Habous.gov.ma Prayer Times Scraper
Runs daily via GitHub Actions. Output served via GitHub Pages.
Updated: All 191 cities extracted from habous.gov.ma HTML
URLs: Tries 3 different habous.gov.ma endpoints
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
from datetime import datetime

# Three URL patterns to try (in order)
URLS = [
    "https://habous.gov.ma/prieres/horaire_hijri_2.php?ville={}",          # Arabic page
    "https://www.habous.gov.ma/prieres/horaire_hijri_fr.php?ville={}",      # French iframe
    "https://www.habous.gov.ma/horaire%20de%20priere/horaire-fm6oafr.php?ville={}", # French alt
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,ar;q=0.8",
    "Referer": "https://habous.gov.ma/",
}

MONTH_MAP = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
    # Arabic month names (Moroccan dialect)
    "يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4, "ماي": 5, "يونيو": 6,
    "يوليوز": 7, "غشت": 8, "شتنبر": 9, "أكتوبر": 10, "نونبر": 11, "دجنبر": 12,
}

# Complete list of ALL 191 cities from habous.gov.ma
CITIES = {
    1: "الرباط",
    2: "الخميسات",
    3: "تيفلت",
    4: "الرماني",
    5: "والماس",
    6: "بوزنيقة",
    7: "القنيطرة",
    8: "سيدي قاسم",
    9: "سيدي يحيى الغرب",
    10: "سيدي سليمان",
    11: "سوق أربعاء الغرب",
    12: "عرباوة",
    13: "مولاي بوسلهام",
    14: "طنجة",
    15: "تطوان",
    16: "العرائش",
    17: "أصيلة",
    18: "شفشاون",
    19: "مرتيل",
    20: "المضيق",
    21: "القصر الكبير",
    22: "القصر الصغير",
    23: "الحسيمة",
    24: "سبتة",
    25: "الفنيدق",
    26: "الجبهة",
    27: "واد لاو",
    28: "باب برد",
    29: "وزان",
    30: "بوسكور",
    31: "وجدة",
    32: "بركان",
    33: "فكيك",
    34: "بوعرفة",
    35: "كرسيف",
    36: "جرادة",
    37: "عين الشعير",
    38: "تاوريرت",
    39: "الناظور",
    40: "مليلية",
    41: "دبدو",
    42: "سلوان",
    43: "بني أنصار",
    44: "فرخانة",
    45: "تالسينت",
    46: "تندرارة",
    47: "العيون الشرقية",
    48: "بني ادرار",
    49: "السعيدية",
    50: "رأس الماء",
    51: "تافوغالت",
    52: "فزوان",
    53: "أحفير",
    54: "زايو",
    55: "دريوش",
    56: "بني تجيت",
    57: "بوعنان",
    58: "الدار البيضاء",
    59: "المحمدية",
    60: "بن سليمان",
    61: "سطات",
    62: "الكارة",
    63: "البروج",
    64: "ابن أحمد",
    65: "برشيد",
    66: "الجديدة",
    67: "أزمور",
    68: "سيدي بنور",
    69: "خميس الزمامرة",
    70: "خنيفرة",
    71: "مولاي بوعزة",
    72: "زاوية أحنصال",
    73: "بني ملال",
    74: "أزيلال",
    75: "الفقيه بنصالح",
    76: "دمنات",
    77: "القصيبة",
    78: "قصبة تادلة",
    79: "خريبكة",
    80: "وادي زم",
    81: "فاس",
    82: "صفرو",
    83: "مولاي يعقوب",
    84: "بولمان",
    85: "ميسور",
    86: "رباط الخير",
    87: "المنزل بني يازغة",
    88: "إموزار كندر",
    89: "تازة",
    90: "تاونات",
    91: "أكنول",
    92: "تيزي وسلي",
    93: "بورد",
    94: "تاهلة",
    95: "تيسة",
    96: "قرية با محمد",
    97: "كتامة",
    98: "واد أمليل",
    99: "مكناس",
    100: "يفرن",
    101: "الحاجب",
    102: "زرهون",
    103: "آزرو",
    104: "مراكش",
    105: "قلعة السراغنة",
    106: "الصويرة",
    107: "شيشاوة",
    108: "بنجرير",
    109: "الرحامنة",
    110: "تمنار",
    111: "آسفي",
    112: "الوليدية",
    113: "اليوسفية",
    114: "تسلطانت",
    115: "تامصلوحت",
    116: "قطارة",
    117: "أكادير",
    118: "تارودانت",
    119: "تزنيت",
    120: "إغرم",
    121: "تالوين",
    122: "تافراوت",
    123: "طاطا",
    124: "أقا",
    125: "فم لحصن",
    126: "بويكرة",
    127: "أولاد تايمة",
    128: "الرشيدية",
    129: "الريصاني",
    130: "أرفود",
    131: "تنديت",
    132: "كلميمة",
    133: "إملشيل",
    134: "تنجداد",
    135: "الريش",
    136: "ميدلت",
    137: "زاكورة",
    138: "ورزازات",
    139: "تنغير",
    140: "هسكورة",
    141: "قلعة مكونة",
    142: "أكدز",
    143: "بومالن دادس",
    144: "النيف",
    145: "أسول",
    146: "أمسمرير",
    147: "تازارين",
    148: "سيدي إفني",
    149: "كلميم",
    150: "أسا",
    151: "الزاك",
    152: "طانطان",
    153: "بويزكارن",
    154: "المحبس",
    155: "لمسيد",
    156: "العيون",
    157: "السمارة",
    158: "بوجدور",
    159: "طرفاية",
    160: "تفاريتي",
    161: "بوكراع",
    162: "كلتة زمور",
    163: "أمكالة",
    164: "أخفنير",
    165: "الداخلة",
    166: "الكويرة",
    167: "أوسرد",
    168: "بئر كندوز",
    169: "بئر أنزاران",
    301: "خميس سيدي عبد الجليل",
    302: "أولاد عياد",
    303: "تاهلة",
    304: "مطماطة",
    305: "إيمنتانوت",
    306: "سيدي غانم",
    307: "تفنتان",
    308: "آيت القاق",
    309: "أكدال أملشيل",
    310: "اكودال املشيل ميدلت",
    311: "أكايوار",
    312: "عين العودة",
    313: "أسكين",
    314: "آيت ورير",
    315: "زاوية مولاي ابراهيم",
    316: "تولكولت",
    317: "إيكس",
    318: "كرس",
    319: "تيسنت",
    320: "فم زكيد",
    321: "قصر إيش",
    322: "إيمين ثلاث"
}

def parse_first_month(text):
    lower = text.lower().strip()
    # Try French months
    for name, num in MONTH_MAP.items():
        if name in lower:
            return num
    return datetime.now().month

def find_prayer_table(soup):
    """Find the prayer table using multiple strategies"""
    # Strategy 1: by ID
    table = soup.find("table", id="horaire")
    if table:
        return table
    
    # Strategy 2: by class
    table = soup.find("table", class_="horaire")
    if table:
        return table
    
    # Strategy 3: find table containing prayer-related words
    prayer_words = ["الفجر", "الصبح", "الشروق", "الظهر", "العصر", "المغرب", "العشاء",
                    "Alfajr", "Fajr", "Chourouq", "Dhuhr", "Asr", "Maghrib", "Isha"]
    for t in soup.find_all("table"):
        text = t.get_text()
        if sum(1 for w in prayer_words if w in text) >= 3:
            return t
    
    return None

def scrape_city(session, city_id):
    """Try all URL patterns until one works"""
    for url_pattern in URLS:
        url = url_pattern.format(city_id)
        try:
            resp = session.get(url, timeout=25)
            resp.encoding = "utf-8"
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, "html.parser")
            table = find_prayer_table(soup)
            if not table:
                continue
            
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue
            
            # Parse header
            hdr = [c.get_text(strip=True) for c in rows[0].find_all(["td", "th"])]
            hijri_month = hdr[1] if len(hdr) > 1 else ""
            greg_text = hdr[2] if len(hdr) > 2 else ""
            start_month = parse_first_month(greg_text)
            
            # Parse data rows
            days = []
            cur_month = start_month
            prev = 0
            
            for i in range(1, len(rows)):
                cells = rows[i].find_all("td")
                if len(cells) < 9:
                    continue
                c = [cell.get_text(strip=True) for cell in cells]
                
                is_moon = any(w in " ".join(c) for w in ["Selon", "حسب", "observation", "المراقبة"])
                
                try:
                    gd = int(c[2])
                except:
                    continue
                try:
                    hd = int(c[1])
                except:
                    hd = 0
                
                if gd < prev and prev > 0:
                    cur_month = cur_month + 1 if cur_month < 12 else 1
                prev = gd
                
                f, ch, d = c[3].strip(), c[4].strip(), c[5].strip()
                a, m, ish = c[6].strip(), c[7].strip(), c[8].strip()
                
                if not re.match(r"^\d{1,2}:\d{2}$", f):
                    continue
                
                days.append({
                    "dn": c[0], "hd": hd, "gd": gd, "gm": cur_month,
                    "f": f, "c": ch, "d": d, "a": a, "m": m, "i": ish,
                    "ms": is_moon
                })
            
            if days:
                return {
                    "id": city_id,
                    "ar": CITIES.get(city_id, ""),
                    "hm": hijri_month,
                    "gm": greg_text,
                    "url": url,
                    "days": days
                }
        except Exception as e:
            continue
    
    return None

def main():
    print(f"=== Khachi3 Scraper — {datetime.utcnow().isoformat()} ===")
    print(f"Cities to scrape: {len(CITIES)}")
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Warm up session with cookies
    for warmup_url in ["https://habous.gov.ma/", "https://habous.gov.ma/fr/horaires-de-prière.html"]:
        try:
            session.get(warmup_url, timeout=10)
        except:
            pass
    
    results = {}
    ok = fail = 0
    
    for cid, ar_name in sorted(CITIES.items()):
        r = scrape_city(session, cid)
        if r and len(r["days"]) > 0:
            results[str(cid)] = r
            ok += 1
            print(f"  ✅ {cid} {ar_name}: {len(r['days'])} days (via {r['url'][:50]}...)")
        else:
            fail += 1
            print(f"  ❌ {cid} {ar_name}")
        time.sleep(0.3)
    
    output = {
        "scraped_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "https://habous.gov.ma",
        "total_cities": len(results),
        "cities": results
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/prayer_times.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))
    
    size_kb = os.path.getsize("data/prayer_times.json") / 1024
    print(f"\nDone: {ok} OK, {fail} failed, {size_kb:.0f} KB")
    
    # Verify
    if "108" in results:
        bg = results["108"]
        print(f"\nVerify Benguerir (108): {len(bg['days'])} days")
        for d in bg["days"][:3]:
            print(f"  {d['gd']}/{d['gm']}: Fajr={d['f']} Maghrib={d['m']} Isha={d['i']}")

if __name__ == "__main__":
    main()
