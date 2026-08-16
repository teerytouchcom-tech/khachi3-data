#!/usr/bin/env python3
"""
Khachi3 — Habous.gov.ma Prayer Times Scraper
Uses Playwright (headless Chrome) to avoid being blocked.
"""

import json
import re
import os
import asyncio
from datetime import datetime, timezone
from playwright.async_api import async_playwright

BASE_URL = "https://habous.gov.ma/prieres/horaire_hijri_2.php"

MONTH_MAP = {
    "يناير":1,"فبراير":2,"مارس":3,"أبريل":4,"ماي":5,"يونيو":6,
    "يوليوز":7,"غشت":8,"شتنبر":9,"أكتوبر":10,"نونبر":11,"دجنبر":12,
    "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,
    "juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,
    "décembre":12,"decembre":12,
}

CITIES = {
    1:"الرباط",2:"الخميسات",3:"تيفلت",4:"الرماني",5:"والماس",6:"بوزنيقة",
    7:"القنيطرة",8:"سيدي قاسم",9:"سيدي يحيى الغرب",10:"سيدي سليمان",
    11:"سوق أربعاء الغرب",12:"عرباوة",13:"مولاي بوسلهام",14:"طنجة",
    15:"تطوان",16:"العرائش",17:"أصيلة",18:"شفشاون",19:"مرتيل",20:"المضيق",
    21:"القصر الكبير",22:"القصر الصغير",23:"الحسيمة",24:"سبتة",25:"الفنيدق",
    26:"الجبهة",27:"واد لاو",28:"باب برد",29:"وزان",30:"بوسكور",
    31:"وجدة",32:"بركان",33:"فكيك",34:"بوعرفة",35:"كرسيف",36:"جرادة",
    37:"عين الشعير",38:"تاوريرت",39:"الناظور",40:"مليلية",41:"دبدو",
    42:"سلوان",43:"بني أنصار",44:"فرخانة",45:"تالسينت",46:"تندرارة",
    47:"العيون الشرقية",48:"بني ادرار",49:"السعيدية",50:"رأس الماء",
    51:"تافوغالت",52:"فزوان",53:"أحفير",54:"زايو",55:"دريوش",
    56:"بني تجيت",57:"بوعنان",58:"الدار البيضاء",59:"المحمدية",
    60:"بن سليمان",61:"سطات",62:"الكارة",63:"البروج",64:"ابن أحمد",
    65:"برشيد",66:"الجديدة",67:"أزمور",68:"سيدي بنور",69:"خميس الزمامرة",
    70:"خنيفرة",71:"مولاي بوعزة",72:"زاوية أحنصال",73:"بني ملال",74:"أزيلال",
    75:"الفقيه بنصالح",76:"دمنات",77:"القصيبة",78:"قصبة تادلة",79:"خريبكة",
    80:"وادي زم",81:"فاس",82:"صفرو",83:"مولاي يعقوب",84:"بولمان",85:"ميسور",
    86:"رباط الخير",87:"المنزل بني يازغة",88:"إموزار كندر",89:"تازة",
    90:"تاونات",91:"أكنول",92:"تيزي وسلي",93:"بورد",94:"تاهلة",95:"تيسة",
    96:"قرية با محمد",97:"كتامة",98:"واد أمليل",99:"مكناس",100:"يفرن",
    101:"الحاجب",102:"زرهون",103:"آزرو",104:"مراكش",105:"قلعة السراغنة",
    106:"الصويرة",107:"شيشاوة",108:"بنجرير",109:"الرحامنة",110:"تمنار",
    111:"آسفي",112:"الوليدية",113:"اليوسفية",114:"تسلطانت",115:"تامصلوحت",
    116:"قطارة",117:"أكادير",118:"تارودانت",119:"تزنيت",120:"إغرم",
    121:"تالوين",122:"تافراوت",123:"طاطا",124:"أقا",125:"فم لحصن",
    126:"بويكرة",127:"أولاد تايمة",128:"الرشيدية",129:"الريصاني",130:"أرفود",
    131:"تنديت",132:"كلميمة",133:"إملشيل",134:"تنجداد",135:"الريش",
    136:"ميدلت",137:"زاكورة",138:"ورزازات",139:"تنغير",140:"هسكورة",
    141:"قلعة مكونة",142:"أكدز",143:"بومالن دادس",144:"النيف",145:"أسول",
    146:"أمسمرير",147:"تازارين",148:"سيدي إفني",149:"كلميم",150:"أسا",
    151:"الزاك",152:"طانطان",153:"بويزكارن",154:"المحبس",155:"لمسيد",
    156:"العيون",157:"السمارة",158:"بوجدور",159:"طرفاية",160:"تفاريتي",
    161:"بوكراع",162:"كلتة زمور",163:"أمكالة",164:"أخفنير",165:"الداخلة",
    166:"الكويرة",167:"أوسرد",168:"بئر كندوز",169:"بئر أنزاران",
    301:"خميس سيدي عبد الجليل",302:"أولاد عياد",303:"تاهلة",304:"مطماطة",
    305:"إيمنتانوت",306:"سيدي غانم",307:"تفنتان",308:"آيت القاق",
    309:"أكدال أملشيل",310:"اكودال املشيل ميدلت",311:"أكايوار",312:"عين العودة",
    313:"أسكين",314:"آيت ورير",315:"زاوية مولاي ابراهيم",316:"تولكولت",
    317:"إيكس",318:"كرس",319:"تيسنت",320:"فم زكيد",321:"قصر إيش",
    322:"إيمين ثلاث",
}

def parse_first_month(text):
    lower = text.lower().strip()
    for name, num in MONTH_MAP.items():
        if name in lower:
            return num
    return datetime.now().month

def parse_table_html(html_content, city_id):
    table_match = re.search(r'<table[^>]*id=["\']?horaire["\']?[^>]*>(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
    if not table_match:
        for m in re.finditer(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL):
            if any(w in m.group(1) for w in ['الفجر','الصبح','الشروق','الظهر','Alfajr','Chourouq']):
                table_match = m
                break

    if not table_match:
        return None

    table_html = table_match.group(1)
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    if len(rows) < 2:
        return None

    header_cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', rows[0], re.DOTALL)
    header_texts = [re.sub(r'<[^>]+>', '', c).strip() for c in header_cells]

    hijri_month = header_texts[1] if len(header_texts) > 1 else ""
    greg_text = header_texts[2] if len(header_texts) > 2 else ""
    start_month = parse_first_month(greg_text)

    days = []
    cur_month = start_month
    prev = 0

    for i in range(1, len(rows)):
        cells = re.findall(r'<td[^>]*>(.*?)</td>', rows[i], re.DOTALL)
        if len(cells) < 9:
            continue
        c = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]

        is_moon = any(w in ' '.join(c) for w in ['Selon','حسب','observation','المراقبة'])

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

        if not re.match(r'^\d{1,2}:\d{2}$', f):
            continue

        days.append({
            "dn":c[0],"hd":hd,"gd":gd,"gm":cur_month,
            "f":f,"c":ch,"d":d,"a":a,"m":m,"i":ish,"ms":is_moon
        })

    if not days:
        return None

    return {"id":city_id,"ar":CITIES.get(city_id,""),"hm":hijri_month,"gm":greg_text,"days":days}

async def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"=== Khachi3 Scraper (Playwright) — {now} ===")
    print(f"Cities: {len(CITIES)}")

    results = {}
    ok = fail = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            locale="fr-FR",
        )
        page = await context.new_page()

        # Warmup
        try:
            await page.goto("https://habous.gov.ma/", timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            print("  Warmup OK")
        except:
            print("  Warmup skipped")

        for city_id in sorted(CITIES.keys()):
            ar = CITIES[city_id]
            try:
                resp = await page.goto(f"{BASE_URL}?ville={city_id}", timeout=30000, wait_until="domcontentloaded")
                if resp and resp.status != 200:
                    fail += 1
                    print(f"  ❌ {city_id} {ar}: HTTP {resp.status}")
                    continue

                try:
                    await page.wait_for_selector("table#horaire, table", timeout=10000)
                except:
                    await asyncio.sleep(2)

                html = await page.content()
                result = parse_table_html(html, city_id)

                if result and len(result["days"]) > 0:
                    results[str(city_id)] = result
                    ok += 1
                    d0 = result["days"][0]
                    print(f"  ✅ {city_id} {ar}: {len(result['days'])} days (first: {d0['gd']}/{d0['gm']} F={d0['f']} M={d0['m']})")
                else:
                    fail += 1
                    print(f"  ❌ {city_id} {ar}: parse failed")

                await asyncio.sleep(0.3)
            except Exception as e:
                fail += 1
                print(f"  ❌ {city_id} {ar}: {type(e).__name__}")

        await browser.close()

    output = {
        "scraped_at": now,
        "source": "https://habous.gov.ma",
        "total_cities": len(results),
        "cities": results
    }

    os.makedirs("data", exist_ok=True)
    with open("data/prayer_times.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize("data/prayer_times.json") / 1024
    print(f"\nDone: {ok} OK, {fail} failed, {size_kb:.0f} KB")

    if "108" in results:
        bg = results["108"]
        print(f"\nBenguerir: {len(bg['days'])} days")
        for d in bg["days"][:3]:
            print(f"  {d['gd']}/{d['gm']}: F={d['f']} C={d['c']} D={d['d']} A={d['a']} M={d['m']} I={d['i']}")

if __name__ == "__main__":
    asyncio.run(main())
