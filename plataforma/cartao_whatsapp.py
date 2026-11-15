"""O cartão de situação das mensagens de WhatsApp: uma imagem com os próximos 10 dias do rio.

Vai no topo das mensagens (boas-vindas e alertas), como imagem de cabeçalho dos modelos aprovados
pela Meta. Mostra, numa olhadela:
  * o nível de cheia (a cor do alerta, em grande);
  * a QUANTIDADE de água: o caudal previsto dia a dia, com a faixa de incerteza e o limite amarelo;
  * a QUALIDADE: a cor da água prevista em Marracuene, um quadrado por dia (os degraus do mapa);
  * o endereço da plataforma.
1200 x 628 píxeis (a proporção que a Meta recomenda para imagens de cabeçalho), PNG de 60-90 KB.
Usa só o tipo de letra que vem com o matplotlib (DejaVu Sans), para sair igual no computador do
projecto, no GitHub e no Streamlit Cloud.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
TINTA, RIO, MUDO, LINHA, FUNDO = "#212529", "#615C9F", "#6C6E74", "#E2E1EA", "#F6F6F9"          # the platform's colours (Copernicus purple)
NIVEIS = {"verde": "#27AE60", "amarelo": "#F1C40F", "laranja": "#E67E22", "vermelho": "#C0392B"}
CORES_AGUA = {"muito clara": "#1D6B8F", "clara": "#6FAFC9", "habitual": "#E3D5A8", "turva": "#C08A45", "muito turva": "#6F3B14"}
TEXTOS = {
    "pt": {"titulo": "Rio Incomáti · Marracuene", "periodo": "Próximos 10 dias · {de} a {ate}", "cheia": "CHEIAS", "agua": "ÁGUA DO RIO EM MARRACUENE",
           "quantidade": "QUANTIDADE DE ÁGUA · caudal previsto (m³/s)", "qualidade": "QUALIDADE · cor da água prevista, dia a dia",
           "limite": "limite amarelo {v}", "rodape": "Mais detalhes e o mapa: {site}", "aviso": "Serviço experimental. Não substitui os avisos do INGD.",
           "niveis": {"verde": "VERDE", "amarelo": "AMARELO", "laranja": "LARANJA", "vermelho": "VERMELHO"},
           "frases": {"verde": "Sem sinais de cheia", "amarelo": "Atenção: o rio está a subir", "laranja": "A água pode chegar às zonas baixas",
                      "vermelho": "Cheia provável nas zonas baixas"},
           "agua_frases": {"muito clara": "Muito mais clara do que o costume", "clara": "Mais clara do que o costume", "habitual": "Com a cor do costume",
                           "turva": "Mais turva do que o costume", "muito turva": "Muito mais turva do que o costume"},
           "beber": "Trate sempre a água antes de beber.", "indisponivel": "Previsão indisponível",
           "degraus": {"muito clara": "muito clara", "clara": "clara", "habitual": "habitual", "turva": "turva", "muito turva": "muito turva"}},
    "en": {"titulo": "Incomati River · Marracuene", "periodo": "Next 10 days · {de} to {ate}", "cheia": "FLOODS", "agua": "RIVER WATER AT MARRACUENE",
           "quantidade": "WATER QUANTITY · forecast flow (m³/s)", "qualidade": "QUALITY · forecast colour of the water, day by day",
           "limite": "yellow limit {v}", "rodape": "More details and the map: {site}", "aviso": "Experimental service. It does not replace INGD warnings.",
           "niveis": {"verde": "GREEN", "amarelo": "YELLOW", "laranja": "ORANGE", "vermelho": "RED"},
           "frases": {"verde": "No signs of flooding", "amarelo": "Attention: the river is rising", "laranja": "Water may reach low-lying areas",
                      "vermelho": "Flooding likely in low-lying areas"},
           "agua_frases": {"muito clara": "Much clearer than usual", "clara": "Clearer than usual", "habitual": "Its usual colour",
                           "turva": "Muddier than usual", "muito turva": "Much muddier than usual"},
           "beber": "Always treat the water before drinking.", "indisponivel": "Forecast unavailable",
           "degraus": {"muito clara": "very clear", "clara": "clear", "habitual": "usual", "turva": "muddy", "muito turva": "very muddy"}},
    "fr": {"titulo": "Fleuve Incomati · Marracuene", "periodo": "10 prochains jours · du {de} au {ate}", "cheia": "CRUES", "agua": "EAU DU FLEUVE À MARRACUENE",
           "quantidade": "QUANTITÉ D'EAU · débit prévu (m³/s)", "qualidade": "QUALITÉ · couleur de l'eau prévue, jour par jour",
           "limite": "limite jaune {v}", "rodape": "Plus de détails et la carte : {site}", "aviso": "Service expérimental. Ne remplace pas les alertes de l'INGD.",
           "niveis": {"verde": "VERT", "amarelo": "JAUNE", "laranja": "ORANGE", "vermelho": "ROUGE"},
           "frases": {"verde": "Aucun signe de crue", "amarelo": "Attention : le fleuve monte", "laranja": "L'eau peut atteindre les zones basses",
                      "vermelho": "Crue probable dans les zones basses"},
           "agua_frases": {"muito clara": "Beaucoup plus claire que d'habitude", "clara": "Plus claire que d'habitude", "habitual": "De sa couleur habituelle",
                           "turva": "Plus trouble que d'habitude", "muito turva": "Beaucoup plus trouble que d'habitude"},
           "beber": "Traitez toujours l'eau avant de la boire.", "indisponivel": "Prévision indisponible",
           "degraus": {"muito clara": "très claire", "clara": "claire", "habitual": "habituelle", "turva": "trouble", "muito turva": "très trouble"}},
}
DEGRAUS_AGUA = ["muito clara", "clara", "habitual", "turva", "muito turva"]


def dias(boletim: dict, prevista: pd.DataFrame | None, n: int = 10) -> pd.DataFrame:
    """Os próximos `n` dias (a partir de amanhã): nível de cheia, caudal (mediana, p10, p90) e a cor
    da água prevista (a da semana, com maré média: o que se espera nesse dia, seja a que hora for)."""
    linhas = pd.DataFrame(boletim.get("previsao_diaria", []))
    if linhas.empty:
        return linhas
    linhas["data"] = pd.to_datetime(linhas["data"])
    linhas = linhas.iloc[1:n + 1].set_index("data")
    if prevista is not None and len(prevista):
        coluna = "ndti_semana" if "ndti_semana" in prevista else "ndti_q8"
        valores = prevista[coluna].copy()
        valores.index = pd.to_datetime(valores.index)
        linhas["indice_agua"] = valores.reindex(linhas.index)
    return linhas


def degrau(valor: float, passos) -> str | None:
    if valor is None or pd.isna(valor):
        return None
    k = sum(valor >= p for p in passos)
    return DEGRAUS_AGUA[k]


def desenhar(boletim: dict, prevista: pd.DataFrame | None, passos, lingua: str = "pt", site: str = "") -> bytes:
    """O cartão (PNG) para uma língua. `passos` = os quatro limites dos degraus de cor (turbidity_map.STEPS)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    from PIL import Image

    tx = TEXTOS.get(lingua, TEXTOS["pt"])
    tabela = dias(boletim, prevista)
    valido = bool(boletim.get("seguro_mostrar")) and len(tabela) > 0
    nivel = boletim.get("nivel_maximo_provavel", "verde") if valido else None
    fig = plt.figure(figsize=(12, 6.28), dpi=100, facecolor="white")
    plt.rcParams["font.family"] = "DejaVu Sans"

    def caixa(x, y, w, h, cor, raio=0.012, **kw):           # boxes stay under the logo, the charts and the words (zorder -1)
        fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={raio}", transform=fig.transFigure, facecolor=cor,
                                          edgecolor=kw.pop("borda", "none"), linewidth=kw.pop("espessura", 0), zorder=-1, **kw))

    # faixa de cima: marca, rio, datas
    caixa(0, 0.855, 1, 0.145, RIO, raio=0)
    logo = AQUI / "static" / "ete.png"
    if logo.exists():
        eixo = fig.add_axes([0.022, 0.868, 0.068, 0.118])
        eixo.imshow(Image.open(logo).convert("RGBA")), eixo.set_axis_off()
    fig.text(0.105, 0.94, "Eyes to Earth", color="white", fontsize=22, fontweight="bold", va="center")
    fig.text(0.105, 0.888, tx["titulo"], color="#ECEAFA", fontsize=14, va="center")
    if valido:
        fig.text(0.975, 0.915, tx["periodo"].format(de=f"{tabela.index[0]:%d/%m}", ate=f"{tabela.index[-1]:%d/%m}"), color="white", fontsize=14, ha="right", va="center")

    # esquerda: o nível de cheia e o estado da água
    caixa(0.022, 0.475, 0.335, 0.345, FUNDO)
    fig.text(0.045, 0.775, tx["cheia"], color=MUDO, fontsize=11, fontweight="bold")
    if valido:
        caixa(0.045, 0.635, 0.29, 0.11, NIVEIS[nivel], raio=0.02)
        fig.text(0.19, 0.69, tx["niveis"][nivel], color="black" if nivel == "amarelo" else "white", fontsize=24, fontweight="bold", ha="center", va="center")
        fig.text(0.045, 0.565, tx["frases"][nivel], color=TINTA, fontsize=14.5, fontweight="bold", wrap=True)
    else:
        fig.text(0.045, 0.68, tx["indisponivel"], color=TINTA, fontsize=18, fontweight="bold")
    caixa(0.022, 0.105, 0.335, 0.345, FUNDO)
    fig.text(0.045, 0.405, tx["agua"], color=MUDO, fontsize=11, fontweight="bold")
    hoje = degrau(tabela["indice_agua"].iloc[:7].mean(), passos) if valido and "indice_agua" in tabela else None
    if hoje:
        import textwrap

        caixa(0.045, 0.285, 0.05, 0.095, CORES_AGUA[hoje], raio=0.012)
        fig.text(0.108, 0.333, textwrap.fill(tx["agua_frases"][hoje], 22), color=TINTA, fontsize=14, fontweight="bold", va="center", linespacing=1.25)
        fig.text(0.045, 0.165, textwrap.fill(tx["beber"], 38), color=TINTA, fontsize=12.5, va="center", linespacing=1.3)

    # direita, em cima: a quantidade (caudal)
    fig.text(0.39, 0.79, tx["quantidade"], color=MUDO, fontsize=11, fontweight="bold")
    eixo = fig.add_axes([0.395, 0.495, 0.58, 0.27])
    if valido and "caudal_mediana_m3s" in tabela:
        x = range(len(tabela))
        eixo.fill_between(x, tabela["caudal_p10_m3s"], tabela["caudal_p90_m3s"], color=RIO, alpha=0.14, linewidth=0)
        eixo.plot(x, tabela["caudal_mediana_m3s"], color=RIO, linewidth=3, marker="o", markersize=5)
        amarelo = (boletim.get("estado", {}).get("limites_caudal") or {}).get("amarelo")
        topo = max(float(tabela["caudal_p90_m3s"].max()), float(tabela["caudal_mediana_m3s"].max())) * 1.15
        if amarelo and amarelo < topo * 2.2:
            eixo.axhline(amarelo, color="#D4AC0D", linestyle=(0, (5, 3)), linewidth=2)
            eixo.text(len(tabela) - 1, amarelo, tx["limite"].format(v=f"{amarelo:.0f}"), color="#9A7D0A", fontsize=11, ha="right", va="bottom", fontweight="bold")
            topo = max(topo, amarelo * 1.12)
        eixo.set_ylim(0, topo)
        eixo.set_xticks(list(x), [f"{d:%d/%m}" for d in tabela.index], fontsize=10, color=MUDO)
        eixo.tick_params(axis="y", labelsize=10, colors=MUDO)
    for lado in ("top", "right"):
        eixo.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        eixo.spines[lado].set_color(LINHA)
    eixo.grid(axis="y", color="#EEE9DD", linewidth=1)

    # direita, em baixo: a qualidade (cor da água dia a dia)
    fig.text(0.39, 0.405, tx["qualidade"], color=MUDO, fontsize=11, fontweight="bold")
    if valido and "indice_agua" in tabela:
        largura = 0.58 / len(tabela)
        for i, (dia, valor) in enumerate(tabela["indice_agua"].items()):
            nome = degrau(valor, passos)
            caixa(0.395 + i * largura + 0.004, 0.24, largura - 0.008, 0.13, CORES_AGUA.get(nome, "#B4B9BE"), raio=0.01)
            fig.text(0.395 + (i + 0.5) * largura, 0.205, f"{dia:%d/%m}", color=MUDO, fontsize=10, ha="center", va="center")
        x = 0.395
        for nome in DEGRAUS_AGUA:                                       # a legenda dos cinco degraus (os nomes curtos da plataforma)
            caixa(x, 0.135, 0.016, 0.03, CORES_AGUA[nome], raio=0.004)
            fig.text(x + 0.021, 0.15, tx["degraus"][nome], color=MUDO, fontsize=10, va="center")
            x += 0.116

    # rodapé
    fig.text(0.022, 0.045, tx["rodape"].format(site=site.replace("https://", "")) if site else "", color=RIO, fontsize=12.5, fontweight="bold", va="center")
    fig.text(0.975, 0.045, tx["aviso"], color=MUDO, fontsize=10.5, ha="right", va="center")
    saida = io.BytesIO()
    fig.savefig(saida, format="png", dpi=100, facecolor="white")
    plt.close(fig)
    imagem = Image.open(saida).convert("RGB")
    final = io.BytesIO()
    imagem.quantize(colors=128, method=Image.Quantize.MEDIANCUT).save(final, "PNG", optimize=True)
    return final.getvalue()
