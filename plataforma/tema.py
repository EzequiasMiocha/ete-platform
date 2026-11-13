"""Sistema de desenho da plataforma ETE: paleta, tipografia, estilo e componentes de página.

Uma só fonte para as cores e as formas, para a plataforma ter o mesmo aspecto em todas as páginas
e não parecer uma aplicação Streamlit: barra de navegação fixa, tipografia própria, cartões,
tabelas em HTML e botões em forma de pílula.

Paleta "Incomáti"
  tinta       verde-escuro quase preto (texto, rodapé, botão principal)
  rio, lagoa  verdes-água profundos (marca, ligações, realces)
  espuma      verde-água muito claro (fundos suaves)
  areia       creme quente (fundo da página); cartões brancos, linhas finas cor de areia
  alertas     verde, amarelo, laranja, vermelho: SÓ para níveis de alerta, sempre com a palavra
  água        azul claro (normal), castanho (elevada), castanho escuro (muito elevada): vêm do catálogo

Tipografia
  títulos     Fraunces (serifa suave e calorosa)
  texto       Plus Jakarta Sans

Movimento
  entradas em cascata em todos os ecrãs; reacções ao passar o cursor só com rato ou trackpad
  (num ecrã táctil o "hover" fica preso depois de tocar); nada se mexe para quem pede menos
  movimento nas definições do sistema
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import idioma as L
from idioma import t

INK, RIO, LAGOA, MARE, ESPUMA = "#10231F", "#0B4F4A", "#0F766E", "#2BB5A0", "#E3F1EC"
AREIA, CARD, BORDER, SOFT = "#F7F3EA", "#FFFFFF", "#E8E1D2", "#F1ECDF"
MUTED = "#5C6B66"
NAVY, BLUE, TEAL, BG = INK, LAGOA, LAGOA, AREIA          # names used by earlier versions
ALERT_TEXT = {"verde": "#FFFFFF", "amarelo": "#2B2300", "laranja": "#FFFFFF", "vermelho": "#FFFFFF"}
ALERT_WORD = {"verde": "Sem sinais de cheia", "amarelo": "Atenção", "laranja": "Preparação", "vermelho": "Cheia provável"}
ALERT_HEADLINE = {"verde": "Sem sinais de cheia no Incomáti.", "amarelo": "Atenção ao rio Incomáti.", "laranja": "É tempo de preparação.",
                  "vermelho": "Cheia provável no Incomáti."}
LEVELS = ["verde", "amarelo", "laranja", "vermelho"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MESES_LONGOS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
DIAS_CURTOS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]

LOGO = ("<svg width='38' height='38' viewBox='0 0 44 44' xmlns='http://www.w3.org/2000/svg' aria-hidden='true'>"
        "<circle cx='22' cy='22' r='22' fill='#0B4F4A'/>"
        "<path d='M7 21c4.6-6.6 9.6-9.9 15-9.9S32.400 14.400 37 21c-4.600 6.600-9.600 9.900-15 9.900S11.600 27.600 7 21z' fill='none' stroke='#FFFFFF' stroke-width='2.200'/>"
        "<circle cx='22' cy='21' r='5.200' fill='#7FE0CE'/>"
        "<path d='M10 35c3.200-2.400 6-2.400 9.200 0s6 2.400 9.200 0 4.200-1.800 5.600-1.800' fill='none' stroke='#7FE0CE' stroke-width='2.200' stroke-linecap='round'/></svg>")

_SVG = "<svg width='SIZE' height='SIZE' viewBox='0 0 24 24' fill='none' stroke='STROKE' stroke-width='1.800' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
_PATHS = {
    "verde": "<circle cx='12' cy='12' r='9'/><path d='M8 12.500l3 3 5-6'/>",
    "amarelo": "<path d='M12 3.500l9.500 16.500h-19z'/><path d='M12 10v4.500'/><circle cx='12' cy='17.300' r='.600'/>",
    "laranja": "<path d='M12 3.500l9.500 16.500h-19z'/><path d='M12 10v4.500'/><circle cx='12' cy='17.300' r='.600'/>",
    "vermelho": "<path d='M3 16c2-2 4-2 6 0s4 2 6 0 4-2 6 0'/><path d='M3 20c2-2 4-2 6 0s4 2 6 0 4-2 6 0'/><path d='M12 3v7'/><path d='M9 7.500l3 3 3-3'/>",
    "indisponivel": "<circle cx='12' cy='12' r='9'/><path d='M10 9v6M14 9v6'/>",
    "gota": "<path d='M12 3.200c3.600 4.200 6 7.300 6 10.300a6 6 0 0 1-12 0c0-3 2.400-6.100 6-10.300z'/>",
    "onda": "<path d='M2.500 9c2.400-2.200 4.700-2.200 7.100 0s4.700 2.200 7.100 0 3.600-1.900 4.800-1.400'/><path d='M2.500 15c2.400-2.200 4.700-2.200 7.100 0s4.700 2.200 7.100 0 3.600-1.900 4.800-1.400'/>",
    "chuva": "<path d='M7 15.500a4.500 4.500 0 0 1 .600-8.960A5.500 5.500 0 0 1 18.200 8.300 3.700 3.700 0 0 1 17.500 15.500z'/><path d='M8.500 18.500l-.800 2M12.500 18.500l-.800 2M16.500 18.500l-.800 2'/>",
    "satelite": "<rect x='9' y='9' width='6' height='6' rx='1' transform='rotate(45 12 12)'/><path d='M5.200 9.800L2.800 7.400l3-3 2.400 2.400M18.800 14.200l2.400 2.400-3 3-2.400-2.400'/><path d='M4 17a3.200 3.200 0 0 0 3 3'/>",
    "mapa": "<path d='M12 21s-6.500-5.600-6.500-10.500a6.500 6.500 0 0 1 13 0C18.500 15.400 12 21 12 21z'/><circle cx='12' cy='10.500' r='2.300'/>",
    "pessoas": "<circle cx='9' cy='8.500' r='3'/><path d='M3.500 19.500c.500-3.300 2.700-5 5.500-5s5 1.700 5.500 5'/><circle cx='17' cy='9.500' r='2.300'/><path d='M16.500 14.600c2.300.200 3.700 1.700 4 4.400'/>",
    "escudo": "<path d='M12 3.200l7 2.600v5.400c0 4.300-2.900 7.800-7 9.600-4.100-1.800-7-5.300-7-9.600V5.800z'/><path d='M9 12l2.200 2.200L15 10.400'/>",
    "cerebro": "<circle cx='6' cy='7' r='2'/><circle cx='18' cy='7' r='2'/><circle cx='12' cy='12' r='2.200'/><circle cx='6' cy='17' r='2'/><circle cx='18' cy='17' r='2'/><path d='M7.700 8.200l2.600 2.400M16.300 8.200l-2.600 2.400M7.700 15.800l2.600-2.400M16.300 15.800l-2.600-2.400'/>",
    "relogio": "<circle cx='12' cy='12' r='9'/><path d='M12 7v5.200l3.300 2'/>",
    "mensagem": "<path d='M4 5.500h16v10.500H10.500L6 19.500V16H4z'/><path d='M8 9.500h8M8 12.500h5'/>",
    "campo": "<path d='M12 21V10'/><path d='M12 10c0-3.200 2-5.400 5.500-5.800C17.800 7.800 15.600 10 12 10z'/><path d='M12 14c0-2.600-1.700-4.400-4.700-4.800C7 12.300 8.900 14 12 14z'/><path d='M5 21h14'/>",
    "livro": "<path d='M4 5.500c2.800-.900 5.400-.600 8 1v12.500c-2.600-1.600-5.200-1.900-8-1z'/><path d='M20 5.500c-2.800-.900-5.400-.600-8 1v12.500c2.600-1.600 5.200-1.900 8-1z'/>",
    "info": "<circle cx='12' cy='12' r='9'/><path d='M12 11v5.500'/><circle cx='12' cy='7.800' r='.600'/>",
    "seta": "<path d='M5 12h14M13 6l6 6-6 6'/>",
    "calendario": "<rect x='4' y='5.500' width='16' height='14.500' rx='2.500'/><path d='M4 10h16M8.500 3.500v4M15.500 3.500v4'/>",
    "casa": "<path d='M4 11.500L12 4.500l8 7'/><path d='M6.500 10v9.500h11V10'/><path d='M10.300 19.500v-5h3.400v5'/>",
    "regua": "<path d='M4 19.500V5M4 19.500h16'/><path d='M7.500 15.500l3.500-4 3 2.500 4.500-6'/>",
}


def icon(name: str, size: int = 22, stroke: str = "currentColor") -> str:
    return _SVG.replace("SIZE", str(size)).replace("STROKE", stroke) + _PATHS.get(name, _PATHS["info"]) + "</svg>"


ICONS = {k: icon(k, 46, "STROKE") for k in ("verde", "amarelo", "laranja", "vermelho", "indisponivel")}      # kept for earlier callers

FONTES = "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..650&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap"

CSS = "<style>@import url('" + FONTES + "');" + """
:root {
  --tinta: #10231F; --rio: #0B4F4A; --lagoa: #0F766E; --mare: #2BB5A0; --espuma: #E3F1EC;
  --areia: #F7F3EA; --cartao: #FFFFFF; --linha: #E8E1D2; --suave: #F1ECDF; --mudo: #5C6B66;
  --titulo: 'Fraunces', 'Iowan Old Style', 'Palatino Linotype', Georgia, serif;
  --texto: 'Plus Jakarta Sans', 'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif;
  --raio: 22px; --raio-p: 14px;
  --sombra: 0 1px 2px rgba(16,35,31,.04), 0 8px 24px -12px rgba(16,35,31,.12);
  --sombra-alta: 0 2px 4px rgba(16,35,31,.05), 0 24px 48px -20px rgba(16,35,31,.28);
}

/* ---------------------------------------------------------------- page: no Streamlit chrome */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stAppDeployButton"], #MainMenu, footer, [data-testid="stSidebarCollapsedControl"] {display: none !important;}
.stApp {background: radial-gradient(1100px 520px at 88% -8%, #DCEFE8 0%, rgba(220,239,232,0) 62%), radial-gradient(900px 480px at -6% 4%, #F3E9D2 0%, rgba(243,233,210,0) 60%), var(--areia);}
html, body, .stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp button, .stApp textarea, .stApp table, [data-testid="stMarkdownContainer"] {font-family: var(--texto) !important;}
.stApp {color: var(--tinta);}
[data-testid="stMainBlockContainer"], .block-container {max-width: 1220px; padding: .8rem 1.4rem 0 1.4rem;}
[data-testid="stMarkdownContainer"] p {line-height: 1.6;}
.stApp a {color: var(--lagoa); text-underline-offset: 3px;}
::selection {background: #BFE6DA;}
[data-testid="stElementToolbar"] {display: none !important;}
[data-testid="stHeadingWithActionElements"] a, [data-testid="stHeaderActionElements"] {display: none !important;}
[data-stale="true"] {opacity: .75 !important; transition: opacity .3s ease;}
@keyframes ete-sobe {from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: none;}}
@keyframes ete-pulsa {0% {box-shadow: 0 0 0 0 rgba(43,181,160,.55);} 70% {box-shadow: 0 0 0 9px rgba(43,181,160,0);} 100% {box-shadow: 0 0 0 0 rgba(43,181,160,0);}}

/* ---------------------------------------------------------------- navigation bar (floating, sticky) */
.st-key-cabecalho {position: sticky; top: 10px; z-index: 9990; flex-flow: row wrap !important; align-items: center !important; gap: 6px 14px !important;
  background: rgba(255,255,255,.82); -webkit-backdrop-filter: saturate(160%) blur(16px); backdrop-filter: saturate(160%) blur(16px);
  border: 1px solid rgba(232,225,210,.9); border-radius: 26px; padding: 8px 10px 8px 14px; box-shadow: var(--sombra); margin-bottom: 14px;}
.st-key-cabecalho > div {width: auto !important; flex: 0 0 auto !important; min-width: 0;}
.st-key-cabecalho > .st-key-pagina {flex: 1 1 0 !important; width: 0 !important; min-width: 0; overflow: hidden;}
.st-key-pagina .stRadio {width: 100%;}
.ete-marca {display: flex; align-items: center; gap: 10px; text-decoration: none;}
.ete-marca .nome {font-family: var(--titulo); font-weight: 600; font-size: 1.120rem; line-height: 1.05; color: var(--tinta); letter-spacing: -.01em; white-space: nowrap;}
.ete-marca .lema {font-size: .680rem; color: var(--mudo); letter-spacing: .09em; text-transform: uppercase; font-weight: 600; white-space: nowrap;}
.ete-estado {display: flex; align-items: center; gap: 8px; background: var(--espuma); color: var(--rio); border-radius: 999px; padding: 7px 13px; font-size: .780rem; font-weight: 600; white-space: nowrap;}
.ete-estado i {width: 8px; height: 8px; border-radius: 50%; background: var(--mare); animation: ete-pulsa 2.400s infinite;}
.ete-estado.velho {background: #FBEBD3; color: #7A4A06;} .ete-estado.velho i {background: #E08A00; animation: none;}
.st-key-pagina div[role="radiogroup"] {flex-flow: row nowrap; gap: 1px; overflow-x: auto; scrollbar-width: none; justify-content: safe center;}
.st-key-pagina div[role="radiogroup"]::-webkit-scrollbar {display: none;}
.st-key-pagina label[data-testid="stRadioOption"] {padding: 8px 8px !important; border-radius: 999px; margin: 0 !important; cursor: pointer; transition: background .18s ease, color .18s ease; flex: 0 0 auto; background: transparent !important; border: 0 !important;}
.st-key-pagina label[data-testid="stRadioOption"] p {font-weight: 600; color: var(--mudo); font-size: .860rem; white-space: nowrap; line-height: 1.2;}
.st-key-pagina label[data-testid="stRadioOption"]:hover {background: var(--suave) !important;}
.st-key-pagina label[data-testid="stRadioOption"]:hover p {color: var(--tinta);}
.st-key-pagina label[data-testid="stRadioOption"][data-selected="true"] {background: var(--tinta) !important;}
.st-key-pagina label[data-testid="stRadioOption"][data-selected="true"] p {color: #fff;}

/* every radio: chips instead of round radio buttons */
label[data-testid="stRadioOption"] div:has(+ div[data-testid="stMarkdownContainer"]) {display: none !important;}
div[role="radiogroup"] {gap: 8px;}
label[data-testid="stRadioOption"] {background: var(--cartao); border: 1px solid var(--linha); border-radius: 999px; padding: 7px 14px !important; margin: 0 !important; cursor: pointer; transition: all .18s ease;}
label[data-testid="stRadioOption"] p {font-size: .880rem; font-weight: 600; color: var(--mudo);}
label[data-testid="stRadioOption"]:hover {border-color: var(--lagoa);}
label[data-testid="stRadioOption"][data-selected="true"] {background: var(--espuma); border-color: var(--lagoa);}
label[data-testid="stRadioOption"][data-selected="true"] p {color: var(--rio);}
[data-testid="stCheckbox"] [data-testid="stWidgetLabel"] p {font-size: .900rem !important; font-weight: 600 !important; letter-spacing: 0 !important; text-transform: none !important; color: var(--tinta) !important;}
[data-testid="stWidgetLabel"] p {font-size: .760rem !important; font-weight: 700 !important; letter-spacing: .08em; text-transform: uppercase; color: var(--mudo) !important;}

/* ---------------------------------------------------------------- text blocks */
.ete-olho {display: inline-flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: .14em; font-size: .700rem; font-weight: 700; color: var(--lagoa);}
.ete-olho::before {content: ""; width: 22px; height: 2px; border-radius: 2px; background: var(--mare);}
.ete-seccao {margin: 34px 0 14px 0;}
.ete-seccao .titulo {font-family: var(--titulo); font-weight: 560; font-size: clamp(1.450rem, 2.400vw, 1.900rem); line-height: 1.15; letter-spacing: -.015em; color: var(--tinta); margin-top: 6px;}
.ete-seccao .sub {color: var(--mudo); font-size: 1rem; margin-top: 6px; max-width: 760px; line-height: 1.55;}
.ete-cabeca {margin: 18px 0 20px 0; padding: 34px 36px; border-radius: 30px; background: linear-gradient(120deg, #FFFFFF 0%, #F3FAF7 60%, #E3F1EC 100%); border: 1px solid var(--linha); position: relative; overflow: hidden; animation: ete-sobe .5s ease both;}
.ete-cabeca .titulo {font-family: var(--titulo); font-weight: 560; font-size: clamp(1.900rem, 4vw, 2.900rem); line-height: 1.06; letter-spacing: -.02em; color: var(--tinta); margin-top: 10px; max-width: 820px;}
.ete-cabeca .sub {color: var(--mudo); font-size: 1.080rem; margin-top: 12px; max-width: 720px; line-height: 1.55;}
.ete-cabeca .arte {position: absolute; right: -30px; bottom: -40px; width: 380px; opacity: .55; pointer-events: none;}
.ete-sub {color: var(--mudo); font-size: .930rem; margin: 0 0 12px 0;}
.ete-legenda-texto {color: var(--mudo); font-size: .860rem; line-height: 1.55; margin: 2px 2px 14px 2px; max-width: 900px;}
.ete-legenda-texto b {color: var(--tinta);}
.ete-titulo-p {font-family: var(--titulo); font-weight: 560; font-size: 1.200rem; color: var(--tinta); margin: 18px 0 8px 0; letter-spacing: -.01em;}

/* ---------------------------------------------------------------- hero (first page) */
.ete-hero {position: relative; overflow: hidden; border-radius: 34px; padding: 46px 46px 42px 46px; color: #fff; display: grid; grid-template-columns: minmax(0, 1.450fr) minmax(280px, .850fr); gap: 34px; align-items: center;
  background: linear-gradient(135deg, #082F2C 0%, #0B4F4A 48%, #128074 100%); box-shadow: var(--sombra-alta); margin: 6px 0 16px 0; animation: ete-sobe .6s ease both;}
.ete-hero.nv-amarelo {background: linear-gradient(135deg, #17211F 0%, #23302D 55%, #4A4310 100%);}
.ete-hero.nv-laranja {background: linear-gradient(135deg, #3A1C08 0%, #7A3A0C 55%, #B8590F 100%);}
.ete-hero.nv-vermelho {background: linear-gradient(135deg, #3A0D09 0%, #7C1D14 55%, #B2301F 100%);}
.ete-hero.nv-indisponivel {background: linear-gradient(135deg, #252D31 0%, #3C484E 60%, #56656C 100%);}
.ete-hero .ondas {position: absolute; inset: auto 0 0 0; width: 100%; height: 62%; opacity: .16; pointer-events: none;}
.ete-hero .esq, .ete-hero .selo {position: relative; z-index: 1;}
.ete-hero .data {font-size: .780rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 600; opacity: .78;}
.ete-hero .grande {font-family: var(--titulo); font-weight: 500; font-size: clamp(2.100rem, 4.600vw, 3.700rem); line-height: 1.03; letter-spacing: -.025em; margin: 14px 0 0 0;}
.ete-hero .grande em {font-style: italic; font-weight: 400; color: #A8ECDD;}
.ete-hero.nv-amarelo .grande em {color: #F7DC6F;} .ete-hero.nv-laranja .grande em {color: #FFD9B0;} .ete-hero.nv-vermelho .grande em {color: #FFCFC6;} .ete-hero.nv-indisponivel .grande em {color: #D5DEE2;}
.ete-hero .lead {font-size: 1.080rem; line-height: 1.6; opacity: .92; max-width: 560px; margin: 16px 0 0 0;}
.ete-hero .fazer {margin-top: 22px; display: flex; gap: 12px; align-items: flex-start; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.18); border-radius: 18px; padding: 14px 16px; max-width: 580px;}
.ete-hero .fazer .ic {flex: 0 0 auto; line-height: 0; margin-top: 2px; opacity: .9;}
.ete-hero .fazer b {display: block; font-size: .720rem; letter-spacing: .12em; text-transform: uppercase; opacity: .78; margin-bottom: 3px;}
.ete-hero .fazer span {font-size: .980rem; line-height: 1.5;}
.ete-hero .selo {background: rgba(255,255,255,.97); color: var(--tinta); border-radius: 26px; padding: 24px 24px 20px 24px; box-shadow: 0 30px 60px -30px rgba(0,0,0,.55);}
.ete-hero .selo .topo {display: flex; align-items: center; gap: 14px;}
.ete-hero .selo .anel {flex: 0 0 auto; width: 66px; height: 66px; border-radius: 50%; display: flex; align-items: center; justify-content: center; line-height: 0;}
.ete-hero .selo .palavra {font-size: .760rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; color: var(--mudo);}
.ete-hero .selo .nivel {font-family: var(--titulo); font-weight: 600; font-size: 1.850rem; line-height: 1.1; letter-spacing: -.015em;}
.ete-escala {display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; margin: 20px 0 6px 0;}
.ete-escala span {height: 9px; border-radius: 9px; opacity: .22;}
.ete-escala span.activo {opacity: 1; box-shadow: 0 0 0 3px #fff, 0 0 0 5px var(--tinta);}
.ete-escala-nomes {display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; font-size: .700rem; color: var(--mudo); text-align: center; font-weight: 600;}
.ete-escala-nomes .activo {color: var(--tinta); font-weight: 700;}
.ete-hero .selo .pe {border-top: 1px solid var(--linha); margin-top: 16px; padding-top: 12px; font-size: .800rem; color: var(--mudo); line-height: 1.5;}
.ete-hero .selo .pe b {color: var(--tinta);}

/* ---------------------------------------------------------------- cards, tiles */
.ete-cartao {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); padding: 22px 24px; box-shadow: var(--sombra); margin-bottom: 14px; line-height: 1.6;}
.ete-cartao .cab {font-family: var(--titulo); font-weight: 560; font-size: 1.180rem; color: var(--tinta); margin: 6px 0 8px 0; letter-spacing: -.01em; line-height: 1.25;}
.ete-cartao p {margin: 0 0 8px 0;} .ete-cartao p:last-child {margin-bottom: 0;}
.ete-cartao.suave {background: var(--espuma); border-color: #CFE6DE; box-shadow: none;}
.ete-cartao.tinta {background: var(--tinta); border-color: var(--tinta); color: #E9F3F0;} .ete-cartao.tinta .cab {color: #fff;} .ete-cartao.tinta .ete-olho {color: #7FE0CE;}
.ete-kpis {display: grid; grid-template-columns: repeat(auto-fit, minmax(168px, 1fr)); gap: 12px; margin: 4px 0 16px 0;}
.ete-kpi {background: var(--cartao); border: 1px solid var(--linha); border-radius: 20px; padding: 18px 18px 16px 18px; box-shadow: var(--sombra); transition: transform .2s ease, box-shadow .2s ease;}
.ete-kpi:hover {transform: translateY(-2px); box-shadow: var(--sombra-alta);}
.ete-kpi .rotulo {color: var(--mudo); font-size: .760rem; font-weight: 600; line-height: 1.35; min-height: 2.050em;}
.ete-kpi .valor {font-family: var(--titulo); font-size: 2.050rem; font-weight: 560; color: var(--tinta); line-height: 1.1; letter-spacing: -.02em; margin-top: 6px; font-variant-numeric: lining-nums;}
.ete-kpi .valor small {font-family: var(--texto); font-size: .820rem; font-weight: 600; color: var(--mudo); letter-spacing: 0;}
.ete-kpi .nota {color: var(--mudo); font-size: .760rem; margin-top: 6px; line-height: 1.4;}
.ete-chip {display: inline-flex; align-items: center; border-radius: 999px; padding: 4px 12px; margin: 3px 6px 3px 0; font-size: .800rem; font-weight: 500; border: 1px solid var(--linha); background: var(--cartao); color: var(--tinta); line-height: 1.4;}
.ete-ponto {display: inline-block; width: .640em; height: .640em; border-radius: 50%; margin-right: .5em; flex: 0 0 auto; vertical-align: middle;}
.ete-grelha {display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 14px; margin-bottom: 14px;}
.ete-grelha .ete-cartao {margin-bottom: 0;}
.ete-carta-ic {width: 46px; height: 46px; border-radius: 14px; background: var(--espuma); color: var(--rio); display: flex; align-items: center; justify-content: center; line-height: 0; margin-bottom: 14px;}
.ete-resultado {font-family: var(--titulo); font-weight: 560; font-size: 1.350rem; color: var(--rio); margin: 10px 0 2px 0; letter-spacing: -.01em;}
.ete-miudo {color: var(--mudo); font-size: .820rem; line-height: 1.5;}

/* the ten days */
.ete-dias {display: grid; grid-template-columns: repeat(var(--n, 10), minmax(0, 1fr)); gap: 8px; margin: 10px 0 14px 0;}
.ete-dia {background: var(--cartao); border: 1px solid var(--linha); border-radius: 16px; padding: 10px 4px 9px 4px; text-align: center; line-height: 1.2; position: relative; overflow: hidden;}
.ete-dia .sem {font-size: .660rem; text-transform: uppercase; letter-spacing: .1em; color: var(--mudo); font-weight: 700;}
.ete-dia .num {font-family: var(--titulo); font-size: 1.350rem; font-weight: 560; color: var(--tinta); margin: 2px 0 4px 0;}
.ete-dia .nv {font-size: .680rem; font-weight: 600; color: var(--mudo); display: flex; align-items: center; justify-content: center;}
.ete-dia::after {content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 5px; background: var(--c, #bbb);}
.ete-dia.escolhido {background: var(--tinta); border-color: var(--tinta); box-shadow: var(--sombra-alta); transform: translateY(-3px);}
.ete-dia.escolhido .num {color: #fff;} .ete-dia.escolhido .sem, .ete-dia.escolhido .nv {color: #B9CFC9;}

/* the river, border to mouth: a line with nine stations */
.ete-rio-caixa {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); box-shadow: var(--sombra); padding: 22px 12px 16px 12px; margin: 6px 0 12px 0; overflow-x: auto;}
.ete-rio {display: grid; grid-auto-flow: column; grid-auto-columns: minmax(104px, 1fr); min-width: 100%;}
.ete-troco {position: relative; text-align: center; padding: 0 6px; font-size: .760rem; line-height: 1.35; color: var(--mudo);}
.ete-troco .fio {position: absolute; top: 15px; left: 0; right: 0; height: 8px; background: var(--c, #bdc3c7); opacity: .34;}
.ete-troco:first-child .fio {left: 50%; border-radius: 8px 0 0 8px;} .ete-troco:last-child .fio {right: 50%; border-radius: 0 8px 8px 0;}
.ete-troco .no {position: relative; z-index: 1; width: 38px; height: 38px; border-radius: 50%; margin: 0 auto 10px auto; background: var(--c, #bdc3c7); color: #fff; font-weight: 700; font-size: .780rem; display: flex; align-items: center; justify-content: center; border: 4px solid #fff; box-shadow: 0 0 0 1px var(--linha), 0 6px 14px -6px rgba(16,35,31,.4);}
.ete-troco b {display: block; color: var(--tinta); font-size: .840rem; font-weight: 600;}
.ete-troco .cls {display: inline-block; margin-top: 4px; padding: 2px 9px; border-radius: 999px; background: var(--suave); font-weight: 600; color: var(--tinta); font-size: .700rem;}
.ete-troco.escolhido .no {box-shadow: 0 0 0 3px var(--tinta), 0 8px 18px -6px rgba(16,35,31,.5); transform: scale(1.1);}
.ete-troco.escolhido b {color: var(--rio);}
.ete-rio-pontas {display: flex; justify-content: space-between; font-size: .680rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 700; color: var(--mudo); padding: 0 14px 12px 14px;}

/* alert levels explained */
.ete-niveis {display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; margin-bottom: 12px;}
.ete-nivel {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); overflow: hidden; box-shadow: var(--sombra); font-size: .900rem; line-height: 1.55;}
.ete-nivel .tampo {padding: 14px 18px; font-family: var(--titulo); font-weight: 600; font-size: 1.150rem;}
.ete-nivel .tampo small {display: block; font-family: var(--texto); font-size: .720rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; opacity: .85;}
.ete-nivel .corpo {padding: 14px 18px 18px 18px;}
.ete-nivel .regra {color: var(--mudo); font-size: .840rem; border-bottom: 1px dashed var(--linha); padding-bottom: 10px; margin-bottom: 10px;}

/* numbered steps */
.ete-passos {display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; counter-reset: passo; margin-bottom: 14px;}
.ete-passo {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); padding: 20px 20px 18px 20px; font-size: .900rem; line-height: 1.55; color: var(--mudo); box-shadow: var(--sombra);}
.ete-passo::before {counter-increment: passo; content: counter(passo, decimal-leading-zero); font-family: var(--titulo); font-size: 1.600rem; font-weight: 500; color: var(--mare); display: block; line-height: 1; margin-bottom: 10px;}
.ete-passo b {display: block; color: var(--tinta); font-size: 1rem; margin-bottom: 4px;}

/* notes (instead of Streamlit's coloured boxes) */
.ete-nota {display: flex; gap: 12px; align-items: flex-start; border-radius: 18px; padding: 14px 18px; margin: 4px 0 14px 0; font-size: .940rem; line-height: 1.55; background: var(--espuma); color: #0C3F3B; border: 1px solid #CFE6DE;}
.ete-nota .ic {flex: 0 0 auto; line-height: 0; margin-top: 2px;}
.ete-nota.aviso {background: #FFF6E3; color: #5C3D05; border-color: #F3E0B5;}
.ete-nota.neutra {background: var(--suave); color: var(--tinta); border-color: var(--linha);}

/* tables in HTML */
.ete-tabela-caixa {background: var(--cartao); border: 1px solid var(--linha); border-radius: 18px; overflow: auto; box-shadow: var(--sombra); margin: 4px 0 12px 0;}
table.ete-tabela {width: 100%; border-collapse: separate; border-spacing: 0; font-size: .860rem; line-height: 1.45;}
table.ete-tabela th {position: sticky; top: 0; z-index: 1; background: #FBF9F3; text-align: left; font-size: .700rem; letter-spacing: .08em; text-transform: uppercase; font-weight: 700; color: var(--mudo); padding: 12px 16px; border-bottom: 1px solid var(--linha); white-space: nowrap;}
table.ete-tabela {margin: 0 !important;}
table.ete-tabela th, table.ete-tabela td {border: 0 !important;}
table.ete-tabela th {border-bottom: 1px solid var(--linha) !important;}
table.ete-tabela td {padding: 11px 16px; border-bottom: 1px solid #F1ECE0 !important; color: var(--tinta); vertical-align: top;}
table.ete-tabela tr:last-child td {border-bottom: 0 !important;}
table.ete-tabela tbody tr:hover td {background: #FAFCFB;}
table.ete-tabela td.n, table.ete-tabela th.n {text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap;}
table.ete-tabela td:first-child {font-weight: 600; min-width: 130px;}
table.ete-tabela .ete-chip {margin: 0; padding: 2px 10px; font-size: .760rem; white-space: nowrap;}

/* stepper (back and forward) */
[class*="st-key-passo_"] {background: var(--cartao); border: 1px solid var(--linha); border-radius: 999px; padding: 5px 6px; box-shadow: var(--sombra); flex-flow: row nowrap !important; align-items: center !important; justify-content: space-between !important; max-width: 460px; margin: 2px auto 4px auto;}
[class*="st-key-passo_"] > div {width: auto !important; flex: 0 0 auto !important;}
[class*="st-key-passo_"] > div:has(.ete-seletor) {flex: 1 1 auto !important;}
[class*="st-key-passo_"] button {width: 40px !important; height: 40px !important; min-height: 0 !important; padding: 0 !important; border-radius: 50% !important; background: var(--suave) !important; border: 0 !important; color: var(--tinta) !important; box-shadow: none !important;}
[class*="st-key-passo_"] button p {font-size: 1.150rem !important; line-height: 1 !important;}
[class*="st-key-passo_"] button:hover:not(:disabled) {background: var(--tinta) !important; color: #fff !important; transform: none !important;}
[class*="st-key-passo_"] button:disabled {opacity: .35;}
.ete-seletor {text-align: center; font-weight: 700; color: var(--tinta); font-size: .950rem; line-height: 1.2; padding: 0 8px;}
[class*="st-key-passo_"] [data-testid="stMarkdownContainer"] {margin: 0 !important;}
.ete-seletor small {display: block; font-weight: 500; color: var(--mudo); font-size: .720rem; line-height: 1.3;}

/* message for community leaders: a phone bubble */
.ete-msg {max-width: 460px; background: #E9F7EF; border: 1px solid #CDE9D8; border-radius: 6px 20px 20px 20px; padding: 14px 16px 10px 16px; font-size: .920rem; line-height: 1.5; white-space: pre-wrap; color: #14302A; box-shadow: var(--sombra); margin: 6px 0 12px 0;}
.ete-msg .hora {display: block; text-align: right; font-size: .700rem; color: #5F7A70; margin-top: 6px;}

/* footer */
.ete-rodape {margin: 56px -1.4rem 0 -1.4rem; background: var(--tinta); color: #C7D6D1; border-radius: 34px 34px 0 0; padding: 44px 46px 30px 46px; font-size: .880rem; line-height: 1.65;}
.ete-rodape .cols {display: grid; grid-template-columns: 1.350fr 1fr 1.150fr 1.150fr; gap: 34px;}
.ete-rodape .nome {font-family: var(--titulo); font-size: 1.500rem; color: #fff; font-weight: 500; letter-spacing: -.01em; display: flex; align-items: center; gap: 12px; margin-bottom: 10px;}
.ete-rodape h6, .ete-rodape .h {font-size: .700rem; letter-spacing: .14em; text-transform: uppercase; color: #7FE0CE; font-weight: 700; margin: 0 0 10px 0; padding: 0;}
.ete-rodape a {color: #fff !important; text-decoration: underline; text-decoration-color: rgba(255,255,255,.35);}
.ete-rodape .fim {border-top: 1px solid rgba(255,255,255,.14); margin-top: 28px; padding-top: 18px; font-size: .780rem; color: #9DB3AD; display: flex; flex-wrap: wrap; gap: 6px 20px; justify-content: space-between;}

/* ---------------------------------------------------------------- native widgets, brought into the same look */
.stButton > button, .stDownloadButton > button {border-radius: 999px !important; border: 1px solid var(--linha) !important; background: var(--cartao) !important; color: var(--tinta) !important; font-weight: 600 !important; padding: .580rem 1.200rem !important;
  box-shadow: 0 1px 2px rgba(16,35,31,.05); transition: transform .18s ease, box-shadow .18s ease, background .18s ease, border-color .18s ease !important;}
.stButton > button p, .stDownloadButton > button p {font-weight: 600 !important; font-size: .900rem !important;}
.stButton > button:hover, .stDownloadButton > button:hover {border-color: var(--tinta) !important; transform: translateY(-1px); box-shadow: 0 8px 18px -10px rgba(16,35,31,.45);}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible, label[data-testid="stRadioOption"]:has(input:focus-visible) {outline: 3px solid #9ADBCB !important; outline-offset: 2px;}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"], .stDownloadButton > button[data-testid="stBaseButton-primary"] {background: var(--tinta) !important; border-color: var(--tinta) !important; color: #fff !important;}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {background: var(--rio) !important; border-color: var(--rio) !important;}
.stButton > button[kind="tertiary"], .stButton > button[data-testid="stBaseButton-tertiary"] {background: transparent !important; border-color: transparent !important; color: var(--lagoa) !important; box-shadow: none !important; padding-left: .2rem !important;}

/* tabs as a row of pills */
[data-testid="stTabs"] [role="tablist"] {gap: 4px !important; background: var(--suave); border-radius: 999px; padding: 5px; width: fit-content; max-width: 100%; overflow-x: auto; scrollbar-width: none;
  border: 1px solid var(--linha) !important; box-shadow: none !important; flex-wrap: nowrap;}
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar {display: none;}
[data-testid="stTabs"] [role="tablist"]::before, [data-testid="stTabs"] [role="tablist"]::after, [data-testid="stTabs"] > div::before, [data-testid="stTabs"] > div::after {display: none !important;}
[data-testid="stTabs"] > div {border: 0 !important; box-shadow: none !important;}
[data-testid="stTabs"] .react-aria-SelectionIndicator, [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {display: none !important;}
[data-testid="stTab"] {border-radius: 999px !important; padding: 9px 17px !important; height: auto !important; background: transparent !important; margin: 0 !important; flex: 0 0 auto; cursor: pointer; border: 0 !important; transition: background .18s ease;}
[data-testid="stTab"] p {font-weight: 600 !important; font-size: .880rem !important; color: var(--mudo) !important; white-space: nowrap; line-height: 1.2;}
[data-testid="stTab"]:hover p {color: var(--tinta) !important;}
[data-testid="stTab"][data-selected="true"] {background: var(--cartao) !important; box-shadow: 0 1px 2px rgba(16,35,31,.08), 0 6px 14px -8px rgba(16,35,31,.3);}
[data-testid="stTab"][data-selected="true"] p {color: var(--tinta) !important;}
[data-testid="stTab"]:focus-visible {outline: 3px solid #9ADBCB; outline-offset: 1px;}
[data-testid="stTabs"] [role="tabpanel"] {padding-top: 20px !important;}

/* accordion */
[data-testid="stExpander"] {border: 0 !important; margin-bottom: 2px;}
[data-testid="stExpander"] details {background: var(--cartao); border: 1px solid var(--linha) !important; border-radius: 18px !important; box-shadow: var(--sombra); overflow: hidden;}
[data-testid="stExpander"] summary {padding: 15px 20px !important; border-radius: 18px;}
[data-testid="stExpander"] summary p {font-weight: 600 !important; font-size: .960rem !important; color: var(--tinta);}
[data-testid="stExpander"] summary:hover {background: #FAFCFB; color: var(--rio) !important;}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {padding: 2px 20px 18px 20px !important;}

/* inputs */
[data-baseweb="select"] > div {border-radius: 14px !important; border-color: var(--linha) !important; background: var(--cartao) !important; min-height: 44px;}
[data-baseweb="select"] > div:hover {border-color: var(--lagoa) !important;}
[data-baseweb="tag"] {border-radius: 999px !important; background: var(--espuma) !important; color: var(--rio) !important;}
[data-baseweb="tag"] span, [data-baseweb="tag"] svg {color: var(--rio) !important; fill: var(--rio) !important;}
[data-baseweb="popover"] ul {border-radius: 14px !important;}
[data-testid="stAlert"] > div, [data-testid="stAlertContainer"] {border-radius: 18px !important;}
[data-testid="stCaptionContainer"] p {color: var(--mudo) !important; font-size: .860rem !important; line-height: 1.55 !important;}
[data-testid="stCaptionContainer"] strong {color: var(--tinta);}

/* charts, maps and images as cards */
[data-testid="stVegaLiteChart"] {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); box-shadow: var(--sombra); padding: 16px 14px 8px 14px; box-sizing: border-box; overflow: hidden;}
[data-testid="stVegaLiteChart"] summary {display: none !important;}
[data-testid="stImage"] img {border-radius: var(--raio); border: 1px solid var(--linha); box-shadow: var(--sombra); background: var(--cartao);}
[data-testid="stImage"] button, [data-testid="StyledFullScreenButton"] {display: none !important;}
iframe[title*="folium"], [data-testid="stCustomComponentV1"] {border-radius: var(--raio); border: 1px solid var(--linha) !important; box-shadow: var(--sombra); background: var(--cartao);}
[data-testid="stCode"] pre, [data-testid="stCodeBlock"] pre {border-radius: 6px 20px 20px 20px !important; background: #E9F7EF !important; border: 1px solid #CDE9D8; font-family: var(--texto) !important; white-space: pre-wrap !important;}
[data-testid="stCode"] code, [data-testid="stCodeBlock"] code {font-family: var(--texto) !important; font-size: .920rem !important; white-space: pre-wrap !important; color: #14302A !important;}

/* ---------------------------------------------------------------- utility bar: bulletin, contacts, language */
.st-key-utilidades {flex-flow: row wrap !important; align-items: center !important; justify-content: space-between !important; gap: 8px 14px !important;
  background: var(--tinta); border-radius: 20px; padding: 7px 8px 7px 16px; margin: 0 0 8px 0; box-shadow: var(--sombra);}
.st-key-utilidades > div {width: auto !important; flex: 0 0 auto !important;}
.st-key-utilidades > div:first-child {flex: 1 1 auto !important; min-width: 0;}
.st-key-utilidades [data-testid="stMarkdownContainer"], .st-key-utilidades .stMarkdown {margin: 0 !important;}
.st-key-utilidades .ete-estado {background: transparent; color: #CFE3DC; padding: 0; font-weight: 500;}
.st-key-utilidades .ete-estado span {white-space: normal;}
.st-key-utilidades .ete-estado .sep {opacity: .45; margin: 0 8px;}
.st-key-utilidades .ete-estado.velho {color: #F6C77A;}
.ete-redes {display: flex; gap: 8px; align-items: center; margin: 4px 0 14px 0;}
.ete-redes.pequenas {margin: 0; gap: 4px;}
.ete-rede {width: 38px; height: 38px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: #E9F3F0 !important;
  background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); text-decoration: none !important;}
.ete-redes.claras .ete-rede {color: var(--rio) !important; background: var(--espuma); border-color: #CFE6DE; width: 42px; height: 42px;}
.ete-redes.pequenas .ete-rede {width: 32px; height: 32px; background: transparent; border-color: transparent;}
.ete-rede svg {display: block;}
/* the language switch: a pill with the three languages, the chosen one filled */
.st-key-lingua div[role="radiogroup"] {flex-flow: row nowrap; gap: 0 !important; border: 1.500px solid var(--mare); border-radius: 999px; padding: 2px; background: transparent;}
.st-key-lingua label[data-testid="stRadioOption"] {background: transparent !important; border: 0 !important; border-radius: 999px !important; padding: 5px 13px !important; min-width: 0;}
.st-key-lingua label[data-testid="stRadioOption"] p {color: #E9F3F0 !important; font-weight: 700 !important; font-size: .780rem !important; letter-spacing: .06em;}
.st-key-lingua label[data-testid="stRadioOption"][data-selected="true"] {background: var(--mare) !important;}
.st-key-lingua label[data-testid="stRadioOption"][data-selected="true"] p {color: var(--tinta) !important;}
.st-key-lingua label[data-testid="stRadioOption"]:not([data-selected="true"]):hover {background: rgba(43,181,160,.18) !important; transform: none !important;}
/* logos */
.ete-marca img {display: block; width: 44px; height: 44px; border-radius: 50%; box-shadow: 0 0 0 2px #fff, 0 0 0 3px var(--linha);}
.ete-rodape .nome img {border-radius: 50%; box-shadow: 0 0 0 2px rgba(255,255,255,.15);}
.ete-apoios {display: flex; flex-wrap: wrap; align-items: center; gap: 18px 26px; margin: 2px 0 6px 0;}
.ete-apoios a {background: none !important; line-height: 0; opacity: .92;}
.ete-apoios img {display: block; width: auto;}
.ete-rodape p.contacto {margin: 0 0 8px 0; display: flex; flex-direction: column;}
.ete-rodape p.contacto a {font-size: .820rem; overflow-wrap: anywhere;}
.ete-rodape p.contacto span {font-size: .720rem; letter-spacing: .08em; text-transform: uppercase; color: #9DB3AD;}
.ete-cartao .ete-apoios img {height: 58px;}

/* ---------------------------------------------------------------- WhatsApp alerts: top-bar button, invitation window, sign-up form */
.st-key-ir_alertas button {background: var(--mare) !important; border-color: var(--mare) !important; color: var(--tinta) !important; padding: .380rem .950rem !important; min-height: 0 !important;}
.st-key-ir_alertas button p {font-size: .800rem !important; font-weight: 700 !important;}
.st-key-ir_alertas button:hover {background: #7FE0CE !important; border-color: #7FE0CE !important;}
div[role="dialog"] {border-radius: 28px !important; border: 1px solid var(--linha); box-shadow: 0 40px 80px -30px rgba(16,35,31,.45) !important; background: var(--cartao) !important;}
div[role="dialog"] h2, div[role="dialog"] [data-testid="stHeading"] * {font-family: var(--titulo) !important; font-weight: 560 !important; color: var(--tinta); letter-spacing: -.01em;}
.ete-convite {display: flex; gap: 14px; align-items: flex-start; background: var(--espuma); border-radius: 18px; padding: 14px 16px; margin-bottom: 6px;}
.ete-convite .ic {flex: 0 0 auto; width: 52px; height: 52px; border-radius: 16px; background: var(--lagoa); color: #fff; display: flex; align-items: center; justify-content: center; line-height: 0;}
.ete-convite ul {margin: 0; padding-left: 1.100rem; color: #0C3F3B; font-size: .930rem; line-height: 1.55;}
.ete-convite li {margin-bottom: 4px;}
.st-key-caixa_inscricao {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); padding: 18px 22px 20px 22px; box-shadow: var(--sombra);}
.st-key-caixa_inscricao .ete-titulo-p {margin-top: 2px;}
.st-key-caixa_sair {max-width: 560px;}
[data-baseweb="input"], [data-baseweb="base-input"] {border-radius: 14px !important; background: var(--cartao) !important;}
[data-baseweb="input"] {border-color: var(--linha) !important; min-height: 46px;}
[data-baseweb="input"]:focus-within {border-color: var(--lagoa) !important; box-shadow: 0 0 0 3px rgba(43,181,160,.2);}
[data-testid="stCheckbox"] label p {font-size: .900rem !important; line-height: 1.5 !important; color: var(--tinta) !important;}
[data-testid="stForm"] {border: 0 !important; padding: 0 !important;}
.stFormSubmitButton > button {border-radius: 999px !important; font-weight: 700 !important; padding: .700rem 1.200rem !important; border: 1px solid var(--linha) !important;}
.stFormSubmitButton > button[data-testid="stBaseButton-primary"] {background: var(--tinta) !important; border-color: var(--tinta) !important; color: #fff !important;}
.stFormSubmitButton > button[data-testid="stBaseButton-primary"]:hover {background: var(--rio) !important;}

/* ---------------------------------------------------------------- advice: situations of the day and advice lists */
.ete-situacoes {display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-bottom: 14px;}
.ete-situacao {background: var(--cartao); border: 1px solid var(--linha); border-top: 6px solid var(--c); border-radius: var(--raio); padding: 18px 20px; box-shadow: var(--sombra); font-size: .920rem; line-height: 1.55;}
.ete-situacao .cab, .ete-conselho .cab {font-family: var(--titulo); font-weight: 560; font-size: 1.150rem; color: var(--tinta); margin: 8px 0 4px 0; letter-spacing: -.01em; line-height: 1.25;}
.ete-situacao p {margin: 0; color: var(--mudo);}
.ete-situacao .porque {margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--linha); font-size: .840rem; color: var(--tinta);}
.prio {display: inline-block; background: var(--f); color: var(--c); font-size: .700rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; border-radius: 999px; padding: 3px 10px;}
.ete-conselho {background: var(--cartao); border: 1px solid var(--linha); border-left: 6px solid var(--c); border-radius: var(--raio); padding: 18px 22px; box-shadow: var(--sombra); margin-bottom: 14px;}
.ete-conselho .topo {display: flex; align-items: center; gap: 10px; flex-wrap: wrap;}
.ete-conselho ul {list-style: none; margin: 8px 0 0 0; padding: 0;}
.ete-conselho li {display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid #F1ECE0; font-size: .960rem; line-height: 1.5; color: var(--tinta);}
.ete-conselho li:last-child {border-bottom: 0;}
.ete-conselho li .v {flex: 0 0 auto; width: 26px; height: 26px; border-radius: 50%; background: var(--f); color: var(--c); display: flex; align-items: center; justify-content: center; line-height: 0; margin-top: 1px;}
.st-key-publico_conselhos div[role="radiogroup"] {gap: 8px; flex-wrap: wrap;}
.st-key-publico_conselhos label[data-testid="stRadioOption"] {padding: 9px 16px !important;}
.st-key-publico_conselhos label[data-testid="stRadioOption"][data-selected="true"] {background: var(--tinta) !important; border-color: var(--tinta) !important;}
.st-key-publico_conselhos label[data-testid="stRadioOption"][data-selected="true"] p {color: #fff !important;}
.ete-diarreia {background: #FFF6E3; border: 1px solid #F3E0B5; border-radius: var(--raio); padding: 18px 22px; color: #3F2A05; line-height: 1.55;}
.ete-diarreia .cab {font-family: var(--titulo); font-weight: 560; font-size: 1.180rem; margin-bottom: 6px;}
.ete-diarreia ol {margin: 0; padding-left: 1.200rem;} .ete-diarreia li {margin-bottom: 6px;}
@media (hover: hover) and (pointer: fine) {
  .ete-situacao, .ete-conselho {transition: transform var(--medio) var(--mola), box-shadow var(--medio) var(--mola);}
  .ete-situacao:hover, .ete-conselho:hover {transform: translateY(-3px); box-shadow: var(--sombra-alta);}
  .ete-conselho li .v {transition: transform var(--medio) var(--mola);}
  .ete-conselho li:hover .v {transform: scale(1.15) rotate(-8deg);}
}

/* ---------------------------------------------------------------- motion
   Hover effects only where there is a real pointer (mouse or trackpad): on a phone a "hover"
   sticks after a tap, so touch screens get the entrances but no lifts. Everything stops for
   people who ask their system for less motion (rule at the end of this sheet). */
:root {--mola: cubic-bezier(.22,1,.36,1); --rapido: .22s; --medio: .38s;}
@keyframes ete-respira {from {transform: translateY(0) scaleY(1);} to {transform: translateY(-10px) scaleY(1.08);}}
@keyframes ete-deriva {from {transform: translateX(0);} to {transform: translateX(-26px);}}
@keyframes ete-anel {0% {box-shadow: 0 0 0 0 var(--c, #2BB5A0);} 100% {box-shadow: 0 0 0 14px rgba(255,255,255,0);}}
@keyframes ete-brilho {from {transform: translateX(-120%) skewX(-18deg);} to {transform: translateX(260%) skewX(-18deg);}}
@keyframes ete-entra {from {opacity: 0; transform: translateY(14px) scale(.985);} to {opacity: 1; transform: none;}}

/* always: the hero waves breathe slowly, and blocks arrive one after another */
.ete-hero .ondas {transform-origin: 50% 100%; animation: ete-respira 9s ease-in-out infinite alternate;}
.ete-cabeca .arte {animation: ete-deriva 14s ease-in-out infinite alternate;}
.ete-kpi, .ete-grelha > .ete-cartao, .ete-passo, .ete-nivel, .ete-dia, .ete-troco, .ete-hero .selo {animation: ete-entra .6s var(--mola) backwards;}
.ete-kpi:nth-child(2), .ete-grelha > :nth-child(2), .ete-passo:nth-child(2), .ete-nivel:nth-child(2), .ete-dia:nth-child(2), .ete-troco:nth-child(2) {animation-delay: .05s;}
.ete-kpi:nth-child(3), .ete-grelha > :nth-child(3), .ete-passo:nth-child(3), .ete-nivel:nth-child(3), .ete-dia:nth-child(3), .ete-troco:nth-child(3) {animation-delay: .1s;}
.ete-kpi:nth-child(4), .ete-grelha > :nth-child(4), .ete-passo:nth-child(4), .ete-nivel:nth-child(4), .ete-dia:nth-child(4), .ete-troco:nth-child(4) {animation-delay: .15s;}
.ete-kpi:nth-child(5), .ete-grelha > :nth-child(5), .ete-passo:nth-child(5), .ete-dia:nth-child(5), .ete-troco:nth-child(5) {animation-delay: .2s;}
.ete-kpi:nth-child(6), .ete-grelha > :nth-child(6), .ete-passo:nth-child(6), .ete-dia:nth-child(6), .ete-troco:nth-child(6) {animation-delay: .25s;}
.ete-dia:nth-child(7), .ete-troco:nth-child(7) {animation-delay: .3s;} .ete-dia:nth-child(8), .ete-troco:nth-child(8) {animation-delay: .35s;}
.ete-dia:nth-child(9), .ete-troco:nth-child(9) {animation-delay: .4s;} .ete-dia:nth-child(n+10) {animation-delay: .45s;}
.ete-hero .selo {animation-delay: .25s;}

/* pressing anything clickable gives a small physical "push" */
.stButton > button:active, .stDownloadButton > button:active, label[data-testid="stRadioOption"]:active, [data-testid="stTab"]:active {transform: scale(.96) !important; transition-duration: .08s !important;}

@media (hover: hover) and (pointer: fine) {
  /* cards rise a little and their border takes the river colour */
  .ete-cartao, .ete-kpi, .ete-passo, .ete-nivel, .ete-msg, .ete-rio-caixa, .ete-tabela-caixa, .ete-nota,
  [data-testid="stVegaLiteChart"], [data-testid="stImage"] img, [data-testid="stExpander"] details {
    transition: transform var(--medio) var(--mola), box-shadow var(--medio) var(--mola), border-color var(--medio) ease, background-color var(--medio) ease;}
  .ete-cartao:hover, .ete-passo:hover, .ete-nivel:hover, .ete-kpi:hover {transform: translateY(-4px); box-shadow: var(--sombra-alta); border-color: #BFE0D6;}
  .ete-cartao.tinta:hover {border-color: var(--rio);}
  .ete-msg:hover {transform: translateY(-3px) rotate(-.4deg); box-shadow: var(--sombra-alta);}
  .ete-rio-caixa:hover, .ete-tabela-caixa:hover, [data-testid="stVegaLiteChart"]:hover, [data-testid="stExpander"] details:hover {box-shadow: var(--sombra-alta); border-color: #CFE6DE;}
  [data-testid="stImage"] img:hover {transform: scale(1.012); box-shadow: var(--sombra-alta);}
  .ete-nota:hover {transform: translateX(3px);}

  /* the number in a tile turns river-green and a thin line grows under it */
  .ete-kpi {position: relative; overflow: hidden;}
  .ete-kpi::after {content: ""; position: absolute; left: 18px; bottom: 0; height: 3px; width: 0; border-radius: 3px 3px 0 0; background: linear-gradient(90deg, var(--mare), var(--lagoa)); transition: width .5s var(--mola);}
  .ete-kpi:hover::after {width: calc(100% - 36px);}
  .ete-kpi .valor {transition: color var(--medio) ease, transform var(--medio) var(--mola); transform-origin: left bottom;}
  .ete-kpi:hover .valor {color: var(--rio); transform: scale(1.04);}

  /* card icons fill with colour and turn a little; step numbers grow */
  .ete-carta-ic {transition: transform .5s var(--mola), background-color var(--medio) ease, color var(--medio) ease;}
  .ete-cartao:hover .ete-carta-ic {transform: rotate(-8deg) scale(1.08); background: var(--lagoa); color: #fff;}
  .ete-passo::before {transition: transform .5s var(--mola), color var(--medio) ease; transform-origin: left bottom;}
  .ete-passo:hover::before {transform: scale(1.18); color: var(--lagoa);}
  .ete-passo b, .ete-cartao .cab {transition: color var(--medio) ease;}
  .ete-passo:hover b, .ete-cartao:not(.tinta):hover .cab {color: var(--rio);}
  .ete-resultado {transition: letter-spacing var(--medio) var(--mola);}
  .ete-nivel .tampo {transition: padding var(--medio) var(--mola);}
  .ete-nivel:hover .tampo {padding-left: 24px;}

  /* chips */
  .ete-chip {transition: transform var(--rapido) var(--mola), border-color var(--rapido) ease, box-shadow var(--rapido) ease;}
  .ete-chip:hover {transform: translateY(-2px); border-color: var(--lagoa); box-shadow: 0 6px 12px -8px rgba(15,118,110,.6);}
  .ete-chip .ete-ponto {transition: transform var(--rapido) var(--mola);}
  .ete-chip:hover .ete-ponto {transform: scale(1.4);}

  /* the ten days: a day rises and its alert bar thickens */
  .ete-dia {transition: transform var(--medio) var(--mola), box-shadow var(--medio) var(--mola), border-color var(--rapido) ease;}
  .ete-dia::after {transition: height var(--medio) var(--mola);}
  .ete-dia:hover {transform: translateY(-5px); box-shadow: var(--sombra-alta); border-color: var(--c);}
  .ete-dia:hover::after {height: 9px;}
  .ete-dia.escolhido:hover {transform: translateY(-6px);}

  /* the river: a station swells and sends out a ripple in its own colour */
  .ete-troco .no {transition: transform .45s var(--mola);}
  .ete-troco:hover .no {transform: scale(1.22); animation: ete-anel 1.1s ease-out infinite;}
  .ete-troco b {transition: color var(--rapido) ease;}
  .ete-troco:hover b {color: var(--rio);}
  .ete-troco .fio {transition: opacity var(--medio) ease;}
  .ete-troco:hover .fio {opacity: .7;}

  /* hero: the status card leans in, the active level glows, the waves speed up */
  .ete-hero .selo {transition: transform .6s var(--mola), box-shadow .6s var(--mola);}
  .ete-hero .selo:hover {transform: translateY(-6px) rotate(-.6deg); box-shadow: 0 40px 70px -30px rgba(0,0,0,.6);}
  .ete-hero .selo .anel {transition: transform .6s var(--mola);}
  .ete-hero .selo:hover .anel {transform: rotate(-10deg) scale(1.06);}
  .ete-escala span {transition: opacity var(--medio) ease, transform var(--medio) var(--mola);}
  .ete-escala:hover span {opacity: .55;}
  .ete-escala span:hover {opacity: 1; transform: scaleY(1.6);}
  .ete-hero:hover .ondas {animation-duration: 4s;}
  .ete-hero .fazer {transition: background-color var(--medio) ease, transform var(--medio) var(--mola);}
  .ete-hero .fazer:hover {background: rgba(255,255,255,.16); transform: translateX(4px);}
  .ete-cabeca .arte {transition: opacity .6s ease;}
  .ete-cabeca:hover .arte {opacity: .85; animation-duration: 5s;}

  /* buttons: a sweep of light crosses the main ones, the arrows nudge */
  .stButton > button, .stDownloadButton > button {position: relative; overflow: hidden;}
  .stButton > button[data-testid="stBaseButton-primary"]::after, .stDownloadButton > button[data-testid="stBaseButton-primary"]::after {
    content: ""; position: absolute; top: 0; bottom: 0; left: 0; width: 40%; background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.28), rgba(255,255,255,0));
    transform: translateX(-120%) skewX(-18deg); pointer-events: none;}
  .stButton > button[data-testid="stBaseButton-primary"]:hover::after, .stDownloadButton > button[data-testid="stBaseButton-primary"]:hover::after {animation: ete-brilho .9s var(--mola);}
  .stButton > button:hover, .stDownloadButton > button:hover {transform: translateY(-2px);}
  .stButton > button[data-testid="stBaseButton-tertiary"] p {transition: letter-spacing var(--medio) var(--mola);}
  .stButton > button[data-testid="stBaseButton-tertiary"]:hover p {letter-spacing: .02em; text-decoration: underline; text-underline-offset: 4px;}
  [class*="st-key-passo_"] button {transition: background-color var(--rapido) ease, color var(--rapido) ease, transform var(--medio) var(--mola) !important;}
  [class*="st-key-passo_"] [class*="_prev"] button:hover:not(:disabled) {transform: translateX(-3px) !important;}
  [class*="st-key-passo_"] [class*="_next"] button:hover:not(:disabled) {transform: translateX(3px) !important;}

  /* navigation and tabs: the hovered item lifts, the logo winks */
  .st-key-pagina label[data-testid="stRadioOption"] {transition: background-color var(--rapido) ease, transform var(--rapido) var(--mola) !important;}
  .st-key-pagina label[data-testid="stRadioOption"]:hover {transform: translateY(-1px);}
  .ete-marca img {transition: transform .6s var(--mola);}
  .ete-marca:hover img {transform: rotate(-14deg) scale(1.06);}
  .ete-rede {transition: background-color var(--rapido) ease, color var(--rapido) ease, transform var(--medio) var(--mola), border-color var(--rapido) ease;}
  .ete-rede:hover {background: var(--mare); color: var(--tinta) !important; border-color: var(--mare); transform: translateY(-3px) rotate(-6deg);}
  .ete-apoios a {transition: opacity var(--medio) ease, transform var(--medio) var(--mola);}
  .ete-apoios a:hover {opacity: 1; transform: translateY(-3px) scale(1.04);}
  label[data-testid="stRadioOption"]:not(.st-key-pagina *) {transition: border-color var(--rapido) ease, background-color var(--rapido) ease, transform var(--rapido) var(--mola) !important;}
  label[data-testid="stRadioOption"]:hover {transform: translateY(-1px);}
  [data-testid="stTab"] {transition: background-color var(--rapido) ease, box-shadow var(--rapido) ease !important;}
  [data-testid="stTab"]:not([data-selected="true"]):hover {background: rgba(255,255,255,.6) !important;}

  /* tables: the row under the pointer is marked on its left edge */
  table.ete-tabela td {transition: background-color .15s ease;}
  table.ete-tabela tbody tr:hover td {background: #F4FAF8;}
  table.ete-tabela tbody tr:hover td:first-child {box-shadow: inset 3px 0 0 var(--mare);}

  /* footer links draw their underline */
  .ete-rodape a {text-decoration: none !important; background: linear-gradient(currentColor, currentColor) 0 100% / 0 1px no-repeat; transition: background-size .4s var(--mola);}
  .ete-rodape a:hover {background-size: 100% 1px;}
}

/* ---------------------------------------------------------------- small screens */
@media (max-width: 980px) {
  .ete-hero {grid-template-columns: 1fr; padding: 34px 28px;}
  .ete-rodape .cols {grid-template-columns: 1fr 1fr;}
  .ete-marca .lema {display: none;}
}
@media (max-width: 700px) {
  .ete-passos.fixas {grid-template-columns: 1fr 1fr !important;}
  [data-testid="stMainBlockContainer"], .block-container {padding-left: .8rem; padding-right: .8rem;}
  .st-key-cabecalho {top: 6px; border-radius: 22px; padding: 8px 8px 6px 10px;}
  .st-key-cabecalho > .st-key-pagina {flex: 1 1 100% !important; width: 100% !important; order: 3;}
  .st-key-pagina div[role="radiogroup"] {justify-content: flex-start;}
  .ete-rodape .cols {grid-template-columns: 1fr;}
  .st-key-utilidades {padding: 8px 10px; border-radius: 18px;}
  .st-key-utilidades > div:first-child {flex: 1 1 100% !important; order: -1; position: static !important;}
  .st-key-utilidades {row-gap: 10px !important;}
  .ete-hero {padding: 28px 20px 22px 20px; border-radius: 26px; gap: 22px;}
  .ete-hero .selo {padding: 18px;} .ete-hero .selo .nivel {font-size: 1.550rem;}
  .ete-cabeca {padding: 24px 20px; border-radius: 24px;} .ete-cabeca .arte {display: none;}
  .ete-dias {grid-template-columns: repeat(auto-fill, minmax(56px, 1fr));}
  .ete-kpis {grid-template-columns: repeat(2, minmax(0, 1fr));} .ete-kpi .valor {font-size: 1.650rem;}
  .ete-rodape {margin: 40px -.8rem 0 -.8rem; padding: 32px 22px 24px 22px; border-radius: 26px 26px 0 0;}
  .ete-cartao {padding: 18px;}
}
@media (prefers-reduced-motion: reduce) {*, *::before, *::after {animation: none !important; transition: none !important;} .ete-kpi, .ete-cartao, .ete-dia, .ete-troco .no {transform: none !important;}}
</style>
"""

ONDAS = ("<svg class='ondas' viewBox='0 0 1200 300' preserveAspectRatio='none' aria-hidden='true'><g fill='none' stroke='#FFFFFF' stroke-width='2'>"
         + "".join(f"<path d='M0 {40 + 36 * i}c150-{30 + 4 * i} 300-{30 + 4 * i} 450 0s300 {30 + 4 * i} 450 0 200-{20 + 3 * i} 300-10'/>" for i in range(7)) + "</g></svg>")
ARTE = ("<svg class='arte' viewBox='0 0 380 260' aria-hidden='true'><g fill='none' stroke='#2BB5A0' stroke-width='1.600'>"
        + "".join(f"<path d='M0 {30 + 30 * i}c60-{18 + 3 * i} 120-{18 + 3 * i} 190 0s130 {18 + 3 * i} 190 0'/>" for i in range(8)) + "</g></svg>")


# ----------------------------------------------------------------------------- contacts and logos
CONTACTOS = {
    "facebook": "https://www.facebook.com/share/p/1KXjcbTmvm/",
    "linkedin": "https://www.linkedin.com/posts/sadi-mozambique-656809437_eyestoearth-ete-mozambique-share-7515663344184516608-0BSp/",
    "whatsapp": "https://wa.me/258841349563",
    "telefone": "+258 84 134 9563",
    "email": "ezequias.miocha6162@gmail.com",
}
APOIOS = [("oad", "IAU Office of Astronomy for Development", "https://www.astro4dev.org/"),
          ("dara", "DARA: Development in Africa with Radio Astronomy", "https://www.dara-project.org/")]
STATIC = "app/static/"                                    # files in plataforma/static/, served by Streamlit (enableStaticServing)

_REDES = {
    "facebook": "<svg viewBox='0 0 24 24' width='18' height='18' aria-hidden='true'><path fill='currentColor' d='M13.5 21v-7.600h2.600l.400-3h-3V8.500c0-.900.300-1.500 1.600-1.500H16.700V4.300c-.300 0-1.200-.100-2.300-.100-2.300 0-3.900 1.400-3.900 4v2.200H8v3h2.500V21z'/></svg>",
    "whatsapp": "<svg viewBox='0 0 24 24' width='18' height='18' fill='none' stroke='currentColor' stroke-width='1.700' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
                "<path d='M4.200 19.800l1.100-3.900A8.300 8.300 0 1 1 8.300 19z'/><path d='M9.200 8.300c.300-.600.700-.600 1-.500l.800 1.700c.100.300 0 .500-.200.700l-.500.600c.500 1.100 1.400 2 2.500 2.500l.600-.500c.200-.200.400-.300.700-.200l1.700.800c.100.300.100.700-.500 1-.700.400-1.600.500-2.600.100a8.400 8.400 0 0 1-4.100-4.100c-.400-1-.300-1.900.100-2.600z' fill='currentColor' stroke='none'/></svg>",
    "linkedin": "<svg viewBox='0 0 24 24' width='17' height='17' aria-hidden='true'><path fill='currentColor' d='M5.200 8.800h3.100V19H5.200zM6.700 4a1.800 1.800 0 1 1 0 3.600 1.800 1.800 0 0 1 0-3.600zM10.300 8.800h3v1.400c.400-.800 1.500-1.700 3.100-1.700 3.300 0 3.900 2.200 3.900 5V19h-3.100v-4.900c0-1.200 0-2.700-1.700-2.700s-1.900 1.300-1.900 2.600V19h-3.100z'/></svg>",
    "email": "<svg viewBox='0 0 24 24' width='18' height='18' fill='none' stroke='currentColor' stroke-width='1.700' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'><rect x='3.500' y='5.500' width='17' height='13' rx='2.500'/><path d='M4 7l8 6 8-6'/></svg>",
}


def social(small: bool = False) -> str:
    """Round buttons for Facebook, WhatsApp, LinkedIn and e-mail (they open in a new tab)."""
    items = [("facebook", CONTACTOS["facebook"], "Facebook"), ("whatsapp", CONTACTOS["whatsapp"], "WhatsApp " + CONTACTOS["telefone"]),
             ("linkedin", CONTACTOS["linkedin"], "LinkedIn"), ("email", "mailto:" + CONTACTOS["email"], t("Questões técnicas") + ": " + CONTACTOS["email"])]
    links = "".join(f"<a class='ete-rede' href='{href}' target='_blank' rel='noopener' title='{label}' aria-label='{label}'>{_REDES[k]}</a>" for k, href, label in items)
    return f"<div class='ete-redes{' pequenas' if small else ''}'>{links}</div>"


# ----------------------------------------------------------------------------- helpers
def html(text: str, width: str = "stretch") -> None:
    st.markdown(text, unsafe_allow_html=True, width=width)


def _bold(text: str) -> str:
    """**words** written the Markdown way become bold in the HTML blocks."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", str(text))


def agora() -> datetime:
    return datetime.now(ZoneInfo("Africa/Maputo"))


def saudacao() -> str:
    hora = agora().hour
    return t("Bom dia") if 5 <= hora < 12 else t("Boa tarde") if hora < 19 else t("Boa noite")


def data_longa(dia) -> str:
    return L.data_longa(dia)


def dot(colour: str) -> str:
    return f"<span class='ete-ponto' style='background:{colour}'></span>"


def chip(text: str, colour: str | None = None) -> str:
    return f"<span class='ete-chip'>{dot(colour) if colour else ''}{t(text)}</span>"


def fmt(value, decimals: int | None = None) -> str:
    """A value as text in the reader's language: decimal comma or point, a dash for 'no value'."""
    if value is None or (not isinstance(value, (str, list, dict)) and pd.isna(value)):
        return "–"
    if isinstance(value, bool) or type(value).__name__ == "bool_":
        return t("sim") if value else t("não")
    if isinstance(value, int) or type(value).__name__.startswith("int"):
        return L.numero(value, 0) if abs(value) >= 10000 else str(value)
    if isinstance(value, float) or type(value).__name__.startswith("float"):
        if decimals is None:
            size = abs(value)
            decimals = 0 if size >= 100 or float(value).is_integer() else 1 if size >= 10 else 2 if size >= 1 else 3
        return L.numero(value, decimals)
    return t(str(value))


@contextmanager
def guard(what: str):
    """Error boundary: a broken section says so and the rest of the page still shows."""
    try:
        yield
    except Exception:                                        # last line of defence
        st.warning(t("Não foi possível mostrar: {o}.", o=t(what)))


# ----------------------------------------------------------------------------- shell
def brand() -> None:
    html(f"<div class='ete-marca'><img src='{STATIC}ete.png' alt='Eyes to Earth' width='44' height='44'>"
         f"<div><div class='nome'>Eyes to Earth</div><div class='lema'>{t('Rio Incomáti · Marracuene')}</div></div></div>", "content")


def status(issued: str, valid: bool, valid_until: str = "") -> None:
    today = issued.startswith(f"{agora():%d/%m}")
    if valid:
        text = (t("Boletim de hoje, {hora}", hora=issued.split(", ")[-1]) if today else t("Boletim de {data}", data=issued))
        text += f"<span class='sep'>·</span>{t('válido até {dia}', dia=valid_until)}" if valid_until else ""
    else:
        text = t("Boletim desactualizado")
    html(f"<div class='ete-estado{'' if valid else ' velho'}'><i></i><span>{text}</span></div>", "content")


def top_bar(issued: str, valid: bool) -> None:           # kept for earlier callers
    brand()
    status(issued, valid)


def support_logos(dark_background: bool = True) -> str:
    suffix = "claro" if dark_background else "escuro"
    return "<div class='ete-apoios'>" + "".join(
        f"<a href='{url}' target='_blank' rel='noopener' title='{name}'><img src='{STATIC}{key}_{suffix}.png' alt='{name}' height='{66 if key == 'oad' else 54}'></a>"
        for key, name, url in APOIOS) + "</div>"


def footer(notice: str, light_page: str = "") -> None:
    light = f"<p><a href='{light_page}'>{t('Versão leve do boletim')}</a>, {t('para quando há pouca rede.')}</p>" if light_page else ""
    html("<div class='ete-rodape'><div class='cols'>"
         f"<div><div class='nome'><img src='{STATIC}ete.png' alt='' width='46' height='46'>Eyes to Earth</div>"
         f"<p>{t('Olhos no céu para proteger quem vive junto ao rio. Monitorização da qualidade da água do Incomáti e alertas de cheia para Marracuene, com satélites e machine learning, actualizados todas as manhãs.')}</p></div>"
         f"<div><div class='h'>{t('Contactos')}</div>{social()}"
         f"<p class='contacto'><span>{t('Questões técnicas')}</span><a href='mailto:{CONTACTOS['email']}'>{CONTACTOS['email']}</a></p>"
         f"<p class='contacto'><span>WhatsApp</span><a href='{CONTACTOS['whatsapp']}' target='_blank' rel='noopener'>{CONTACTOS['telefone']}</a></p></div>"
         f"<div><div class='h'>{t('Importante')}</div><p>{t(notice)} {t('Se as autoridades derem uma ordem, siga a ordem.')}</p>{light}</div>"
         f"<div><div class='h'>{t('Com o apoio de')}</div>{support_logos(True)}"
         f"<div class='h' style='margin-top:18px'>{t('Dados abertos')}</div><p>Copernicus, NASA, USGS, ESA, ECMWF, OpenStreetMap, GeoNames.</p></div>"
         f"</div><div class='fim'><span>© {agora().year} Eyes to Earth · Marracuene, {t('Moçambique')}</span><span>{t('Serviço experimental, feito com dados abertos')}</span></div></div>")


# ----------------------------------------------------------------------------- headings and text
def page_head(eyebrow: str, title: str, subtitle: str = "") -> None:
    html(f"<div class='ete-cabeca'>{ARTE}<div class='ete-olho'>{t(eyebrow)}</div><div class='titulo' role='heading' aria-level='1'>{t(title)}</div>"
         + (f"<div class='sub'>{t(subtitle)}</div>" if subtitle else "") + "</div>")


def section(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    html("<div class='ete-seccao'>" + (f"<div class='ete-olho'>{t(eyebrow)}</div>" if eyebrow else "") + f"<div class='titulo' role='heading' aria-level='2'>{t(title)}</div>"
         + (f"<div class='sub'>{t(subtitle)}</div>" if subtitle else "") + "</div>")


def subtitle(text: str) -> None:
    html(f"<div class='ete-titulo-p' role='heading' aria-level='3'>{t(text)}</div>")


def caption(text: str) -> None:
    html(f"<div class='ete-legenda-texto'>{_bold(t(text))}</div>")


def note(text: str, kind: str = "info") -> None:
    """A quiet note. kind: 'info' (green), 'aviso' (amber) or 'neutra' (sand)."""
    html(f"<div class='ete-nota {kind}'><span class='ic'>{icon('amarelo' if kind == 'aviso' else 'info', 20)}</span><div>{_bold(t(text))}</div></div>")


def intro(title: str, text: str) -> None:                 # kept for earlier callers
    page_head("O projecto", title, text)


# ----------------------------------------------------------------------------- first page
def _scale(level: str | None, colours: dict) -> str:
    bars = "".join(f"<span class='{'activo' if k == level else ''}' style='background:{colours[k]}'></span>" for k in LEVELS)
    names = "".join(f"<span class='{'activo' if k == level else ''}'>{t(k)}</span>" for k in LEVELS)
    return f"<div class='ete-escala'>{bars}</div><div class='ete-escala-nomes'>{names}</div>"


_FEMININO_FR = {"verde": "verte", "amarelo": "jaune", "laranja": "orange", "vermelho": "rouge"}   # "alerte" is feminine in French


def alert_name(level: str) -> str:
    """'Alerta VERDE' · 'GREEN alert' · 'Alerte VERTE'"""
    word = _FEMININO_FR.get(level, level) if L.lingua() == "fr" else t(level)
    return t("Alerta {nivel}", nivel=word.upper())


def hero(level: str, title: str, colour: str, advice: str = "", valid_until: str = "", issued: str = "", colours: dict | None = None, day=None) -> None:
    """The answer of the day, in plain words, with the level on a four-step scale."""
    scale = _scale(level, colours) if colours else ""
    foot = (f"<div class='pe'>{t('Válido até <b>{dia}</b>', dia=valid_until)}" + (f" · {t('emitido a {quando}', quando=issued)}" if issued else "") + "</div>") if valid_until else ""
    do = f"<div class='fazer'><span class='ic'>{icon('escudo', 22, '#FFFFFF')}</span><div><b>{t('O que fazer hoje')}</b><span>{t(advice)}</span></div></div>" if advice else ""
    html(f"<div class='ete-hero nv-{level}'>{ONDAS}<div class='esq'><div class='data'>{data_longa(day or agora())} · Marracuene</div>"
         f"<div class='grande' role='heading' aria-level='1'>{saudacao()}.<br><em>{t(ALERT_HEADLINE[level])}</em></div><p class='lead'>{L.titulo_boletim(title)}</p>{do}</div>"
         f"<div class='selo'><div class='topo'><div class='anel' style='background:{colour}'>{icon(level, 36, ALERT_TEXT[level])}</div>"
         f"<div><div class='palavra'>{t(ALERT_WORD[level])}</div><div class='nivel'>{alert_name(level)}</div></div></div>{scale}{foot}</div></div>")


def hero_unavailable() -> None:
    html(f"<div class='ete-hero nv-indisponivel'>{ONDAS}<div class='esq'><div class='data'>{data_longa(agora())} · Marracuene</div>"
         f"<div class='grande' role='heading' aria-level='1'>{saudacao()}.<br><em>{t('Hoje não temos previsão.')}</em></div>"
         f"<p class='lead'>{t('Não há um boletim das últimas 36 horas. Isto não quer dizer que não há perigo.')}</p>"
         f"<div class='fazer'><span class='ic'>{icon('escudo', 22, '#FFFFFF')}</span><div><b>{t('O que fazer')}</b><span>{t('Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul.')}</span></div></div></div>"
         f"<div class='selo'><div class='topo'><div class='anel' style='background:#56656C'>{icon('indisponivel', 36, '#FFFFFF')}</div>"
         f"<div><div class='palavra'>{t('Sem boletim válido')}</div><div class='nivel'>{t('Previsão indisponível')}</div></div></div>"
         f"<div class='pe'>{t('Nunca mostramos um nível de alerta com dados antigos.')}</div></div></div>")


# ----------------------------------------------------------------------------- components
def kpis(items: list[dict]) -> None:
    """Tiles: each item has rotulo, valor, and optionally unidade and nota."""
    tiles = "".join(f"<div class='ete-kpi'><div class='rotulo'>{t(i['rotulo'])}</div><div class='valor'>{t(i['valor'])}"
                    + (f" <small>{i['unidade']}</small>" if i.get("unidade") else "") + "</div>" + (f"<div class='nota'>{t(i['nota'])}</div>" if i.get("nota") else "") + "</div>" for i in items)
    html(f"<div class='ete-kpis'>{tiles}</div>")


def card(title: str, body: str, eyebrow: str = "", kind: str = "") -> None:
    html(f"<div class='ete-cartao {kind}'>" + (f"<div class='ete-olho'>{t(eyebrow)}</div>" if eyebrow else "") + (f"<div class='cab'>{t(title)}</div>" if title else "") + t(body) + "</div>")


def feature_cards(items: list[dict]) -> None:
    """A grid of cards: each item has titulo and texto, and optionally icone, olho, resultado and chips."""
    cards = "".join(
        "<div class='ete-cartao'>" + (f"<div class='ete-carta-ic'>{icon(i['icone'], 24)}</div>" if i.get("icone") else "") + (f"<div class='ete-olho'>{t(i['olho'])}</div>" if i.get("olho") else "")
        + f"<div class='cab'>{t(i['titulo'])}</div><div class='ete-miudo' style='font-size:.920rem'>{t(i['texto'])}</div>" + (f"<div class='ete-resultado'>{t(i['resultado'])}</div>" if i.get("resultado") else "")
        + (f"<div class='ete-miudo'>{t(i['nota'])}</div>" if i.get("nota") else "") + ("<div style='margin-top:10px'>" + "".join(chip(c) for c in i["chips"]) + "</div>" if i.get("chips") else "") + "</div>" for i in items)
    html(f"<div class='ete-grelha'>{cards}</div>")


def day_tiles(days: list[dict], colours: dict, chosen: int) -> None:
    tiles = ""
    for i, d in enumerate(days):
        day = pd.Timestamp(d["data"])
        tiles += (f"<div class='ete-dia{' escolhido' if i == chosen else ''}' style='--c:{colours[d['alerta']]}'><div class='sem'>{L.dia_curto(day)}</div>"
                  f"<div class='num'>{day.day}</div><div class='nv'>{t(d['alerta'])}</div></div>")
    html(f"<div class='ete-dias' style='--n:{len(days)}'>{tiles}</div>")


def river_tiles(state: pd.DataFrame, colours: dict, chosen: str | None = None) -> None:
    """The river from the border (left) to the mouth (right): a line with one station per section, coloured by its state."""
    stations = ""
    for code, row in state.iterrows():
        name = str(row["nome"]).split(" ", 1)[1] if " " in str(row["nome"]) else ""
        stations += (f"<div class='ete-troco{' escolhido' if code == chosen else ''}' style='--c:{colours.get(row['classe'], '#bdc3c7')}'><span class='fio'></span><div class='no'>{code}</div>"
                     f"<b>{t(name)}</b><span class='cls'>{t(row['classe'])}</span></div>")
    html(f"<div class='ete-rio-caixa'><div class='ete-rio-pontas'><span>← {t('fronteira')}</span><span>{t('foz')} →</span></div><div class='ete-rio'>{stations}</div></div>")


def chips(items: list[tuple[str, str, str]]) -> None:
    html("".join(f"<span class='ete-chip'>{dot(colour)}<b>{t(name)}</b>{'&nbsp;· ' + t(state) if state else ''}</span>" for name, state, colour in items))


def legend(items: list[dict]) -> None:
    html(" ".join(chip(i["nome"], i["cor"]) for i in items))


def level_cards(limits: dict, colours: dict, advice: dict) -> None:
    rules = {"verde": t("Nenhum cenário passa os limites nos próximos 10 dias."),
             "amarelo": t("Caudal previsto acima de {v} m³/s, ou chuva de 7 dias muito acima do normal.", v=L.numero(limits.get("amarelo", 0))),
             "laranja": t("Caudal previsto acima de {v} m³/s em metade dos cenários, ou chuva excepcional.", v=L.numero(limits.get("laranja", 0))),
             "vermelho": t("Caudal previsto acima de {v} m³/s em metade dos cenários.", v=L.numero(limits.get("vermelho", 0)))}
    cards = "".join(f"<div class='ete-nivel'><div class='tampo' style='background:{colours[k]};color:{ALERT_TEXT[k]}'><small>{t(ALERT_WORD[k])}</small>{t(k).capitalize()}</div>"
                    f"<div class='corpo'><div class='regra'>{rules[k]}</div>{t(advice[k])}</div></div>" for k in LEVELS)
    html(f"<div class='ete-niveis'>{cards}</div>")


def steps(items: list[tuple[str, str]], colunas: int | None = None) -> None:
    estilo = f" style='grid-template-columns:repeat({colunas},minmax(0,1fr))'" if colunas else ""
    html(f"<div class='ete-passos{' fixas' if colunas else ''}'{estilo}>" + "".join(f"<div class='ete-passo'><b>{t(title)}</b>{t(text)}</div>" for title, text in items) + "</div>")


def message(text: str) -> None:
    html(f"<div class='ete-msg'>{text}<span class='hora'>{agora():%H:%M} ✓✓</span></div>")


def table(frame: pd.DataFrame, colours: dict | None = None, height: int | None = None, decimals: dict | None = None) -> None:
    """A data frame as a clean HTML table, in the reader's language. `colours` maps a column to
    {value: colour} to draw the value as a chip with a coloured dot; `height` (px) makes long
    tables scroll under a fixed header."""
    colours, decimals = colours or {}, decimals or {}
    numeric = {c: pd.api.types.is_numeric_dtype(frame[c]) and not pd.api.types.is_bool_dtype(frame[c]) for c in frame.columns}
    head = "".join(f"<th class='{'n' if numeric[c] else ''}'>{t(str(c))}</th>" for c in frame.columns)
    rows = []
    for record in frame.itertuples(index=False):
        cells = ""
        for column, value in zip(frame.columns, record):
            if column in colours and isinstance(value, str):
                text = chip(value, colours[column].get(value, "#C9CFCB"))
            elif isinstance(value, str) and re.match(r"^(Q\d|\d) ", value):
                text = L.troco(value)
            else:
                text = fmt(value, decimals.get(column))
            cells += f"<td class='{'n' if numeric[column] else ''}'>{text}</td>"
        rows.append(f"<tr>{cells}</tr>")
    style = f" style='max-height:{height}px'" if height else ""
    html(f"<div class='ete-tabela-caixa'{style}><table class='ete-tabela'><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


def stepper(key: str, options: list, label=str, caption: str = "") -> object:
    """Back and forward buttons around a value: returns the chosen option. The position is kept in
    the session, so it survives moving between pages."""
    state = f"{key}_i"
    if state not in st.session_state or not 0 <= st.session_state[state] < len(options):
        st.session_state[state] = len(options) - 1 if key.startswith(("mes", "ano")) else 0

    def move(step: int) -> None:
        st.session_state[state] = min(max(st.session_state[state] + step, 0), len(options) - 1)

    with st.container(key=f"passo_{key}", horizontal=True, vertical_alignment="center", gap="small"):
        st.button("←", key=f"{key}_prev", on_click=move, args=(-1,), disabled=st.session_state[state] == 0, help=t("Anterior"))
        chosen = options[st.session_state[state]]
        position = t("{n} de {total}", n=st.session_state[state] + 1, total=len(options))
        html(f"<div class='ete-seletor'>{label(chosen)}<small>{t(caption) if caption else position}</small></div>")
        st.button("→", key=f"{key}_next", on_click=move, args=(1,), disabled=st.session_state[state] == len(options) - 1, help=t("Seguinte"))
    return chosen


# ----------------------------------------------------------------------------- advice
PRIORIDADE = {"alto": ("Prioridade alta", "#9A3412", "#FDEBD8"), "atencao": ("Atenção", "#8A5A00", "#FFF4D6"), "info": ("Sempre", "#0B4F4A", "#E3F1EC")}
VISTO = ("<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.400' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
         "<path d='M5 12.500l4.500 4.500L19 7.500'/></svg>")


def situation_cards(situacoes: list[dict], razoes) -> None:
    """Today's situations as cards: priority (in words, not colour only), what it means and why (the numbers)."""
    cartoes = ""
    for s in situacoes:
        rotulo, cor, fundo = PRIORIDADE[s["nivel"]]
        porque = razoes(s)
        cartoes += (f"<div class='ete-situacao' style='--c:{cor};--f:{fundo}'><span class='prio'>{t(rotulo)}</span><div class='cab'>{t(s['titulo'])}</div>"
                    f"<p>{t(s['texto'])}</p>" + (f"<div class='porque'>{porque}</div>" if porque else "") + "</div>")
    html(f"<div class='ete-situacoes'>{cartoes}</div>")


def advice_card(titulo: str, itens: list[str], nivel: str = "info", olho: str = "") -> None:
    rotulo, cor, fundo = PRIORIDADE[nivel]
    lista = "".join(f"<li><span class='v'>{VISTO}</span><span>{t(i)}</span></li>" for i in itens)
    html(f"<div class='ete-conselho' style='--c:{cor};--f:{fundo}'><div class='topo'><span class='prio'>{t(rotulo)}</span>"
         + (f"<span class='ete-olho'>{t(olho)}</span>" if olho else "") + f"</div><div class='cab'>{t(titulo)}</div><ul>{lista}</ul></div>")
