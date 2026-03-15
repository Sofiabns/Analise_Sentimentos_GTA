"""
scraper.py — Pipeline de coleta multi-plataforma
Tema: Franquia GTA (Grand Theft Auto)

Fontes:
  1. Steam        — API pública Valve (store.steampowered.com/appreviews/)
                    Reviews escritas por jogadores verificados, PT + EN

  2. Reddit       — API JSON pública (reddit.com/r/.../hot.json)
                    User-Agent no formato correto para evitar 403
                    Fallback: RSS feed com BeautifulSoup (parse de XML)

  3. Google News  — RSS de busca do Google News (news.google.com/rss/search)
                    Sem autenticação, sem chave, sem scraping de HTML
                    Retorna títulos + descrições de artigos/notícias sobre GTA
                    Fonte completamente diferente do Reddit — jornalistas,
                    portais especializados (IGN, Kotaku, Polygon, Eurogamer...)
                    BeautifulSoup é usado apenas para parsear o XML do RSS feed
"""

import requests
import pandas as pd
from datetime import datetime
import time
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURAÇÕES — somente jogos GTA
# ─────────────────────────────────────────────────────────────────────────────

GTA_STEAM_GAMES = {
    "271590": "GTA V",
    "12210":  "GTA IV",
    "12120":  "GTA San Andreas",   # ~82k reviews, muita discussão sobre nostalgia vs. remasterização
}

REDDIT_SUBREDDITS = ["GTA6", "GrandTheftAutoV", "GTAVI", "GTA"]

# Google News RSS — queries de busca sobre GTA
# URL: https://news.google.com/rss/search?q=QUERY&hl=en-US&gl=US&ceid=US:en
GNEWS_QUERIES = [
    "Grand Theft Auto VI",
    "GTA 6 Rockstar",
    "GTA 6 release",
    "Grand Theft Auto San Andreas",
    "GTA V review",
    "GTA IV review",
    "Rockstar Games GTA",
    "Grand Theft Auto Online",
]

# Headers por destino
HEADERS_STEAM = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}
# Reddit exige formato "<platform>:<app>:<version>" — sem isso retorna 403
HEADERS_REDDIT = {
    "User-Agent": "python:gta-nlp-analysis:v2.0 (by u/academic_nlp_project)",
    "Accept":     "application/json",
}
HEADERS_RSS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


# ─────────────────────────────────────────────────────────────────────────────
#  ETAPA 1-A — STEAM  (requests + API JSON Valve)
# ─────────────────────────────────────────────────────────────────────────────

def get_steam_reviews(app_id, game_name, max_reviews):
    url = f"https://store.steampowered.com/appreviews/{app_id}"
    reviews_data = []
    lang_limit = max(1, max_reviews // 2)
    print(f"  [Steam] {game_name} — limite: {max_reviews}")

    for lang in ("portuguese", "english"):
        cursor = "*"
        collected = 0
        while collected < lang_limit:
            batch = min(100, lang_limit - collected)
            params = {"json": 1, "language": lang, "filter": "recent",
                      "num_per_page": batch, "cursor": cursor}
            try:
                resp = requests.get(url, params=params, headers=HEADERS_STEAM, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"    Erro Steam ({lang}): {e}")
                break
            if data.get("success") != 1:
                break
            raw = data.get("reviews", [])
            if not raw:
                break
            for r in raw:
                if collected >= lang_limit:
                    break
                text = r.get("review", "").replace("\n", " ").strip()
                if not text or len(text) < 10:
                    continue
                reviews_data.append({
                    "fonte":            "Steam",
                    "jogo":             game_name,
                    "review_id":        str(r.get("recommendationid", "")),
                    "texto":            text,
                    "data":             datetime.fromtimestamp(
                                            r.get("timestamp_created", 0)
                                        ).strftime("%Y-%m-%d"),
                    "idioma":           lang,
                    "score_plataforma": "Positivo" if r.get("voted_up") else "Negativo",
                })
                collected += 1
            cursor = data.get("cursor", "")
            if not cursor:
                break
            time.sleep(1)
        print(f"    [{lang}] {collected} avaliações.")
    return reviews_data[:max_reviews]


def fetch_steam(max_total=200):
    per_game = max(10, max_total // len(GTA_STEAM_GAMES))
    all_reviews = []
    for app_id, name in GTA_STEAM_GAMES.items():
        reviews = get_steam_reviews(app_id, name, max_reviews=per_game)
        all_reviews.extend(reviews)
        print(f"    → Acumulado Steam: {len(all_reviews)}")
        time.sleep(2)
    df = pd.DataFrame(all_reviews)
    print(f"  [Steam] Total: {len(df)} registros.\n")
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  ETAPA 1-B — REDDIT  (API JSON + RSS fallback com BeautifulSoup)
# ─────────────────────────────────────────────────────────────────────────────

def _reddit_row(p, label):
    title    = p.get("title", "").strip()
    selftext = p.get("selftext", "").strip()
    texto    = (f"{title} — {selftext[:600]}"
                if selftext not in ("", "[removed]", "[deleted]") else title)
    return {
        "fonte":            "Reddit",
        "jogo":             label,
        "review_id":        p.get("id", ""),
        "texto":            texto,
        "data":             datetime.fromtimestamp(
                                p.get("created_utc", 0)
                            ).strftime("%Y-%m-%d"),
        "idioma":           "en/pt",
        "score_plataforma": "N/A",
    }


def get_reddit_json(subreddit, limit):
    """API JSON pública do Reddit com User-Agent correto para evitar 403."""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}&raw_json=1"
    try:
        resp = requests.get(url, headers=HEADERS_REDDIT, timeout=15)
        resp.raise_for_status()
        posts = []
        for child in resp.json().get("data", {}).get("children", []):
            row = _reddit_row(child.get("data", {}), f"r/{subreddit}")
            if len(row["texto"]) >= 10:
                posts.append(row)
        print(f"    [Reddit JSON] r/{subreddit}: {len(posts)} posts.")
        return posts[:limit]
    except Exception as e:
        print(f"    [Reddit JSON] r/{subreddit}: {e}")
        return []


def get_reddit_rss(subreddit, limit):
    """
    Fallback: RSS público do Reddit.
    BeautifulSoup parseia o XML — sem autenticação, sempre acessível.
    """
    url = f"https://www.reddit.com/r/{subreddit}/hot.rss?limit={limit}"
    try:
        resp = requests.get(url, headers=HEADERS_REDDIT, timeout=15)
        resp.raise_for_status()
        soup  = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("entry") or soup.find_all("item")
        if not items:
            soup  = BeautifulSoup(resp.text, "html.parser")
            items = soup.find_all("entry") or soup.find_all("item")

        posts = []
        for item in items[:limit]:
            t_el  = item.find("title")
            c_el  = item.find("content") or item.find("description") or item.find("summary")
            title = t_el.get_text(strip=True) if t_el else ""
            desc  = ""
            if c_el:
                inner = BeautifulSoup(c_el.get_text(), "html.parser")
                desc  = inner.get_text(separator=" ", strip=True)[:600]
            texto = f"{title} — {desc}" if desc else title
            if len(texto) < 10:
                continue
            pub      = item.find("published") or item.find("updated") or item.find("pubDate")
            data_str = datetime.now().strftime("%Y-%m-%d")
            if pub:
                try:
                    from email.utils import parsedate_to_datetime
                    data_str = parsedate_to_datetime(pub.get_text()).strftime("%Y-%m-%d")
                except Exception:
                    pass
            posts.append({
                "fonte":            "Reddit",
                "jogo":             f"r/{subreddit}",
                "review_id":        f"rss_{abs(hash(texto)) % 10**7}",
                "texto":            texto,
                "data":             data_str,
                "idioma":           "en/pt",
                "score_plataforma": "N/A",
            })
        print(f"    [Reddit RSS] r/{subreddit}: {len(posts)} posts.")
        return posts
    except Exception as e:
        print(f"    [Reddit RSS] r/{subreddit}: {e}")
        return []


def fetch_reddit(max_total=150):
    per_sub   = max(5, max_total // len(REDDIT_SUBREDDITS))
    all_items = []

    for sub in REDDIT_SUBREDDITS:
        posts = get_reddit_json(sub, limit=per_sub)
        if not posts:
            print(f"    JSON falhou r/{sub}, tentando RSS...")
            posts = get_reddit_rss(sub, limit=per_sub)
        all_items.extend(posts)
        print(f"    r/{sub}: acumulado = {len(all_items)}")
        time.sleep(2)
        if len(all_items) >= max_total:
            break

    # Deduplica por review_id
    seen = set()
    unique = []
    for row in all_items:
        if row["review_id"] not in seen:
            seen.add(row["review_id"])
            unique.append(row)

    df = pd.DataFrame(unique[:max_total]) if unique else pd.DataFrame()
    print(f"  [Reddit] Total: {len(df)} registros.\n")
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  ETAPA 1-C — GOOGLE NEWS RSS
#
#  O Google News oferece feeds RSS públicos de busca, sem autenticação e sem
#  chave de API. Retorna artigos de portais especializados (IGN, Kotaku, Polygon,
#  Eurogamer, Rock Paper Shotgun, etc.) sobre a franquia GTA.
#
#  URL do endpoint:
#    https://news.google.com/rss/search?q=QUERY&hl=en-US&gl=US&ceid=US:en
#
#  Campos relevantes do RSS (parseados com BeautifulSoup):
#    <title>   — título do artigo
#    <description> — trecho/resumo do artigo
#    <pubDate> — data de publicação
#    <source>  — nome do portal de origem (IGN, Kotaku, etc.)
# ─────────────────────────────────────────────────────────────────────────────

def get_gnews_rss(query, max_items=30):
    """
    Busca artigos no Google News RSS para uma query específica.
    Usa BeautifulSoup para parsear o XML retornado.
    Combina título + descrição como texto da análise de sentimento.
    """
    url = (
        f"https://news.google.com/rss/search"
        f"?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    )
    try:
        resp = requests.get(url, headers=HEADERS_RSS, timeout=20)
        resp.raise_for_status()

        # BeautifulSoup com parser xml para feeds RSS/Atom
        soup  = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")

        if not items:
            # Tenta html.parser como fallback para XML mal-formado
            soup  = BeautifulSoup(resp.text, "html.parser")
            items = soup.find_all("item")

        rows = []
        for item in items[:max_items]:
            # Título do artigo
            t_el  = item.find("title")
            title = t_el.get_text(strip=True) if t_el else ""

            # Descrição / snippet do artigo
            d_el = item.find("description")
            desc = ""
            if d_el:
                # Descrição pode ter HTML embutido — BeautifulSoup extrai só o texto
                inner = BeautifulSoup(d_el.get_text(), "html.parser")
                desc  = inner.get_text(separator=" ", strip=True)[:500]

            # Monta texto combinando título + descrição
            texto = f"{title}. {desc}" if desc else title
            if len(texto) < 20:
                continue

            # Data de publicação
            pub_el   = item.find("pubDate")
            data_str = datetime.now().strftime("%Y-%m-%d")
            if pub_el:
                try:
                    from email.utils import parsedate_to_datetime
                    data_str = parsedate_to_datetime(pub_el.get_text()).strftime("%Y-%m-%d")
                except Exception:
                    pass

            # Portal de origem (campo <source> do RSS do Google News)
            src_el = item.find("source")
            fonte_orig = src_el.get_text(strip=True) if src_el else "Google News"

            rows.append({
                "fonte":            "Google News",
                "jogo":             f"GTA — '{query}'",
                "review_id":        f"gn_{abs(hash(title)) % 10**8}",
                "texto":            texto,
                "data":             data_str,
                "idioma":           "en",
                "score_plataforma": fonte_orig,   # usa campo score para mostrar portal
            })

        print(f"    [Google News] '{query}': {len(rows)} artigos.")
        return rows

    except Exception as e:
        print(f"    [Google News] '{query}': {e}")
        return []


def fetch_google_news(max_total=150):
    """
    Coleta artigos do Google News RSS para todas as queries GTA configuradas.
    Deduplica por review_id para evitar repetição de artigos entre queries.
    """
    all_items = []
    seen_ids  = set()
    per_query = max(10, max_total // len(GNEWS_QUERIES))

    print(f"  [Google News] {len(GNEWS_QUERIES)} queries, até {per_query} artigos cada...")

    for query in GNEWS_QUERIES:
        if len(all_items) >= max_total:
            break
        rows = get_gnews_rss(query, max_items=per_query)
        for row in rows:
            if row["review_id"] not in seen_ids and len(all_items) < max_total:
                seen_ids.add(row["review_id"])
                all_items.append(row)
        time.sleep(1.5)   # pausa entre queries para não sobrecarregar

    df = pd.DataFrame(all_items[:max_total]) if all_items else pd.DataFrame()
    print(f"  [Google News] Total: {len(df)} registros.\n")
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  ETAPA 2 — LIMPEZA E PREPARAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

def limpar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = re.sub(r"https?://\S+", " ", texto)
    texto = re.sub(r"[@#]\w+", " ", texto)
    texto = re.sub(r"[^\x00-\x7FÀ-ÿ\u0100-\u024F\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def preparar_dados(df):
    if df.empty:
        return df
    df = df.copy()
    df["texto_original"] = df["texto"]
    df["texto"]          = df["texto"].apply(limpar_texto)
    antes = len(df)
    df.drop_duplicates(subset=["texto"], keep="first", inplace=True)
    print(f"  [Limpeza] Duplicatas removidas: {antes - len(df)}")
    df = df[df["texto"].str.len() >= 15].copy()
    print(f"  [Limpeza] Registros após filtro: {len(df)}")
    df["tamanho_texto"] = df["texto"].str.len()
    df.reset_index(drop=True, inplace=True)
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  PIPELINE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def coletar_tudo(
    max_steam       = 200,
    max_reddit      = 100,
    max_google_news = 150,
    fontes_ativas   = None,
    output_file     = "avaliacoes_gta.csv",
    progress_callback = None,
):
    """
    Pipeline completo: coleta (Steam + Reddit + Google News) + limpeza.

    Fontes:
      Steam       — reviews de jogadores verificados (API Valve)
      Reddit      — posts de subreddits GTA (API JSON + RSS fallback)
      Google News — artigos de portais especializados (RSS público)
    """
    if fontes_ativas is None:
        fontes_ativas = ["Steam", "Reddit", "Google News"]
    frames = []

    def _upd(pct, msg):
        print(f"  [{pct:3d}%] {msg}")
        if progress_callback:
            progress_callback(pct, msg)

    if "Steam" in fontes_ativas and max_steam > 0:
        _upd(5, f"Coletando Steam — reviews de GTA (limite: {max_steam})...")
        df_s = fetch_steam(max_total=max_steam)
        if not df_s.empty:
            frames.append(df_s)

    if "Reddit" in fontes_ativas and max_reddit > 0:
        _upd(35, f"Coletando Reddit — API JSON + RSS fallback (limite: {max_reddit})...")
        df_r = fetch_reddit(max_total=max_reddit)
        if not df_r.empty:
            frames.append(df_r)

    if "Google News" in fontes_ativas and max_google_news > 0:
        _upd(60, f"Coletando Google News RSS — artigos sobre GTA (limite: {max_google_news})...")
        df_g = fetch_google_news(max_total=max_google_news)
        if not df_g.empty:
            frames.append(df_g)

    if not frames:
        print("Nenhum dado coletado.")
        return pd.DataFrame()

    _upd(80, "Consolidando e limpando dados...")
    df_total = pd.concat(frames, ignore_index=True)
    df_total = preparar_dados(df_total)
    df_total.to_csv(output_file, index=False, encoding="utf-8-sig")
    _upd(100, f"Concluído — {len(df_total)} registros em '{output_file}'.")
    return df_total


if __name__ == "__main__":
    df = coletar_tudo(
        max_steam=60, max_reddit=60, max_google_news=60,
        output_file="avaliacoes_gta.csv",
    )
    if not df.empty:
        print(df[["fonte", "jogo", "texto"]].head(10).to_string(index=False))
