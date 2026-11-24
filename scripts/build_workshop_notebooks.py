"""Gera todo o material da aula prática do Workshop 1 em Pratica_Workshop_1/.

    .venv/bin/python scripts/build_workshop_data.py        # primeiro: os dados (.npz) e as respostas
    .venv/bin/python scripts/build_workshop_notebooks.py   # depois: notebooks, textos e imagens dos slides
    .venv/bin/python scripts/test_workshop.py              # por fim: corre tudo como um aluno

Os notebooks são gerados aqui: não os edite à mão (as alterações perdem-se na próxima geração).
O texto de cada ano (história, desafio, resposta) está em scripts/workshop/exercicios.py.
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workshop import documentos, exercicios, extras, guia, guia_completo, introducao  # noqa: E402
from workshop.comum import AULA  # noqa: E402


def imagens_para_slides():
    """Falsa cor e índices de 2026 para os Módulos 3 e 4 (lista de preparação do plano)."""
    pasta = AULA / "0_facilitadores/imagens_para_slides"
    pasta.mkdir(parents=True, exist_ok=True)
    img = {}
    for epoca, nome in [("seca", "incomati_2026_seca.npz"), ("cheia", "incomati_2026_cheia.npz")]:
        z = np.load(AULA / "2_aula_guiada/dados" / nome)
        img[epoca] = ({b: z[b] / 10000 for b in ("azul", "verde", "vermelho", "nir", "swir")}, str(z["data"]))
    feitos = []

    b, data = img["seca"]
    plt.figure(figsize=(7, 10))
    plt.imshow(np.clip(np.dstack([b["nir"], b["vermelho"], b["verde"]]) / 0.35, 0, 1))
    plt.title(f"Marracuene em falsa cor (NIR, vermelho, verde) · Sentinel-2 · {data}\n"
              "vegetação = vermelho · água = quase preto", fontsize=12)
    plt.axis("off")
    feitos.append(pasta / "modulo3_falsa_cor_marracuene.png")
    plt.savefig(feitos[-1], dpi=150, bbox_inches="tight")
    plt.close()

    fig, eixos = plt.subplots(2, 3, figsize=(15, 14))
    for linha, epoca in enumerate(["seca", "cheia"]):
        b, data = img[epoca]
        with np.errstate(divide="ignore", invalid="ignore"):
            ndwi = (b["verde"] - b["nir"]) / (b["verde"] + b["nir"])
            mndwi = (b["verde"] - b["swir"]) / (b["verde"] + b["swir"])
        eixos[linha, 0].imshow(np.clip(np.dstack([b["vermelho"], b["verde"], b["azul"]]) / 0.15, 0, 1))
        eixos[linha, 0].set_title(f"{epoca.upper()} · {data} · cor natural")
        for col, (indice, nome) in enumerate([(ndwi, "NDWI"), (mndwi, "MNDWI")], start=1):
            f = eixos[linha, col].imshow(indice, cmap="RdYlBu", vmin=-1, vmax=1)
            eixos[linha, col].set_title(f"{epoca.upper()} · {nome}")
    for e in eixos.ravel():
        e.axis("off")
    fig.colorbar(f, ax=eixos, shrink=0.4, label="azul = água")
    fig.suptitle("Incomáti em Marracuene: seca e cheia de janeiro de 2026 (Sentinel-2)", fontsize=15)
    feitos.append(pasta / "modulo4_seca_vs_cheia_ndwi_mndwi.png")
    fig.savefig(feitos[-1], dpi=120, bbox_inches="tight")
    plt.close(fig)
    return feitos


def main() -> None:
    respostas = json.loads((AULA / "0_facilitadores/respostas_de_referencia.json").read_text(encoding="utf-8"))
    feitos = introducao.construir()
    feitos += guia.construir(respostas)
    feitos += guia_completo.construir(respostas)
    ex, sondas = exercicios.construir(respostas)
    feitos += ex
    feitos += extras.construir(respostas)
    feitos += documentos.construir(respostas, sondas)
    feitos += imagens_para_slides()
    for f in feitos:
        print(f.relative_to(ROOT))
    print(len(feitos), "ficheiros")


if __name__ == "__main__":
    main()
