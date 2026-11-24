"""Dados da prática do Workshop 2 (IA para monitorizar a água e avisar das cheias).

    .venv/bin/python scripts/build_workshop2_data.py

Não descarrega nada: reaproveita as imagens do Workshop 1 (Pratica_Workshop_1/, que vêm de
scripts/download_workshop_scenes.py), o terreno do projecto e os rótulos do Copernicus EMS.
Escreve em Workshop_2/2_pratica/dados/ SÓ o que as aulas usam (build_workshop2_aulas.py confirma-o):

  incomati_2026_cheia.npz                           a imagem da cheia de 24/01/2026 (Sentinel-2, 30 m): Aulas 1 e 2, Prática 2
  incomati_AAAA_chuvosa.npz                         um dia de chuvas de cada ano do par (2014, 2021, 2022, 2024, 2025): Prática 1
  mapa_oficial_cheia_2026.npz                       rotulo: 1 água, 0 não água, -1 sem rótulo. Amostras do Copernicus EMS
                                                    (EMSR857), feitas por especialistas: o exame da Aula 2 e da Prática 2
  exemplos_da_equipa.json                           os pontos de exemplo (linha, coluna) de cada imagem: água e não água
  caudal_e_chuva_diarios.csv                        caudal e chuva diários, 2006-2026 (Tema 4)
  cor_do_rio_e_mare.csv                             a turbidez (NDTI) de 3 troços e a maré à hora do satélite (Tema 3)

Em data/interim/workshop2/ (fora da pasta dos alunos) guarda o que só serve para refazer figuras antigas dos
slides (workshop2/figuras.py, workshop2/referencia.py): incomati_2026_seca.npz e camadas_extra.npz (terreno,
ems_2026, verif_agua = JRC >= 90 %, verif_terra = HAND >= 10 m e JRC = 0).
"""

import json
import shutil
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
WS1 = ROOT / "workshops" / "Pratica_Workshop_1"
WS2 = ROOT / "workshops" / "Workshop_2"
DADOS = WS2 / "2_pratica/dados"
DADOS_SLIDES = ROOT / "data/interim/workshop2"      # fora da pasta dos alunos: só para refazer figuras antigas dos slides
OBSOLETOS = ["incomati_2026_seca.npz", "camadas_extra.npz"]   # estavam na pasta dos alunos e nenhuma aula os usa
ANOS_TESTE = [2014, 2021, 2022, 2024, 2025]
RAIO = 2              # cada ponto marcado vale um quadrado de 5 x 5 píxeis (150 m x 150 m)


def copiar_imagens():
    DADOS.mkdir(parents=True, exist_ok=True)
    DADOS_SLIDES.mkdir(parents=True, exist_ok=True)
    shutil.copy(WS1 / "2_aula_guiada/dados/incomati_2026_seca.npz", DADOS_SLIDES)
    shutil.copy(WS1 / "2_aula_guiada/dados/incomati_2026_cheia.npz", DADOS)
    for ano in ANOS_TESTE:
        shutil.copy(WS1 / f"3_exercicios/ano_{ano}/dados/incomati_{ano}_chuvosa.npz", DADOS)


def camadas_extra():
    """Terreno, rótulos EMS e máscaras de verificação, na mesma grelha das imagens (735 x 1110, 30 m).

    Para os alunos vai só o mapa oficial (mapa_oficial_cheia_2026.npz); o resto fica em data/interim/workshop2/."""
    ref = ROOT / "data/raw/optical/workshop_1/2026_chuvosa_sentinel2_2026-01-24_30m.tif"
    with rasterio.open(ref) as src:
        transform, shape = src.transform, (src.height, src.width)
    with rasterio.open(ROOT / "data/interim/features/static_stack_marracuene_30m.tif") as st:
        lin0 = round((st.transform.f - transform.f) / 30)
        col0 = round((transform.c - st.transform.c) / 30)
        janela = (slice(lin0, lin0 + shape[0]), slice(col0, col0 + shape[1]))
        nomes = list(st.descriptions)

        def camada(nome):
            v = st.read(nomes.index(nome) + 1)[janela].astype("float32")
            v[v < -1000] = np.nan
            return v

        hand, altitude, declive, jrc = camada("hand"), camada("elevation"), camada("slope"), camada("jrc_occurrence")
    zona = np.load(DADOS / "incomati_2026_cheia.npz")["zona"]           # a mesma zona da imagem da seca
    g = gpd.read_file(ROOT / "data/raw/labels/ems_unosat/ems_labels.gpkg").to_crs(32736)
    ems = rasterize([(geom, 0) for geom in g[g["class"] == "non_water"].geometry], out_shape=shape,
                    transform=transform, fill=-1, dtype="int16")
    agua = rasterize([(geom, 1) for geom in g[g["class"] == "water"].geometry], out_shape=shape,
                     transform=transform, fill=0, dtype="uint8")
    ems[agua == 1] = 1
    # O EMS mapeia só a água DA CHEIA, não a água de sempre: as amostras "não água" caíram em cima do leito
    # normal do rio (99% dos "falsos alarmes" do modelo estavam aí). Onde o arquivo JRC viu água na maior parte
    # das observações de 1984-2021, o rio estava lá a 24 jan 2026: o rótulo passa a "água".
    corrigidos = int(((ems == 0) & (np.nan_to_num(jrc) >= 50)).sum())
    ems[(ems == 0) & (np.nan_to_num(jrc) >= 50)] = 1
    verif_agua = (np.nan_to_num(jrc) >= 90) & zona
    verif_terra = (np.nan_to_num(hand) >= 10) & (np.nan_to_num(jrc, nan=1) == 0) & zona
    np.savez_compressed(DADOS / "mapa_oficial_cheia_2026.npz", rotulo=ems.astype("int8"),
                        nota=("O mapa oficial da cheia de 24/01/2026 (Copernicus EMS, activação EMSR857), feito por "
                              "especialistas. rotulo: 1 = água, 0 = não água, -1 = sem rótulo. Onde o mapa dizia não água "
                              "em cima do leito normal do rio (água em 50 % ou mais das observações JRC de 1984-2021), o "
                              "rótulo passou a água: o mapa oficial só desenha a água da cheia."))
    np.savez_compressed(DADOS_SLIDES / "camadas_extra.npz", hand=hand, altitude=altitude, declive=declive,
                        ems_2026=ems.astype("int8"), verif_agua=verif_agua, verif_terra=verif_terra,
                        nota=("ems_2026: amostras Copernicus EMS EMSR857 (1 água, 0 não água, -1 sem rótulo), com o leito "
                              "permanente do rio (JRC >= 50%) passado a água; verif_agua: JRC >= 90%; "
                              "verif_terra: HAND >= 10 m e JRC = 0"))
    return dict(ems_agua=int((ems == 1).sum()), ems_terra=int((ems == 0).sum()), ems_rio_corrigido=corrigidos,
                verif_agua=int(verif_agua.sum()), verif_terra=int(verif_terra.sum()))


def indices(z):
    b = {k: z[k] / 10000 for k in ("azul", "verde", "vermelho", "nir", "swir")}
    with np.errstate(divide="ignore", invalid="ignore"):
        b["ndwi"] = (b["verde"] - b["nir"]) / (b["verde"] + b["nir"])
        b["mndwi"] = (b["verde"] - b["swir"]) / (b["verde"] + b["swir"])
        b["ndvi"] = (b["nir"] - b["vermelho"]) / (b["nir"] + b["vermelho"])
    return b


def escolher(mascara, n, rng, distancia_min=40, ja=(), margem=RAIO + 1):
    """n pontos dentro da máscara (longe da borda `margem` píxeis), afastados entre si pelo menos distancia_min."""
    cand = np.argwhere(ndimage.binary_erosion(mascara, iterations=margem))
    rng.shuffle(cand)
    escolhidos = list(ja)
    novos = []
    for p in cand:
        if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) >= distancia_min for q in escolhidos):
            escolhidos.append(tuple(p))
            novos.append((int(p[0]), int(p[1])))
            if len(novos) == n:
                break
    return novos


def exemplos_da_equipa(extra):
    """Pontos da equipa: variados, como um bom par faria (vários tipos de água e de terra)."""
    rng = np.random.default_rng(2026)
    z = np.load(DADOS / "incomati_2026_cheia.npz")
    b = indices(z)
    vista = z["zona"] & ~z["nuvem"]
    jrc_rio = extra["verif_agua"]
    agua = (escolher(vista & (b["mndwi"] > 0.4) & ~jrc_rio & (b["vermelho"] > 0.08), 8, rng)        # cheia barrenta
            + escolher(vista & jrc_rio & (b["mndwi"] > 0.2), 4, rng)                                # rio
            + escolher(vista & (b["mndwi"] > 0.3) & (b["vermelho"] < 0.05), 3, rng))                # água escura (lagoas)
    # na imagem da cheia quase tudo o que se vê é água: as manchas de terra são pequenas, daí margem=1
    terra = (escolher(vista & (b["ndvi"] > 0.55), 6, rng)                                                       # vegetação densa
             + escolher(vista & (b["ndvi"] > 0.2) & (b["ndvi"] < 0.45) & (b["mndwi"] < -0.2), 4, rng, margem=1)  # campos e mato
             + escolher(vista & (b["ndvi"] < 0.3) & (b["vermelho"] > 0.09) & (b["mndwi"] < -0.05), 3, rng, margem=1)  # solo claro e areia
             + escolher(vista & (b["ndvi"] > 0.15) & (b["ndvi"] < 0.35) & (b["vermelho"] > 0.07), 2, rng, margem=1))  # vila e mato seco
    exemplos = {"2026": {"agua": agua, "nao_agua": terra}}
    for ano in ANOS_TESTE:
        zy = np.load(DADOS / f"incomati_{ano}_chuvosa.npz")
        by = indices(zy)
        vy = zy["zona"] & ~zy["nuvem"]
        exemplos[str(ano)] = {
            "agua": escolher(vy & extra["verif_agua"], 5, rng, 60),
            "nao_agua": escolher(vy & ~extra["verif_agua"] & (np.nan_to_num(extra["hand"]) < 5) & (by["ndvi"] > 0.3) & (by["mndwi"] < -0.1), 5, rng, 60),
        }
    return exemplos


def caudal_e_chuva():
    """Série diária para a regressão (Parte F): caudal do Incomáti em Marracuene (GloFAS) e chuva na bacia (CHIRPS)."""
    series = ROOT / "data/processed/series"
    q = pd.read_csv(series / "hydromet_daily.csv", parse_dates=["date"], usecols=["date", "discharge_m3s"])
    c = pd.read_csv(series / "rain_daily.csv", parse_dates=["date"],
                    usecols=["date", "rain_basin", "p7_basin", "p14_basin", "p30_basin"])
    d = q.merge(c, on="date").dropna().sort_values("date")
    d = d.rename(columns={"date": "data", "discharge_m3s": "caudal_m3s", "rain_basin": "chuva_dia_mm",
                          "p7_basin": "chuva_7d_mm", "p14_basin": "chuva_14d_mm", "p30_basin": "chuva_30d_mm"})
    d["data"] = d["data"].dt.strftime("%Y-%m-%d")
    destino = DADOS / "caudal_e_chuva_diarios.csv"
    d.round(1).to_csv(destino, index=False)
    print(destino.name, len(d), "dias,", d["data"].iloc[0], "a", d["data"].iloc[-1])
    return destino


TROCOS_MARE = {"2 troço médio": "troço médio", "3 jusante": "jusante", "4 foz / estuário": "foz"}


def cor_do_rio_e_mare():
    """Tabela do Tema 3 (a cor do rio e a maré): uma linha por manhã com imagem Sentinel-2 limpa e por troço.

    Vem da mesma tabela que treina o modelo de turbidez do projecto (forecast_models.tide_model_table):
    ndti        o índice de turbidez do troço (NDTI = (vermelho - verde) / (vermelho + verde)): mais alto = mais barrenta
    caudal_m3s  o caudal do Incomáti nesse dia (GloFAS); chuva_7d_mm: a chuva na bacia nos 7 dias anteriores
    altura_da_mare_m  a maré calculada na baía de Maputo à hora do satélite (models/mare_maputo.json), em metros
    turva       1 quando o NDTI está acima da mediana desse troço em 2017-2022 (os anos de treino da aula)
    """
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from ete.config import load_config
    from ete.forecast_models import tide_model_table

    d = tide_model_table(load_config())
    t = pd.DataFrame({"data": d["date"].dt.strftime("%Y-%m-%d"), "ano": d["date"].dt.year, "mes": d["date"].dt.month,
                      "troco": d["troco"].map(TROCOS_MARE), "ndti": d["ndti"].round(3), "caudal_m3s": d["q"].round(1),
                      "chuva_7d_mm": d["p7"].round(1), "altura_da_mare_m": d["t_h"].round(2)})
    assert t["troco"].notna().all(), "troço desconhecido na tabela da maré"
    mediana = t[t["ano"] <= 2022].groupby("troco")["ndti"].median()
    t["turva"] = (t["ndti"] > t["troco"].map(mediana)).astype(int)
    t = t.sort_values(["data", "troco"]).reset_index(drop=True)
    destino = DADOS / "cor_do_rio_e_mare.csv"
    t.to_csv(destino, index=False)
    print(destino.name, len(t), "manhãs x troço,", t["data"].iloc[0], "a", t["data"].iloc[-1],
          "| medianas 2017-2022:", mediana.round(3).to_dict())
    return destino


def main() -> None:
    copiar_imagens()
    caudal_e_chuva()
    cor_do_rio_e_mare()
    resumo = camadas_extra()
    extra = dict(np.load(DADOS_SLIDES / "camadas_extra.npz"))
    for nome in OBSOLETOS:
        (DADOS / nome).unlink(missing_ok=True)
    exemplos = exemplos_da_equipa(extra)
    (DADOS / "exemplos_da_equipa.json").write_text(json.dumps(exemplos, indent=1), encoding="utf-8")
    tamanhos = {f.name: round(f.stat().st_size / 1e6, 1) for f in sorted(DADOS.glob("*"))}
    print(json.dumps(resumo), json.dumps(tamanhos), sep="\n")
    print({k: (len(v["agua"]), len(v["nao_agua"])) for k, v in exemplos.items()})


if __name__ == "__main__":
    main()
