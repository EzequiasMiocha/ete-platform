"""Imagens para os slides do Workshop 2, em Workshop_2/0_facilitadores/imagens_para_slides/.

    cd scripts && ../.venv/bin/python -m workshop2.figuras

Feitas com os mesmos dados e o mesmo modelo da prática (os pontos da equipa). Os mapas não têm texto:
os títulos e as legendas ficam nos slides. Os gráficos têm letra grande, para se lerem projectados.
"""

import json
import os

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from .comum import ANOS_TESTE, DADOS_SLIDES, FAC, PRATICA, ROOT, ferramentas_namespace  # noqa: E402

OUT = FAC / "imagens_para_slides"
FUNDO = "#FFFFFF"          # fundo branco, como os slides (estilo académico)
TINTA = "#1B1F24"
SUAVE = "#4A5563"
GRELHA = "#D9DEE4"
AZUL_ETE = "#034581"        # o azul do logótipo ETE
AGUA = (31, 111, 178)
TERRA = (233, 228, 216)
NUVEM = (190, 190, 198)
plt.rcParams.update({"font.family": ["Arial", "Liberation Sans", "DejaVu Sans"], "font.size": 22, "text.color": TINTA,
                     "axes.edgecolor": "#9AA4AF", "axes.labelcolor": SUAVE, "xtick.color": SUAVE, "ytick.color": SUAVE})


def guardar(arr, nome, escala=1):
    im = Image.fromarray(arr)
    if escala != 1:
        im = im.resize((im.width * escala, im.height * escala), Image.NEAREST)
    im.save(OUT / nome, optimize=True)
    return OUT / nome


def u8(rgb):
    return (np.clip(np.nan_to_num(rgb), 0, 1) * 255).astype("uint8")


def cor(f, img):
    return u8(f["cor_natural"](img))


def mapa_regra(agua, nuvem):
    out = np.empty(agua.shape + (3,), "uint8")
    out[:] = TERRA
    out[agua] = AGUA
    out[nuvem] = NUVEM
    return out


def esbatido(rgb_u8, quanto=0.6):
    return (rgb_u8 * (1 - quanto) + 255 * quanto).astype("uint8")


def figuras_de_dados(f):
    feitos = []
    os.chdir(PRATICA / "dados")
    ex = json.loads(open("exemplos_da_equipa.json").read())
    extra = dict(np.load(DADOS_SLIDES / "camadas_extra.npz"))
    cheia, seca = f["carregar"]("incomati_2026_cheia.npz"), f["carregar"](str(DADOS_SLIDES / "incomati_2026_seca.npz"))
    zona = seca["zona"]
    CAR = f["BANDAS"] + f["INDICES"]

    # 1. cor natural, seca e cheia
    feitos.append(guardar(cor(f, seca), "seca_2025_cor_natural.png"))
    feitos.append(guardar(cor(f, cheia), "cheia_2026_cor_natural.png"))

    # 2. o mapa do Workshop 1 (MNDWI > 0): água de sempre e água nova, fora da zona transparente
    a_seca = (seca["mndwi"] > 0) & zona & ~seca["nuvem"]
    nova = (cheia["mndwi"] > 0) & ~(seca["mndwi"] > 0) & zona & ~seca["nuvem"] & ~cheia["nuvem"]
    m = np.zeros(zona.shape + (4,), "uint8")
    m[zona] = (237, 231, 218, 255)
    m[a_seca] = (8, 46, 102, 255)
    m[nova] = (43, 181, 160, 255)
    m[zona & (seca["nuvem"] | cheia["nuvem"])] = (184, 184, 191, 255)
    feitos.append(guardar(m, "mapa_agua_2026_workshop1.png"))

    # 3. as regras falham: 2021 (NDWI) e 2024 (MNDWI), recorte do rio no sul; e o modelo da equipa
    X, y = f["exemplos"](cheia, ex["2026"]["agua"], ex["2026"]["nao_agua"], CAR)
    modelo = f["RandomForestClassifier"](n_estimators=100, random_state=0, n_jobs=-1).fit(X, y)
    # recortes de 460 x 380 píxeis onde o rio se vê melhor (mais rio JRC visível, menos nuvens)
    recortes = {2021: (slice(580, 1040), slice(110, 490)), 2024: (slice(650, 1110), slice(40, 420))}
    for ano, regra in [(2021, "ndwi"), (2024, "mndwi")]:
        rec = recortes[ano]
        img = f["carregar"](f"incomati_{ano}_chuvosa.npz")
        feitos.append(guardar(cor(f, img)[rec], f"regra_{ano}_cor_natural.png", 2))
        feitos.append(guardar(mapa_regra(img[regra] > 0, img["nuvem"])[rec], f"regra_{ano}_{regra}.png", 2))
        outra = "mndwi" if regra == "ndwi" else "ndwi"
        feitos.append(guardar(mapa_regra(img[outra] > 0, img["nuvem"])[rec], f"regra_{ano}_{outra}.png", 2))
        p = f["prever"](modelo, img, CAR)
        feitos.append(guardar(mapa_regra(p > 0.5, img["nuvem"])[rec], f"modelo_{ano}_so_2026.png", 2))
        xa, ya = f["exemplos"](img, ex[str(ano)]["agua"], ex[str(ano)]["nao_agua"], CAR)
        m2 = f["RandomForestClassifier"](n_estimators=100, random_state=0, n_jobs=-1).fit(np.concatenate([X, xa]), np.concatenate([y, ya]))
        p2 = f["prever"](m2, img, CAR)
        feitos.append(guardar(mapa_regra(p2 > 0.5, img["nuvem"])[rec], f"modelo_{ano}_ensinado.png", 2))

    # 4. os pontos da equipa (rótulos) sobre a cheia
    base = Image.fromarray(cor(f, cheia)).resize((735 * 2, 1110 * 2), Image.NEAREST)
    d = ImageDraw.Draw(base)
    for linha, coluna in ex["2026"]["agua"]:
        x, yy = coluna * 2, linha * 2
        d.ellipse([x - 18, yy - 18, x + 18, yy + 18], fill=(0, 229, 255), outline=(16, 35, 31), width=5)
    for linha, coluna in ex["2026"]["nao_agua"]:
        x, yy = coluna * 2, linha * 2
        d.rectangle([x - 16, yy - 16, x + 16, yy + 16], fill=(255, 165, 0), outline=(16, 35, 31), width=5)
    base.save(OUT / "rotulos_pontos_2026.png", optimize=True)
    feitos.append(OUT / "rotulos_pontos_2026.png")

    # 5. probabilidade de água (votos) e 6. mapa dos erros contra o exame EMS
    p = f["prever"](modelo, cheia, CAR)
    pr = np.zeros(zona.shape + (4,), "uint8")
    pr[..., :3] = u8(plt.get_cmap("Blues")(p)[..., :3])
    pr[..., 3] = 255
    pr[cheia["nuvem"]] = (*NUVEM, 255)
    pr[~zona] = (0, 0, 0, 0)
    feitos.append(guardar(pr, "probabilidade_2026.png"))
    ems = extra["ems_2026"]
    teste = (ems >= 0) & ~cheia["nuvem"]
    er = esbatido(cor(f, cheia), 0.65)
    prev = p > 0.5
    er[teste & (ems == 1) & prev] = (59, 115, 217)
    er[teste & (ems == 0) & ~prev] = (176, 170, 156)
    er[teste & (ems == 0) & prev] = (215, 38, 61)
    er[teste & (ems == 1) & ~prev] = (242, 140, 40)
    feitos.append(guardar(er, "erros_exame_2026.png"))

    # 7. o exame: as amostras do Copernicus EMS (com o leito do rio juntado)
    exm = esbatido(cor(f, cheia), 0.45)
    exm[ems == 1] = (59, 115, 217)
    exm[ems == 0] = (242, 140, 40)
    feitos.append(guardar(exm, "exame_ems_2026.png"))

    # 8. a cor da água: a pluma barrenta da foz na cheia e o mesmo sítio na seca
    rec2 = (slice(820, 1110), slice(120, 735))
    feitos.append(guardar(cor(f, cheia)[rec2], "cor_da_agua_cheia.png", 2))
    feitos.append(guardar(cor(f, seca)[rec2], "cor_da_agua_seca.png", 2))
    return feitos


def grafico_anos(ref):
    anos = list(ref["anos"])
    series = [("Regra NDWI > 0", "ndwi_rio", "#C5CDD6"), ("Regra MNDWI > 0", "mndwi_rio", "#7A8594"),
              ("IA treinada só com 2026", "antes_rio", "#1F5FA8"), ("IA ensinada com 5 + 5 pontos do ano", "depois_rio", "#E07B00")]
    fig, ax = plt.subplots(figsize=(16, 7.6), dpi=100, facecolor=FUNDO)
    ax.set_facecolor(FUNDO)
    x = np.arange(len(anos))
    w = 0.2
    for k, (nome, chave, c) in enumerate(series):
        v = [ref["anos"][a][chave] for a in anos]
        barras = ax.bar(x + (k - 1.5) * w, v, w * 0.92, color=c, label=nome)
        for b, val in zip(barras, v):
            if val < 60:
                ax.text(b.get_x() + b.get_width() / 2, val + 2, f"{val:.0f}", ha="center", fontsize=18, color=TINTA, fontweight="bold")
    ax.set_xticks(x, [f"{a}\n{ref['anos'][a]['satelite']}" for a in anos], fontsize=22)
    ax.set_ylabel("% do rio encontrado", fontsize=22)
    ax.set_ylim(0, 112)
    ax.legend(ncol=2, fontsize=19, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.2))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRELHA)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "ia_contra_regras_por_ano.png", facecolor=FUNDO)
    plt.close(fig)
    return OUT / "ia_contra_regras_por_ano.png"


def grafico_caudal():
    q = pd.read_csv(ROOT / "data/processed/series/hydromet_daily.csv", parse_dates=["date"],
                    usecols=["date", "discharge_m3s"]).set_index("date")["discharge_m3s"]["2025-12-20":"2026-02-15"].bfill()
    fig, ax = plt.subplots(figsize=(16, 7), dpi=100, facecolor=FUNDO)
    ax.set_facecolor(FUNDO)
    for lim, nome, c in [(164, "amarelo", "#B88A00"), (376, "laranja", "#E07B00"), (970, "vermelho", "#C0392B")]:
        ax.axhline(lim, color=c, lw=3, ls="--")
        ax.text(q.index[0], lim + 40, f"{nome}: {lim} m³/s", color=c, fontsize=22, fontweight="bold")
    ax.fill_between(q.index, q.values, color="#1F5FA8", alpha=0.15, lw=0)
    ax.plot(q.index, q.values, color=AZUL_ETE, lw=4)
    pico = q.idxmax()
    ax.annotate(f"pico {q.max():.0f} m³/s\n19 jan", (pico, q.max()), xytext=(25, -10), textcoords="offset points",
                fontsize=22, fontweight="bold", color=TINTA, va="top")
    img = pd.Timestamp("2026-01-24")
    ax.scatter([img], [q[img]], s=180, color=TINTA, zorder=5)
    ax.annotate("imagem Sentinel-2\n24 jan", (img, q[img]), xytext=(18, 10), textcoords="offset points", fontsize=20, color=SUAVE)
    ax.set_ylabel("Caudal (m³/s)", fontsize=22)
    ax.set_ylim(0, 3400)
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 15]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRELHA)
    fig.tight_layout()
    fig.savefig(OUT / "caudal_cheia_2026.png", facecolor=FUNDO)
    plt.close(fig)
    return OUT / "caudal_cheia_2026.png"


def grafico_ndti():
    s = pd.read_csv(ROOT / "plataforma/dados/qualidade/serie_mensal.csv")
    q = s[s["troco"] == "Q8"].dropna(subset=["ndti"]).copy()
    q["data"] = pd.to_datetime(q["month"])
    q["anomalia"] = q["ndti"] - q["mes_do_ano"].map(q.groupby("mes_do_ano")["ndti"].median())
    fig, ax = plt.subplots(figsize=(16, 6.4), dpi=100, facecolor=FUNDO)
    ax.set_facecolor(FUNDO)
    ax.bar(q["data"], q["anomalia"], width=28, color=np.where(q["anomalia"] > 0, "#8B5A2B", "#1F5FA8"))
    ax.axhline(0, color=TINTA, lw=1.5)
    ax.set_ylabel("NDTI acima ou abaixo\ndo normal do mês", fontsize=20)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.grid(axis="y", color=GRELHA)
    fig.tight_layout()
    fig.savefig(OUT / "turbidez_anomalias_marracuene.png", facecolor=FUNDO)
    plt.close(fig)
    return OUT / "turbidez_anomalias_marracuene.png"


def mapa_trocos():
    gpkg = ROOT / "data/interim/water_quality/trocos_rio.gpkg"
    linhas = gpd.read_file(gpkg, layer="linhas").to_crs(4326)
    bacia = gpd.read_file(ROOT / "data/raw/aoi/incomati_basin.geojson").to_crs(4326)
    rios = gpd.read_file(ROOT / "data/raw/static/hydrography/rivers_incomati.geojson").to_crs(4326)
    distrito = gpd.read_file(ROOT / "data/raw/aoi/marracuene_district.geojson").to_crs(4326)
    fig, ax = plt.subplots(figsize=(14, 10), dpi=100, facecolor=FUNDO)
    ax.set_facecolor(FUNDO)
    bacia.plot(ax=ax, color="#E3EBE2", edgecolor="#B8C8BD", lw=1)
    rios.cx[31.8:33.2, -26.0:-24.8].plot(ax=ax, color="#9FBFC4", lw=0.8)
    distrito.plot(ax=ax, color="#E8893A", alpha=0.22, edgecolor="#E8893A", lw=2)
    cmap = plt.get_cmap("viridis")
    halo = [patheffects.withStroke(linewidth=5, foreground="white")]
    for _, r in linhas.iterrows():
        c = cmap((r.numero - 1) / 8)
        if r.geometry.geom_type.endswith("Point"):
            ax.scatter(r.geometry.x, r.geometry.y, s=500, color=c, zorder=5, edgecolor="white", lw=2)
            ponto = r.geometry
        else:
            gpd.GeoSeries([r.geometry]).plot(ax=ax, color=c, lw=8, zorder=4)
            ponto = r.geometry.interpolate(0.5, normalized=True)
        ax.text(ponto.x + 0.035, ponto.y, r.troco, fontsize=26, fontweight="bold", color=TINTA, zorder=6, path_effects=halo)
    ax.text(32.36, -25.74, "Marracuene", fontsize=24, color="#A04A00", fontweight="bold", path_effects=halo)
    ax.text(31.88, -25.47, "Ressano Garcia\n(fronteira)", fontsize=20, color=SUAVE, path_effects=halo)
    ax.set_xlim(31.85, 33.15)
    ax.set_ylim(-25.95, -24.9)
    ax.set_aspect(1 / np.cos(np.radians(25.4)))
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "trocos_do_rio.png", facecolor=FUNDO)
    plt.close(fig)
    return OUT / "trocos_do_rio.png"


def capturas_da_plataforma():
    pasta = ROOT / "reports/plataforma"
    cortes = {"plataforma_inicio.png": ("v8/v8_inicio.png", 0), "plataforma_cheias.png": ("v4/3_cheias.png", 0),
              "plataforma_agua.png": ("v4/2_agua_do_rio.png", 0), "plataforma_mapa.png": ("v4/4_mapa.png", 0),
              "plataforma_alertas.png": ("v6/v6_alertas.png", 0), "plataforma_conselhos.png": ("v8/v8_conselhos.png", 0)}
    feitos = []
    for nome, (origem, topo) in cortes.items():
        im = Image.open(pasta / origem).convert("RGB")
        im = im.crop((0, topo, im.width, topo + round(im.width * 9 / 16)))
        im.save(OUT / nome, optimize=True)
        feitos.append(OUT / nome)
    return feitos


def logotipos():
    """ETE em círculo; IAU-OAD e DARA nas cores originais e num só tom, claro (fundo escuro) e escuro (fundo claro).
    O original da IAU-OAD tem o texto a branco: em fundo claro usa-se logo_oad_escuro."""
    feitos = []
    im = Image.open(ROOT / "logos/ETE_Log.jpeg").convert("RGB")
    w, h = im.size
    r = min(w, h) / 2 - 30
    mascara = Image.new("L", (w * 4, h * 4), 0)
    ImageDraw.Draw(mascara).ellipse([(w / 2 - r) * 4, (h / 2 - r) * 4, (w / 2 + r) * 4, (h / 2 + r) * 4], fill=255)
    im = im.convert("RGBA")
    im.putalpha(mascara.resize((w, h), Image.LANCZOS))
    im.crop((int(w / 2 - r), int(h / 2 - r), int(w / 2 + r), int(h / 2 + r))).resize((600, 600), Image.LANCZOS).save(OUT / "logo_ete.png")
    feitos.append(OUT / "logo_ete.png")
    for nome, ficheiro in [("oad", "01_IAU-OAD_transparent.png"), ("dara", "DARA_logo.avif")]:
        im = Image.open(ROOT / "logos" / ficheiro).convert("RGBA")
        im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
        im = im.resize((round(im.width * 300 / im.height), 300), Image.LANCZOS)
        im.save(OUT / f"logo_{nome}.png")
        for sufixo, tom in (("claro", (247, 243, 234, 255)), ("escuro", (16, 35, 31, 255))):
            mono = Image.new("RGBA", im.size, tom)
            mono.putalpha(im.getchannel("A"))
            mono.save(OUT / f"logo_{nome}_{sufixo}.png")
            feitos.append(OUT / f"logo_{nome}_{sufixo}.png")
        feitos.append(OUT / f"logo_{nome}.png")
    return feitos


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ref = json.loads((FAC / "resultados_de_referencia.json").read_text(encoding="utf-8"))
    f = ferramentas_namespace()
    feitos = figuras_de_dados(f)
    feitos += [grafico_anos(ref), grafico_caudal(), grafico_ndti(), mapa_trocos()]
    feitos += capturas_da_plataforma() + logotipos()
    for p in feitos:
        im = Image.open(p)
        print(f"{p.name:40s} {im.size[0]:5d} x {im.size[1]:5d}  {p.stat().st_size / 1024:6.0f} KB")
    print(len(feitos), "imagens")


if __name__ == "__main__":
    main()
