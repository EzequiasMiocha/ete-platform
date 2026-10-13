"""Sistema de desenho da plataforma ETE: paleta, estilo e componentes de página.

Uma só fonte para as cores e as formas, para a plataforma ter o mesmo aspecto em todas as páginas.

Paleta
  marca       azul-marinho (cabeçalho, títulos), azul (acções), verde-água (realces)
  superfícies fundo cinzento muito claro, cartões brancos, linhas finas
  alertas     verde, amarelo, laranja, vermelho: SÓ para níveis de alerta, sempre com a palavra
  água        azul claro (normal), castanho (elevada), castanho escuro (muito elevada)
"""

from __future__ import annotations

from contextlib import contextmanager

import pandas as pd
import streamlit as st

NAVY, BLUE, TEAL = "#0B2A4A", "#1769AA", "#0E9AA7"
BG, CARD, BORDER, SOFT = "#F4F7FA", "#FFFFFF", "#E1E7EF", "#EAF2FA"
INK, MUTED = "#14212E", "#5A6B7D"
ALERT_TEXT = {"verde": "#FFFFFF", "amarelo": "#2B2300", "laranja": "#FFFFFF", "vermelho": "#FFFFFF"}
ALERT_WORD = {"verde": "Sem sinais de cheia", "amarelo": "Atenção", "laranja": "Preparação", "vermelho": "Cheia provável"}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MESES_LONGOS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

LOGO = ("<svg width='44' height='44' viewBox='0 0 44 44' xmlns='http://www.w3.org/2000/svg' aria-hidden='true'>"
        "<circle cx='22' cy='22' r='21' fill='#FFFFFF' fill-opacity='.12' stroke='#FFFFFF' stroke-opacity='.5'/>"
        "<path d='M6 22c5-8 11-12 16-12s11 4 16 12c-5 8-11 12-16 12S11 30 6 22z' fill='none' stroke='#FFFFFF' stroke-width='2'/>"
        "<circle cx='22' cy='22' r='6' fill='#7FD6DC'/>"
        "<path d='M9 33c4-3 7-3 11 0s7 3 11 0 4-2 5-2' fill='none' stroke='#7FD6DC' stroke-width='2' stroke-linecap='round'/></svg>")

_SVG = "<svg width='46' height='46' viewBox='0 0 24 24' fill='none' stroke='STROKE' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
ICONS = {"verde": _SVG + "<circle cx='12' cy='12' r='9'/><path d='M8 12.5l3 3 5-6'/></svg>",
         "amarelo": _SVG + "<path d='M12 3.5l9.5 16.5h-19z'/><path d='M12 10v4.5'/><circle cx='12' cy='17.3' r='.6'/></svg>",
         "laranja": _SVG + "<path d='M12 3.5l9.5 16.5h-19z'/><path d='M12 10v4.5'/><circle cx='12' cy='17.3' r='.6'/></svg>",
         "vermelho": _SVG + "<path d='M3 16c2-2 4-2 6 0s4 2 6 0 4-2 6 0'/><path d='M3 20c2-2 4-2 6 0s4 2 6 0 4-2 6 0'/><path d='M12 3v7'/><path d='M9 7.5l3 3 3-3'/></svg>",
         "indisponivel": _SVG + "<circle cx='12' cy='12' r='9'/><path d='M10 9v6M14 9v6'/></svg>"}

CSS = f"""
<style>
  .stApp {{background: {BG};}}
  header[data-testid="stHeader"] {{background: transparent; height: 0;}}
  .block-container {{padding-top: 1rem; padding-bottom: 3rem; max-width: 1180px;}}
  html, body, [class*="css"] {{color: {INK};}}
  h1, h2, h3 {{color: {NAVY}; letter-spacing: -.01em;}}
  h2 {{font-size: 1.35rem !important; margin-top: .4rem !important;}}
  h3 {{font-size: 1.08rem !important;}}

  /* top bar */
  .ete-top {{background: linear-gradient(120deg, {NAVY} 0%, #12497A 60%, {TEAL} 130%); border-radius: 18px; padding: 18px 22px; color: #fff;
            display: flex; align-items: center; gap: 14px; flex-wrap: wrap; box-shadow: 0 6px 22px rgba(11,42,74,.18);}}
  .ete-top .nome {{font-size: 1.28rem; font-weight: 700; line-height: 1.15;}}
  .ete-top .lema {{font-size: .88rem; opacity: .85;}}
  .ete-top .direita {{margin-left: auto; display: flex; gap: 8px; flex-wrap: wrap;}}
  .ete-pilula {{background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.28); border-radius: 999px; padding: 4px 12px; font-size: .8rem; white-space: nowrap;}}
  .ete-pilula i {{display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle;}}

  /* navigation: the page selector drawn as a tab bar */
  .st-key-pagina {{margin: 10px 0 6px 0;}}
  .st-key-pagina div[role="radiogroup"] {{background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 6px; gap: 4px; box-shadow: 0 1px 3px rgba(20,33,46,.05);}}
  .st-key-pagina label[data-testid="stRadioOption"] {{padding: 8px 13px !important; border-radius: 10px; margin: 0 !important; cursor: pointer; transition: background .15s;}}
  .st-key-pagina label[data-testid="stRadioOption"] div:has(+ div[data-testid="stMarkdownContainer"]) {{display: none;}}
  .st-key-pagina label[data-testid="stRadioOption"] p {{font-weight: 600; color: {MUTED}; font-size: .92rem; white-space: nowrap;}}
  .st-key-pagina label[data-testid="stRadioOption"]:hover {{background: {SOFT};}}
  .st-key-pagina label[data-testid="stRadioOption"]:has(input:checked) {{background: {NAVY};}}
  .st-key-pagina label[data-testid="stRadioOption"]:has(input:checked) p {{color: #fff;}}

  /* cards and tiles */
  .ete-cartao {{background: {CARD}; border: 1px solid {BORDER}; border-radius: 16px; padding: 16px 18px; box-shadow: 0 1px 3px rgba(20,33,46,.05); margin-bottom: 12px;}}
  .ete-cartao h4 {{margin: 0 0 6px 0; font-size: 1rem; color: {NAVY};}}
  .ete-olho {{text-transform: uppercase; letter-spacing: .08em; font-size: .72rem; font-weight: 700; color: {TEAL}; margin-bottom: 2px;}}
  .ete-sub {{color: {MUTED}; font-size: .93rem; margin: -2px 0 12px 0;}}
  .ete-heroi {{border-radius: 18px; padding: 22px 24px; display: flex; gap: 18px; align-items: flex-start; flex-wrap: wrap; box-shadow: 0 6px 22px rgba(20,33,46,.12); margin: 6px 0 14px 0;}}
  .ete-heroi .selo {{line-height: 0; background: rgba(255,255,255,.18); border-radius: 16px; padding: 12px;}}
  .ete-heroi .nivel {{font-size: 1.9rem; font-weight: 800; line-height: 1.1;}}
  .ete-heroi .palavra {{font-size: 1rem; font-weight: 600; opacity: .92;}}
  .ete-heroi .texto {{font-size: 1.02rem; margin-top: 6px; max-width: 760px;}}
  .ete-kpis {{display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 14px;}}
  .ete-kpi {{background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 12px 14px;}}
  .ete-kpi .rotulo {{color: {MUTED}; font-size: .78rem; font-weight: 600;}}
  .ete-kpi .valor {{font-size: 1.5rem; font-weight: 700; color: {NAVY}; line-height: 1.2;}}
  .ete-kpi .valor small {{font-size: .85rem; font-weight: 600; color: {MUTED};}}
  .ete-kpi .nota {{color: {MUTED}; font-size: .78rem;}}
  .ete-dias {{display: grid; grid-template-columns: repeat(auto-fit, minmax(64px, 1fr)); gap: 6px; margin: 4px 0 10px 0;}}
  .ete-dia {{border-radius: 12px; padding: 8px 4px; text-align: center; font-size: .78rem; line-height: 1.25; border: 3px solid transparent;}}
  .ete-dia b {{display: block; font-size: 1rem;}}
  .ete-dia.escolhido {{border-color: {NAVY}; box-shadow: 0 3px 10px rgba(11,42,74,.25);}}
  .ete-rio {{display: grid; grid-template-columns: repeat(auto-fit, minmax(92px, 1fr)); gap: 6px; margin: 6px 0 10px 0;}}
  .ete-troco {{background: {CARD}; border: 1px solid {BORDER}; border-top: 6px solid #bdc3c7; border-radius: 12px; padding: 8px 9px; font-size: .78rem; line-height: 1.3;}}
  .ete-troco b {{font-size: .98rem; color: {NAVY}; display: block;}}
  .ete-troco.escolhido {{box-shadow: 0 0 0 2px {NAVY};}}
  .ete-chip {{display: inline-block; border-radius: 999px; padding: 3px 11px; margin: 2px 4px 2px 0; font-size: .82rem; border: 1px solid {BORDER}; background: {CARD};}}
  .ete-ponto {{display: inline-block; width: .7em; height: .7em; border-radius: 50%; margin-right: .4em; vertical-align: middle;}}
  .ete-niveis {{display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px;}}
  .ete-nivel {{background: {CARD}; border: 1px solid {BORDER}; border-left: 8px solid #999; border-radius: 14px; padding: 12px 14px; font-size: .9rem;}}
  .ete-nivel b {{font-size: 1.05rem; display: block; color: {NAVY};}}
  .ete-passos {{display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; counter-reset: passo;}}
  .ete-passo {{background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 14px; font-size: .9rem; position: relative;}}
  .ete-passo::before {{counter-increment: passo; content: counter(passo); background: {TEAL}; color: #fff; width: 26px; height: 26px; border-radius: 50%;
                       display: inline-flex; align-items: center; justify-content: center; font-weight: 700; margin-bottom: 6px;}}
  .ete-passo b {{display: block; color: {NAVY};}}
  .ete-seletor {{text-align: center; font-weight: 700; color: {NAVY}; font-size: 1.05rem; padding-top: 6px;}}
  .ete-seletor small {{display: block; font-weight: 500; color: {MUTED}; font-size: .8rem;}}
  .ete-rodape {{color: {MUTED}; font-size: .8rem; border-top: 1px solid {BORDER}; margin-top: 2.2rem; padding-top: .8rem;}}

  /* native widgets, brought into the same look */
  div[data-testid="stExpander"] {{background: {CARD}; border-radius: 14px; border: 1px solid {BORDER};}}
  div[data-testid="stAlert"] {{border-radius: 14px;}}
  .stButton > button, .stDownloadButton > button {{border-radius: 10px; border: 1px solid {BORDER}; font-weight: 600;}}
  .stButton > button:hover {{border-color: {BLUE}; color: {BLUE};}}
  button[data-baseweb="tab"] p {{font-weight: 600;}}
  div[data-testid="stVegaLiteChart"], div[data-testid="stDataFrame"], iframe {{background: {CARD}; border-radius: 14px;}}
  div[data-testid="stVegaLiteChart"] {{border: 1px solid {BORDER}; overflow: hidden; box-sizing: border-box;}}
  div[data-testid="stImage"] img {{border-radius: 14px; border: 1px solid {BORDER};}}

  @media (max-width: 640px) {{
    .block-container {{padding-left: .7rem; padding-right: .7rem;}}
    .ete-top {{padding: 14px 16px;}} .ete-top .direita {{margin-left: 0;}}
    .ete-heroi .nivel {{font-size: 1.5rem;}}
    .st-key-pagina label[data-testid="stRadioOption"] {{padding: 7px 10px !important;}}
  }}
</style>
"""


# ----------------------------------------------------------------------------- building blocks
def html(text: str) -> None:
    st.markdown(text, unsafe_allow_html=True)


@contextmanager
def guard(what: str):
    """Error boundary: a broken section says so and the rest of the page still shows."""
    try:
        yield
    except Exception:                                        # last line of defence
        st.warning(f"Não foi possível mostrar: {what}.")


def top_bar(issued: str, valid: bool) -> None:
    dot = "#58D68D" if valid else "#F5B041"
    state = "boletim em dia" if valid else "boletim desactualizado"
    html(f"<div class='ete-top'>{LOGO}<div><div class='nome'>Eyes to Earth · Incomáti</div><div class='lema'>Cheias e água do rio em Marracuene, vistas por satélite</div></div>"
         f"<div class='direita'><span class='ete-pilula'><i style='background:{dot}'></i>{state}</span><span class='ete-pilula'>Boletim de {issued}</span></div></div>")


def section(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    html((f"<div class='ete-olho'>{eyebrow}</div>" if eyebrow else "") + f"<h2>{title}</h2>" + (f"<p class='ete-sub'>{subtitle}</p>" if subtitle else ""))


def hero(level: str, title: str, colour: str) -> None:
    html(f"<div class='ete-heroi' style='background:{colour};color:{ALERT_TEXT[level]}'><div class='selo'>{ICONS[level].replace('STROKE', ALERT_TEXT[level])}</div>"
         f"<div><div class='palavra'>{ALERT_WORD[level]}</div><div class='nivel'>Alerta {level.upper()}</div><div class='texto'>{title}</div></div></div>")


def hero_unavailable() -> None:
    html("<div class='ete-heroi' style='background:#56677A;color:#fff'><div class='selo'>" + ICONS["indisponivel"].replace("STROKE", "#FFFFFF") + "</div><div><div class='palavra'>Sem boletim válido</div>"
         "<div class='nivel'>Previsão indisponível</div><div class='texto'>Não há um boletim das últimas 36 horas. Isto não quer dizer que não há perigo. "
         "Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul.</div></div></div>")


def kpis(items: list[dict]) -> None:
    """Tiles: each item has rotulo, valor, and optionally unidade and nota."""
    tiles = "".join(f"<div class='ete-kpi'><div class='rotulo'>{i['rotulo']}</div><div class='valor'>{i['valor']}"
                    + (f" <small>{i['unidade']}</small>" if i.get("unidade") else "") + "</div>" + (f"<div class='nota'>{i['nota']}</div>" if i.get("nota") else "") + "</div>" for i in items)
    html(f"<div class='ete-kpis'>{tiles}</div>")


def card(title: str, body: str, eyebrow: str = "") -> None:
    html("<div class='ete-cartao'>" + (f"<div class='ete-olho'>{eyebrow}</div>" if eyebrow else "") + (f"<h4>{title}</h4>" if title else "") + body + "</div>")


def day_tiles(days: list[dict], colours: dict, chosen: int) -> None:
    tiles = "".join(f"<div class='ete-dia{' escolhido' if i == chosen else ''}' style='background:{colours[d['alerta']]};color:{ALERT_TEXT[d['alerta']]}'>"
                    f"<b>{pd.Timestamp(d['data']).strftime('%d/%m')}</b>{d['alerta']}</div>" for i, d in enumerate(days))
    html(f"<div class='ete-dias'>{tiles}</div>")


def river_tiles(state: pd.DataFrame, colours: dict, chosen: str | None = None) -> None:
    """The river from the border (left) to the mouth (right): one tile per section, topped by the colour of its state."""
    tiles = "".join(f"<div class='ete-troco{' escolhido' if code == chosen else ''}' style='border-top-color:{colours.get(row['classe'], '#bdc3c7')}'><b>{code}</b>"
                    f"{str(row['nome']).split(' ', 1)[1] if ' ' in str(row['nome']) else ''}<br><span style='color:{MUTED}'>{row['classe']}</span></div>" for code, row in state.iterrows())
    html(f"<div class='ete-rio'>{tiles}</div>")


def chips(items: list[tuple[str, str, str]]) -> None:
    html("".join(f"<span class='ete-chip'><span class='ete-ponto' style='background:{colour}'></span><b>{name}</b>{': ' + state if state else ''}</span>" for name, state, colour in items))


def legend(items: list[dict]) -> None:
    html(" ".join(f"<span class='ete-chip'><span class='ete-ponto' style='background:{i['cor']}'></span>{i['nome']}</span>" for i in items))


def level_cards(limits: dict, colours: dict, advice: dict) -> None:
    rules = {"verde": "Nenhum cenário passa os limites nos próximos 10 dias.",
             "amarelo": f"Caudal previsto acima de {limits.get('amarelo', 0):.0f} m³/s, ou chuva de 7 dias muito acima do normal.",
             "laranja": f"Caudal previsto acima de {limits.get('laranja', 0):.0f} m³/s em metade dos cenários, ou chuva excepcional.",
             "vermelho": f"Caudal previsto acima de {limits.get('vermelho', 0):.0f} m³/s em metade dos cenários."}
    cards = "".join(f"<div class='ete-nivel' style='border-left-color:{colours[k]}'><b>{k.capitalize()} · {ALERT_WORD[k]}</b>"
                    f"<span style='color:{MUTED}'>{rules[k]}</span><br><br>{advice[k]}</div>" for k in ("verde", "amarelo", "laranja", "vermelho"))
    html(f"<div class='ete-niveis'>{cards}</div>")


def steps(items: list[tuple[str, str]]) -> None:
    html("<div class='ete-passos'>" + "".join(f"<div class='ete-passo'><b>{title}</b>{text}</div>" for title, text in items) + "</div>")


def stepper(key: str, options: list, label=str, caption: str = "") -> object:
    """Back and forward buttons around a value: returns the chosen option. The position is kept in
    the session, so it survives moving between pages."""
    state = f"{key}_i"
    if state not in st.session_state or not 0 <= st.session_state[state] < len(options):
        st.session_state[state] = len(options) - 1 if key.startswith(("mes", "ano")) else 0

    def move(step: int) -> None:
        st.session_state[state] = min(max(st.session_state[state] + step, 0), len(options) - 1)

    left, middle, right = st.columns([1.4, 3, 1.4], vertical_alignment="center")
    left.button("◀ Anterior", key=f"{key}_prev", on_click=move, args=(-1,), disabled=st.session_state[state] == 0, use_container_width=True)
    right.button("Seguinte ▶", key=f"{key}_next", on_click=move, args=(1,), disabled=st.session_state[state] == len(options) - 1, use_container_width=True)
    chosen = options[st.session_state[state]]
    middle.markdown(f"<div class='ete-seletor'>{label(chosen)}<small>{caption or f'{st.session_state[state] + 1} de {len(options)}'}</small></div>", unsafe_allow_html=True)
    return chosen


def footer(text: str) -> None:
    html(f"<div class='ete-rodape'>{text}</div>")
