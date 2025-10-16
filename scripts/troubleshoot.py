import requests
from bs4 import BeautifulSoup

url = "https://www.imdb.com/pt/chart/top/?ref_=hm_nv_menu"
resp = requests.get(url)
soup = BeautifulSoup(resp.text, "html.parser")

movies = soup.select("li.ipc-metadata-list-summary-item")

print(f"Found {len(movies)} movies")

for i, m in enumerate(movies[:5], 1):
    link = m.select_one("a.ipc-title-link-wrapper")
    print(f"{i}: {link.text.strip() if link else 'N/A'}")
