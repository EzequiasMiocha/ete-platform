"""Certificados de participação do Workshop 2 (A4 deitado, PDF).

    .venv/bin/python scripts/build_workshop2_certificados.py

Lê Workshop_2/0_facilitadores/certificados/participantes.csv (uma coluna "nome"; cria-o vazio se não existir)
e escreve na mesma pasta:
  certificado_modelo.pdf          sem nome, com uma linha para escrever à mão
  certificado_NN_nome.pdf         um por participante
  certificados_todos.pdf          todos juntos, para imprimir de uma vez
"""

import csv
import re
import sys
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from workshop2.comum import FAC  # noqa: E402

PASTA = FAC / "certificados"
LOGOS = FAC / "imagens_para_slides"
AREIA, ESCURO, TEAL, SUAVE = "#F7F3EA", "#082F2C", "#0F766E", "#3D5752"
W, H = 11.69, 8.27            # A4 deitado, em polegadas


def logotipo(fig, ficheiro, x, y, altura):
    """Põe um logótipo com o canto inferior esquerdo em (x, y), em fracções da página."""
    im = Image.open(LOGOS / ficheiro).convert("RGBA")
    largura = altura * (im.width / im.height) * (H / W)
    ax = fig.add_axes([x, y, largura, altura])
    ax.imshow(im)
    ax.axis("off")
    return largura


def certificado(nome: str | None):
    fig = plt.figure(figsize=(W, H), facecolor=AREIA)
    fundo = fig.add_axes([0, 0, 1, 1])
    fundo.set_xlim(0, 1)
    fundo.set_ylim(0, 1)
    fundo.axis("off")
    fundo.add_patch(Rectangle((0.025, 0.035), 0.95, 0.93, fill=False, edgecolor=TEAL, lw=4))
    fundo.add_patch(Rectangle((0.035, 0.049), 0.93, 0.902, fill=False, edgecolor=TEAL, lw=1))
    logotipo(fig, "logo_ete.png", 0.07, 0.80, 0.12)
    fundo.text(0.165, 0.86, "PROJECTO EYES TO EARTH (ETE)", fontsize=13, fontweight="bold", color=TEAL, va="center")
    fundo.text(0.5, 0.72, "Certificado de participação", fontsize=34, family="DejaVu Serif", color=ESCURO, ha="center")
    fundo.text(0.5, 0.645, "Certifica-se que", fontsize=14, color=SUAVE, ha="center")
    if nome:
        fundo.text(0.5, 0.565, nome, fontsize=30, family="DejaVu Serif", fontweight="bold", color=ESCURO, ha="center")
    else:
        fundo.plot([0.2, 0.8], [0.555, 0.555], color=SUAVE, lw=1)
    corpo = ("participou no Workshop de Estudantes 2,\n"
             "«Inteligência Artificial para monitorizar a água e avisar das cheias»,\n"
             "realizado em Maputo a 21 de Novembro de 2026, com a duração de 6 horas,\n"
             "no âmbito do projecto EYES TO EARTH (ETE).")
    fundo.text(0.5, 0.445, corpo, fontsize=13, color=SUAVE, ha="center", va="center", linespacing=1.6)
    conteudos = ("Inteligência Artificial e Machine Learning: como uma máquina aprende com exemplos ·\n"
                 "classificação e regressão em Python (Jupyter Notebook) · qualidade da água vista por satélite e a maré ·\n"
                 "a plataforma de alertas de cheia EYES TO EARTH")
    fundo.text(0.5, 0.33, conteudos, fontsize=10.5, color=SUAVE, ha="center", va="center", linespacing=1.5, style="italic")
    for x, papel in [(0.25, "Coordenação do projecto EYES TO EARTH"), (0.75, "Moderação do workshop")]:
        fundo.plot([x - 0.16, x + 0.16], [0.20, 0.20], color=SUAVE, lw=1)
        fundo.text(x, 0.18, papel, fontsize=11, color=SUAVE, ha="center", va="top")
    fundo.text(0.5, 0.245, "Maputo, 21 de Novembro de 2026", fontsize=11, color=SUAVE, ha="center")
    fundo.text(0.07, 0.09, "Com o apoio de", fontsize=11, color=SUAVE, va="center")
    x = 0.175
    x += logotipo(fig, "logo_oad_escuro.png", x, 0.055, 0.07) + 0.02
    logotipo(fig, "logo_dara.png", x, 0.058, 0.062)
    return fig


def slug(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", sem_acentos).strip("_").lower()[:40]


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    lista = PASTA / "participantes.csv"
    if not lista.exists():
        lista.write_text("nome\n", encoding="utf-8")
        print("Criei", lista.relative_to(ROOT), "(vazio): escreva um nome por linha e corra outra vez.")
    with open(lista, encoding="utf-8") as f:
        nomes = [linha["nome"].strip() for linha in csv.DictReader(f) if linha.get("nome", "").strip()]
    fig = certificado(None)
    fig.savefig(PASTA / "certificado_modelo.pdf", facecolor=AREIA)
    plt.close(fig)
    print("certificado_modelo.pdf")
    if nomes:
        with PdfPages(PASTA / "certificados_todos.pdf") as todos:
            for i, nome in enumerate(nomes, start=1):
                fig = certificado(nome)
                fig.savefig(PASTA / f"certificado_{i:02d}_{slug(nome)}.pdf", facecolor=AREIA)
                todos.savefig(fig, facecolor=AREIA)
                plt.close(fig)
        print(f"{len(nomes)} certificados e certificados_todos.pdf")


if __name__ == "__main__":
    main()
