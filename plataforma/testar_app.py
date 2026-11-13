"""Teste da aplicação sem abrir o navegador: corre cada página, nas três línguas, e falha se houver algum erro.

    cd plataforma && python testar_app.py
    ETE_REGISTAR_EM_FALTA=1 python testar_app.py      # também escreve os textos sem tradução em textos_em_falta.txt

Verifica: todas as páginas abrem sem erros nem secções em falha, em português, inglês e francês;
os botões de anterior e seguinte funcionam; os mapas interactivos carregam quando são pedidos;
e, com um boletim antigo, a primeira página diz "previsão indisponível" e não mostra nenhum
nível de alerta.
"""

import sqlite3
import os
import sys
import tempfile
from pathlib import Path

from streamlit.testing.v1 import AppTest

import leitor

# sign-ups made by the test go to a temporary file, never to the real list
LISTA = Path(tempfile.mkdtemp()) / "subscritores.db"
os.environ["ETE_SUBSCRITORES_DB"] = str(LISTA)
os.environ["ETE_SUBSCRITORES"] = "sqlite"

failures = 0
PAGES = ["inicio", "agua", "conselhos", "cheias", "alertas", "mapa", "lugares", "historico", "modelos", "projecto", "sobre"]
BROKEN = ("Não foi possível mostrar", "Could not show", "Impossible d'afficher")


def open_page(name: str, language: str = "pt", invitation_seen: bool = True):
    app = AppTest.from_file("app.py", default_timeout=240)
    app.session_state["lingua"] = language
    app.session_state["pagina"] = name
    app.session_state["_convite_visto"] = invitation_seen
    return app.run()


def report(name: str, app, extra_ok: bool = True) -> None:
    global failures
    errors = [str(e.value) for e in app.exception]
    broken = [str(w.value) for w in app.warning if str(w.value).startswith(BROKEN)]
    ok = not errors and not broken and extra_ok
    failures += 0 if ok else 1
    print(f"{'ok   ' if ok else 'FALHA'} {name}")
    for problem in errors + broken:
        print("      ", problem[:300])


for language in ("pt", "en", "fr"):
    for page in PAGES:
        report(f"[{language}] página {page}", open_page(page, language))

# back and forward buttons (tested with the bulletin treated as fresh, whatever its real age)
leitor.HORAS_ATE_DESATUALIZADO = 10 ** 6
app = open_page("inicio")
app.button(key="dia_next").click().run()
app.button(key="dia_next").click().run()
report("Início: seguinte, seguinte chega ao 3.º dia", app, app.session_state["dia_i"] == 2)
app.button(key="dia_prev").click().run()
report("Início: anterior volta ao 2.º dia", app, app.session_state["dia_i"] == 1)
app = open_page("historico")
last = app.session_state["ano_hist_i"]
app.button(key="ano_hist_prev").click().run()
report("Histórico: anterior recua um ano", app, app.session_state["ano_hist_i"] == last - 1)
app = open_page("agua")
year = app.session_state["ano_agua_i"]
app.button(key="ano_agua_prev").click().run()
report("Qualidade da água: painel, ano anterior", app, app.session_state["ano_agua_i"] == year - 1)
start = app.session_state["troco_i"]
app.button(key="troco_prev").click().run()
report("Qualidade da água: anterior sobe um troço", app, app.session_state["troco_i"] == start - 1)

# interactive maps and the radar month stepper
app = open_page("mapa")
app.toggle(key="mapa_cheias").set_value(True).run()
report("Mapa interactivo das zonas", app)
app.radio(key="camada_mapa").set_value("agua_mensal").run()
month = app.session_state["mes_radar_i"]
app.button(key="mes_radar_prev").click().run()
report("Mapa: radar, mês anterior", app, app.session_state["mes_radar_i"] == month - 1)
app = open_page("agua")          # widgets are set in Portuguese: the test tool formats menu options outside the page, without its language
app.toggle(key="mapa_agua").set_value(True).run()
report("Mapa interactivo dos troços", app)

# shortcut buttons move between pages; the language switch keeps the page
app = open_page("inicio")
app.button(key="ir_agua").click().run()
report("Início: o botão 'Ver a qualidade da água' muda de página", app, app.session_state["pagina"] == "agua")
app.radio(key="lingua").set_value("fr").run()
report("Mudar para francês mantém a página", app, app.session_state["pagina"] == "agua" and any("Qualité de l'eau" in str(m.value) for m in app.markdown))

# WhatsApp alerts: the invitation on the first visit, signing up and leaving
app = open_page("inicio", invitation_seen=False)
report("Início com o convite para os alertas", app, any("convite_agora_nao" == getattr(b, "key", None) for b in app.button))


def rows():
    if not LISTA.exists():
        return []
    with sqlite3.connect(LISTA) as ligacao:
        ligacao.row_factory = sqlite3.Row
        return [dict(r) for r in ligacao.execute("SELECT * FROM subscritores")]


def submit(app, label):
    next(b for b in app.button if label in str(b.label)).click().run()


app = open_page("alertas")
app.text_input(key="pagina_telefone").input("84 123 4567")
app.selectbox(key="pagina_lugar").set_value("Machubo")
app.selectbox(key="pagina_sexo").set_value("mulher")
app.selectbox(key="pagina_idade").set_value("60_mais")
app.selectbox(key="pagina_profissao").set_value("agricultor")
submit(app, "Quero receber")
report("Inscrição sem marcar «Aceito» é recusada", app, rows() == [])
app.checkbox(key="pagina_aceito").check()
submit(app, "Quero receber")
report("Inscrição guarda o número, o lugar e o perfil", app,
       [(r["telefone"], r["lugar"], r["estado"], r["sexo"], r["faixa_etaria"], r["profissao"]) for r in rows()] == [("258841234567", "Machubo", "activa", "mulher", "60_mais", "agricultor")])
app.text_input(key="pagina_telefone").input("12 34")
submit(app, "Quero receber")
report("Número errado não é guardado", app, len(rows()) == 1)
app.text_input(key="sair_telefone").input("+258 84 123 4567")
submit(app, "Deixar de receber os alertas")
report("Deixar de receber marca o número como removido", app, [r["estado"] for r in rows()] == ["removido"])
shown = " ".join(str(m.value) for m in app.markdown)
report("A plataforma nunca mostra a lista de números", app, "258841234567" not in shown)

# translations added while the platform is running must be used without restarting it
import idioma
import textos

anterior = textos.TEXTOS
textos.TEXTOS = {**anterior, "__texto_novo__": ("new text", "texte nouveau")}     # what a reload of textos.py does
novo_visto = "__texto_novo__" in idioma._tabela()
textos.TEXTOS = anterior
failures += 0 if novo_visto else 1
print(f"{'ok   ' if novo_visto else 'FALHA'} Traduções novas usadas sem reiniciar o servidor")

# safety rule: with an old bulletin the first page must say "indisponível" and must not show an alert level
leitor.HORAS_ATE_DESATUALIZADO = -1                     # pretend the bulletin is too old
for language, unavailable in (("pt", "Previsão indisponível"), ("en", "Forecast unavailable"), ("fr", "Prévision indisponible")):
    app = open_page("inicio", language)
    shown = " ".join(str(m.value) for m in app.markdown)
    report(f"[{language}] boletim antigo: diz '{unavailable}' e não mostra nível", app,
           unavailable in shown and not any(w in shown.upper() for w in ("ALERTA VERDE", "GREEN ALERT", "ALERTE VERTE", "ALERTA VERMELHO", "RED ALERT", "ALERTE ROUGE")))

print("APLICAÇÃO SEM ERROS" if not failures else f"{failures} ERRO(S)")
sys.exit(1 if failures else 0)
