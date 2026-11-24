"""Escreve o deck do Módulo 2 (Como uma máquina aprende) em reports/apresentacao/workshop2_modulo2/project.

    cd scripts && ../.venv/bin/python -m workshop2.figuras_modulo2      # 1. as figuras (dados e modelos das aulas)
    .venv/bin/python scripts/build_workshop2_modulo2.py                 # 2. os slides

As imagens estão carregadas no artefacto «Módulo 2: Como uma máquina aprende» (os endereços /_blob/ estão em
reports/apresentacao/workshop2_modulo2/imagens.json). Se uma figura mudar, carreguem-na outra vez e actualizem lá o
endereço e o tamanho. O conteúdo está em scripts/workshop2/modulo2.py.

Verifica as regras do deck principal (letra de 24 px ou mais, cores, sem emojis, notas até 4000 caracteres, só
imagens do artefacto, no máximo 200 elementos por slide) e que os minutos das notas somam os 50 minutos do módulo
(09:05–09:55), com as perguntas da turma.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from workshop2 import modulo2 as M  # noqa: E402
from workshop2 import slides_base as B  # noqa: E402

PROJ = M.DECK / "project"
CORES = {c.upper() for c in [B.BRANCO, B.TINTA, B.SUAVE, B.ACENTO, B.PRETO, B.CAB_TABELA, B.CAIXA, B.LINHA, B.REALCE]}
CORES_SO_NA_ARVORE = {B.AGUA.upper(), M.TERRA.upper()}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️]")
CSS = """/* Módulo 2 do Workshop 2: os slides têm o estilo escrito em cada elemento (como o deck principal). */
section { font-family: Arial, sans-serif; }
"""


def verificar():
    avisos = []
    assert len(M.ORDEM) == len(set(M.ORDEM)), "slide repetido"
    assert set(M.ORDEM) == set(M.S) == set(dict(M.NOTAS)), (set(M.ORDEM) ^ set(M.S), set(M.ORDEM) ^ set(dict(M.NOTAS)))
    total = 0.0
    for sid in M.ORDEM:
        html = M.html(sid)
        assert html.count("<section") == 1 and html.rstrip().endswith("</section>"), sid
        assert html.count("<aside>") == 1 and len(M.NOTAS[sid]) <= 4000, (sid, len(M.NOTAS[sid]))
        assert min(int(x) for x in re.findall(r"font-size:(\d+)px", html)) >= 24, sid
        elementos = len(re.findall(r"<(?!/|br|b>|i>|u>|span)[a-z][a-z0-9-]*", html))
        assert elementos <= 200, (sid, elementos)
        assert not re.search(r"margin:|z-index|var\(|class=", html), sid
        for src in re.findall(r'src="([^"]+)"', html):
            assert src.startswith("/_blob/"), (sid, src)
        corpo = re.sub(r"<aside>.*?</aside>", "", html, flags=re.S)
        for cor in {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}\b", corpo)}:
            assert cor in CORES or (cor in CORES_SO_NA_ARVORE and sid == "m2-arvore"), (sid, cor)
        for texto in (corpo, M.NOTAS[sid]):
            assert not EMOJI.search(re.sub(r"<[^>]+>", " ", texto)), (sid, "emoji")
        m = re.search(r"<h2[^>]*>(.*?)</h2>", html)
        if m and B.larg_titulo(re.sub("<[^>]+>", "", m.group(1)), 52) > 1544:
            avisos.append(f"título em 2 linhas: {sid}")
        n = B.palavras_visiveis(html)
        if n > 70:
            avisos.append(f"{n} palavras visíveis: {sid}")
        minutos = M.minutos(M.NOTAS[sid])
        assert minutos > 0, (sid, "a nota não diz quantos minutos")
        total += minutos
    assert abs(total + M.MINUTOS_DE_PERGUNTAS - 50) < 0.01, f"os minutos somam {total} + {M.MINUTOS_DE_PERGUNTAS}, não 50"
    return avisos, total


def main() -> int:
    avisos, total = verificar()
    htmls, conta = B.numerar_legendas([M.html(sid) for sid in M.ORDEM])
    assert not any("§N§" in h for h in htmls)
    (PROJ / "slides").mkdir(parents=True, exist_ok=True)
    for sid, html in zip(M.ORDEM, htmls):
        (PROJ / "slides" / f"{sid}.html").write_text(html, encoding="utf-8")
    antigos = sorted(f.stem for f in (PROJ / "slides").glob("*.html") if f.stem not in M.ORDEM)
    for sid in antigos:
        (PROJ / "slides" / f"{sid}.html").unlink()

    indice = PROJ / "deck.json"
    criado = (json.loads(indice.read_text(encoding="utf-8"))["createdOnFiles"] if indice.exists()
              else {"v": 1, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    deck = {"v": 5, "createdOnFiles": criado, "lists": "css", "format": {"v": 1, "shared": ["project/deck.css"]},
            "title": "Módulo 2: Como uma máquina aprende", "order": M.ORDEM,
            "sections": {k: {"description": d, "start": s} for k, (s, d) in M.SECCOES_DECK.items()}, "cover": "m2",
            "faces": {"archivo-black": {"family": "Archivo Black",
                                        "href": "https://fonts.googleapis.com/css2?family=Archivo+Black&display=swap"}},
            "designSystems": []}
    indice.write_text(json.dumps(deck, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PROJ / "deck.css").write_text(CSS, encoding="utf-8")

    palavras = sorted(((B.palavras_visiveis(h), sid) for sid, h in zip(M.ORDEM, htmls)), reverse=True)
    print(f"{len(M.ORDEM)} slides em {PROJ.relative_to(ROOT)}; {conta['Figura']} figuras e {conta['Tabela']} tabelas numeradas")
    print(f"Minutos: {total:g} de conteúdo + {M.MINUTOS_DE_PERGUNTAS} de perguntas = 50 (09:05–09:55)")
    print(f"Palavras visíveis: média {sum(n for n, _ in palavras) / len(palavras):.0f}; mais carregados: "
          + ", ".join(f"{sid} ({n})" for n, sid in palavras[:5]))
    for a in avisos:
        print("AVISO", a)
    if antigos:
        print("Slides antigos apagados:", ", ".join(antigos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
