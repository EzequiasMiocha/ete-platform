"""Dados leves para a aula prática do Workshop 1 (ficheiros .npz que só precisam de numpy).

    .venv/bin/python scripts/build_workshop_data.py

Lê as imagens de data/raw/optical/workshop_1/ (scripts/download_workshop_scenes.py) e escreve:
  Pratica_Workshop_1/2_aula_guiada/dados/      2026: seca, cheia e o recorte 10 m vs 30 m
  Pratica_Workshop_1/3_exercicios/ano_AAAA/dados/   seca e chuvosa de cada ano
  Pratica_Workshop_1/0_facilitadores/respostas_de_referencia.json   (as contas feitas com o mesmo código dos estudantes)

Cada .npz tem as bandas azul, verde, vermelho, nir, swir em números inteiros (reflectância x 10 000,
uint16), `nuvem` (True = nuvem, sombra ou sem dados), `zona` (True = dentro do distrito de
Marracuene e fora do mar), a data, o satélite, o caudal do rio nesse dia e o pico do ano.

A `zona` corrige o erro do notebook original: sem ela, o mar entra nas contas como "água"
e esconde a cheia (14 487 ha na seca contra 14 461 ha na "cheia").
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from download_workshop_scenes import SCENES  # noqa: E402

RAW = ROOT / "data/raw/optical/workshop_1"
OUT = ROOT / "workshops" / "Pratica_Workshop_1"
BANDS = ["azul", "verde", "vermelho", "nir", "swir"]
NOMES_SATELITE = {"landsat": "Landsat 8", "sentinel2": "Sentinel-2"}
GUIA = 2026


def caudal():
    q = pd.read_csv(ROOT / "data/processed/series/hydromet_daily.csv", parse_dates=["date"],
                    usecols=["date", "discharge_m3s"]).set_index("date")["discharge_m3s"]
    return q


def ler(ficheiro: Path):
    with rasterio.open(ficheiro) as src:
        b = {n: src.read(i + 1) for i, n in enumerate(src.descriptions)}
        nodata = b["azul"] == src.nodata
        transform, crs, shape, bounds = src.transform, src.crs, (src.height, src.width), src.bounds
    out = {k: np.clip(b[k], 0, 10000).astype("uint16") for k in BANDS}
    for k in BANDS:
        out[k][nodata] = 0
    out["nuvem"] = nodata | (b["nuvem"] != 0)
    return out, transform, crs, shape, bounds


def mar(img) -> np.ndarray:
    """Mar = água (MNDWI > 0) ligada à borda leste da imagem. O rio não toca nessa borda."""
    v, s = img["verde"].astype(float), img["swir"].astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        agua = ((v - s) / (v + s)) > 0
    rotulos, _ = ndimage.label(agua)
    borda = np.unique(rotulos[:, -1][rotulos[:, -1] > 0])
    return ndimage.binary_closing(np.isin(rotulos, borda), iterations=3)


def indices(img):
    """Exactamente as contas que os estudantes fazem (reflectância = inteiro / 10 000)."""
    r = {k: img[k] / 10000 for k in BANDS}
    with np.errstate(divide="ignore", invalid="ignore"):
        ndwi = (r["verde"] - r["nir"]) / (r["verde"] + r["nir"])
        mndwi = (r["verde"] - r["swir"]) / (r["verde"] + r["swir"])
    return ndwi, mndwi


def guardar(destino: Path, img, zona, info):
    destino.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(destino, **{k: img[k] for k in BANDS}, nuvem=img["nuvem"], zona=zona, **info)
    return destino.stat().st_size / 1e6


def recorte_10m_30m():
    """A mesma zona agrícola a 10 m (Sentinel-2A, 23 out 2025) e a 30 m (Landsat 9, 22 set 2025): só cor natural."""
    from pyproj import Transformer
    campo = (32.765, -25.515, 32.815, -25.470)
    t = Transformer.from_crs(4326, "EPSG:32736", always_xy=True)
    (x0, y0), (x1, y1) = t.transform(campo[0], campo[1]), t.transform(campo[2], campo[3])
    out = {}
    pasta = ROOT / "data/raw/optical/cenas_cheia_2026"
    for nome, ficheiro in [("s2_10m", "sentinel2_antes_2025-10-23_zona_agricola_10m.tif"),
                           ("landsat_30m", "landsat_antes_2025-09-22_30m.tif")]:
        with rasterio.open(pasta / ficheiro) as src:
            win = from_bounds(x0, y0, x1, y1, src.transform).round_offsets().round_lengths()
            for banda, chave in [("red", "vermelho"), ("green", "verde"), ("blue", "azul")]:
                i = list(src.descriptions).index(banda) + 1
                out[f"{nome}_{chave}"] = np.clip(src.read(i, window=win), 0, 10000).astype("uint16")
    destino = OUT / "2_aula_guiada/dados/zona_agricola_10m_e_30m.npz"
    np.savez_compressed(destino, **out, data_s2="2025-10-23", data_landsat="2025-09-22",
                        nota="Sentinel-2A a 10 m e Landsat 9 a 30 m, zona agrícola a norte da vila (5 x 5 km)")
    return destino.stat().st_size / 1e6


def main() -> None:
    q = caudal()
    dist = gpd.read_file(ROOT / "data/raw/aoi/marracuene_district.geojson").to_crs(32736)
    respostas = {}
    for ano, (sensor, data_seca, data_chuvosa) in SCENES.items():
        g = q[f"{ano - 1}-10-01":f"{ano}-09-30"]
        pico_data, pico = g.idxmax(), float(g.max())
        seca, transform, crs, shape, bounds = ler(RAW / f"{ano}_seca_{sensor}_{data_seca}_30m.tif")
        chuvosa, *_ = ler(RAW / f"{ano}_chuvosa_{sensor}_{data_chuvosa}_30m.tif")
        no_distrito = geometry_mask(dist.geometry, shape, transform, invert=True)
        zona = no_distrito & ~mar(seca)
        comum = {"satelite": NOMES_SATELITE[sensor], "resolucao_m": 30, "ano": ano,
                 "caudal_pico_m3s": round(pico), "data_pico": str(pico_data.date()),
                 "crs": str(crs), "limites_utm": np.array(bounds)}
        if ano == GUIA:
            pasta, nomes = OUT / "2_aula_guiada/dados", (f"incomati_{ano}_seca.npz", f"incomati_{ano}_cheia.npz")
        else:
            pasta, nomes = OUT / f"3_exercicios/ano_{ano}/dados", (f"incomati_{ano}_seca.npz", f"incomati_{ano}_chuvosa.npz")
        tamanhos = []
        for img, data, nome, epoca in [(seca, data_seca, nomes[0], "seca"), (chuvosa, data_chuvosa, nomes[1], "chuvosa")]:
            info = comum | {"data": data, "epoca": epoca, "caudal_m3s": round(float(q[data]), 1)}
            tamanhos.append(guardar(pasta / nome, img, zona, info))

        # respostas de referência: o mesmo código que os estudantes correm
        ndwi0, mndwi0 = indices(seca)
        ndwi1, mndwi1 = indices(chuvosa)
        ok0, ok1 = zona & ~seca["nuvem"], zona & ~chuvosa["nuvem"]
        ha = 30 * 30 / 10000
        r = {
            "ano": ano, "satelite": NOMES_SATELITE[sensor], "data_seca": data_seca, "data_chuvosa": data_chuvosa,
            "caudal_seca": round(float(q[data_seca]), 1), "caudal_chuvosa": round(float(q[data_chuvosa])),
            "caudal_pico": round(pico), "data_pico": str(pico_data.date()),
            "area_pixel_ha": ha,
            "nuvem_seca_pct": round(100 * seca["nuvem"][zona].mean(), 1),
            "nuvem_chuvosa_pct": round(100 * chuvosa["nuvem"][zona].mean(), 1),
            "agua_seca_ha": round(float(((mndwi0 > 0) & ok0).sum() * ha)),
            "agua_chuvosa_ha": round(float(((mndwi1 > 0) & ok1).sum() * ha)),
            "agua_nova_ha": round(float(((mndwi1 > 0) & ~(mndwi0 > 0) & ok0 & ok1).sum() * ha)),
            "ndwi_agua_seca_ha": round(float(((ndwi0 > 0) & ok0).sum() * ha)),
            "ndwi_agua_chuvosa_ha": round(float(((ndwi1 > 0) & ok1).sum() * ha)),
            "ndwi_agua_nova_ha": round(float(((ndwi1 > 0) & ~(ndwi0 > 0) & ok0 & ok1).sum() * ha)),
            "zona_ha": round(float(zona.sum() * ha)),
            "pixeis": int(zona.size), "forma": list(shape), "mb": round(sum(tamanhos), 1),
        }
        respostas[ano] = r
        print(f"{ano}  {r['satelite']:10s} seca {data_seca} chuvosa {data_chuvosa}  nuvem {r['nuvem_chuvosa_pct']:5.1f}%  "
              f"água {r['agua_seca_ha']:6d} -> {r['agua_chuvosa_ha']:6d} ha  nova {r['agua_nova_ha']:6d} ha  "
              f"(NDWI nova {r['ndwi_agua_nova_ha']:6d})  {r['mb']} MB")
    print(f"recorte 10 m vs 30 m: {recorte_10m_30m():.1f} MB")
    destino = OUT / "0_facilitadores/respostas_de_referencia.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(respostas, indent=1, ensure_ascii=False), encoding="utf-8")
    print("respostas:", destino.relative_to(ROOT))


if __name__ == "__main__":
    main()
