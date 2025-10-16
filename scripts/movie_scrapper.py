import requests
from bs4 import BeautifulSoup
import mysql.connector
import re
from datetime import datetime

# Faz o webscrapping dos dados do IMDb

# ---------- CONFIG ---------- #
BASE_URL = "https://www.imdb.com"
TOP_URL = "https://www.imdb.com/pt/chart/top/?ref_=nv_mv_250"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# !!! Chegar os dados de DB_CONFIG antes de rodar o script !!!

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "yourpassword",
    "database": "imdb_scraper"
}

# ---------- DATABASE UTILS ---------- #
def get_or_create(cursor, table, column, value):
    if not value:
        return None
    cursor.execute(f"SELECT id FROM {table} WHERE {column} = %s", (value,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(f"INSERT INTO {table} ({column}) VALUES (%s)", (value,))
    return cursor.lastrowid

def get_or_create_actor(cursor, actor):
    cursor.execute("SELECT id FROM Ator WHERE nome = %s", (actor["nome"],))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("""
        INSERT INTO Ator (nome, sobrenome, dtNascimento, sexo, Nacionalidade_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        actor["nome"],
        actor["sobrenome"],
        actor["nascimento"],
        actor["sexo"],
        actor["nacionalidade_id"]
    ))
    return cursor.lastrowid

# ---------- SCRAPING FUNCTIONS ---------- #
def get_top_movie_links(limit=30):
    res = requests.get(TOP_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    links = []
    for a in soup.select("ul.ipc-metadata-list li a.ipc-title-link-wrapper")[:limit]:
        href = a.get("href")
        if href:
            links.append(BASE_URL + href.split("?")[0])
    return links

def scrape_movie(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    def txt(sel):
        el = soup.select_one(sel)
        return el.get_text(strip=True) if el else None

    movie = {}
    movie["titulo"] = txt("h1[data-testid='hero__pageTitle']")
    movie["descricao"] = txt("span[data-testid='plot-l']") or txt("span[data-testid='plot-xs_to_m']")
    movie["ano"] = txt("ul li a[href*='releaseinfo']")

    genres = [g.get_text(strip=True) for g in soup.select("div[data-testid='genres'] a")]
    movie["categoria"] = genres[0] if genres else None

    langs = [l.get_text(strip=True) for l in soup.select("li[data-testid='title-details-languages'] a")]
    movie["idioma"] = langs[0] if langs else None

    rating_tag = soup.find("a", href=lambda x: x and "parentalguide" in x)
    movie["classificacao"] = rating_tag.get_text(strip=True) if rating_tag else None

    imdb_rating = txt("span[data-testid='hero-rating-bar__aggregate-rating__score']")
    if imdb_rating:
        imdb_rating = re.search(r"[\d\.]+", imdb_rating).group(0)
    movie["nota"] = float(imdb_rating) if imdb_rating else None

    cast = [a.get_text(strip=True) for a in soup.select("div[data-testid='title-cast'] a[data-testid='title-cast-item__actor']")[:5]]
    movie["atores"] = cast

    return movie

# ---------- WIKIPEDIA FETCH ---------- #
def fetch_actor_details(name):
    """Try to extract nationality and birthdate from Wikipedia."""
    actor = {
        "nome": name.split()[0],
        "sobrenome": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
        "nascimento": None,
        "sexo": None,
        "nacionalidade_id": None
    }

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
    res = requests.get(url)
    if res.status_code != 200:
        return actor

    data = res.json()
    extract = data.get("extract", "")

    # Try to extract nationality
    nationality = None
    match_nat = re.search(r"([A-Z][a-z]+)(?:\-|\s)?[A-Z]?[a-z]* actor", extract)
    if match_nat:
        nationality = match_nat.group(1)

    # Try to extract birthdate
    match_date = re.search(r"\(born ([A-Za-z]+ \d{1,2}, \d{4})", extract)
    birthdate = None
    if match_date:
        try:
            birthdate = datetime.strptime(match_date.group(1), "%B %d, %Y").date()
        except Exception:
            pass

    actor["nascimento"] = birthdate
    actor["sexo"] = "M"  # IMDb doesn’t expose gender
    actor["nacionalidade"] = nationality
    return actor

# ---------- MAIN INSERTION ---------- #
def insert_movie_with_cast(conn, movie):
    cursor = conn.cursor()

    categoria_id = get_or_create(cursor, "Categoria", "descricao", movie["categoria"])
    idioma_id = get_or_create(cursor, "Idioma", "descricao", movie["idioma"])
    classificacao_id = get_or_create(cursor, "Classificacao", "descricao", movie["classificacao"])

    cursor.execute("""
        INSERT INTO Filme (titulo, descricao, ano, nota, Categoria_id, Idioma_id, Classificacao_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        movie["titulo"], movie["descricao"], movie["ano"], movie["nota"],
        categoria_id, idioma_id, classificacao_id
    ))
    filme_id = cursor.lastrowid

    for actor_name in movie["atores"]:
        actor_data = fetch_actor_details(actor_name)
        if actor_data.get("nacionalidade"):
            actor_data["nacionalidade_id"] = get_or_create(cursor, "Nacionalidade", "nacionalidade", actor_data["nacionalidade"])
        actor_id = get_or_create_actor(cursor, actor_data)
        cursor.execute("INSERT INTO Ator_has_Filme (Ator_id, Filme_id) VALUES (%s, %s)", (actor_id, filme_id))

    conn.commit()
    cursor.close()
    print(f"✅ Saved movie: {movie['titulo']}")


# ---------- MAIN ---------- #
def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    movies = get_top_movie_links()

    for i, url in enumerate(movies, start=1):
        print(f"[{i}] Scraping {url}")
        try:
            movie = scrape_movie(url)
            insert_movie_with_cast(conn, movie)
        except Exception as e:
            print(f"❌ Error with {url}: {e}")

    conn.close()
    print("✅ All movies saved!")

if __name__ == "__main__":
    main()
