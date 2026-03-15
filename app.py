"""
app.py — Dashboard Streamlit Profissional
Análise de Sentimento: Franquia GTA & Rockstar Games
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import io
import json
from scraper import coletar_tudo
from sentiment import process_file
from report import gerar_resumo_analitico

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GTA — Análise NLP",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  PALETA
# ─────────────────────────────────────────────────────────────────────────────

C = {
    "Positivo": "#2E7D32",
    "Negativo": "#C62828",
    "Neutro":   "#E65100",
    "accent":   "#1A3A5C",
    "border":   "#D0D7E2",
}

# ─────────────────────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
  /* Base */
  .stApp {{ background-color: #F0F2F6; }}

  /* Sidebar */
  section[data-testid="stSidebar"] {{ background-color: #1A3A5C !important; }}
  section[data-testid="stSidebar"] .stMarkdown p,
  section[data-testid="stSidebar"] .stMarkdown li,
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] .stSlider label,
  section[data-testid="stSidebar"] .stNumberInput label,
  section[data-testid="stSidebar"] .stMultiSelect label,
  section[data-testid="stSidebar"] span {{
    color: #ECF0F1 !important;
  }}
  section[data-testid="stSidebar"] hr {{ border-color: #2C5F8A !important; }}
  section[data-testid="stSidebar"] .stButton > button {{
    background: #2C5F8A !important; color: white !important;
    border: 1px solid #4A90D9 !important; border-radius: 6px !important;
    font-weight: 600 !important; width: 100% !important; padding: 0.5rem 1rem !important;
  }}
  section[data-testid="stSidebar"] .stButton > button:hover {{ background: #4A90D9 !important; }}

  /* Cards métricas */
  .metric-card {{
    background: white; border: 1px solid {C['border']};
    border-left: 5px solid var(--accent); border-radius: 8px;
    padding: 16px 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); margin-bottom: 14px;
  }}
  .metric-card h4 {{
    margin: 0 0 4px; font-size: 12px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px; color: #666;
  }}
  .metric-card .val {{ font-size: 30px; font-weight: 800; line-height: 1.1; }}
  .metric-card .sub {{ font-size: 11px; color: #999; margin-top: 3px; }}
  .mc-tot {{ --accent: {C['accent']}; }} .mc-tot .val {{ color: {C['accent']}; }}
  .mc-pos {{ --accent: {C['Positivo']}; }} .mc-pos .val {{ color: {C['Positivo']}; }}
  .mc-neg {{ --accent: {C['Negativo']}; }} .mc-neg .val {{ color: {C['Negativo']}; }}
  .mc-neu {{ --accent: {C['Neutro']}; }}   .mc-neu .val {{ color: {C['Neutro']}; }}

  /* Cabeçalho de seção */
  .sec-head {{
    background: white; border: 1px solid {C['border']}; border-radius: 8px;
    padding: 13px 20px; margin: 24px 0 16px;
    display: flex; align-items: center; gap: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  }}
  .sec-head h2 {{ margin: 0; font-size: 16px; font-weight: 700; color: {C['accent']}; }}
  .sec-num {{
    background: {C['accent']}; color: white; border-radius: 50%;
    width: 26px; height: 26px; display: flex; align-items: center;
    justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0;
  }}

  /* Caixas de info/aviso com texto SEMPRE visível */
  .box-info {{
    background: #E3F2FD; border: 1px solid #90CAF9; border-radius: 6px;
    padding: 11px 15px; font-size: 13px; color: #0D47A1;
    margin: 8px 0; line-height: 1.5;
  }}
  .box-warn {{
    background: #FFF3E0; border: 1px solid #FFB74D; border-radius: 6px;
    padding: 11px 15px; font-size: 13px; color: #BF360C;
    margin: 8px 0; line-height: 1.5;
  }}
  .box-ok {{
    background: #E8F5E9; border: 1px solid #81C784; border-radius: 6px;
    padding: 11px 15px; font-size: 13px; color: #1B5E20;
    margin: 8px 0; line-height: 1.5;
  }}

  /* Texto de progresso (status_text) — visível sobre fundo branco */
  .progress-text {{
    background: #E8EAF6; border-radius: 6px; padding: 8px 14px;
    font-size: 13px; color: #1A237E; font-weight: 500; margin: 6px 0;
  }}

  /* Rótulos de seção sidebar */
  .sb-label {{
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.8px; color: #7FB3D3 !important; margin-bottom: 4px; display: block;
  }}

  /* Títulos de sub-seção no conteúdo */
  .subsec {{ font-size: 14px; font-weight: 700; color: {C['accent']};
             margin: 16px 0 10px; display: block; }}

  /* Download buttons */
  .stDownloadButton > button {{
    background: {C['accent']} !important; color: white !important;
    border: none !important; border-radius: 6px !important;
    font-weight: 600 !important; padding: 0.45rem 1rem !important;
  }}
  .stDownloadButton > button:hover {{ opacity: 0.88; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def sec(icon, title, num):
    st.markdown(
        f'<div class="sec-head"><div class="sec-num">{num}</div>'
        f'<h2>{icon} {title}</h2></div>',
        unsafe_allow_html=True,
    )

def mcard(title, val, sub, css):
    st.markdown(
        f'<div class="metric-card {css}"><h4>{title}</h4>'
        f'<div class="val">{val}</div><div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )

def box(msg, kind="info"):
    css = {"info": "box-info", "warn": "box-warn", "ok": "box-ok"}.get(kind, "box-info")
    st.markdown(f'<div class="{css}">{msg}</div>', unsafe_allow_html=True)

def graf_style(fig, ax):
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#FAFAFA")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color("#DDD")
    ax.spines["bottom"].set_color("#DDD")
    ax.tick_params(colors="#444", labelsize=10)
    ax.grid(axis="y", color="#EEEEEE", linestyle="--", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)


# ─────────────────────────────────────────────────────────────────────────────
#  ESTADO DA SESSÃO
# ─────────────────────────────────────────────────────────────────────────────

for k in ("data", "analisado", "resumo_analitico"):
    if k not in st.session_state:
        st.session_state[k] = None if k != "analisado" else False


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:14px 0 6px">
      <div style="font-size:26px">🎮</div>
      <div style="font-size:15px;font-weight:700;color:white;margin-top:3px">GTA — Análise NLP</div>
      <div style="font-size:11px;color:#7FB3D3;margin-top:1px">Rockstar Games · Sentimentos</div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    api_key = os.getenv("MARITACA_API_KEY", "")
    if api_key:
        st.markdown('<span style="color:#2ECC71;font-size:13px">✔ Sabiá-4 conectado</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#E74C3C;font-size:13px">✖ MARITACA_API_KEY ausente</span>',
                    unsafe_allow_html=True)

    st.divider()

    # Etapa 1 — Coleta
    st.markdown('<span class="sb-label">Etapa 1 — Coleta de Dados</span>',
                unsafe_allow_html=True)
    fontes = st.multiselect("Fontes ativas",
                            ["Steam", "Reddit", "Google News"],
                            default=["Steam", "Reddit", "Google News"],
                            label_visibility="collapsed")
    max_steam  = st.slider("Steam (reviews)",     20, 400, 100, 20) if "Steam"      in fontes else 0
    max_reddit = st.slider("Reddit (posts)",      20, 200,  80, 20) if "Reddit"     in fontes else 0
    max_gnews = st.slider("Google News (artigos)", 20, 200, 80, 20) if "Google News" in fontes else 0

    btn_coletar = st.button("▶ Iniciar Coleta", use_container_width=True)

    st.divider()
    st.markdown('<span class="sb-label">OU carregar dados existentes</span>',
                unsafe_allow_html=True)
    # Aceita CSV e JSON
    uploaded = st.file_uploader("Carregar CSV ou JSON",
                                type=["csv", "json"],
                                label_visibility="collapsed")

    st.divider()

    # Etapa 2 — Análise
    st.markdown('<span class="sb-label">Etapa 2 — Análise de Sentimentos</span>',
                unsafe_allow_html=True)
    max_analise = st.number_input("Máx. textos a analisar",
                                  min_value=10, max_value=2000, value=200, step=10)
    st.markdown(
        '<div style="background:#0D2137;border-radius:5px;padding:8px 10px;margin-top:4px;">'
        '<span style="font-size:11px;color:#F39C12;line-height:1.5">'
        '⚠ Textos são amostrados proporcionalmente entre as fontes '
        'para garantir representatividade na análise.</span></div>',
        unsafe_allow_html=True,
    )
    btn_analisar = st.button("▶ Executar Análise", use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
#  CABEÇALHO
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="background:white;border-radius:10px;border:1px solid {C['border']};
     padding:22px 26px;margin-bottom:22px;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="font-size:36px">🎮</div>
    <div>
      <h1 style="margin:0;font-size:22px;color:{C['accent']};font-weight:800">
        Análise de Sentimento — Franquia GTA & Rockstar Games</h1>
      <p style="margin:3px 0 0;color:#555;font-size:13px">
        Pipeline NLP/PLN · Steam · Reddit · Google News · Sabiá-4</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  AÇÃO: COLETA
# ─────────────────────────────────────────────────────────────────────────────

if btn_coletar:
    if not fontes:
        st.error("Selecione ao menos uma fonte.")
    else:
        sec("📡", "Coletando Dados", "1")
        prog = st.progress(0)
        stat = st.empty()

        def cb(pct, msg):
            prog.progress(min(pct, 100))
            stat.markdown(f'<div class="box-info">⏳ {msg}</div>',
                          unsafe_allow_html=True)

        df = coletar_tudo(
            max_steam=max_steam, max_reddit=max_reddit, max_google_news=max_gnews,
            fontes_ativas=fontes, output_file="avaliacoes_gta.csv",
            progress_callback=cb,
        )
        st.session_state.data      = df
        st.session_state.analisado = False
        prog.progress(100)
        stat.markdown(
            f'<div class="box-ok">✔ Coleta concluída — <strong>{len(df)}</strong> registros obtidos.</div>',
            unsafe_allow_html=True,
        )

# Upload CSV ou JSON
if uploaded is not None:
    try:
        if uploaded.name.endswith(".json"):
            st.session_state.data = pd.read_json(uploaded)
        else:
            st.session_state.data = pd.read_csv(uploaded)
        st.session_state.analisado = "sentiment_sabia" in st.session_state.data.columns
        box(f"✔ Arquivo <strong>{uploaded.name}</strong> carregado — "
            f"{len(st.session_state.data)} registros.", "ok")
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")


# ─────────────────────────────────────────────────────────────────────────────
#  AÇÃO: ANÁLISE
# ─────────────────────────────────────────────────────────────────────────────

if btn_analisar:
    if st.session_state.data is None:
        st.error("Colete ou carregue os dados primeiro.")
    elif not api_key:
        st.error("MARITACA_API_KEY não encontrada no .env.")
    else:
        sec("🧠", "Análise de Sentimentos — Sabiá-4", "2")
        df_full = st.session_state.data
        n_total = len(df_full)
        n_max   = int(max_analise)

        # Amostragem estratificada por fonte
        if n_total > n_max and "fonte" in df_full.columns:
            partes = []
            for f in df_full["fonte"].unique():
                sub  = df_full[df_full["fonte"] == f]
                cota = max(1, round(len(sub) / n_total * n_max))
                partes.append(sub.sample(n=min(cota, len(sub)), random_state=42))
            df_proc = pd.concat(partes).sample(frac=1, random_state=42).head(n_max).copy()
        else:
            df_proc = df_full.head(n_max).copy()

        box(
            f"📊 Analisando <strong>{len(df_proc)}</strong> textos "
            f"(de {n_total} coletados, amostrados proporcionalmente por fonte).",
            "info",
        )

        prog2 = st.progress(0)
        stat2 = st.empty()   # placeholder para texto de progresso

        temp = "temp_gta.csv"
        df_proc.to_csv(temp, index=False, encoding="utf-8-sig")

        try:
            # Wrapper de status com texto visível
            def status_update(progress_bar, status_placeholder):
                # Retorna funções que o process_file usa
                pass

            processed = process_file(temp, api_key, prog2, stat2)
            st.session_state.data           = processed
            st.session_state.analisado      = True
            st.session_state.resumo_analitico = None  # reseta ao reanalisar
            prog2.progress(100)
            stat2.markdown(
                '<div class="box-ok">✔ Análise concluída com sucesso!</div>',
                unsafe_allow_html=True,
            )
            st.rerun()
        except Exception as e:
            st.error(f"Erro durante a análise: {e}")


# ─────────────────────────────────────────────────────────────────────────────
#  VISUALIZAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

df = st.session_state.data

if df is not None and not df.empty:

    # ── Pré-visualização ───────────────────────────────────────────────────────
    sec("📋", "Pré-visualização dos Dados Coletados", "1")

    st_n = int(len(df[df["fonte"] == "Steam"]))      if "fonte" in df.columns else 0
    re_n = int(len(df[df["fonte"] == "Reddit"]))     if "fonte" in df.columns else 0
    me_n = int(len(df[df["fonte"] == "Google News"])) if "fonte" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: mcard("Total de Registros", len(df), "dataset completo",      "mc-tot")
    with c2: mcard("Steam",              st_n,    "reviews GTA",           "mc-pos")
    with c3: mcard("Reddit",             re_n,    "posts e comentários",   "mc-neg")
    with c4: mcard("Google News", me_n, "artigos especializados", "mc-neu")

    cols_show = [c for c in ["fonte","jogo","texto","data","idioma","score_plataforma"]
                 if c in df.columns]
    st.dataframe(df[cols_show].head(20), use_container_width=True, height=300)

    # ── Sentimento ─────────────────────────────────────────────────────────────
    if "sentiment_sabia" in df.columns:
        sec("📊", "Resultados da Análise de Sentimento", "3")

        valid  = df[df["sentiment_sabia"].isin(["Positivo","Negativo","Neutro"])].copy()
        counts = valid["sentiment_sabia"].value_counts()
        total  = len(valid)

        if total == 0:
            box("Nenhum sentimento classificado.", "warn")
        else:
            pos = int(counts.get("Positivo", 0))
            neg = int(counts.get("Negativo", 0))
            neu = int(counts.get("Neutro",   0))

            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1: mcard("Total Analisado", total, "textos classificados", "mc-tot")
            with mc2: mcard("Positivos", f"{pos} ({pos/total*100:.1f}%)", "sentimento favorável",   "mc-pos")
            with mc3: mcard("Negativos", f"{neg} ({neg/total*100:.1f}%)", "sentimento desfavorável","mc-neg")
            with mc4: mcard("Neutros",   f"{neu} ({neu/total*100:.1f}%)", "sentimento neutro/misto","mc-neu")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Gráfico 1: Pizza + Barras por Fonte ────────────────────────────
            g1, g2 = st.columns([1, 1.6])

            with g1:
                st.markdown('<span class="subsec">Distribuição Geral</span>',
                            unsafe_allow_html=True)
                fig, ax0 = plt.subplots(figsize=(5, 4))
                ax0.set_visible(False)
                ax2 = fig.add_subplot(111)
                fig.patch.set_facecolor("white")

                fl = [(l, s, c) for l, s, c in zip(
                    ["Positivo","Negativo","Neutro"],
                    [pos, neg, neu],
                    [C["Positivo"], C["Negativo"], C["Neutro"]]
                ) if s > 0]

                wedges, _, ats = ax2.pie(
                    [x[1] for x in fl], colors=[x[2] for x in fl],
                    autopct="%1.1f%%", startangle=140, pctdistance=0.72,
                    wedgeprops={"linewidth": 2, "edgecolor": "white"},
                )
                for at in ats:
                    at.set_fontsize(11); at.set_color("white"); at.set_fontweight("bold")
                ax2.legend(wedges, [x[0] for x in fl],
                           loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.06),
                           frameon=False, fontsize=10)
                ax2.set_aspect("equal")
                fig.tight_layout(pad=1.5)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

            with g2:
                st.markdown('<span class="subsec">Sentimentos por Fonte</span>',
                            unsafe_allow_html=True)
                if "fonte" in valid.columns:
                    fs = (valid.groupby(["fonte","sentiment_sabia"])
                          .size().unstack(fill_value=0))
                    for col in ["Positivo","Negativo","Neutro"]:
                        if col not in fs.columns: fs[col] = 0
                    fs = fs[["Positivo","Negativo","Neutro"]]

                    fig2, ax2 = plt.subplots(figsize=(7, 4))
                    graf_style(fig2, ax2)
                    x = range(len(fs)); w = 0.26
                    for i, (col, cor) in enumerate(zip(
                        ["Positivo","Negativo","Neutro"],
                        [C["Positivo"], C["Negativo"], C["Neutro"]]
                    )):
                        bars = ax2.bar([xi + i*w for xi in x], fs[col],
                                       width=w, color=cor, label=col, zorder=3, linewidth=0)
                        for b in bars:
                            h = b.get_height()
                            if h > 0:
                                ax2.text(b.get_x()+b.get_width()/2, h+0.4, str(int(h)),
                                         ha="center", va="bottom", fontsize=8,
                                         color="#333", fontweight="600")
                    ax2.set_xticks([xi+w for xi in x])
                    ax2.set_xticklabels(fs.index, fontsize=10)
                    ax2.set_ylabel("Nº de textos", fontsize=10, color="#555")
                    ax2.legend(frameon=False, fontsize=9)
                    fig2.tight_layout(pad=1.5)
                    st.pyplot(fig2, use_container_width=True)
                    plt.close(fig2)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Gráfico 2: Horizontal por Jogo (normalizado) ───────────────────
            if "jogo" in valid.columns:
                st.markdown('<span class="subsec">Sentimentos por Jogo GTA</span>',
                            unsafe_allow_html=True)

                # Mapa de normalização: converte qualquer valor da coluna "jogo"
                # para o nome canônico do jogo — independente da fonte de origem
                JOGO_CANON = {
                    # GTA VI / GTA 6
                    "GTA VI":                    "GTA VI",
                    "GTA 6":                     "GTA VI",
                    "r/GTA6":                    "GTA VI",
                    "r/GTAVI":                   "GTA VI",
                    "GTA — 'Grand Theft Auto VI'":"GTA VI",
                    "GTA — 'GTA 6 Rockstar'":    "GTA VI",
                    "GTA — 'GTA 6 release'":     "GTA VI",
                    # GTA V
                    "GTA V":                     "GTA V",
                    "r/GrandTheftAutoV":         "GTA V",
                    "GTA — 'GTA V review'":      "GTA V",
                    # GTA IV
                    "GTA IV":                    "GTA IV",
                    "GTA — 'GTA IV review'":     "GTA IV",
                    # GTA San Andreas
                    "GTA San Andreas":           "GTA San Andreas",
                    "GTA — 'Grand Theft Auto San Andreas'": "GTA San Andreas",
                    # GTA Online / genérico
                    "GTA — 'Grand Theft Auto Online'":      "GTA Online",
                    "GTA — 'Rockstar Games GTA'":           "GTA (Geral)",
                    "r/GTA":                                "GTA (Geral)",
                }

                def normalizar_jogo(valor):
                    """
                    Aplica o mapa exato primeiro, depois tenta correspondência
                    por substring para cobrir valores não mapeados explicitamente.
                    """
                    if not isinstance(valor, str):
                        return "Outros"
                    # Correspondência exata
                    if valor in JOGO_CANON:
                        return JOGO_CANON[valor]
                    v = valor.lower()
                    # Correspondência por substring
                    if "gta vi" in v or "gta 6" in v or "gtavi" in v or "r/gta6" in v:
                        return "GTA VI"
                    if "san andreas" in v:
                        return "GTA San Andreas"
                    if "gta v" in v or "grandtheftautov" in v or "gtav" in v:
                        return "GTA V"
                    if "gta iv" in v or "gtaiv" in v:
                        return "GTA IV"
                    if "gta iii" in v or "gta3" in v or "gta 3" in v:
                        return "GTA III"
                    if "vice city" in v:
                        return "GTA Vice City"
                    if "online" in v:
                        return "GTA Online"
                    if "rockstar" in v or "r/gta" in v:
                        return "GTA (Geral)"
                    return "GTA (Geral)"

                # Cria coluna normalizada e agrupa
                v2 = valid.copy()
                v2["jogo_norm"] = v2["jogo"].apply(normalizar_jogo)

                # Ordem de exibição preferida (do mais clássico ao mais recente)
                ORDEM = ["GTA III", "GTA Vice City", "GTA San Andreas",
                         "GTA IV", "GTA V", "GTA Online", "GTA VI", "GTA (Geral)"]

                js = (v2.groupby(["jogo_norm", "sentiment_sabia"])
                        .size().unstack(fill_value=0))
                for col in ["Positivo", "Negativo", "Neutro"]:
                    if col not in js.columns:
                        js[col] = 0
                js = js[["Positivo", "Negativo", "Neutro"]]

                # Reordena pelas entradas que existem, respeitando ORDEM
                idx_sorted = [j for j in ORDEM if j in js.index] + \
                             [j for j in js.index if j not in ORDEM]
                js = js.loc[idx_sorted]

                fig3, ax3 = plt.subplots(figsize=(10, max(3.5, len(js) * 0.7)))
                graf_style(fig3, ax3)
                ax3.spines["left"].set_color("#DDD")
                ax3.grid(axis="x", color="#EEEEEE", linestyle="--", linewidth=0.8, alpha=0.8)
                ax3.grid(axis="y", visible=False)

                y = range(len(js))
                h = 0.26
                for i, (col, cor) in enumerate(zip(
                    ["Positivo", "Negativo", "Neutro"],
                    [C["Positivo"], C["Negativo"], C["Neutro"]]
                )):
                    bars = ax3.barh([yi + i * h for yi in y], js[col],
                                    height=h, color=cor, label=col, zorder=3, linewidth=0)
                    for b in bars:
                        w_v = b.get_width()
                        if w_v > 0:
                            ax3.text(w_v + 0.2, b.get_y() + b.get_height() / 2,
                                     str(int(w_v)), va="center", ha="left",
                                     fontsize=8, color="#333", fontweight="600")

                ax3.set_yticks([yi + h for yi in y])
                ax3.set_yticklabels(js.index.tolist(), fontsize=11, fontweight="600")
                ax3.set_xlabel("Nº de textos classificados", fontsize=10, color="#555")
                ax3.legend(frameon=False, fontsize=10, loc="lower right")
                fig3.tight_layout(pad=1.5)
                st.pyplot(fig3, use_container_width=True)
                plt.close(fig3)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Etapa 4 — Resumo Analítico via Sabiá-4 (RAG) ──────────────────────
            sec("🤖", "Etapa 4 — Resumo Analítico (RAG / Sabiá-4)", "4")

            box(
                "📝 O Sabiá-4 analisa os dados coletados e gera automaticamente: "
                "resumo geral · padrões encontrados · principais reclamações · "
                "percepções positivas · temas recorrentes · recomendações estratégicas.",
                "info",
            )

            # Guarda o resumo no session_state para não precisar regenerar a cada rerun
            if "resumo_analitico" not in st.session_state:
                st.session_state.resumo_analitico = None

            btn_resumo = st.button("🤖 Gerar Resumo Analítico com Sabiá-4",
                                   use_container_width=False)

            if btn_resumo:
                if not api_key:
                    st.error("MARITACA_API_KEY não encontrada no .env.")
                else:
                    gen_ph = st.empty()
                    gen_ph.markdown(
                        '<div style="background:#E8EAF6;border-radius:8px;padding:14px 18px;'
                        'font-size:14px;color:#1A237E;font-weight:600;margin:8px 0;">'
                        '⏳ Gerando resumo analítico com Sabiá-4... aguarde ~20 segundos'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    try:
                        resultado = gerar_resumo_analitico(valid, api_key)
                        st.session_state.resumo_analitico = resultado
                        gen_ph.empty()
                        st.rerun()
                    except Exception as e:
                        gen_ph.empty()
                        st.error(f"Erro ao gerar resumo: {e}")

            # Exibe o resumo se já foi gerado
            if st.session_state.get("resumo_analitico"):
                r = st.session_state.resumo_analitico

                def card_resumo(icon, titulo, cor_borda, conteudo):
                    # Normaliza qualquer tipo retornado pelo Sabiá (str, list, dict...)
                    if isinstance(conteudo, list):
                        conteudo = "\n".join(
                            str(item) for item in conteudo if item
                        )
                    elif not isinstance(conteudo, str):
                        conteudo = str(conteudo) if conteudo else ""
                    # Formata listas numeradas com bullet visual
                    linhas = conteudo.strip().split("\n")
                    html_linhas = ""
                    for ln in linhas:
                        ln = ln.strip()
                        if not ln:
                            continue
                        # Linha numerada: "1. texto"
                        if ln and ln[0].isdigit() and ". " in ln[:4]:
                            num, txt = ln.split(". ", 1)
                            html_linhas += (
                                f'<div style="display:flex;gap:10px;margin-bottom:8px;">'
                                f'<span style="background:{cor_borda};color:white;border-radius:50%;'
                                f'min-width:22px;height:22px;display:flex;align-items:center;'
                                f'justify-content:center;font-size:11px;font-weight:700;flex-shrink:0">'
                                f'{num}</span>'
                                f'<span style="font-size:13px;color:#333;line-height:1.6">{txt}</span>'
                                f'</div>'
                            )
                        else:
                            html_linhas += f'<p style="font-size:13px;color:#333;line-height:1.7;margin:0 0 6px">{ln}</p>'

                    st.markdown(
                        f'<div style="background:white;border:1px solid #E0E0E0;'
                        f'border-left:5px solid {cor_borda};border-radius:8px;'
                        f'padding:18px 20px;margin-bottom:14px;'
                        f'box-shadow:0 1px 4px rgba(0,0,0,0.05);">'
                        f'<div style="font-size:14px;font-weight:700;color:{cor_borda};'
                        f'margin-bottom:12px">{icon} {titulo}</div>'
                        f'{html_linhas}</div>',
                        unsafe_allow_html=True,
                    )

                card_resumo("📋", "Resumo Geral",                   "#1A3A5C", r.get("resumo", ""))
                card_resumo("📈", "Principais Padrões Encontrados", "#2C5F8A", r.get("padroes", ""))

                col_a, col_b = st.columns(2)
                with col_a:
                    card_resumo("⚠️",  "Principais Reclamações",   C["Negativo"], r.get("reclamacoes", ""))
                with col_b:
                    card_resumo("✅", "Percepções Positivas",       C["Positivo"], r.get("percepcoes_positivas", ""))

                card_resumo("🔁", "Temas Recorrentes",              C["Neutro"],   r.get("temas_recorrentes", ""))
                card_resumo("🎯", "Recomendações para o Marketing", "#6A1B9A",     r.get("recomendacoes", ""))

                box("✔ Resumo analítico gerado pelo Sabiá-4 com base nos dados reais coletados (RAG).", "ok")

            # ── Exportação ─────────────────────────────────────────────────────
            sec("📥", "Exportação do Dataset", "5")

            st.markdown(
                '<span style="font-size:14px;font-weight:600;color:#1A3A5C;">'
                'Exportar dataset completo com sentimentos:</span>',
                unsafe_allow_html=True,
            )
            ec1, ec2 = st.columns(2)
            with ec1:
                st.download_button(
                    "⬇ Baixar CSV",
                    data=valid.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="gta_sentimentos.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with ec2:
                st.download_button(
                    "⬇ Baixar JSON",
                    data=valid.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8"),
                    file_name="gta_sentimentos.json",
                    mime="application/json",
                    use_container_width=True,
                )

    else:
        box(
            "🧠 Execute a <strong>Análise de Sentimentos</strong> no menu lateral "
            "para visualizar os gráficos e resultados.",
            "info",
        )

else:
    # ── Tela inicial ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:white;border:1px solid {C['border']};border-radius:10px;
         padding:30px;text-align:center;margin:20px 0;">
      <div style="font-size:44px;margin-bottom:10px">🚀</div>
      <h3 style="color:{C['accent']};margin:0 0 8px">Bem-vindo ao Pipeline de Análise NLP</h3>
      <p style="color:#555;font-size:14px;max-width:500px;margin:0 auto">
        Use o menu lateral para iniciar a coleta de dados de Steam, Reddit e Google News,
        e em seguida executar a análise de sentimentos com o modelo Sabiá-4.
      </p>
    </div>
    """, unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns(3)
    cards = [
        ("🎮", "Steam", "Reviews de GTA V, GTA IV e GTA San Andreas via API pública da Valve"),
        ("💬", "Reddit", "Posts dos subreddits r/GTA6, r/GTAVI, r/GrandTheftAutoV via API JSON + RSS"),
        ("📰", "Google News", "Artigos de portais especializados (IGN, Kotaku, Eurogamer...) via RSS público"),
    ]
    for col, (icon, title, desc) in zip([fc1, fc2, fc3], cards):
        with col:
            st.markdown(f"""
            <div style="background:white;border:1px solid {C['border']};border-radius:8px;
                 padding:18px;text-align:center;">
              <div style="font-size:26px;margin-bottom:6px">{icon}</div>
              <strong style="color:{C['accent']}">{title}</strong>
              <p style="color:#555;font-size:12px;margin:8px 0 0">{desc}</p>
            </div>""", unsafe_allow_html=True)
