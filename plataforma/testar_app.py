"""Teste da aplicação sem abrir o navegador: corre cada página e falha se houver algum erro.

    cd plataforma && python testar_app.py

Verifica: todas as páginas abrem sem erros nem secções em falha; os botões de anterior e
seguinte funcionam; os mapas interactivos carregam quando são pedidos; e, com um boletim
antigo, a primeira página diz "previsão indisponível" e não mostra nenhum nível de alerta.
"""

import sys

from streamlit.testing.v1 import AppTest

import leitor

failures = 0


def open_page(name: str):
    app = AppTest.from_file("app.py", default_timeout=240).run()
    label = next(o for o in app.radio(key="pagina").options if name in o)
    app.radio(key="pagina").set_value(label).run()
    return app


def report(name: str, app, extra_ok: bool = True) -> None:
    global failures
    errors = [str(e.value) for e in app.exception]
    broken = [str(w.value) for w in app.warning if str(w.value).startswith("Não foi possível mostrar")]
    ok = not errors and not broken and extra_ok
    failures += 0 if ok else 1
    print(f"{'ok   ' if ok else 'FALHA'} {name}")
    for problem in errors + broken:
        print("      ", problem[:300])


for page in ("Início", "Cheias", "Mapa", "Água do rio", "Histórico", "Lugares", "Modelos", "Como funciona"):
    report(f"página {page}", open_page(page))

# back and forward buttons
app = open_page("Início")
app.button(key="dia_next").click().run()
app.button(key="dia_next").click().run()
report("Início: seguinte, seguinte chega ao 3.º dia", app, app.session_state["dia_i"] == 2)
app.button(key="dia_prev").click().run()
report("Início: anterior volta ao 2.º dia", app, app.session_state["dia_i"] == 1)
app = open_page("Histórico")
last = app.session_state["ano_hist_i"]
app.button(key="ano_hist_prev").click().run()
report("Histórico: anterior recua um ano", app, app.session_state["ano_hist_i"] == last - 1)
app = open_page("Água do rio")
year = app.session_state["ano_agua_i"]
app.button(key="ano_agua_prev").click().run()
report("Água do rio: painel, ano anterior", app, app.session_state["ano_agua_i"] == year - 1)
start = app.session_state["troco_i"]
app.button(key="troco_prev").click().run()
report("Água do rio: anterior sobe um troço", app, app.session_state["troco_i"] == start - 1)

# interactive maps and the radar month stepper
app = open_page("Mapa")
app.toggle(key="mapa_cheias").set_value(True).run()
report("Mapa interactivo das zonas", app)
app.radio(key="camada_mapa").set_value("Água vista por radar, mês a mês").run()
month = app.session_state["mes_radar_i"]
app.button(key="mes_radar_prev").click().run()
report("Mapa: radar, mês anterior", app, app.session_state["mes_radar_i"] == month - 1)
app = open_page("Água do rio")
app.toggle(key="mapa_agua").set_value(True).run()
report("Mapa interactivo dos troços", app)

# shortcut buttons move between pages
app = open_page("Início")
app.button(key="ir_agua").click().run()
report("Início: o botão 'Ver a água do rio' muda de página", app, "Água do rio" in app.session_state["pagina"])

# safety rule: with an old bulletin the first page must say "indisponível" and must not show an alert level
leitor.HORAS_ATE_DESATUALIZADO = -1                     # pretend the bulletin is too old
app = AppTest.from_file("app.py", default_timeout=240).run()
shown = " ".join(str(m.value) for m in app.markdown)
report("boletim antigo: diz 'previsão indisponível' e não mostra nível", app, "Previsão indisponível" in shown and "Alerta VERDE" not in shown and "Alerta VERMELHO" not in shown)

print("APLICAÇÃO SEM ERROS" if not failures else f"{failures} ERRO(S)")
sys.exit(1 if failures else 0)
