"""Teste da aplicação sem abrir o navegador: corre cada página, nas três línguas, e falha se houver algum erro.

    cd plataforma && python testar_app.py
    ETE_REGISTAR_EM_FALTA=1 python testar_app.py      # também escreve os textos sem tradução em textos_em_falta.txt

Verifica: as cinco páginas e a página de um lugar abrem sem erros nem secções em falha, em português,
inglês e francês; a página de cada um dos lugares abre; a barra de pesquisa leva a um lugar ou à secção
certa de uma página (e cada secção que a pesquisa abre existe); um endereço partilhado (?p=zona&lugar=...)
abre o lugar; as curiosidades aparecem;
os endereços das páginas antigas (?p=mapa, ?p=conselhos...) abrem a página que agora as tem;
os botões de anterior e seguinte funcionam; os mapas interactivos carregam quando são pedidos;
a barra de baixo dos telemóveis acompanha a página; o mapa da cor da água diz numa frase como
está a água; as plantas só dão aviso com duas imagens recentes num troço fiável; e, com um
boletim antigo, a primeira página diz "previsão indisponível" e não mostra nenhum nível de alerta.
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
PAGES = ["inicio", "agua", "cheias", "alertas", "sobre"]
BROKEN = ("Não foi possível mostrar", "Could not show", "Impossible d'afficher")


def open_page(name: str, language: str = "pt", invitation_seen: bool = True, place: str | None = None):
    app = AppTest.from_file("app.py", default_timeout=240)
    app.session_state["lingua"] = language
    app.session_state["pagina"] = name
    app.session_state["_convite_visto"] = invitation_seen
    if place is not None:
        app.session_state["zona"] = place
    return app.run()


def page_text(app) -> str:
    """Everything the page wrote: the Markdown blocks and the HTML blocks."""
    return " ".join(str(m.value) for m in app.markdown) + " " + " ".join(getattr(h.proto, "body", "") for h in app.get("html"))


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
    app = open_page("zona", language, place="Machubo")
    report(f"[{language}] página de um lugar (Machubo)", app, "ete-comparar" in page_text(app) and "ete-respostas" in page_text(app))

# the pages that no longer exist: an old link or an old session opens the page that has their content now
for old, new in (("mapa", "cheias"), ("lugares", "cheias"), ("historico", "cheias"), ("conselhos", "agua"), ("modelos", "sobre"), ("projecto", "sobre"), ("mais", "inicio")):
    app = open_page(old)
    report(f"Página antiga «{old}» abre «{new}»", app, app.session_state["pagina"] == new)

# back and forward buttons (tested with the bulletin treated as fresh, whatever its real age)
leitor.HORAS_ATE_DESATUALIZADO = 10 ** 6
app = open_page("inicio")
app.button(key="dia_next").click().run()
app.button(key="dia_next").click().run()
report("Início: seguinte, seguinte chega ao 3.º dia", app, app.session_state["dia_i"] == 2)
app.button(key="dia_prev").click().run()
report("Início: anterior volta ao 2.º dia", app, app.session_state["dia_i"] == 1)
app = open_page("cheias")
last = app.session_state["ano_hist_i"]
app.button(key="ano_hist_prev").click().run()
report("Cheias: um ano em detalhe, anterior recua um ano", app, app.session_state["ano_hist_i"] == last - 1)
app = open_page("agua")
year = app.session_state["ano_agua_i"]
app.button(key="ano_agua_prev").click().run()
report("Qualidade da água: painel, ano anterior", app, app.session_state["ano_agua_i"] == year - 1)
start = app.session_state["troco_i"]
app.button(key="troco_prev").click().run()
report("Qualidade da água: anterior sobe um troço", app, app.session_state["troco_i"] == start - 1)

# the floods page: the photographs from space, the radar month by month, a place and the interactive map
app = open_page("cheias")          # widgets are set in Portuguese: the test tool formats menu options outside the page, without its language
report("Cheias: as fotografias da cheia de 2026 aparecem", app, any("ete-comparar" in str(h.proto) for h in app.get("html")))
month = app.session_state["mes_radar_i"]
app.button(key="mes_radar_prev").click().run()
report("Cheias: radar, mês anterior", app, app.session_state["mes_radar_i"] == month - 1)
app.selectbox(key="lugar_mapa").set_value("Machubo").run()
shown = " ".join(str(m.value) for m in app.markdown)
report("Cheias: procurar um lugar mostra o seu cartão", app, "Edifícios num raio de 500 m" in shown)
app.toggle(key="mapa_cheias").set_value(True).run()
report("Cheias: mapa interactivo das zonas", app)

# shortcut buttons move between pages (some to a section of the page); the language switch keeps the page
app = open_page("inicio")
app.button(key="ir_agua").click().run()
report("Início: o botão 'Ver a qualidade da água' muda de página", app, app.session_state["pagina"] == "agua")
app.radio(key="lingua").set_value("fr").run()
report("Mudar para francês mantém a página", app, app.session_state["pagina"] == "agua" and any("Qualité de l'eau" in str(m.value) for m in app.markdown))
app = open_page("agua")
app.button(key="ir_modelos_agua").click().run()
report("Água: «Ver os modelos» abre O projecto na secção dos modelos", app,
       app.session_state["pagina"] == "sobre" and any("const id = 'modelos'" in getattr(h.proto, "body", "") for h in app.get("html")))
app = open_page("inicio")
app.button(key="ir_projecto").click().run()
report("Início: «Conhecer o projecto» abre O projecto", app, app.session_state["pagina"] == "sobre")

# the bar at the bottom of phones follows the page, whichever bar was used
app = open_page("inicio")
app.radio(key="nav_movel").set_value("agua").run()
report("Telemóvel: a barra de baixo abre a Água", app, app.session_state["pagina"] == "agua")
app.radio(key="nav_movel").set_value("alertas").run()
report("Telemóvel: a barra de baixo abre os Alertas", app, app.session_state["pagina"] == "alertas")
app.radio(key="nav_topo").set_value("cheias").run()
report("A barra de cima também acerta a de baixo", app, app.session_state["pagina"] == "cheias" and app.session_state["nav_movel"] == "cheias")

# the water page in time, one part after the other: the next four weeks and the past months (when the package has them)
app = open_page("agua")
if any(getattr(r, "key", None) == "semana_cor" for r in app.radio):
    app.radio(key="semana_cor").set_value(3).run()
    shown = " ".join(str(m.value) for m in app.markdown)
    report("Qualidade da água: a previsão mostra a 4.ª semana", app, app.session_state["semana_cor"] == 3 and "a água deve estar" in shown)
if any(getattr(b, "key", None) == "ano_passado_prev" for b in app.button):
    ano = app.session_state["ano_passado_i"]
    app.button(key="ano_passado_prev").click().run()
    shown = " ".join(str(m.value) for m in app.markdown)
    report("Qualidade da água: o passado recua um ano e diz como esteve a água", app,
           app.session_state["ano_passado_i"] == ano - 1 and ("a água esteve" in shown or "as nuvens não deixaram" in shown))

# the map of the water colour says in one sentence how the water is
app = open_page("agua")
shown = " ".join(str(m.value) for m in app.markdown)
has_map = "cor_da_agua_mapa" in {c["id"] for c in leitor.catalogo()["camadas"]}
report("Qualidade da água: o mapa da cor diz como está a água", app, not has_map or "a água está" in shown or "as nuvens tapavam" in shown)

# the search bar: a place opens its page; a question opens a page at the right section
import pesquisa

app = open_page("inicio")
app.selectbox(key="pesquisa").set_value("lugar:Macaneta").run()
report("Pesquisa: escolher um lugar abre a página do lugar", app, app.session_state["pagina"] == "zona" and app.session_state["zona"] == "Macaneta")
report("Na página de um lugar nenhuma barra fica acesa", app, app.session_state["nav_topo"] is None and app.session_state["nav_movel"] is None)
app.selectbox(key="pesquisa").set_value("tema:beber").run()
report("Pesquisa: «Posso beber a água do rio?» abre a Água nos conselhos", app,
       app.session_state["pagina"] == "agua" and any("const id = 'conselhos'" in getattr(h.proto, "body", "") for h in app.get("html")))
app.selectbox(key="pesquisa").set_value("tema:tratar").run()
report("Pesquisa: uma secção da mesma página também rola até ela", app, any("const id = 'tratar'" in getattr(h.proto, "body", "") for h in app.get("html")))
# free text (typed and Enter): the test tool cannot type into the bar, so the results box is filled as the bar does
app.session_state["_pesquisa"] = {"texto": "mach", "achados": pesquisa.procurar("mach", ["Machavo", "Machubo"])}
app.run()
app.button(key="resultado_1").click().run()
report("Pesquisa: um resultado de texto livre abre o lugar", app, app.session_state["pagina"] == "zona" and app.session_state["zona"] == "Machubo")
app.session_state["_pesquisa"] = {"texto": "xyzw", "achados": []}
app.run()
report("Pesquisa: sem resultados, diz o que escrever", app, "Não encontrámos «xyzw»" in page_text(app))
names = list(dict.fromkeys(leitor.serie("lugares_por_ordem")["lugar"]))
for typed, expected in (("machubu", "lugar:Machubo"), ("Macaneta", "lugar:Macaneta"), ("posso beber agua", "tema:beber"), ("satelite", "tema:satelite"),
                        ("vazao", "tema:caudal"), ("quando vai alagar", "tema:cheia_dias"), ("agua", None), ("xyzw", None)):
    found = pesquisa.decidir(typed, names)
    good = found == expected
    failures += 0 if good else 1
    print(f"{'ok   ' if good else 'FALHA'} Pesquisa por texto: «{typed}» abre {expected or 'uma lista'} ({found})")
# every section a topic of the search opens exists on its page
for page in sorted({p for _, _, _, p, a, _ in pesquisa.TEMAS if a}):
    app = open_page(page)
    shown = page_text(app)
    missing = [a for _, _, _, p, a, _ in pesquisa.TEMAS if p == page and a and f"id='{a}'" not in shown]
    report(f"Pesquisa: as secções que abre na página «{page}» existem", app, not missing)
    if missing:
        print("       em falta:", missing)

# the page of every place opens, with its pictures; a shared address opens the place; an unknown place asks to choose
app = open_page("zona", place="")
report("Página de um lugar sem lugar: pede para escolher", app, "Procure o seu lugar" in page_text(app))
broken_places = []
for name in names:
    app.session_state["zona"] = name
    app.run()
    if app.exception or [w for w in app.warning if str(w.value).startswith(BROKEN)] or "ete-comparar" not in page_text(app):
        broken_places.append(name)
report(f"As páginas dos {len(names)} lugares abrem, com as imagens de satélite", app, not broken_places)
if broken_places:
    print("       com problemas:", broken_places)
shared = AppTest.from_file("app.py", default_timeout=240)
shared.query_params["p"] = "zona"
shared.query_params["lugar"] = "Aldeia Verde"
shared.session_state["_convite_visto"] = True
shared.run()
report("Endereço partilhado ?p=zona&lugar=Aldeia Verde abre o lugar", shared, shared.session_state["pagina"] == "zona" and shared.session_state["zona"] == "Aldeia Verde")
app = open_page("cheias")
app.selectbox(key="lugar_mapa").set_value("Machubo").run()
app.button(key="ir_zona_mapa").click().run()
report("Cheias: «Ver tudo sobre» um lugar abre a página do lugar", app, app.session_state["pagina"] == "zona" and app.session_state["zona"] == "Machubo")
app.button(key="ir_alertas_zona").click().run()
report("Lugar: «Receber alertas» abre a inscrição com o lugar escolhido", app, app.session_state["pagina"] == "alertas" and app.session_state["pagina_lugar"] == "Machubo")

# curiosities: three on the home page, all of them in O projecto
app = open_page("inicio")
report("Início: três curiosidades", app, page_text(app).count("class='ete-curiosidade'") == 3)
app = open_page("sobre")
import curiosidades

report("O projecto: todas as curiosidades", app, page_text(app).count("class='ete-curiosidade'") == len(curiosidades.CURIOSIDADES))

# plants on the water: no warning from a single image, an old month, an unreliable section or a small share
import conselhos
import pandas as pd

bulletin = {"seguro_mostrar": True, "nivel_maximo_provavel": "verde", "estado": {"data_da_previsao": "2026-11-14"}}


def plants(**row):
    base = {"troco": "Q7", "nome": "Q7 Manhiça", "mes": "2026-11", "classe": "normal", "fiabilidade": "boa", "vegetacao": 0.45, "imagens_plantas": 3}
    return any(s["chave"] == "plantas" for s in conselhos.detectar(bulletin, None, pd.DataFrame([{**base, **row}]), None))


for name, found, expected in [("em 3 imagens deste mês dão aviso", plants(), True), ("uma só imagem não dá aviso", plants(imagens_plantas=1), False),
                              ("um mês antigo não dá aviso", plants(mes="2026-08"), False), ("um troço pouco fiável não dá aviso", plants(fiabilidade="reduzida"), False),
                              ("menos de 30 % não dá aviso", plants(vegetacao=0.12), False)]:
    good = found == expected
    failures += 0 if good else 1
    print(f"{'ok   ' if good else 'FALHA'} Plantas: {name}")

# WhatsApp alerts: the invitation on the first visit, signing up and leaving
app = open_page("inicio", invitation_seen=False)
report("Início com o convite para os alertas", app, any("convite_agora_nao" == getattr(b, "key", None) for b in app.button))
app.button(key="convite_agora_nao").click().run()
# the test tool keeps showing a dialog's old content after it closes; in a real browser it closes (checked with
# scripts/capturar_plataforma.py's Firefox): what is tested here is that the click marks the invitation as seen
report("«Agora não» marca o convite como visto (a janela fecha e não volta)", app, app.session_state["_convite_visto"] is True)


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
app.text_input(key="pagina_nome").input("Maria")
app.selectbox(key="pagina_lugar").set_value("Machubo")
app.selectbox(key="pagina_sexo").set_value("mulher")
app.selectbox(key="pagina_idade").set_value("60_mais")
app.selectbox(key="pagina_profissao").set_value("agricultor")
app.checkbox(key="pagina_aceito").check()
submit(app, "Quero receber")
report("Inscrição sem o nome completo é recusada (as mensagens usam-no)", app, rows() == [] and "nome completo" in page_text(app))
app.text_input(key="pagina_nome").input("Maria  Cossa")
app.checkbox(key="pagina_aceito").uncheck()
submit(app, "Quero receber")
report("Inscrição sem marcar «Aceito» é recusada", app, rows() == [])
app.checkbox(key="pagina_aceito").check()
submit(app, "Quero receber")
report("Inscrição guarda o nome completo, o número, o lugar e o perfil", app,
       [(r["nome"], r["telefone"], r["lugar"], r["estado"], r["sexo"], r["faixa_etaria"], r["profissao"]) for r in rows()]
       == [("Maria Cossa", "258841234567", "Machubo", "activa", "mulher", "60_mais", "agricultor")])
app.text_input(key="pagina_telefone").input("12 34")
submit(app, "Quero receber")
report("Número errado não é guardado", app, len(rows()) == 1)
app.text_input(key="sair_telefone").input("+258 84 123 4567")
submit(app, "Deixar de receber os alertas")
report("Deixar de receber marca o número como removido", app, [r["estado"] for r in rows()] == ["removido"])
shown = " ".join(str(m.value) for m in app.markdown)
report("A plataforma nunca mostra a lista de números", app, "258841234567" not in shown)

# accounts: open one, the recovery code once, sign out, a wrong password, sign in, the details in the sign-up form, alerts, delete
import contas

app = open_page("conta")
report("Conta: a página pede para entrar ou criar uma conta", app, "Entre ou crie a sua conta" in page_text(app))
for chave, valor in (("criar_nome", "Ana  Cossa"), ("criar_utilizador", "Ana.Cossa"), ("criar_senha", "Rio-Incomati-26"), ("criar_repetida", "Rio-Incomati-26"),
                     ("criar_telefone", "84 765 4321")):
    app.text_input(key=chave).input(valor)
app.selectbox(key="criar_lugar").set_value("Macaneta")
app.checkbox(key="criar_manter").uncheck()
app.button(key="criar_enviar").click().run()
report("Conta: sem marcar «Aceito» não cria a conta", app, "conta" not in app.session_state)
app.checkbox(key="criar_aceito").check()
app.button(key="criar_enviar").click().run()
report("Conta: cria a conta e mostra o código de recuperação", app, "conta" in app.session_state and app.session_state["conta"]["nome"] == "Ana Cossa"
       and "Guarde este código" in page_text(app))
report("Conta: a sessão do navegador não guarda a senha", app, "senha" not in app.session_state["conta"])
report("Conta: o botão do cabeçalho passa a dizer o primeiro nome", app, any(b.key == "ir_conta" and str(b.label) == "Ana" for b in app.button))
app.button(key="codigo_guardado").click().run()
report("Conta: o código só se mostra uma vez", app, "Guarde este código" not in page_text(app))
app.button(key="conta_sair").click().run()
report("Conta: sair fecha a conta e volta ao início", app, "conta" not in app.session_state and app.session_state["pagina"] == "inicio")
app = open_page("conta")
app.text_input(key="entrar_utilizador").input("ana.cossa")
app.text_input(key="entrar_senha").input("senha-errada-1")
app.button(key="entrar_enviar").click().run()
report("Conta: senha errada não entra, e não diz o que falhou", app, "conta" not in app.session_state and "O nome de utilizador ou a senha não estão certos" in page_text(app))
app.text_input(key="entrar_senha").input("Rio-Incomati-26")
app.button(key="entrar_enviar").click().run()
report("Conta: entra com a senha certa", app, "conta" in app.session_state and app.session_state["conta"]["utilizador"] == "ana.cossa")
app.session_state["pagina"] = "inicio"
app.run()
report("Conta: a primeira página cumprimenta pelo nome e leva ao lugar", app, ", Ana." in page_text(app) and any(b.key == "ir_minha_zona" for b in app.button))
app.session_state["pagina"] = "alertas"
app.run()
report("Conta: o formulário dos alertas já vem com o nome, o número e o lugar", app, app.session_state["pagina_nome"] == "Ana Cossa"
       and app.session_state["pagina_telefone"] == "+258 84 765 4321" and app.session_state["pagina_lugar"] == "Macaneta")
app.session_state["pagina"] = "conta"
app.run()
app.checkbox(key="conta_aceito").check()
app.button(key="conta_receber").click().run()
report("Conta: recebe os alertas no número da conta, com o nome completo", app,
       any(r["telefone"] == "258847654321" and r["nome"] == "Ana Cossa" and r["estado"] == "activa" for r in rows()))
app.text_input(key="apagar_senha").input("Rio-Incomati-26")
app.button(key="apagar_enviar").click().run()
report("Conta: apagar a conta (com a senha) apaga-a e pára os alertas", app, "conta" not in app.session_state and contas.entrar("ana.cossa", "Rio-Incomati-26")[0] == "errado"
       and not any(r["telefone"] == "258847654321" and r["estado"] == "activa" for r in rows()))

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
    app = open_page("zona", language, place="Machubo")
    shown = page_text(app)
    report(f"[{language}] boletim antigo: a página de um lugar também não mostra nível", app,
           unavailable in shown and not any(w in shown.upper() for w in ("ALERTA VERDE", "GREEN ALERT", "ALERTE VERTE", "ALERTA VERMELHO", "RED ALERT", "ALERTE ROUGE")))

print("APLICAÇÃO SEM ERROS" if not failures else f"{failures} ERRO(S)")
sys.exit(1 if failures else 0)
