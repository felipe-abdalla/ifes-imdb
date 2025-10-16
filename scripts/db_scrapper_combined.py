import requests
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import re
import time

# Cria o banco de dados e faz o web scrapping no mesmo script

# !!! Checar os dados de DB_CONFIG antes de rodar o script !!!

# ========= DATABASE CONFIG =========
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root', 
    'database': 'imdb'
}

# ========= SQL: CREATE TABLES =========
CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS Nacionalidade (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nacionalidade VARCHAR(255) UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Ator (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(255),
        sobrenome VARCHAR(255),
        dtNascimento DATE,
        sexo CHAR(1),
        Nacionalidade_id INT,
        FOREIGN KEY (Nacionalidade_id) REFERENCES Nacionalidade(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Categoria (
        id INT AUTO_INCREMENT PRIMARY KEY,
        descricao VARCHAR(255) UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Idioma (
        id INT AUTO_INCREMENT PRIMARY KEY,
        descricao VARCHAR(255) UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Classificacao (
        id INT AUTO_INCREMENT PRIMARY KEY,
        descricao VARCHAR(255) UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Filme (
        id INT AUTO_INCREMENT PRIMARY KEY,
        titulo VARCHAR(255),
        descricao VARCHAR(255),
        ano INT,
        nota FLOAT,
        Nacionalidade_id INT,
        Categoria INT,
        Idioma_id INT,
        Classificacao_id INT,
        FOREIGN KEY (Nacionalidade_id) REFERENCES Nacionalidade(id),
        FOREIGN KEY (Categoria) REFERENCES Categoria(id),
        FOREIGN KEY (Idioma_id) REFERENCES Idioma(id),
        FOREIGN KEY (Classificacao_id) REFERENCES Classificacao(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Ator_has_Filme (
        Ator_id INT,
        Filme_id INT,
        PRIMARY KEY (Ator_id, Filme_id),
        FOREIGN KEY (Ator_id) REFERENCES Ator(id),
        FOREIGN KEY (Filme_id) REFERENCES Filme(id)
    )
    """
]

# ========= DATABASE CONNECTION =========

def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("✅ Connected to database")
            return conn
    except Error as e:
        print("❌ Database connection error:", e)
        return None

def create_tables(conn):
    cursor = conn.cursor()
    for sql in CREATE_TABLES_SQL:
        cursor.execute(sql)
    conn.commit()
    print("📦 Tables verified/created successfully")

# ========= HELPER FUNCTIONS =========

def get_or_create(cursor, table, column, value):
    """Insert if not exists and return ID."""
    if value is None:
        return None
    cursor.execute(f"SELECT id FROM {table} WHERE {column} = %s", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    cursor.execute(f"INSERT INTO {table} ({column}) VALUES (%s)", (value,))
    return cursor.lastrowid

# ========= SCRAPER FUNCTIONS =========

def scrape_top_movies(limit=30):
    url = "https://www.imdb.com/pt/chart/top/?ref_=hm_nv_menu"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    movies = []
    rows = soup.select("li.ipc-metadata-list-summary-item")[:limit]
    for row in rows:
        link_tag = row.select_one("a.ipc-title-link-wrapper")
        if not link_tag:
            continue
        href = link_tag.get("href")
        title = link_tag.get_text(strip=True)
        movie_url = "https://www.imdb.com" + href
        movies.append({"title": title, "url": movie_url})
    return movies

def scrape_movie_details(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract info
    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else "N/A"

    desc_tag = soup.find("span", {"data-testid": "plot-l"})
    description = desc_tag.text.strip() if desc_tag else None

    year_tag = soup.select_one('ul li a[href*="releaseinfo"]')
    year = int(re.search(r"\d{4}", year_tag.text).group()) if year_tag else None

    genre_tag = soup.select_one('a[href*="/search/title/?genres="]')
    genre = genre_tag.text.strip() if genre_tag else None

    lang_tag = soup.find("a", href=re.compile("/language/"))
    language = lang_tag.text.strip() if lang_tag else None

    rating_tag = soup.find("span", class_="sc-d541859f-1")
    content_rating = rating_tag.text.strip() if rating_tag else None

    imdb_rating_tag = soup.find("span", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
    imdb_rating = float(imdb_rating_tag.text.split("/")[0]) if imdb_rating_tag else None

    # Main cast
    cast_tags = soup.select("div.sc-bfec09a1-1 span a")
    cast = [c.text.strip() for c in cast_tags[:5]]  # top 5 cast

    return {
        "title": title,
        "description": description,
        "year": year,
        "genre": genre,
        "language": language,
        "content_rating": content_rating,
        "rating": imdb_rating,
        "cast": cast
    }

# ========= MAIN FUNCTION =========

def main():
    conn = connect_db()
    if not conn:
        return
    create_tables(conn)
    cursor = conn.cursor()

    movies = scrape_top_movies(limit=30)

    for m in movies:
        print(f"🎬 Processing: {m['title']}")
        data = scrape_movie_details(m["url"])

        # insert or get IDs for related tables
        categoria_id = get_or_create(cursor, "Categoria", "descricao", data["genre"])
        idioma_id = get_or_create(cursor, "Idioma", "descricao", data["language"])
        classificacao_id = get_or_create(cursor, "Classificacao", "descricao", data["content_rating"])

        # insert movie
        cursor.execute("""
            INSERT INTO Filme (titulo, descricao, ano, nota, Categoria, Idioma_id, Classificacao_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data["title"], data["description"], data["year"], data["rating"],
              categoria_id, idioma_id, classificacao_id))
        filme_id = cursor.lastrowid

        # insert cast
        for actor_name in data["cast"]:
            names = actor_name.split(" ", 1)
            nome = names[0]
            sobrenome = names[1] if len(names) > 1 else ""
            cursor.execute("INSERT INTO Ator (nome, sobrenome) VALUES (%s, %s)", (nome, sobrenome))
            ator_id = cursor.lastrowid
            cursor.execute("INSERT INTO Ator_has_Filme (Ator_id, Filme_id) VALUES (%s, %s)", (ator_id, filme_id))

        conn.commit()
        time.sleep(1)  # polite delay

    print("✅ All movies processed and inserted successfully!")
    cursor.close()
    conn.close()

# ========= RUN =========
if __name__ == "__main__":
    main()
