"""
sentiment.py — Análise de Sentimentos via Sabiá-4 (Maritaca AI) exclusivamente.
O léxico local foi removido — somente o LLM classifica os textos.
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
import time

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
#  SYSTEM PROMPT — contexto especializado GTA / jogos
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Você é um especialista em Processamento de Linguagem Natural (NLP/PLN) especializado em análise de sentimentos sobre jogos eletrônicos, especialmente a franquia GTA e jogos da Rockstar Games.

Sua tarefa é classificar o sentimento do texto fornecido em UMA das três categorias:
- Positivo
- Negativo
- Neutro

Critérios de classificação:
- Positivo: entusiasmo, elogio, satisfação, expectativa positiva, diversão, admiração pelo jogo ou pela Rockstar.
- Negativo: frustração, decepção, raiva, crítica forte, insatisfação, rejeição ao jogo ou à empresa.
- Neutro: texto informativo/descritivo sem carga emocional clara, ou que equilibra positivo e negativo igualmente.

Contexto importante (franquia GTA e Rockstar Games):
- Menções a hype, antecipação e espera pelo GTA 6 são geralmente Positivas.
- Críticas a microtransações, bugs, suporte ou práticas da indústria são geralmente Negativas.
- Descrições factuais de gameplay ou comparações neutras são Neutras.

INSTRUÇÃO CRÍTICA: Responda APENAS com uma única palavra — Positivo, Negativo ou Neutro. Sem pontuação, sem explicações, sem formatação."""


# ─────────────────────────────────────────────────────────────────────────────
#  SABIÁ-4 — função de análise (NÃO MODIFICAR)
# ─────────────────────────────────────────────────────────────────────────────

def analyze_sentiment_sabia(text, api_key):
    """Envia um texto ao Sabiá-4 e retorna 'Positivo', 'Negativo' ou 'Neutro'."""
    url = "https://chat.maritaca.ai/api/chat/completions"
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": "sabiá-4",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f'Texto: "{text[:800]}"\nSentimento:'},
        ],
        "temperature": 0.0,
        "max_tokens":  10,
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=15)
        resp.raise_for_status()
        result    = resp.json()["choices"][0]["message"]["content"].strip().lower()
        if "positivo" in result:
            return "Positivo"
        elif "negativo" in result:
            return "Negativo"
        elif "neutro" in result:
            return "Neutro"
        return "Neutro"
    except Exception as e:
        print(f"  Erro API Sabiá: {str(e)[:80]}")
        return "Erro"


# ─────────────────────────────────────────────────────────────────────────────
#  PROCESSAMENTO
# ─────────────────────────────────────────────────────────────────────────────

def process_file(file_path, api_key, progress_bar=None, status_text=None):
    """
    Classifica cada texto com Sabiá-4.
    Salva progresso a cada 10 registros para evitar perda de dados.
    """
    if not api_key:
        raise ValueError("MARITACA_API_KEY não fornecida.")

    df = pd.read_csv(file_path)

    if "sentiment_sabia" not in df.columns:
        df["sentiment_sabia"] = None

    pendentes = df[df["sentiment_sabia"].isna() | (df["sentiment_sabia"] == "Erro")]
    total     = len(pendentes)
    print(f"Enviando {total} textos ao Sabiá-4...")

    for i, (index, row) in enumerate(pendentes.iterrows()):
        sentiment = analyze_sentiment_sabia(row["texto"], api_key)
        df.at[index, "sentiment_sabia"] = sentiment

        fonte = str(row.get("fonte", "?"))
        jogo  = str(row.get("jogo", "?"))[:30]
        print(f"  [{i+1:>4}/{total}] {fonte:<20} {jogo:<32} → {sentiment}")

        if i % 10 == 0:
            df.to_csv(file_path, index=False, encoding="utf-8-sig")

        # Atualiza barra de progresso e texto de status no Streamlit
        if progress_bar is not None and status_text is not None:
            pct = int(((i + 1) / total) * 100)
            progress_bar.progress(pct)
            cor = {"Positivo": "#2E7D32", "Negativo": "#C62828",
                   "Neutro": "#E65100"}.get(sentiment, "#555")
            status_text.markdown(
                f'<div style="background:#E8EAF6;border-radius:6px;padding:9px 15px;'
                f'font-size:13px;color:#1A237E;font-weight:500;margin:4px 0;">'
                f'⏳ Analisando <strong>{i+1}</strong> de <strong>{total}</strong> '
                f'({pct}%)&nbsp;&nbsp;|&nbsp;&nbsp;Fonte: <strong>{fonte}</strong>'
                f'&nbsp;&nbsp;|&nbsp;&nbsp;Resultado: '
                f'<strong style="color:{cor}">{sentiment}</strong></div>',
                unsafe_allow_html=True,
            )
        time.sleep(0.5)

    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print("Análise Sabiá-4 concluída.")
    return df


if __name__ == "__main__":
    csv = "avaliacoes_gta.csv"
    if os.path.exists(csv):
        process_file(csv, os.getenv("MARITACA_API_KEY"))
    else:
        print(f"'{csv}' não encontrado. Execute scraper.py primeiro.")
