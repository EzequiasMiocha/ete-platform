"""Teste da aplicação sem abrir o navegador: corre cada página e falha se houver algum erro.

    cd plataforma && python testar_app.py

Verifica: todas as páginas abrem sem erros nem secções em falha; o mapa interactivo carrega
quando é pedido; e, com um boletim antigo, a primeira página diz "previsão indisponível" e
não mostra nenhum nível de alerta.
"""

import sys

from streamlit.testing.v1 import AppTest

import leitor

failures = 0


def run(page: str, toggle: str | None = None):
    app = AppTest.from_file("app.py", default_timeout=180).run()
    app.radio(key="pagina").set_value(page).run()
    if toggle:
        app.toggle(key=toggle).set_value(True).run()
    return app


def report(name: str, app, extra_ok: bool = True) -> None:
    global failures
    errors = [str(e.value) for e in app.exception]
    broken = [str(w.value) for w in app.warning if str(w.value).startswith("Não foi possível mostrar")]
    ok = not errors and not broken and extra_ok
    failures += 0 if ok else 1
    print(f"{'ok   ' if ok else 'FALHA'} {name}: {len(app.subheader)} secções")
    for problem in errors + broken:
        print("      ", problem[:300])


for page in ("Hoje", "Cheias", "Água do rio", "Sobre os dados"):
    report(page, run(page))
report("Cheias, mapa interactivo", run("Cheias", "mapa_cheias"))
report("Água do rio, mapa interactivo", run("Água do rio", "mapa_agua"))

# safety rule: with an old bulletin the first page must say "indisponível" and must not show an alert level
leitor.HORAS_ATE_DESATUALIZADO = -1                     # pretend the bulletin is too old
app = AppTest.from_file("app.py", default_timeout=180).run()
shown = " ".join(str(m.value) for m in app.markdown)
report("boletim antigo: diz 'previsão indisponível' e não mostra nível", app, "Previsão indisponível" in shown and "Alerta VERDE" not in shown and "Alerta VERMELHO" not in shown)

print("APLICAÇÃO SEM ERROS" if not failures else f"{failures} ERRO(S)")
sys.exit(1 if failures else 0)
