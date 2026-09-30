import json
import re
import urllib.request
from bs4 import BeautifulSoup

URL = "https://jidelnicek.utb.cz/webkredit/Ordering/Menu"

def get_menu():
    req = urllib.request.Request(
        URL, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print(f"Chyba pri stahovani: {e}")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    items = []
    
    current_day = "Dnešní nabídka"

    # Projdeme celou stranku a vyhledame jidla a alergeny
    for elem in soup.find_all(['h2', 'h3', 'tr', 'div']):
        text = elem.get_text(strip=True)
        
        # Pokud narazime na datum/den
        if any(d in text.lower() for d in ['pondělí', 'úterý', 'středa', 'čtvrtek', 'pátek', 'sobota', 'neděle']):
            if len(text) < 40 and not any(i['nazev'] == text for i in items):
                current_day = text

        # Hledame kody alergenu
        allergens_match = re.search(r'Alergeny:\s*([0-9a-z,\s]+)', text, re.IGNORECASE)
        if allergens_match:
            allergens_str = allergens_match.group(1).strip()
            
            # Ziskame nazev jidla (z textu pred alergeny)
            nazev = text.split('Alergeny:')[0].strip()
            
            # Ocistime nazev od zbytecnych znaku
            nazev = re.sub(r'^\d+\s*|\s*\d+,-.*$', '', nazev).strip()

            if len(nazev) > 3:
                # Kontrola lepku (alergen 1, 1a, 1b atd.)
                has_gluten = bool(re.search(r'\b1[a-z]?\b', allergens_str))
                
                items.append({
                    "den": current_day,
                    "nazev": nazev,
                    "alergeny": allergens_str,
                    "obsahuje_lepek": has_gluten
                })

    # Pokud bychom nenašli přesnou strukturu, uděláme jednoduchou zálohu
    if not items:
        for row in soup.find_all('tr'):
            row_text = row.get_text(" ", strip=True)
            if "Alergeny" in row_text or "1" in row_text:
                has_gluten = " 1 " in f" {row_text} " or "1a" in row_text or "1," in row_text
                items.append({
                    "den": current_day,
                    "nazev": row_text[:80],
                    "alergeny": "Uvedeno v popisu",
                    "obsahuje_lepek": has_gluten
                })

    return items

if __name__ == "__main__":
    data = get_menu()
    with open('jidelnicek.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Ulozeno {len(data)} jidel do jidelnicek.json")
