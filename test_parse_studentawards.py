from bs4 import BeautifulSoup

html = open('studentawards_utf8.txt', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')
cards = soup.find_all('article')
print(f'Found {len(cards)} articles')
for c in cards:
    print(c.text.strip()[:100])
