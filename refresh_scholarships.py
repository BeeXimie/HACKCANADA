import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import shutil
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

DB_NAME = "scholarships.db"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def setup_db():
    """Drops and recreates the scholarship table to reset IDs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    print("Resetting database table...")
    cursor.execute("DROP TABLE IF EXISTS ouinfo_scholarships")
    cursor.execute("""
        CREATE TABLE ouinfo_scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            university TEXT,
            amount TEXT,
            deadline TEXT,
            type TEXT,
            url TEXT UNIQUE,
            description TEXT,
            eligibility TEXT,
            demographics TEXT,
            match_score INTEGER,
            match_reasoning TEXT
        )
    """)
    conn.commit()
    return conn

# --- OUINFO UTILS ---

def extract_section_text(soup, headers_to_find):
    for header_text in headers_to_find:
        h = soup.find(['h2', 'h3', 'h4'], string=lambda t: t and header_text in str(t))
        if h:
            content = []
            curr = h.find_next_sibling()
            while curr and curr.name not in ['h2', 'h3', 'h4']:
                if curr.name in ['p', 'ul', 'li', 'div']:
                    content.append(curr.get_text(strip=True))
                curr = curr.find_next_sibling()
            if content:
                return "\n".join(content)
    return "Not specified"

def analyze_demographics(text):
    tags = []
    t = text.lower()
    if any(w in t for w in ["women", "female", "femmes", "féminin"]): tags.append("Women")
    if any(w in t for w in ["international", "visa", "foreign"]): tags.append("International")
    else: tags.append("Domestic")
    if any(w in t for w in ["indigenous", "aboriginal", "first nations", "métis", "inuit", "autochtone"]): tags.append("Indigenous")
    if any(w in t for w in ["black", "african", "noir"]): tags.append("Black")
    if any(w in t for w in ["disability", "disabled", "handicap", "deaf", "blind"]): tags.append("Accessibility")
    return ", ".join(tags) if tags else "General"

def parse_ouinfo_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
    except: return None

    title = soup.find('h1')
    title = title.get_text(strip=True) if title else "Unknown"

    # Robust parsing for amount and deadline
    def find_val_by_label(soup, labels):
        for td in soup.find_all(['td', 'th']):
            if any(l in td.get_text() for l in labels):
                nxt = td.find_next_sibling('td')
                if nxt: return nxt.get_text(strip=True)
        for h in soup.find_all(['h2', 'h3', 'h4']):
            if any(l in h.get_text() for l in labels):
                nxt = h.find_next(['p', 'div'])
                if nxt: return nxt.get_text(strip=True)
        return None

    amount = find_val_by_label(soup, ['Value', 'Valeur', 'Amount', 'Montant'])
    if not amount:
        for p in soup.find_all('p', class_='result-attributes'):
            if '$' in p.text or 'value' in p.text.lower():
                amount = p.get_text(strip=True)
                break
    
    deadline = find_val_by_label(soup, ['Deadline', 'Date limite'])
    if not deadline:
        ra = soup.find('div', class_='result-actions')
        if ra:
            at = ra.find('p', class_='actions-text')
            if at: deadline = at.get_text(strip=True)

    university = "Unknown"
    try:
        parts = url.strip('/').split('/')
        if 'scholarships' in parts:
            university = parts[parts.index('scholarships') + 1].replace('-', ' ').title()
    except: pass

    desc = extract_section_text(soup, ["Description"])
    elig = extract_section_text(soup, ["Critères", "Exigences", "Admissibilité", "Eligibility", "Requirements", "Criteria"])
    demo = analyze_demographics(f"{title} {desc} {elig}")

    return (title, university, amount or "Unknown", deadline or "Unknown", "Internal", url, desc, elig, demo)

# --- SCRAPERS ---

def scrape_ouinfo(cursor, conn):
    print("Starting OUInfo Scraper...")
    base_url = "https://www.ouinfo.ca/scholarships"
    urls = set()
    for group in ['a-e', 'f-j', 'k-o', 'p-t', 'u-w', 'x-z']:
        try:
            r = requests.get(f"{base_url}?group={group}", headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                if '/scholarships/' in a['href'] and len(a['href']) > 15:
                    full = urljoin(base_url, a['href'])
                    if '?' not in full: urls.add(full)
        except: continue

    print(f"Found {len(urls)} OUInfo scholarships. Fetching details...")
    for i, url in enumerate(urls):
        try:
            data = parse_ouinfo_page(url)
            if data:
                cursor.execute("""
                    INSERT OR IGNORE INTO ouinfo_scholarships (title, university, amount, deadline, type, url, description, eligibility, demographics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data)
                if i % 10 == 0: conn.commit()
            if i % 20 == 0: 
                print(f"  OUInfo Progress: {i}/{len(urls)}")
                # Quick count check
                cursor.execute("SELECT COUNT(*) FROM ouinfo_scholarships")
                curr_count = cursor.fetchone()[0]
                print(f"  Current DB Count: {curr_count}")
        except Exception as e:
            print(f"  Error at {url}: {e}")
        time.sleep(0.5)
    conn.commit()

def scrape_studentawards(cursor, conn):
    print("Starting StudentAwards Scraper (Selenium)...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get("https://studentawards.com/scholarships/")
        time.sleep(5)
        
        last_h = 0
        for _ in range(30):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_h = driver.execute_script("return document.body.scrollHeight")
            if new_h == last_h: break
            last_h = new_h
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.find_all('div', class_='card')
        print(f"Found {len(cards)} external scholarships.")
        
        for card in cards:
            title_a = card.find('div', class_='title').find('a') if card.find('div', class_='title') else None
            if not title_a: continue
            
            name = title_a.text.strip()
            url = title_a['href']
            amt = "Unknown"
            footer = card.find('footer', class_='card-footer')
            if footer and footer.find('div', class_='value'):
                amt = footer.find('div', class_='value').text.strip()
                
            dl = "Unknown"
            for label in card.find_all('div', class_='label'):
                if 'deadline' in label.text.lower():
                    v = label.parent.find('div', class_='value')
                    if v: dl = v.text.strip()
            
            terms = card.find('div', class_='card-terms')
            demo = terms.text.strip() if terms else "General"
            
            cursor.execute("""
                INSERT INTO ouinfo_scholarships (title, university, amount, deadline, type, url, description, eligibility, demographics)
                VALUES (?, 'External/Various', ?, ?, 'External', ?, 'External StudentAwards scholarship', 'See URL for details', ?)
            """, (name, amt, dl, url, demo))
        conn.commit()
    finally:
        driver.quit()

if __name__ == "__main__":
    conn = setup_db()
    cursor = conn.cursor()
    try:
        scrape_ouinfo(cursor, conn)
        scrape_studentawards(cursor, conn)
        print("\nSUCCESS: All scholarships refreshed and re-indexed sequentially!")
    except Exception as e:
        print(f"\nFATAL ERROR during refresh: {e}")
    finally:
        conn.close()
