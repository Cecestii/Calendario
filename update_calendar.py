import re
import json
import uuid
import time
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# Il parametro ?t=... forza il bypass della cache CDN del sito WordPress
URL = f"https://www.leonessa-brescia.it/calendario-partite-serie-b-nazionale-2026-2027/?nocache={int(time.time())}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache"
}

MONTHS_IT = {
    'Set': ('09', '2026'), 'Ott': ('10', '2026'), 'Nov': ('11', '2026'), 'Dic': ('12', '2026'),
    'Gen': ('01', '2027'), 'Feb': ('02', '2027'), 'Mar': ('03', '2027'), 'Apr': ('04', '2027'),
    'Settembre': ('09', '2026'), 'Ottobre': ('10', '2026'), 'Novembre': ('11', '2026'), 'Dicembre': ('12', '2026'),
    'Gennaio': ('01', '2027'), 'Febbraio': ('02', '2027'), 'Marzo': ('03', '2027'), 'Aprile': ('04', '2027')
}

EXISTING_UIDS = {
    1: "7cd1ee4f-30fe-4808-a9bf-1a00ee8d7910@leonessabrescia.it",
    2: "aa57395b-f38b-4852-bab9-7f24d250bda9@leonessabrescia.it",
    3: "7a40a681-7550-4b5a-976c-97793326989c@leonessabrescia.it",
    4: "4f038278-ff79-4779-a586-ca7e25d1df71@leonessabrescia.it",
    5: "a54c3597-289b-4303-8c93-cc47918700e1@leonessabrescia.it",
    6: "5c292202-3f7e-4b07-b42a-fc7d92f78f47@leonessabrescia.it",
    7: "d8461f5f-8737-4e21-b61f-35bab90cb770@leonessabrescia.it",
    8: "f0d24954-2fc2-4053-8737-a9be32714de4@leonessabrescia.it",
    9: "aa6bf4ba-ec0f-4117-a9ed-b58fc58c5d79@leonessabrescia.it",
    10: "c3b6b285-ce08-4065-9020-dfe3b790d53a@leonessabrescia.it",
    11: "39d26bd9-312c-48d6-b594-8c698fd6cc72@leonessabrescia.it",
    12: "b2e8f9b0-93cb-4231-8956-02ddd4d432c2@leonessabrescia.it",
    13: "eaa4acb8-4861-497f-b71a-f9b308c9fff7@leonessabrescia.it",
    14: "4e1688ec-d632-4320-bf40-2384b4a662f6@leonessabrescia.it",
    15: "77c6d35d-6280-4184-971e-99bac4d33252@leonessabrescia.it",
    16: "bf3483ab-8343-45c7-b765-8fe819778340@leonessabrescia.it",
    17: "f5122755-ed23-4382-94ff-dd84a5e1e046@leonessabrescia.it",
    18: "7748f5bf-11d5-42fe-b1ce-b7d764178c9d@leonessabrescia.it",
    19: "df05450d-20ee-4aee-8a36-755fbfb232fb@leonessabrescia.it",
    20: "719d014d-e038-40e5-95b2-53f28b53b851@leonessabrescia.it",
    21: "ca1020ad-5a6c-4636-8c00-47df5a09099c@leonessabrescia.it",
    22: "ac4a5619-23ad-48f9-82fa-5d21206e69c9@leonessabrescia.it",
    23: "c7ff056e-fbff-474a-a8f8-d971855d3118@leonessabrescia.it",
    24: "449c3eeb-e60f-4252-9e97-39de6c637ea5@leonessabrescia.it",
    25: "cb8c34d9-3017-4c1f-8726-33d8e80a452c@leonessabrescia.it",
    26: "99414edc-48f0-4ee7-9c34-95baf4e0b955@leonessabrescia.it",
    27: "9381712a-ed89-49ad-9299-647d33479b00@leonessabrescia.it",
    28: "ec0283f7-c8a0-4da2-a7a5-f048e7257668@leonessabrescia.it",
    29: "b6b8b809-29c9-48ab-acf1-9e63a394abb6@leonessabrescia.it",
    30: "6a4d0a0d-9930-4155-9749-eebe4e42ccc0@leonessabrescia.it",
    31: "e62610e6-2ca8-4adf-8945-75382b37671f@leonessabrescia.it",
    32: "1684f219-e523-4c01-ad24-8213fe5501a1@leonessabrescia.it",
    33: "f39c031c-cc86-40fc-9f30-a2ff80ba83a4@leonessabrescia.it",
    34: "ed4490d5-35dc-4e0e-9bb0-028765afffa6@leonessabrescia.it"
}

def fetch_matches():
    # Proviamo prima dalla REST API ufficiale di WordPress (pagina ID 3442), che bypassa la cache HTML statica
    api_url = f"https://www.leonessa-brescia.it/wp-json/wp/v2/pages/3442?_={int(time.time())}"
    html_content = None
    
    try:
        r_api = requests.get(api_url, headers=HEADERS, timeout=15)
        if r_api.status_code == 200 and "content" in r_api.json():
            html_content = r_api.json()["content"]["rendered"]
            print(f"[DEBUG] Dati letti da WP REST API (Modified: {r_api.json().get('modified')})")
    except Exception as e:
        print(f"[DEBUG] WP REST API non disponibile ({e}), passo all'HTML diretto...")

    if not html_content:
        resp = requests.get(URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        html_content = resp.text
        print("[DEBUG] Dati letti da pagina HTML standard")

    soup = BeautifulSoup(html_content, "html.parser")
    matches = {}

    next_box = soup.select_one("article.lb-prg-next")
    if next_box:
        g_text = next_box.select_one(".lb-prg__giornata-full").get_text(strip=True)
        g_num = int(re.search(r"\d+", g_text).group(0))
        teams = [t.get_text(strip=True) for t in next_box.select(".lb-prg__nome--full")]
        meta = next_box.select_one(".lb-prg-next__meta").get_text(strip=True)
        parts = [p.strip() for p in meta.split("·")]
        d_match = re.search(r"(\d+)\s+([A-Za-z]+)\s+(\d{4})", parts[0])
        day = d_match.group(1).zfill(2)
        month = MONTHS_IT[d_match.group(2)][0]
        year = d_match.group(3)
        
        punteggio_el = next_box.select_one(".lb-prg__punteggio, .lb-prg-next__vs")
        punteggio = punteggio_el.get_text(strip=True) if punteggio_el else "vs"
        risultato = None if punteggio.lower() == "vs" else punteggio

        print(f"[DEBUG] Box Prossima Partita -> Giornata {g_num}: {teams[0]} vs {teams[1]} | Punteggio letto: {punteggio}")

        matches[g_num] = {
            "giornata": g_num,
            "data": f"{day}/{month}/{year}",
            "ora": parts[1].replace("ore", "").strip(),
            "casa": teams[0],
            "ospite": teams[1],
            "impianto": parts[2],
            "risultato": risultato,
            "cronaca_url": None
        }

    for row in soup.select("li.lb-prg-riga"):
        g_text = row.select_one(".lb-prg__giornata-full").get_text(strip=True)
        g_num = int(re.search(r"\d+", g_text).group(0))
        
        giorno_str = row.select_one(".lb-prg-riga__giorno").get_text(strip=True)
        d_match = re.search(r"(\d+)\s+([A-Za-z]+)", giorno_str)
        day = d_match.group(1).zfill(2)
        month, year = MONTHS_IT[d_match.group(2)]
        
        ora = row.select_one(".lb-prg-riga__ora").get_text(strip=True)
        impianto = row.select_one(".lb-prg-riga__impianto").get_text(strip=True)
        casa = row.select_one(".lb-prg-riga__casa .lb-prg__nome--full").get_text(strip=True)
        ospite = row.select_one(".lb-prg-riga__ospite .lb-prg__nome--full").get_text(strip=True)
        
        punteggio_el = row.select_one(".lb-prg__punteggio")
        punteggio = punteggio_el.get_text(strip=True) if punteggio_el else "vs"
        risultato = None if punteggio.lower() == "vs" else punteggio
        
        cronaca_el = row.select_one("a.lb-prg-riga__cronaca")
        cronaca_url = cronaca_el["href"] if cronaca_el else None

        if risultato:
            print(f"[DEBUG] Partita giocata trovata -> Giornata {g_num}: {casa} - {ospite} ({risultato})")

        matches[g_num] = {
            "giornata": g_num,
            "data": f"{day}/{month}/{year}",
            "ora": ora,
            "casa": casa,
            "ospite": ospite,
            "impianto": impianto,
            "risultato": risultato,
            "cronaca_url": cronaca_url
        }

    return [matches[k] for k in sorted(matches.keys())]

def generate_files(matches):
    with open("calendario.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    ical = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Leonessa Brescia Calendar//EN",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:Leonessa Brescia 26/27"
    ]
    # Usiamo un DTSTAMP statico legato ai dati così Git fa commit solo se cambiano davvero orari o risultati
    dtstamp = "20260901T000000Z"

    for m in matches:
        g = m["giornata"]
        dt_start = datetime.strptime(f"{m['data']} {m['ora']}", "%d/%m/%Y %H:%M")
        dt_end = dt_start + timedelta(hours=2)
        
        uid = EXISTING_UIDS.get(g, f"{uuid.uuid5(uuid.NAMESPACE_DNS, f'leonessa-26-27-g{g}')}@leonessabrescia.it")
        
        summary = f"{m['casa']} - {m['ospite']}"
        if m["risultato"]:
            summary += f" ({m['risultato']})"
            
        desc = f"Giornata {g} - Serie B Nazionale 2026/27"
        if m["cronaca_url"]:
            desc += f"\\nCronaca: {m['cronaca_url']}"

        ical.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART;TZID=Europe/Rome:{dt_start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID=Europe/Rome:{dt_end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{summary}",
            f"LOCATION:{m['impianto']}",
            f"DESCRIPTION:{desc}",
            "END:VEVENT"
        ])

    ical.append("END:VCALENDAR")
    with open("Calendario_Leonessa_Brescia_26_27.ics", "w", encoding="utf-8") as f:
        f.write("\n".join(ical))

if __name__ == "__main__":
    data = fetch_matches()
    generate_files(data)
