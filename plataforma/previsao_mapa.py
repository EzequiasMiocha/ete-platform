"""Desenha os mapas da cor da água prevista, com numpy e Pillow (nada mais).

O modelo do mapa (src/ete/water_colour_model.py) diz, para cada píxel de 20 m do rio:
    cor do píxel = a + b x (cor do rio em Marracuene) + c x (maré)
A cor prevista para Marracuene vem do boletim diário (boletim/cor_prevista.csv). Aqui só se faz a
conta píxel a píxel, se escolhe o degrau de cor e se junta o fundo (terra) e os nomes por cima.
Os ficheiros estão em dados/modelos/ (mapa_cor_modelo.npz, mapa_cor_fundo.png, mapa_cor_letras.png).
O passado usa os mesmos píxeis: mapa_cor_meses.npz tem o degrau de cada píxel do rio em cada mês desde
2017 (a mediana das imagens do mês), e meses_resumo.csv a cor de Marracuene e o caudal desse mês.
"""

from __future__ import annotations

import io
from functools import lru_cache

import numpy as np
from PIL import Image

import leitor

CORES = ("#1D6B8F", "#6FAFC9", "#E3D5A8", "#C08A45", "#6F3B14")      # as cinco cores do mapa observado (turbidity_map.CLASSES)
NOMES = ("muito clara", "clara", "habitual", "turva", "muito turva")


def existe() -> bool:
    pasta = leitor.DADOS / "modelos"
    return all((pasta / f).is_file() for f in ("mapa_cor_modelo.npz", "mapa_cor_fundo.png", "mapa_cor_letras.png"))


@lru_cache(maxsize=1)
def _camadas(versao: float):
    pasta = leitor.DADOS / "modelos"
    m = np.load(pasta / "mapa_cor_modelo.npz")
    modelo = {k: m[k].astype("float32") for k in ("a", "b", "c", "steps")} | {"ok": m["ok"]}
    return modelo, Image.open(pasta / "mapa_cor_fundo.png").convert("RGBA"), Image.open(pasta / "mapa_cor_letras.png").convert("RGBA")


def classe(ndti: float) -> str:
    """O degrau de cor de um valor do índice (os mesmos degraus do mapa observado)."""
    modelo, _, _ = _camadas(_versao())
    return NOMES[int(np.digitize([ndti], modelo["steps"])[0])]


SEM_LEITURA = "#B4B9BE"


def _compor(degrau: np.ndarray, ok: np.ndarray) -> bytes:
    """Pinta cada píxel do rio com o seu degrau (0-4; 5 = sem leitura) e junta o fundo e os nomes."""
    _, fundo, letras = _camadas(_versao())
    pintado = np.zeros(degrau.shape + (4,), "uint8")
    for k, cor in enumerate(CORES + (SEM_LEITURA,)):
        pintado[(degrau == k) & ok] = (int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16), 255)
    rio = Image.fromarray(pintado, "RGBA").resize(fundo.size, Image.NEAREST)
    imagem = Image.alpha_composite(Image.alpha_composite(fundo, rio), letras).convert("RGB")
    saida = io.BytesIO()
    imagem.quantize(colors=96, method=Image.Quantize.MEDIANCUT).save(saida, "PNG", optimize=True)
    return saida.getvalue()


def _versao() -> float:
    return (leitor.DADOS / "modelos" / "mapa_cor_modelo.npz").stat().st_mtime


def desenhar(ndti_marracuene: float, mare_m: float) -> bytes:
    """O mapa previsto (PNG) para uma cor de Marracuene e uma maré."""
    modelo, _, _ = _camadas(_versao())
    valor = modelo["a"] + modelo["b"] * ndti_marracuene + modelo["c"] * mare_m
    return _compor(np.digitize(valor, modelo["steps"]), modelo["ok"])


# ----------------------------------------------------------------------------- o passado: um mapa por mês desde 2017
def ha_meses() -> bool:
    return existe() and (leitor.DADOS / "modelos" / "mapa_cor_meses.npz").is_file()


@lru_cache(maxsize=1)
def _meses(versao: float):
    z = np.load(leitor.DADOS / "modelos" / "mapa_cor_meses.npz")
    return [str(m) for m in z["meses"]], z["codigos"]


def meses() -> list[str]:
    """Os meses com mapa ('AAAA-MM'), do mais antigo ao mais recente."""
    return _meses((leitor.DADOS / "modelos" / "mapa_cor_meses.npz").stat().st_mtime)[0]


def desenhar_mes(mes: str) -> bytes:
    """O mapa observado de um mês: a mediana das imagens do mês, píxel a píxel (cinzento = sem leitura)."""
    modelo, _, _ = _camadas(_versao())
    nomes, codigos = _meses((leitor.DADOS / "modelos" / "mapa_cor_meses.npz").stat().st_mtime)
    degrau = np.full(modelo["ok"].shape, 255, "uint8")
    degrau[modelo["ok"]] = codigos[nomes.index(mes)]
    return _compor(degrau, modelo["ok"])
