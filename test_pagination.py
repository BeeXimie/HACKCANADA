import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base_url = "https://www.ouinfo.ca/scholarships"
all_links = set()

for page in range(1, 10):
    print(f"Page {page}")
    url = f"{base_url}?page={page}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    links = soup.find_all('a', href=True)
    
    found = 0
    for l in links:
        h = l['href']
        if '/scholarships/' in h and len(h) > 15:
            full = urljoin(base_url, h)
            if full != base_url and '?' not in full:
                if full not in all_links:
                    all_links.add(full)
                    found += 1
    print(f"Found {found} new on page {page}")
    if found == 0:
        break

print(f"Total links: {len(all_links)}")
