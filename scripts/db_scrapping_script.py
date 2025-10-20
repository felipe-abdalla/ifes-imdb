import requests
from bs4 import BeautifulSoup
import mysql.connector
import time
import json
import re
from datetime import datetime

# === CONFIG ===
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "dx66ksdc",
    "database": "imdb"
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

# === DATABASE SETUP ===

def connect_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn, conn.cursor(buffered=True)

def create_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Categoria (
            id INT AUTO_INCREMENT PRIMARY KEY,
            descricao VARCHAR(100) UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Idioma (
            id INT AUTO_INCREMENT PRIMARY KEY,
            descricao VARCHAR(100) UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Classificacao (
            id INT AUTO_INCREMENT PRIMARY KEY,
            descricao VARCHAR(100) UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Sexo (
            id INT AUTO_INCREMENT PRIMARY KEY,
            descricao VARCHAR(50) UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Filme (
            id INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) UNIQUE,
            descricao TEXT,
            ano VARCHAR(10),
            nota FLOAT,
            Categoria INT,
            Idioma_id INT,
            Classificacao_id INT,
            FOREIGN KEY (Categoria) REFERENCES Categoria(id),
            FOREIGN KEY (Idioma_id) REFERENCES Idioma(id),
            FOREIGN KEY (Classificacao_id) REFERENCES Classificacao(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ator (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100),
            sobrenome VARCHAR(100),
            data_nascimento VARCHAR(50),
            nacionalidade VARCHAR(100),
            sexo_id INT DEFAULT NULL,
            UNIQUE(nome, sobrenome),
            FOREIGN KEY (sexo_id) REFERENCES Sexo(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ator_has_Filme (
            Ator_id INT,
            Filme_id INT,
            PRIMARY KEY (Ator_id, Filme_id),
            FOREIGN KEY (Ator_id) REFERENCES Ator(id),
            FOREIGN KEY (Filme_id) REFERENCES Filme(id)
        )
    """)

    # popular valores padrão da tabela Sexo
    cursor.execute("INSERT IGNORE INTO Sexo (descricao) VALUES (%s), (%s)", ("masculino", "feminino"))


def get_or_create(cursor, table, column, value):
    if not value or value == "N/A":
        return None
    cursor.execute(f"SELECT id FROM {table} WHERE {column} = %s", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    cursor.execute(f"INSERT INTO {table} ({column}) VALUES (%s)", (value,))
    return cursor.lastrowid

# === SCRAPERS ===

def scrape_top_movies(limit=30):
    url = "https://www.imdb.com/chart/top/"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    movies = []
    for item in soup.select("li.ipc-metadata-list-summary-item"):
        link = item.select_one("a.ipc-title-link-wrapper")
        title_tag = item.select_one("h3.ipc-title__text")
        if link and title_tag:
            href = link.get("href")
            movies.append({
                "title": title_tag.get_text(strip=True),
                "url": "https://www.imdb.com" + href.split("?")[0],
            })
        if len(movies) >= limit:
            break
    print(f"✅ Encontrados {len(movies)} filmes.")
    return movies


def scrape_movie_details(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # === TITLE ===
    title_tag = soup.select_one(".hero__primary-text")
    title = title_tag.get_text(strip=True) if title_tag else "N/A"

    # === DESCRIPTION ===
    description = soup.select_one("span[data-testid='plot-l']")
    if not description:
        description = soup.select_one("span[data-testid='plot-xs_to_m']")
    description = description.get_text(strip=True) if description else "N/A"

    # === YEAR via JSON-LD ===
    year = "N/A"
    ld_json = soup.find("script", type="application/ld+json")
    if ld_json:
        try:
            data_ld = json.loads(ld_json.string)
            dp = data_ld.get("datePublished") or data_ld.get("datePublished")
            if dp:
                # datePublished pode ser '1994-09-23' ou '1994'
                year = dp.split("-")[0]
        except Exception:
            pass

    # fallback: seletor antigo
    if year == "N/A":
        year_tag = soup.select_one("ul[data-testid='hero-title-block__metadata'] li")
        if year_tag:
            year_text = year_tag.get_text(strip=True)
            m = re.search(r"\d{4}", year_text)
            if m:
                year = m.group(0)

    # === IMDb RATING ===
    rating_tag = soup.select_one("div[data-testid='hero-rating-bar__aggregate-rating__score'] span")
    rating = float(rating_tag.get_text(strip=True).replace(",", ".")) if rating_tag else None

    # === GENRE (apenas o primeiro) ===
    genre = "N/A"
    ld_json = soup.find("script", type="application/ld+json")
    if ld_json:
        try:
            data_ld = json.loads(ld_json.string)
            g = data_ld.get("genre")
            if g:
                if isinstance(g, list):
                    genre = g[0]
                else:
                    genre = g.split(",")[0].strip()
        except json.JSONDecodeError:
            pass

    # fallback: primeiro link no HTML
    if genre == "N/A":
        genre_li = soup.select_one("li[data-testid='storyline-genres']")
        if genre_li:
            link = genre_li.select_one("a.ipc-metadata-list-item__list-content-item--link")
            if link:
                genre = link.get_text(strip=True)

    # === LANGUAGE ===
    language = "N/A"
    lang_tag = soup.select_one("li[data-testid='title-details-languages'] a")
    if lang_tag:
        language = lang_tag.get_text(strip=True)

    # === CLASSIFICAÇÃO INDICATIVA via JSON-LD ===
    content_rating = "N/A"
    ld_json = soup.find("script", type="application/ld+json")
    if ld_json:
        try:
            data_ld = json.loads(ld_json.string)
            cr = data_ld.get("contentRating")
            if cr:
                content_rating = cr
        except json.JSONDecodeError:
            pass

    # fallback via HTML
    if content_rating == "N/A":
        cert_li = soup.select_one("li[data-testid='storyline-certificate']")
        if cert_li:
            link = cert_li.select_one("a.ipc-metadata-list-item__list-content-item--link")
            if link:
                content_rating = link.get_text(strip=True)

    # === CAST ===
    cast = [c.get_text(strip=True) for c in soup.select("a[data-testid='title-cast-item__actor']")[:5]]

    return {
        "title": title,
        "description": description,
        "year": year,
        "rating": rating,
        "genre": genre,
        "language": language,
        "content_rating": content_rating,
        "cast": cast,
    }

def get_actor_info_from_wikipedia(name):
    headers_wiki = HEADERS.copy()
    headers_wiki["Accept-Language"] = "en-US,en;q=0.9"

    try:
        url = f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}"
        r = requests.get(url, headers=headers_wiki, timeout=8)
        if r.status_code != 200:
            return None, None
        soup = BeautifulSoup(r.text, "html.parser")

        # 1) span.bday
        birth_date = None
        bday = soup.select_one("span.bday")
        if bday and bday.get_text(strip=True):
            birth_date = bday.get_text(strip=True)

        # 2) time[itemprop='birthDate']
        if not birth_date:
            time_tag = soup.select_one("time[itemprop='birthDate']")
            if time_tag and time_tag.get("datetime"):
                birth_date = time_tag.get("datetime")
            elif time_tag:
                birth_date = time_tag.get_text(strip=True)

        # 3) infobox row 'Born' (en.wikipedia uses 'Born')
        if not birth_date:
            infobox = soup.select_one("table.infobox")
            if infobox:
                for row in infobox.select("tr"):
                    th = row.select_one("th")
                    if th and 'born' == th.get_text(strip=True).lower():
                        td = row.select_one("td")
                        if td:
                            text = td.get_text(" ", strip=True)
                            # tenta encontrar ISO-like date YYYY-MM-DD
                            m = re.search(r"\d{4}-\d{2}-\d{2}", text)
                            if m:
                                birth_date = m.group(0)
                                break
                            # tenta formatos com dia mês ano (e.g., 29 April 1971)
                            m = re.search(r"\d{1,2}\s+[A-Za-z]+\s+\d{4}", text)
                            if m:
                                birth_date = m.group(0)
                                break
                            # tenta formatos com mês dia, ano (e.g., April 29, 1971)
                            m = re.search(r"[A-Za-z]+\s+\d{1,2},\s*\d{4}", text)
                            if m:
                                birth_date = m.group(0)
                                break
                            # fallback: any 4-digit year presence
                            m = re.search(r"\b(\d{4})\b", text)
                            if m:
                                birth_date = m.group(1)
                                break

        # Normalize para ISO YYYY-MM-DD quando possível
        if birth_date:
            try:
                # tenta parse de várias formas
                dt = None
                for fmt in ("%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%Y"):
                    try:
                        dt = datetime.strptime(birth_date, fmt)
                        break
                    except Exception:
                        continue
                if dt:
                    birth_date = dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        # Nacionalidade / local de nascimento
        nationality = None
        birthplace = None
        # busca por 'Born' linha para extrair local depois da data
        infobox = soup.select_one("table.infobox")
        if infobox:
            for row in infobox.select("tr"):
                th = row.select_one("th")
                if th and 'born' == th.get_text(strip=True).lower():
                    td = row.select_one("td")
                    if td:
                        # tenta extrair local entre parênteses ou após a data
                        txt = td.get_text(" ", strip=True)
                        # remove a parte da data para tentar isolar local
                        txt_after_date = re.sub(r".*?(?:\d{4}|\d{1,2}\s+[A-Za-z]+|\w+\s+\d{1,2},\s*\d{4})\s*,?\s*", "", txt, count=1)
                        if txt_after_date and len(txt_after_date) > 2:
                            birthplace = txt_after_date
                        else:
                            # procura por divs ou links com classe birthplace
                            bp = td.select_one(".birthplace")
                            if bp:
                                birthplace = bp.get_text(" ", strip=True)
                    break

        # tentativa de nacionalidade pela presença de 'Nationality' ou 'Citizenship' na infobox
        if infobox and not nationality:
            for row in infobox.select("tr"):
                th = row.select_one("th")
                if th:
                    key = th.get_text(strip=True).lower()
                    if 'nationality' in key or 'citizenship' in key:
                        td = row.select_one("td")
                        if td:
                            nationality = td.get_text(" ", strip=True)
                        break

        # se não encontrou nacionalidade, tenta deduzir do birthplace (se for algo como 'City, Country')
        if not nationality and birthplace:
            parts = [p.strip() for p in re.split(r",|\u2013|-", birthplace) if p.strip()]
            if parts:
                nationality = parts[-1]

        return birth_date, nationality
    except Exception:
        return None, None


# === INSERT / UPDATE LOGIC ===

def insert_or_update_movie(cursor, data, cat_id, lang_id, class_id):
    cursor.execute("SELECT id FROM Filme WHERE titulo = %s", (data["title"],))
    existing = cursor.fetchone()

    if existing:
        filme_id = existing[0]
        cursor.execute("""
            UPDATE Filme SET
                descricao = COALESCE(NULLIF(%s, 'N/A'), descricao),
                ano = COALESCE(NULLIF(%s, 'N/A'), ano),
                nota = COALESCE(%s, nota),
                Categoria = COALESCE(%s, Categoria),
                Idioma_id = COALESCE(%s, Idioma_id),
                Classificacao_id = COALESCE(%s, Classificacao_id)
            WHERE id = %s
        """, (data["description"], data["year"], data["rating"],
              cat_id, lang_id, class_id, filme_id))
        return filme_id
    else:
        cursor.execute("""
            INSERT INTO Filme (titulo, descricao, ano, nota, Categoria, Idioma_id, Classificacao_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data["title"], data["description"], data["year"], data["rating"],
              cat_id, lang_id, class_id))
        return cursor.lastrowid


def insert_or_update_actor(cursor, actor_name):
    first_last = actor_name.split(" ", 1)
    nome = first_last[0]
    sobrenome = first_last[1] if len(first_last) > 1 else ""

    cursor.execute("SELECT id, data_nascimento, nacionalidade FROM Ator WHERE nome = %s AND sobrenome = %s", (nome, sobrenome))
    existing = cursor.fetchone()

    birth_date, nationality = get_actor_info_from_wikipedia(actor_name)

    if existing:
        ator_id = existing[0]
        cursor.execute("""
            UPDATE Ator SET
                data_nascimento = COALESCE(NULLIF(%s, ''), data_nascimento),
                nacionalidade = COALESCE(NULLIF(%s, ''), nacionalidade)
            WHERE id = %s
        """, (birth_date, nationality, ator_id))
    else:
        cursor.execute("""
            INSERT INTO Ator (nome, sobrenome, data_nascimento, nacionalidade)
            VALUES (%s, %s, %s, %s)
        """, (nome, sobrenome, birth_date, nationality))
        ator_id = cursor.lastrowid

    return ator_id

# === MAIN ===

def main():
    conn, cursor = connect_db()
    print("✅ Conectado ao banco de dados")

    create_tables(cursor)
    conn.commit()
    print("📦 Tabelas verificadas/criadas com sucesso")

    movies = scrape_top_movies(limit=30)

    for m in movies:
        print(f"\n🎬 Processando: {m['title']}")
        data = scrape_movie_details(m["url"])

        cat_id = get_or_create(cursor, "Categoria", "descricao", data["genre"])
        lang_id = get_or_create(cursor, "Idioma", "descricao", data["language"])
        class_id = get_or_create(cursor, "Classificacao", "descricao", data["content_rating"])

        filme_id = insert_or_update_movie(cursor, data, cat_id, lang_id, class_id)

        for actor in data["cast"]:
            ator_id = insert_or_update_actor(cursor, actor)
            cursor.execute("INSERT IGNORE INTO Ator_has_Filme (Ator_id, Filme_id) VALUES (%s, %s)", (ator_id, filme_id))

        conn.commit()
        print(f"✅ Inserido/Atualizado: {data['title']}")
        time.sleep(2)

    cursor.close()
    conn.close()
    print("\n🎉 Todos os filmes foram processados com sucesso!")

if __name__ == "__main__":
    main()
