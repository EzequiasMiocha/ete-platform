"""Escreve o deck de slides do Workshop 2 (tipo Claude Slides) em reports/apresentacao/workshop2_slides/project.

    .venv/bin/python scripts/build_workshop2_slides.py

O conteúdo está em scripts/workshop2/slides.py, a ordem em slides_ordem.py e as notas fixas em slides_notas.py.
Este script verifica as regras do deck (letra de 24 px ou mais, sem azul fora da água, sem emoji, notas com 4000
caracteres no máximo, imagens só do repositório do artefacto), numera as figuras e as tabelas pela ordem dos slides,
escreve os ficheiros, actualiza a ordem e as secções do deck.json e escreve ficheiros.json (o mapa para publicar).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from workshop2 import slides as SL  # noqa: E402
from workshop2.slides_base import numerar_legendas, palavras_visiveis  # noqa: E402
from workshop2.slides_ordem import ORDEM, SECCOES_DECK  # noqa: E402

DECK = ROOT / "reports/apresentacao/workshop2_slides"
PROJ = DECK / "project"


def main() -> int:
    avisos = SL.verificar()
    htmls, conta = numerar_legendas([SL.S[sid] for sid in ORDEM])
    assert not any("§N§" in h for h in htmls), "ficou uma legenda sem número"

    (PROJ / "slides").mkdir(parents=True, exist_ok=True)
    for sid, html in zip(ORDEM, htmls):
        (PROJ / "slides" / f"{sid}.html").write_text(html, encoding="utf-8")
    antigos = sorted(f.stem for f in (PROJ / "slides").glob("*.html") if f.stem not in ORDEM)
    for sid in antigos:
        (PROJ / "slides" / f"{sid}.html").unlink()

    deck = json.loads((PROJ / "deck.json").read_text(encoding="utf-8"))
    deck["order"] = ORDEM
    deck["sections"] = {chave: {"description": descricao, "start": inicio} for chave, (inicio, descricao) in SECCOES_DECK.items()}
    assert all(s["start"] in ORDEM for s in deck["sections"].values())
    (PROJ / "deck.json").write_text(json.dumps(deck, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ficheiros = {"project/deck.json": "project/deck.json"}
    ficheiros.update({f"project/slides/{sid}.html": f"project/slides/{sid}.html" for sid in ORDEM})
    (DECK / "ficheiros.json").write_text(json.dumps(ficheiros, indent=1) + "\n", encoding="utf-8")

    palavras = sorted(((palavras_visiveis(h), sid) for sid, h in zip(ORDEM, htmls)), reverse=True)
    media = sum(n for n, _ in palavras) / len(palavras)
    print(f"{len(ORDEM)} slides escritos em {PROJ.relative_to(ROOT)}; {conta['Figura']} figuras e {conta['Tabela']} tabelas numeradas")
    print(f"Palavras visíveis por slide: média {media:.0f}; mais carregados: "
          + ", ".join(f"{sid} ({n})" for n, sid in palavras[:6]))
    if antigos:
        print("Slides antigos apagados da pasta:", ", ".join(antigos))
    for aviso in avisos:
        print("AVISO", aviso)
    return 0


if __name__ == "__main__":
    sys.exit(main())
