"""Sistema de desenho da plataforma ETE: paleta, tipografia, estilo e componentes de página.

Uma só fonte para as cores e as formas, para a plataforma ter o mesmo aspecto em todas as páginas
e não parecer uma aplicação Streamlit: barra de navegação fixa, tipografia própria, cartões,
tabelas em HTML e botões em forma de pílula.

Paleta inspirada no copernicus.eu (tema «genérico» da Copernicus Component Library)
  marca       roxo Copernicus #615C9F (barra de cima, rodapé, botões principais, escolhas); mais escuro ao passar o rato
  tinta       quase preto #212529 (texto)
  lagoa       roxo escuro #4E4A8C (ligações, olhos das secções, ícones)
  maré        lilás #8E8AC4 (pequenos realces)
  espuma      lilás muito claro (fundos suaves); a página é cinzenta muito clara e os cartões brancos
  dados       azul marinho #1F5F8F nos gráficos (a água), perto do azul do serviço marinho do Copernicus
  alertas     verde, amarelo, laranja, vermelho: SÓ para níveis de alerta, sempre com a palavra
  água        azul claro (normal), castanho (elevada), castanho escuro (muito elevada): vêm do catálogo
Sem emojis: os ícones são de traço fino (SVG) e, nas curiosidades, o destaque é um número.

Tipografia
  títulos     Fraunces (serifa suave e calorosa)
  texto       Plus Jakarta Sans

Movimento
  entradas em cascata em todos os ecrãs; reacções ao passar o cursor só com rato ou trackpad
  (num ecrã táctil o "hover" fica preso depois de tocar); nada se mexe para quem pede menos
  movimento nas definições do sistema
"""

from __future__ import annotations

import base64
import io
import re
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import idioma as L
from idioma import t

INK, RIO, LAGOA, MARE, ESPUMA = "#212529", "#615C9F", "#4E4A8C", "#8E8AC4", "#F0EFF8"
AREIA, CARD, BORDER, SOFT = "#F6F6F9", "#FFFFFF", "#E2E1EA", "#EFEFF4"
MUTED = "#6C6E74"
MARCA, MARCA_ESCURA = "#615C9F", "#4E4A85"             # Copernicus generic purple, and a darker step for hover
NAVY, BLUE, TEAL, BG = INK, LAGOA, LAGOA, AREIA          # names used by earlier versions
ALERT_TEXT = {"verde": "#FFFFFF", "amarelo": "#2B2300", "laranja": "#FFFFFF", "vermelho": "#FFFFFF"}
ALERT_WORD = {"verde": "Sem sinais de cheia", "amarelo": "Atenção", "laranja": "Preparação", "vermelho": "Cheia provável"}
ALERT_HEADLINE = {"verde": "Sem sinais de cheia no Incomáti.", "amarelo": "Atenção ao rio Incomáti.", "laranja": "É tempo de preparação.",
                  "vermelho": "Cheia provável no Incomáti."}
LEVELS = ["verde", "amarelo", "laranja", "vermelho"]
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
MESES_LONGOS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
DIAS_CURTOS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]

LOGO = ("<svg width='38' height='38' viewBox='0 0 44 44' xmlns='http://www.w3.org/2000/svg' aria-hidden='true'>"
        "<circle cx='22' cy='22' r='22' fill='#615C9F'/>"
        "<path d='M7 21c4.6-6.6 9.6-9.9 15-9.9S32.400 14.400 37 21c-4.600 6.600-9.600 9.900-15 9.900S11.600 27.600 7 21z' fill='none' stroke='#FFFFFF' stroke-width='2.200'/>"
        "<circle cx='22' cy='21' r='5.200' fill='#D4D1F1'/>"
        "<path d='M10 35c3.200-2.400 6-2.400 9.200 0s6 2.400 9.200 0 4.200-1.800 5.600-1.800' fill='none' stroke='#D4D1F1' stroke-width='2.200' stroke-linecap='round'/></svg>")

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
  --tinta: #212529; --rio: #615C9F; --lagoa: #4E4A8C; --mare: #8E8AC4; --espuma: #F0EFF8;
  --areia: #F6F6F9; --cartao: #FFFFFF; --linha: #E2E1EA; --suave: #EFEFF4; --mudo: #6C6E74;
  --marca: #615C9F; --marca-escura: #4E4A85; --marca-clara: #ECEBF7;
  --titulo: 'Fraunces', 'Iowan Old Style', 'Palatino Linotype', Georgia, serif;
  --texto: 'Plus Jakarta Sans', 'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif;
  --raio: 22px; --raio-p: 14px;
  --sombra: 0 1px 2px rgba(33,37,41,.04), 0 8px 24px -12px rgba(33,37,41,.12);
  --sombra-alta: 0 2px 4px rgba(33,37,41,.05), 0 24px 48px -20px rgba(33,37,41,.28);
}

/* ---------------------------------------------------------------- page: no Streamlit chrome */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stAppDeployButton"], #MainMenu, footer, [data-testid="stSidebarCollapsedControl"] {display: none !important;}
.stApp {background: var(--areia);}
html, body, .stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp button, .stApp textarea, .stApp table, [data-testid="stMarkdownContainer"] {font-family: var(--texto) !important;}
.stApp {color: var(--tinta);}
[data-testid="stMainBlockContainer"], .block-container {max-width: 1220px; padding: .8rem 1.4rem 0 1.4rem;}
[data-testid="stMarkdownContainer"] p {line-height: 1.6;}
.stApp a {color: var(--lagoa); text-underline-offset: 3px;}
::selection {background: #D6D3EF;}
[data-testid="stElementToolbar"] {display: none !important;}
[data-testid="stHeadingWithActionElements"] a, [data-testid="stHeaderActionElements"] {display: none !important;}
[data-stale="true"] {opacity: .75 !important; transition: opacity .3s ease;}
@keyframes ete-sobe {from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: none;}}
@keyframes ete-pulsa {0% {box-shadow: 0 0 0 0 rgba(142,138,196,.55);} 70% {box-shadow: 0 0 0 9px rgba(142,138,196,0);} 100% {box-shadow: 0 0 0 0 rgba(142,138,196,0);}}

/* ---------------------------------------------------------------- navigation bar (floating, sticky) */
.st-key-cabecalho {position: sticky; top: 10px; z-index: 9990; flex-flow: row wrap !important; align-items: center !important; gap: 6px 14px !important;
  background: rgba(255,255,255,.82); -webkit-backdrop-filter: saturate(160%) blur(16px); backdrop-filter: saturate(160%) blur(16px);
  border: 1px solid rgba(226,225,234,.9); border-radius: 26px; padding: 8px 10px 8px 14px; box-shadow: var(--sombra); margin-bottom: 14px;}
.st-key-cabecalho > div {width: auto !important; flex: 0 0 auto !important; min-width: 0;}
.st-key-cabecalho > .st-key-nav_topo {flex: 1 1 0 !important; width: 0 !important; min-width: 0; overflow: hidden;}
.st-key-nav_topo .stRadio {width: 100%;}
.ete-marca {display: flex; align-items: center; gap: 10px; text-decoration: none;}
.ete-marca .nome {font-family: var(--titulo); font-weight: 600; font-size: 1.120rem; line-height: 1.05; color: var(--tinta); letter-spacing: -.01em; white-space: nowrap;}
.ete-marca .lema {font-size: .680rem; color: var(--mudo); letter-spacing: .09em; text-transform: uppercase; font-weight: 600; white-space: nowrap;}
.ete-estado {display: flex; align-items: center; gap: 8px; background: var(--espuma); color: var(--rio); border-radius: 999px; padding: 7px 13px; font-size: .780rem; font-weight: 600; white-space: nowrap;}
.ete-estado i {width: 8px; height: 8px; border-radius: 50%; background: var(--mare); animation: ete-pulsa 2.400s infinite;}
.ete-estado.velho {background: #FBEBD3; color: #7A4A06;} .ete-estado.velho i {background: #E08A00; animation: none;}
.st-key-nav_topo div[role="radiogroup"] {flex-flow: row nowrap; gap: 1px; overflow-x: auto; scrollbar-width: none; justify-content: safe center;}
.st-key-nav_topo div[role="radiogroup"]::-webkit-scrollbar {display: none;}
.st-key-nav_topo label[data-testid="stRadioOption"] {padding: 8px 8px !important; border-radius: 999px; margin: 0 !important; cursor: pointer; transition: background .18s ease, color .18s ease; flex: 0 0 auto; background: transparent !important; border: 0 !important;}
.st-key-nav_topo label[data-testid="stRadioOption"] p {font-weight: 600; color: var(--mudo); font-size: .860rem; white-space: nowrap; line-height: 1.2;}
.st-key-nav_topo label[data-testid="stRadioOption"]:hover {background: var(--suave) !important;}
.st-key-nav_topo label[data-testid="stRadioOption"]:hover p {color: var(--tinta);}
.st-key-nav_topo label[data-testid="stRadioOption"][data-selected="true"] {background: var(--marca) !important;}
.st-key-nav_topo label[data-testid="stRadioOption"][data-selected="true"] p {color: #fff;}

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
.ete-cabeca {margin: 18px 0 20px 0; padding: 34px 36px; border-radius: 30px; background: linear-gradient(120deg, #FFFFFF 0%, #F7F6FC 60%, #F0EFF8 100%); border: 1px solid var(--linha); position: relative; overflow: hidden; animation: ete-sobe .5s ease both;}
.ete-cabeca .titulo {font-family: var(--titulo); font-weight: 560; font-size: clamp(1.900rem, 4vw, 2.900rem); line-height: 1.06; letter-spacing: -.02em; color: var(--tinta); margin-top: 10px; max-width: 820px;}
.ete-cabeca .sub {color: var(--mudo); font-size: 1.080rem; margin-top: 12px; max-width: 720px; line-height: 1.55;}
.ete-cabeca .arte {position: absolute; right: -30px; bottom: -40px; width: 380px; opacity: .55; pointer-events: none;}
.ete-sub {color: var(--mudo); font-size: .930rem; margin: 0 0 12px 0;}
.ete-legenda-texto {color: var(--mudo); font-size: .860rem; line-height: 1.55; margin: 2px 2px 14px 2px; max-width: 900px;}
.ete-legenda-texto b {color: var(--tinta);}
.ete-titulo-p {font-family: var(--titulo); font-weight: 560; font-size: 1.200rem; color: var(--tinta); margin: 18px 0 8px 0; letter-spacing: -.01em;}

/* ---------------------------------------------------------------- hero (first page) */
.ete-hero {position: relative; overflow: hidden; border-radius: 34px; padding: 46px 46px 42px 46px; color: #fff; display: grid; grid-template-columns: minmax(0, 1.450fr) minmax(280px, .850fr); gap: 34px; align-items: center;
  background: linear-gradient(135deg, #2C2950 0%, #46427A 48%, #615C9F 100%); box-shadow: var(--sombra-alta); margin: 6px 0 16px 0; animation: ete-sobe .6s ease both;}
.ete-hero.nv-amarelo {background: linear-gradient(135deg, #1E1F27 0%, #2B2C36 55%, #4A4310 100%);}
.ete-hero.nv-laranja {background: linear-gradient(135deg, #3A1C08 0%, #7A3A0C 55%, #B8590F 100%);}
.ete-hero.nv-vermelho {background: linear-gradient(135deg, #3A0D09 0%, #7C1D14 55%, #B2301F 100%);}
.ete-hero.nv-indisponivel {background: linear-gradient(135deg, #252D31 0%, #3C484E 60%, #56656C 100%);}
.ete-hero .ondas {position: absolute; inset: auto 0 0 0; width: 100%; height: 62%; opacity: .16; pointer-events: none;}
.ete-hero .esq, .ete-hero .selo {position: relative; z-index: 1;}
.ete-hero .data {font-size: .780rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 600; opacity: .78;}
.ete-hero .grande {font-family: var(--titulo); font-weight: 500; font-size: clamp(2.100rem, 4.600vw, 3.700rem); line-height: 1.03; letter-spacing: -.025em; margin: 14px 0 0 0;}
.ete-hero .grande em {font-style: italic; font-weight: 400; color: #DAD7F6;}
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
.ete-cartao.suave {background: var(--espuma); border-color: #DCDAEE; box-shadow: none;}
.ete-cartao.tinta {background: var(--marca-escura); border-color: var(--marca-escura); color: #F1F0FA;} .ete-cartao.tinta .cab {color: #fff;} .ete-cartao.tinta .ete-olho {color: #D4D1F1;}
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
.ete-dia.escolhido {background: var(--marca); border-color: var(--marca); box-shadow: var(--sombra-alta); transform: translateY(-3px);}
.ete-dia.escolhido .num {color: #fff;} .ete-dia.escolhido .sem, .ete-dia.escolhido .nv {color: #DAD8F0;}

/* the river, border to mouth: a line with nine stations */
.ete-rio-caixa {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); box-shadow: var(--sombra); padding: 22px 12px 16px 12px; margin: 6px 0 12px 0; overflow-x: auto;}
.ete-rio {display: grid; grid-auto-flow: column; grid-auto-columns: minmax(104px, 1fr); min-width: 100%;}
.ete-troco {position: relative; text-align: center; padding: 0 6px; font-size: .760rem; line-height: 1.35; color: var(--mudo);}
.ete-troco .fio {position: absolute; top: 15px; left: 0; right: 0; height: 8px; background: var(--c, #bdc3c7); opacity: .34;}
.ete-troco:first-child .fio {left: 50%; border-radius: 8px 0 0 8px;} .ete-troco:last-child .fio {right: 50%; border-radius: 0 8px 8px 0;}
.ete-troco .no {position: relative; z-index: 1; width: 38px; height: 38px; border-radius: 50%; margin: 0 auto 10px auto; background: var(--c, #bdc3c7); color: #fff; font-weight: 700; font-size: .780rem; display: flex; align-items: center; justify-content: center; border: 4px solid #fff; box-shadow: 0 0 0 1px var(--linha), 0 6px 14px -6px rgba(33,37,41,.4);}
.ete-troco b {display: block; color: var(--tinta); font-size: .840rem; font-weight: 600;}
.ete-troco .cls {display: inline-block; margin-top: 4px; padding: 2px 9px; border-radius: 999px; background: var(--suave); font-weight: 600; color: var(--tinta); font-size: .700rem;}
.ete-troco.escolhido .no {box-shadow: 0 0 0 3px var(--marca), 0 8px 18px -6px rgba(33,37,41,.5); transform: scale(1.1);}
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
.ete-nota {display: flex; gap: 12px; align-items: flex-start; border-radius: 18px; padding: 14px 18px; margin: 4px 0 14px 0; font-size: .940rem; line-height: 1.55; background: var(--espuma); color: #37336A; border: 1px solid #DCDAEE;}
.ete-nota .ic {flex: 0 0 auto; line-height: 0; margin-top: 2px;}
.ete-nota.aviso {background: #FFF6E3; color: #5C3D05; border-color: #F3E0B5;}
.ete-nota.neutra {background: var(--suave); color: var(--tinta); border-color: var(--linha);}

/* tables in HTML */
.ete-tabela-caixa {background: var(--cartao); border: 1px solid var(--linha); border-radius: 18px; overflow: auto; box-shadow: var(--sombra); margin: 4px 0 12px 0;}
table.ete-tabela {width: 100%; border-collapse: separate; border-spacing: 0; font-size: .860rem; line-height: 1.45;}
table.ete-tabela th {position: sticky; top: 0; z-index: 1; background: #F7F7FA; text-align: left; font-size: .700rem; letter-spacing: .08em; text-transform: uppercase; font-weight: 700; color: var(--mudo); padding: 12px 16px; border-bottom: 1px solid var(--linha); white-space: nowrap;}
table.ete-tabela {margin: 0 !important;}
table.ete-tabela th, table.ete-tabela td {border: 0 !important;}
table.ete-tabela th {border-bottom: 1px solid var(--linha) !important;}
table.ete-tabela td {padding: 11px 16px; border-bottom: 1px solid #ECEBF2 !important; color: var(--tinta); vertical-align: top;}
table.ete-tabela tr:last-child td {border-bottom: 0 !important;}
table.ete-tabela tbody tr:hover td {background: #F8F8FC;}
table.ete-tabela td.n, table.ete-tabela th.n {text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap;}
table.ete-tabela td:first-child {font-weight: 600; min-width: 130px;}
table.ete-tabela .ete-chip {margin: 0; padding: 2px 10px; font-size: .760rem; white-space: nowrap;}

/* stepper (back and forward) */
[class*="st-key-passo_"] {background: var(--cartao); border: 1px solid var(--linha); border-radius: 999px; padding: 5px 6px; box-shadow: var(--sombra); flex-flow: row nowrap !important; align-items: center !important; justify-content: space-between !important; max-width: 460px; margin: 2px auto 4px auto;}
[class*="st-key-passo_"] > div {width: auto !important; flex: 0 0 auto !important;}
[class*="st-key-passo_"] > div:has(.ete-seletor) {flex: 1 1 auto !important;}
[class*="st-key-passo_"] button {width: 40px !important; height: 40px !important; min-height: 0 !important; padding: 0 !important; border-radius: 50% !important; background: var(--suave) !important; border: 0 !important; color: var(--tinta) !important; box-shadow: none !important;}
[class*="st-key-passo_"] button p {font-size: 1.150rem !important; line-height: 1 !important;}
[class*="st-key-passo_"] button:hover:not(:disabled) {background: var(--marca) !important; color: #fff !important; transform: none !important;}
[class*="st-key-passo_"] button:disabled {opacity: .35;}
.ete-seletor {text-align: center; font-weight: 700; color: var(--tinta); font-size: .950rem; line-height: 1.2; padding: 0 8px;}
[class*="st-key-passo_"] [data-testid="stMarkdownContainer"] {margin: 0 !important;}
.ete-seletor small {display: block; font-weight: 500; color: var(--mudo); font-size: .720rem; line-height: 1.3;}

/* message for community leaders: a phone bubble */
.ete-msg {max-width: 460px; background: #E9F7EF; border: 1px solid #CDE9D8; border-radius: 6px 20px 20px 20px; padding: 14px 16px 10px 16px; font-size: .920rem; line-height: 1.5; white-space: pre-wrap; color: #14302A; box-shadow: var(--sombra); margin: 6px 0 12px 0;}
.ete-msg .hora {display: block; text-align: right; font-size: .700rem; color: #5F7A70; margin-top: 6px;}

/* footer */
.ete-rodape {margin: 56px -1.4rem 0 -1.4rem; background: var(--marca); color: #E6E4F5; border-radius: 34px 34px 0 0; padding: 44px 46px 30px 46px; font-size: .880rem; line-height: 1.65;}
.ete-rodape .cols {display: grid; grid-template-columns: 1.350fr 1fr 1.150fr 1.150fr; gap: 34px;}
.ete-rodape .nome {font-family: var(--titulo); font-size: 1.500rem; color: #fff; font-weight: 500; letter-spacing: -.01em; display: flex; align-items: center; gap: 12px; margin-bottom: 10px;}
.ete-rodape h6, .ete-rodape .h {font-size: .700rem; letter-spacing: .14em; text-transform: uppercase; color: #D4D1F1; font-weight: 700; margin: 0 0 10px 0; padding: 0;}
.ete-rodape a {color: #fff !important; text-decoration: underline; text-decoration-color: rgba(255,255,255,.35);}
.ete-rodape .fim {border-top: 1px solid rgba(255,255,255,.14); margin-top: 28px; padding-top: 18px; font-size: .780rem; color: #CFCCEB; display: flex; flex-wrap: wrap; gap: 6px 20px; justify-content: space-between;}

/* ---------------------------------------------------------------- native widgets, brought into the same look */
.stButton > button, .stDownloadButton > button {border-radius: 999px !important; border: 1px solid var(--linha) !important; background: var(--cartao) !important; color: var(--tinta) !important; font-weight: 600 !important; padding: .580rem 1.200rem !important;
  box-shadow: 0 1px 2px rgba(33,37,41,.05); transition: transform .18s ease, box-shadow .18s ease, background .18s ease, border-color .18s ease !important;}
.stButton > button p, .stDownloadButton > button p {font-weight: 600 !important; font-size: .900rem !important;}
.stButton > button:hover, .stDownloadButton > button:hover {border-color: var(--marca) !important; color: var(--marca) !important; transform: translateY(-1px); box-shadow: 0 8px 18px -10px rgba(33,37,41,.45);}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible, label[data-testid="stRadioOption"]:has(input:focus-visible) {outline: 3px solid #BDB9E3 !important; outline-offset: 2px;}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"], .stDownloadButton > button[data-testid="stBaseButton-primary"] {background: var(--marca) !important; border-color: var(--marca) !important; color: #fff !important;}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {background: var(--marca-escura) !important; border-color: var(--marca-escura) !important; color: #fff !important;}
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
[data-testid="stTab"][data-selected="true"] {background: var(--cartao) !important; box-shadow: 0 1px 2px rgba(33,37,41,.08), 0 6px 14px -8px rgba(33,37,41,.3);}
[data-testid="stTab"][data-selected="true"] p {color: var(--tinta) !important;}
[data-testid="stTab"]:focus-visible {outline: 3px solid #BDB9E3; outline-offset: 1px;}
[data-testid="stTabs"] [role="tabpanel"] {padding-top: 20px !important;}

/* accordion */
[data-testid="stExpander"] {border: 0 !important; margin-bottom: 2px;}
[data-testid="stExpander"] details {background: var(--cartao); border: 1px solid var(--linha) !important; border-radius: 18px !important; box-shadow: var(--sombra); overflow: hidden;}
[data-testid="stExpander"] summary {padding: 15px 20px !important; border-radius: 18px;}
[data-testid="stExpander"] summary p {font-weight: 600 !important; font-size: .960rem !important; color: var(--tinta);}
[data-testid="stExpander"] summary:hover {background: #F8F8FC; color: var(--rio) !important;}
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
  background: var(--marca); border-radius: 20px; padding: 7px 8px 7px 16px; margin: 0 0 8px 0; box-shadow: var(--sombra);}
.st-key-utilidades > div {width: auto !important; flex: 0 0 auto !important;}
.st-key-utilidades > div:first-child {flex: 1 1 auto !important; min-width: 0;}
.st-key-utilidades [data-testid="stMarkdownContainer"], .st-key-utilidades .stMarkdown {margin: 0 !important;}
.st-key-utilidades .ete-estado {background: transparent; color: #ECEAFA; padding: 0; font-weight: 500;}
.st-key-utilidades .ete-estado span {white-space: normal;}
.st-key-utilidades .ete-estado .sep {opacity: .45; margin: 0 8px;}
.st-key-utilidades .ete-estado.velho {color: #F6C77A;}
.st-key-utilidades .ete-estado i {background: #FFFFFF; animation-name: ete-pulsa-branco;}
@keyframes ete-pulsa-branco {0% {box-shadow: 0 0 0 0 rgba(255,255,255,.6);} 70% {box-shadow: 0 0 0 9px rgba(255,255,255,0);} 100% {box-shadow: 0 0 0 0 rgba(255,255,255,0);}}
.ete-redes {display: flex; gap: 8px; align-items: center; margin: 4px 0 14px 0;}
.ete-redes.pequenas {margin: 0; gap: 4px;}
.ete-rede {width: 38px; height: 38px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: #F1F0FA !important;
  background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); text-decoration: none !important;}
.ete-redes.claras .ete-rede {color: var(--rio) !important; background: var(--espuma); border-color: #DCDAEE; width: 42px; height: 42px;}
.ete-redes.pequenas .ete-rede {width: 32px; height: 32px; background: transparent; border-color: transparent;}
.ete-rede svg {display: block;}
/* the language switch: a pill with the three languages, the chosen one filled */
.st-key-lingua div[role="radiogroup"] {flex-flow: row nowrap; gap: 0 !important; border: 1.500px solid rgba(255,255,255,.75); border-radius: 999px; padding: 2px; background: transparent;}
.st-key-lingua label[data-testid="stRadioOption"] {background: transparent !important; border: 0 !important; border-radius: 999px !important; padding: 5px 13px !important; min-width: 0;}
.st-key-lingua label[data-testid="stRadioOption"] p {color: #F1F0FA !important; font-weight: 700 !important; font-size: .780rem !important; letter-spacing: .06em;}
.st-key-lingua label[data-testid="stRadioOption"][data-selected="true"] {background: #FFFFFF !important;}
.st-key-lingua label[data-testid="stRadioOption"][data-selected="true"] p {color: var(--marca) !important;}
.st-key-lingua label[data-testid="stRadioOption"]:not([data-selected="true"]):hover {background: rgba(255,255,255,.18) !important; transform: none !important;}
/* logos */
.ete-marca img {display: block; width: 44px; height: 44px; border-radius: 50%; box-shadow: 0 0 0 2px #fff, 0 0 0 3px var(--linha);}
.ete-rodape .nome img {border-radius: 50%; box-shadow: 0 0 0 2px rgba(255,255,255,.15);}
.ete-apoios {display: flex; flex-wrap: wrap; align-items: center; gap: 18px 26px; margin: 2px 0 6px 0;}
.ete-apoios a {background: none !important; line-height: 0; opacity: .92;}
.ete-apoios img {display: block; width: auto;}
.ete-rodape p.contacto {margin: 0 0 8px 0; display: flex; flex-direction: column;}
.ete-rodape p.contacto a {font-size: .820rem; overflow-wrap: anywhere;}
.ete-rodape p.contacto span {font-size: .720rem; letter-spacing: .08em; text-transform: uppercase; color: #CFCCEB;}
.ete-cartao .ete-apoios img {height: 58px;}

/* ---------------------------------------------------------------- WhatsApp alerts: top-bar button, invitation window, sign-up form */
.st-key-ir_alertas button {background: #FFFFFF !important; border-color: #FFFFFF !important; color: var(--marca) !important; padding: .380rem .950rem !important; min-height: 0 !important;}
.st-key-ir_alertas button p {font-size: .800rem !important; font-weight: 700 !important;}
.st-key-ir_alertas button:hover {background: var(--marca-clara) !important; border-color: var(--marca-clara) !important; color: var(--marca-escura) !important;}
div[role="dialog"] {border-radius: 28px !important; border: 1px solid var(--linha); box-shadow: 0 40px 80px -30px rgba(33,37,41,.45) !important; background: var(--cartao) !important;}
div[role="dialog"] h2, div[role="dialog"] [data-testid="stHeading"] * {font-family: var(--titulo) !important; font-weight: 560 !important; color: var(--tinta); letter-spacing: -.01em;}
.ete-convite {display: flex; gap: 14px; align-items: flex-start; background: var(--espuma); border-radius: 18px; padding: 14px 16px; margin-bottom: 6px;}
.ete-convite .ic {flex: 0 0 auto; width: 52px; height: 52px; border-radius: 16px; background: var(--lagoa); color: #fff; display: flex; align-items: center; justify-content: center; line-height: 0;}
.ete-convite ul {margin: 0; padding-left: 1.100rem; color: #37336A; font-size: .930rem; line-height: 1.55;}
.ete-convite li {margin-bottom: 4px;}
.st-key-caixa_inscricao {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); padding: 18px 22px 20px 22px; box-shadow: var(--sombra);}
.st-key-caixa_inscricao .ete-titulo-p {margin-top: 2px;}
.st-key-caixa_sair {max-width: 560px;}
[data-baseweb="input"], [data-baseweb="base-input"] {border-radius: 14px !important; background: var(--cartao) !important;}
[data-baseweb="input"] {border-color: var(--linha) !important; min-height: 46px;}
[data-baseweb="input"]:focus-within {border-color: var(--lagoa) !important; box-shadow: 0 0 0 3px rgba(142,138,196,.2);}
[data-testid="stCheckbox"] label p {font-size: .900rem !important; line-height: 1.5 !important; color: var(--tinta) !important;}
[data-testid="stForm"] {border: 0 !important; padding: 0 !important;}
.stFormSubmitButton > button {border-radius: 999px !important; font-weight: 700 !important; padding: .700rem 1.200rem !important; border: 1px solid var(--linha) !important;}
.stFormSubmitButton > button[data-testid="stBaseButton-primary"] {background: var(--marca) !important; border-color: var(--marca) !important; color: #fff !important;}
.stFormSubmitButton > button[data-testid="stBaseButton-primary"]:hover {background: var(--marca-escura) !important;}

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
.ete-conselho .sentido {margin: 2px 0 2px 0; color: var(--mudo); font-size: .940rem; line-height: 1.5;}
.ete-conselho .porque {margin-top: 8px; padding-top: 10px; border-top: 1px dashed var(--linha); font-size: .830rem; color: var(--mudo); line-height: 1.5;}
.ete-conselho .porque b {color: var(--tinta); font-weight: 600;}
.ete-conselho li {display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid #ECEBF2; font-size: .960rem; line-height: 1.5; color: var(--tinta);}
.ete-conselho li:last-child {border-bottom: 0;}
.ete-conselho li .v {flex: 0 0 auto; width: 26px; height: 26px; border-radius: 50%; background: var(--f); color: var(--c); display: flex; align-items: center; justify-content: center; line-height: 0; margin-top: 1px;}
.st-key-publico_conselhos div[role="radiogroup"] {gap: 8px; flex-wrap: wrap;}
.st-key-publico_conselhos label[data-testid="stRadioOption"] {padding: 9px 16px !important;}
.st-key-publico_conselhos label[data-testid="stRadioOption"][data-selected="true"] {background: var(--marca) !important; border-color: var(--marca) !important;}
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
@keyframes ete-anel {0% {box-shadow: 0 0 0 0 var(--c, #8E8AC4);} 100% {box-shadow: 0 0 0 14px rgba(255,255,255,0);}}
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
  .ete-cartao:hover, .ete-passo:hover, .ete-nivel:hover, .ete-kpi:hover {transform: translateY(-4px); box-shadow: var(--sombra-alta); border-color: #C9C6E6;}
  .ete-cartao.tinta:hover {border-color: var(--rio);}
  .ete-msg:hover {transform: translateY(-3px) rotate(-.4deg); box-shadow: var(--sombra-alta);}
  .ete-rio-caixa:hover, .ete-tabela-caixa:hover, [data-testid="stVegaLiteChart"]:hover, [data-testid="stExpander"] details:hover {box-shadow: var(--sombra-alta); border-color: #DCDAEE;}
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
  .ete-chip:hover {transform: translateY(-2px); border-color: var(--lagoa); box-shadow: 0 6px 12px -8px rgba(78,74,140,.6);}
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
  .st-key-nav_topo label[data-testid="stRadioOption"] {transition: background-color var(--rapido) ease, transform var(--rapido) var(--mola) !important;}
  .st-key-nav_topo label[data-testid="stRadioOption"]:hover {transform: translateY(-1px);}
  .ete-marca img {transition: transform .6s var(--mola);}
  .ete-marca:hover img {transform: rotate(-14deg) scale(1.06);}
  .ete-rede {transition: background-color var(--rapido) ease, color var(--rapido) ease, transform var(--medio) var(--mola), border-color var(--rapido) ease;}
  .ete-rede:hover {background: #FFFFFF; color: var(--marca) !important; border-color: #FFFFFF; transform: translateY(-3px) rotate(-6deg);}
  .ete-apoios a {transition: opacity var(--medio) ease, transform var(--medio) var(--mola);}
  .ete-apoios a:hover {opacity: 1; transform: translateY(-3px) scale(1.04);}
  label[data-testid="stRadioOption"]:not(.st-key-nav_topo *) {transition: border-color var(--rapido) ease, background-color var(--rapido) ease, transform var(--rapido) var(--mola) !important;}
  label[data-testid="stRadioOption"]:hover {transform: translateY(-1px);}
  [data-testid="stTab"] {transition: background-color var(--rapido) ease, box-shadow var(--rapido) ease !important;}
  [data-testid="stTab"]:not([data-selected="true"]):hover {background: rgba(255,255,255,.6) !important;}

  /* tables: the row under the pointer is marked on its left edge */
  table.ete-tabela td {transition: background-color .15s ease;}
  table.ete-tabela tbody tr:hover td {background: #F7F7FB;}
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
  /* steps as a compact numbered list: the number on the left, the words on the right */
  .ete-passos, .ete-passos.fixas {grid-template-columns: 1fr !important; gap: 8px;}
  .ete-passo {display: grid; grid-template-columns: 30px minmax(0, 1fr); column-gap: 10px; padding: 14px 16px 13px 14px;}
  .ete-passo::before {grid-row: span 2; font-size: 1.250rem; margin: 1px 0 0 0;}
  [data-testid="stMainBlockContainer"], .block-container {padding-left: .8rem; padding-right: .8rem;}
  .st-key-cabecalho {top: 6px; border-radius: 22px; padding: 8px 8px 6px 10px;}
  .st-key-cabecalho > .st-key-nav_topo {flex: 1 1 100% !important; width: 100% !important; order: 3;}
  .st-key-nav_topo div[role="radiogroup"] {justify-content: flex-start;}
  .ete-rodape .cols {grid-template-columns: 1fr;}
  .st-key-utilidades {padding: 8px 10px; border-radius: 18px;}
  .st-key-utilidades > div:first-child {flex: 1 1 100% !important; order: -1; position: static !important;}
  .st-key-utilidades {row-gap: 10px !important;}
  .ete-hero {padding: 28px 20px 22px 20px; border-radius: 26px; gap: 22px;}
  .ete-hero .selo {padding: 18px;} .ete-hero .selo .nivel {font-size: 1.550rem;}
  .ete-cabeca {padding: 24px 20px; border-radius: 24px;} .ete-cabeca .arte {display: none;}
  .ete-dias {grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 6px;}
  .ete-dia {padding: 8px 2px 8px 2px;} .ete-dia .num {font-size: 1.200rem;}
  .ete-kpis {grid-template-columns: repeat(2, minmax(0, 1fr));} .ete-kpi .valor {font-size: 1.650rem;}
  .ete-rodape {margin: 40px -.8rem 0 -.8rem; padding: 32px 22px 24px 22px; border-radius: 26px 26px 0 0;}
  .ete-cartao {padding: 18px;}
}
/* ---------------------------------------------------------------- the map of the water colour */
.ete-leitura {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); padding: 20px 24px 18px 24px; box-shadow: var(--sombra); margin: 2px 0 12px 0; animation: ete-sobe .5s ease backwards;}
.ete-leitura .quando {font-size: .740rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--lagoa);}
.ete-leitura .frase {font-family: var(--titulo); font-size: 1.700rem; line-height: 1.18; margin: 6px 0 12px 0; color: var(--tinta); letter-spacing: -.01em;}
.ete-leitura .trocos {display: flex; flex-wrap: wrap; gap: 6px 8px;}
.ete-leitura .aviso-velho {margin-top: 10px; font-size: .820rem; color: #7A4A06;}
.ete-escala-agua {display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 3px; margin: 10px 0 5px 0;}
.ete-escala-agua span {height: 18px;}
.ete-escala-agua span:first-child {border-radius: 999px 4px 4px 999px;} .ete-escala-agua span:last-child {border-radius: 4px 999px 999px 4px;}
.ete-escala-agua-nomes {display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 3px; font-size: .740rem; font-weight: 600; color: var(--tinta); text-align: center; line-height: 1.2;}
.ete-escala-agua-pontas {display: flex; justify-content: space-between; gap: 12px; font-size: .740rem; color: var(--mudo); margin-top: 7px;}
.ete-sem-leitura {display: flex; align-items: center; gap: 8px; font-size: .780rem; color: var(--mudo); margin-top: 12px; line-height: 1.4;}
.ete-sem-leitura i {flex: 0 0 26px; height: 13px; border-radius: 3px; background: #B4B9BE;}
.st-key-mapa_cor [data-testid="stImage"] img, .st-key-mapa_cor img {border-radius: 18px; border: 1px solid var(--linha); box-shadow: var(--sombra); background: #F3F3F7;}
.st-key-mapa_cor_inicio img {border-radius: 16px; border: 1px solid var(--linha);}

/* ---------------------------------------------------------------- two pictures of the same place (drag to compare) */
.ete-comparar {position: relative; overflow: hidden; border-radius: 18px; border: 1px solid var(--linha); box-shadow: var(--sombra); user-select: none; -webkit-user-select: none;
  max-width: 560px; margin: 0 auto; background: #F3F3F7; line-height: 0;}
.ete-comparar img {display: block; width: 100%; height: auto; pointer-events: none;}
.ete-comparar img.topo {position: absolute; inset: 0; clip-path: inset(0 0 0 var(--pos));}
.ete-comparar .linha {position: absolute; top: 0; bottom: 0; left: var(--pos); width: 3px; margin-left: -1.5px; background: #fff; box-shadow: 0 0 0 1px rgba(33,37,41,.18); pointer-events: none;}
.ete-comparar .pega {position: absolute; top: 50%; left: 50%; width: 44px; height: 44px; margin: -22px 0 0 -22px; border-radius: 50%; background: #fff; color: var(--tinta);
  display: flex; align-items: center; justify-content: center; gap: 7px; box-shadow: 0 6px 18px -6px rgba(33,37,41,.55);}
.ete-comparar .pega::before, .ete-comparar .pega::after {content: ""; width: 8px; height: 8px; border: solid currentColor; border-width: 0 0 2.6px 2.6px; border-radius: 1px;}
.ete-comparar .pega::before {transform: rotate(45deg); margin-left: 4px;} .ete-comparar .pega::after {transform: rotate(-135deg); margin-right: 4px;}
.ete-comparar input[type=range] {position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; opacity: 0; cursor: ew-resize; touch-action: pan-y; -webkit-appearance: none; appearance: none;}
.ete-comparar .rotulo {position: absolute; top: 10px; padding: 5px 11px; border-radius: 999px; background: rgba(33,37,41,.74); color: #fff; font-size: .740rem; font-weight: 700;
  line-height: 1.2; pointer-events: none; letter-spacing: .01em;}
.ete-comparar .rotulo.esquerda {left: 10px;} .ete-comparar .rotulo.direita {right: 46px;}       /* clear of the north arrow of the pictures */
.ete-comparar-nota {max-width: 560px; margin: 8px auto 0 auto; font-size: .820rem; color: var(--mudo); text-align: center; line-height: 1.45;}

/* ---------------------------------------------------------------- a WhatsApp message (preview of what people receive) */
.ete-wa {max-width: 420px; margin: 0 auto; border-radius: 28px; overflow: hidden; border: 8px solid #212529; box-shadow: var(--sombra-alta); background: #EEEEF3;}
.ete-wa .topo {display: flex; align-items: center; gap: 10px; background: #615C9F; color: #fff; padding: 10px 14px;}
.ete-wa .topo img {width: 36px; height: 36px; border-radius: 50%; background: #fff;}
.ete-wa .topo b {display: block; font-size: .95rem;} .ete-wa .topo small {display: block; font-size: .72rem; opacity: .8;}
.ete-wa .conversa {padding: 14px 12px 18px 12px; background: #EEEEF3;}
.ete-wa .bolha {background: #fff; border-radius: 4px 14px 14px 14px; padding: 4px; box-shadow: 0 1px 1px rgba(0,0,0,.08); max-width: 100%;}
.ete-wa .bolha > img {display: block; width: 100%; border-radius: 10px;}
.ete-wa .texto {padding: 8px 8px 2px 8px; font-size: .86rem; line-height: 1.45; color: #111B21; word-wrap: break-word;}
.ete-wa .rodape {display: flex; justify-content: space-between; gap: 8px; padding: 2px 8px 8px 8px; font-size: .70rem; color: #667781;}
.ete-wa .botao {border-top: 1px solid #E9EDEF; padding: 10px; text-align: center; color: #027EB5; font-weight: 600; font-size: .86rem;}
.ete-wa .botao span {margin-right: 6px;}

/* ---------------------------------------------------------------- phones: navigation at the bottom, like an app */
.st-key-nav_movel {display: none !important;}
@media (max-width: 700px) {
  .st-key-nav_movel {display: block !important; position: fixed !important; left: 0; right: 0; bottom: 0; z-index: 9995; margin: 0 !important; width: 100% !important;
    background: rgba(255,255,255,.97); -webkit-backdrop-filter: saturate(160%) blur(14px); backdrop-filter: saturate(160%) blur(14px);
    border-top: 1px solid var(--linha); box-shadow: 0 -10px 26px -18px rgba(33,37,41,.40); padding: 6px 6px calc(6px + env(safe-area-inset-bottom)) 6px;}
  .st-key-nav_movel > div, .st-key-nav_movel [data-testid="stRadio"] {width: 100% !important;}
  .st-key-nav_movel div[role="radiogroup"] {display: grid !important; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 2px !important; width: 100%;}
  .st-key-nav_movel label[data-testid="stRadioOption"] {display: flex !important; justify-content: center; background: transparent !important; border: 0 !important; border-radius: 14px !important;
    padding: 2px 0 1px 0 !important; min-width: 0; box-shadow: none !important;}
  .st-key-nav_movel label[data-testid="stRadioOption"] p {display: flex; flex-direction: column; align-items: center; gap: 2px; margin: 0; font-size: .690rem !important; font-weight: 700 !important;
    letter-spacing: .01em; color: var(--mudo) !important; line-height: 1.1; white-space: nowrap;}
  .st-key-nav_movel span[role="img"] {font-size: 1.500rem !important; line-height: 1 !important; padding: 3px 16px; border-radius: 999px; transition: background .2s ease, color .2s ease; vertical-align: middle !important;}
  .st-key-nav_movel label[data-testid="stRadioOption"][data-selected="true"] {background: transparent !important;}
  .st-key-nav_movel label[data-testid="stRadioOption"][data-selected="true"] p {color: var(--rio) !important;}
  .st-key-nav_movel label[data-testid="stRadioOption"][data-selected="true"] span[role="img"] {background: var(--espuma); color: var(--lagoa);}
  [data-testid="stMainBlockContainer"], .block-container {padding-bottom: 100px !important;}
  /* the top on one slim line: the bulletin and the languages (the alerts are in the bar at the bottom, the social links in the footer) */
  .st-key-utilidades {flex-wrap: nowrap !important; padding: 5px 5px 5px 12px !important; border-radius: 16px; row-gap: 0 !important; margin-bottom: 6px;}
  .st-key-utilidades > div:first-child {flex: 1 1 auto !important; order: 0 !important; min-width: 0 !important;}
  .st-key-utilidades .ete-estado {font-size: .700rem; gap: 6px;}
  .st-key-utilidades .ete-estado > span {white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; min-width: 0;}
  .st-key-utilidades .ete-estado .sep {margin: 0 5px; display: inline;}
  .st-key-utilidades .st-key-ir_alertas, .st-key-utilidades [data-testid="stElementContainer"]:has(.ete-redes) {display: none !important;}
  .st-key-lingua label[data-testid="stRadioOption"] {padding: 3px 9px !important;}
  .st-key-lingua label[data-testid="stRadioOption"] p {font-size: .690rem !important;}
  /* the header: the brand only; the pages are in the bar at the bottom */
  .st-key-cabecalho {position: relative !important; top: 0 !important; padding: 6px 12px !important; border-radius: 18px; margin-bottom: 4px;}
  .st-key-cabecalho > .st-key-nav_topo {display: none !important;}
  .ete-marca img {width: 34px; height: 34px;}
  .ete-marca .nome {font-size: 1rem;}
  .ete-cabeca .titulo {font-size: 1.750rem !important;}
  .ete-cabeca .sub {font-size: .980rem !important;}
  .ete-leitura {padding: 16px 16px 14px 16px;}
  .ete-leitura .frase {font-size: 1.380rem;}
  .ete-escala-agua-nomes {font-size: .660rem;}
}
/* ---------------------------------------------------------------- a card that leads to another page (button inside) */
[class*="st-key-porta_"] {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); padding: 22px 24px 20px 24px; box-shadow: var(--sombra); gap: 4px !important;}
[class*="st-key-porta_"] .cab {font-family: var(--titulo); font-weight: 560; font-size: 1.180rem; color: var(--tinta); margin: 6px 0 6px 0; letter-spacing: -.01em; line-height: 1.25;}
[class*="st-key-porta_"] p {margin: 0 0 12px 0; line-height: 1.6;}
[class*="st-key-porta_"] [data-testid="stMarkdownContainer"] {margin-bottom: 0 !important;}      /* Streamlit pulls text up by 1rem: the button would cover the last line */
.st-key-porta_alertas_inicio {background: var(--espuma); border-color: #DCDAEE; box-shadow: none;}
.ete-seccao {scroll-margin-top: 96px;}
.st-key-mapa_radar img, .st-key-mapa_zonas img {border-radius: 18px; border: 1px solid var(--linha); box-shadow: var(--sombra);}
@media (max-width: 700px) {[class*="st-key-porta_"] {padding: 18px;} .ete-seccao {scroll-margin-top: 12px;}}

/* ---------------------------------------------------------------- the search bar (every page, under the navigation) */
.ete-ancora {scroll-margin-top: 96px; height: 0;}
.st-key-busca {margin: 0 0 12px 0; gap: 6px !important;}
.st-key-busca .react-aria-ComboBox [role="group"] {min-height: 52px; border-radius: 999px !important; border: 1px solid var(--linha) !important; box-shadow: var(--sombra); cursor: text;
  background: #FFFFFF url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%234E4A8C' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='10.5' cy='10.5' r='6.5'/%3E%3Cpath d='M20 20l-4.600-4.600'/%3E%3C/svg%3E") no-repeat 18px center / 21px 21px !important;
  padding-left: 48px !important; transition: border-color .18s ease, box-shadow .18s ease;}
.st-key-busca .react-aria-ComboBox [role="group"]:hover {border-color: #C9C6E6 !important;}
.st-key-busca .react-aria-ComboBox [role="group"]:focus-within {border-color: var(--lagoa) !important; box-shadow: 0 0 0 4px rgba(142,138,196,.18), var(--sombra);}
.st-key-busca .react-aria-ComboBox input {font-size: 1rem !important; background: transparent !important; color: var(--tinta) !important; height: 50px;}
.st-key-busca .react-aria-ComboBox input::placeholder {color: #7D7F86; opacity: 1;}
.ete-busca-dica {font-size: .860rem; color: var(--mudo); margin: 0 4px 4px 20px; line-height: 1.45;}
.ete-busca-dica b {color: var(--tinta); font-weight: 600;}
.st-key-pesquisa_resultados {background: var(--cartao); border: 1px solid var(--linha); border-radius: 20px; padding: 12px 16px 8px 16px; box-shadow: var(--sombra); gap: 0 !important; margin-bottom: 12px;}
.st-key-pesquisa_resultados button {justify-content: flex-start !important; text-align: left;}
.ete-busca-cab {font-size: .760rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; color: var(--mudo); margin: 2px 0 8px 2px;}
.st-key-pesquisa_fechar button p {color: var(--mudo) !important; font-weight: 600; font-size: .860rem;}
[data-key='__creatable__'] > div {font-size: 0 !important; padding-left: 24px !important; background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%234E4A8C' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='10.5' cy='10.5' r='6.5'/%3E%3Cpath d='M20 20l-4.600-4.600'/%3E%3C/svg%3E") no-repeat 0 center / 16px 16px;}
[data-key='__creatable__'] > div::before {font-size: .940rem; font-weight: 600; color: var(--lagoa);}          /* Streamlit's «Add: <text>» becomes «Procurar este texto», with a magnifier (the words are set by the page) */
.ete-busca-nada {font-size: .940rem; line-height: 1.55; color: var(--tinta); margin-bottom: 6px;}
.st-key-lista_lugares {flex-flow: row wrap !important; gap: 8px !important; margin-bottom: 10px;}
.st-key-lista_lugares > div {width: auto !important; flex: 0 0 auto !important;}

/* ---------------------------------------------------------------- a place: three answers, pictures with the place marked */
.ete-cabeca.zona .chips {margin-top: 14px; display: flex; flex-wrap: wrap; gap: 2px;}
.ete-respostas {display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin: 4px 0 10px 0;}
.ete-resposta {position: relative; overflow: hidden; background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); padding: 18px 20px 16px 24px; box-shadow: var(--sombra);}
.ete-resposta::before {content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 7px; background: var(--c, var(--mare));}
.ete-resposta .q {display: flex; align-items: center; gap: 8px; font-size: .740rem; letter-spacing: .09em; text-transform: uppercase; font-weight: 700; color: var(--mudo);}
.ete-resposta .q .ic {color: var(--lagoa); line-height: 0;}
.ete-resposta .r {font-family: var(--titulo); font-weight: 560; font-size: 1.400rem; line-height: 1.2; color: var(--tinta); margin: 10px 0 6px 0; letter-spacing: -.01em;}
.ete-resposta .d {font-size: .880rem; color: var(--mudo); line-height: 1.5;}
.ete-foto {position: relative; overflow: hidden; border-radius: 18px; border: 1px solid var(--linha); box-shadow: var(--sombra); line-height: 0; background: var(--suave);}
.ete-foto img {display: block; width: 100%; height: auto;}
.ete-anel {position: absolute; left: 50%; top: 50%; width: var(--d, 16.7%); aspect-ratio: 1 / 1; transform: translate(-50%, -50%); border-radius: 50%; z-index: 1; pointer-events: none;
  border: 2.5px solid #FFFFFF; box-shadow: 0 0 0 1.5px rgba(33,37,41,.8), inset 0 0 0 1.5px rgba(33,37,41,.8);}
.ete-anel::after {content: ""; position: absolute; left: 50%; top: 50%; width: 8px; height: 8px; margin: -4px 0 0 -4px; border-radius: 50%; background: var(--tinta); box-shadow: 0 0 0 2px #FFFFFF;}
.ete-escala-km {position: absolute; left: 12px; bottom: 12px; z-index: 1; pointer-events: none; line-height: 1; text-align: center;}
.ete-escala-km b {display: block; line-height: 1.2; font-size: .700rem; font-weight: 700; color: #FFFFFF; text-shadow: 0 0 3px rgba(33,37,41,.95), 0 0 1px rgba(33,37,41,.95); margin-bottom: 4px;}
.ete-escala-km i {display: block; height: 4px; background: #FFFFFF; box-shadow: 0 0 0 1.5px rgba(33,37,41,.8);}
.ete-foto .rotulo {position: absolute; top: 10px; left: 10px; z-index: 2; padding: 5px 11px; border-radius: 999px; background: rgba(33,37,41,.74); color: #FFFFFF; font-size: .740rem; font-weight: 700; line-height: 1.3;}
.ete-comparar.com-anel .pega {top: 84%;}
.ete-comparar.com-anel .rotulo.direita {right: 10px;}        /* the pictures of a place have no north arrow */
.ete-foto-nota {font-size: .820rem; color: var(--mudo); line-height: 1.5; margin: 8px 2px 12px 2px;}
.ete-factos {list-style: none; padding: 0; margin: 0;}
.ete-factos li {display: flex; justify-content: space-between; gap: 12px; padding: 9px 0; border-bottom: 1px solid #ECEBF2; font-size: .920rem;}
.ete-factos li:last-child {border-bottom: 0;}
.ete-factos li span {color: var(--mudo);} .ete-factos li b {color: var(--tinta); text-align: right;}

/* ---------------------------------------------------------------- curiosities */
.ete-curiosidades {display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-bottom: 16px;}
.ete-curiosidade {display: flex; flex-direction: column; gap: 8px; background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); padding: 20px 22px 16px 22px; box-shadow: var(--sombra);}
.ete-curiosidade {border-top: 4px solid var(--marca);}
.ete-curiosidade .fig {font-family: var(--titulo); font-weight: 600; font-size: 2.300rem; line-height: 1.05; color: var(--marca); letter-spacing: -.02em; font-variant-numeric: lining-nums;}
.ete-curiosidade .leg {font-size: .720rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--mudo); margin: -2px 0 6px 0; padding-bottom: 10px; border-bottom: 1px solid var(--linha);}
.ete-curiosidade .cab {font-family: var(--titulo); font-weight: 560; font-size: 1.160rem; line-height: 1.25; color: var(--tinta); letter-spacing: -.01em;}
.ete-curiosidade p {margin: 0; font-size: .930rem; line-height: 1.6; color: #343A40;}
.ete-curiosidade .fonte {margin-top: auto; padding-top: 10px; border-top: 1px dashed var(--linha); font-size: .740rem; color: var(--mudo); line-height: 1.45;}
@media (hover: hover) and (pointer: fine) {.ete-curiosidade {transition: transform .25s ease, box-shadow .25s ease;} .ete-curiosidade:hover {transform: translateY(-3px); box-shadow: var(--sombra-alta);}}
@media (max-width: 700px) {
  .ete-ancora {scroll-margin-top: 12px;}
  .st-key-busca .react-aria-ComboBox [role="group"] {min-height: 48px; background-position: 15px center !important; padding-left: 42px !important;}
  .st-key-busca .react-aria-ComboBox input {height: 46px; font-size: .960rem !important;}
  .ete-busca-dica {margin-left: 8px; font-size: .800rem;}
  .ete-respostas {grid-template-columns: 1fr; gap: 10px;}
  .ete-resposta {padding: 14px 16px 12px 20px;} .ete-resposta .r {font-size: 1.200rem; margin: 6px 0 4px 0;}
  .ete-curiosidade {padding: 16px 18px 14px 18px;}
  /* on phones the curiosities slide sideways (the next card peeks out), so the page does not grow by a dozen cards */
  .ete-curiosidades {display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: 12px; margin: 0 -.8rem 14px -.8rem; padding: 2px .8rem 10px .8rem; scrollbar-width: none;}
  .ete-curiosidades::-webkit-scrollbar {display: none;}
  .ete-curiosidades .ete-curiosidade {flex: 0 0 84%; scroll-snap-align: center;}
  .ete-comparar.com-anel .rotulo {font-size: .660rem; padding: 4px 8px; top: 8px;} .ete-comparar.com-anel .rotulo.esquerda {left: 8px;} .ete-comparar.com-anel .rotulo.direita {right: 8px;}
}
/* ---------------------------------------------------------------- accounts: the button in the header, the forms, the recovery code */
.st-key-cabecalho > .st-key-ir_conta {flex: 0 0 auto !important; width: auto !important;}
.st-key-ir_conta button {border-color: var(--marca) !important; color: var(--marca) !important; padding: .420rem .950rem !important; min-height: 0 !important; background: #FFFFFF !important;}
.st-key-ir_conta button p {font-size: .850rem !important; font-weight: 700 !important; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;}
.st-key-ir_conta button:hover {background: var(--marca) !important; color: #FFFFFF !important;}
.st-key-caixa_entrar, .st-key-caixa_criar, .st-key-caixa_dados {background: var(--cartao); border: 1px solid var(--linha); border-radius: var(--raio); padding: 18px 22px 20px 22px; box-shadow: var(--sombra);}
.st-key-caixa_entrar .ete-titulo-p, .st-key-caixa_criar .ete-titulo-p {margin-top: 2px;}
.st-key-caixa_codigo {background: var(--espuma); border: 1px solid var(--marca); border-radius: var(--raio); padding: 20px 24px; margin-bottom: 10px;}
.st-key-caixa_codigo .cab {font-family: var(--titulo); font-weight: 560; font-size: 1.180rem; color: var(--tinta); margin: 6px 0 8px 0;}
.st-key-caixa_codigo [data-testid="stMarkdownContainer"] {margin-bottom: 0 !important;}
.ete-codigo {font-family: ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace; font-size: 1.500rem; font-weight: 700; letter-spacing: .12em; color: var(--marca);
  background: #FFFFFF; border: 1px dashed var(--marca); border-radius: 14px; padding: 10px 16px; display: inline-block; margin: 4px 0 10px 0; user-select: all;}
.st-key-atalho_zona {background: var(--espuma); border: 1px solid #DCDAEE; border-radius: 999px; padding: 4px 8px 4px 18px; margin: 0 0 14px 0; width: fit-content !important; max-width: 100%;}
.ete-atalho {font-size: .900rem; color: var(--tinta);} .ete-atalho b {color: var(--marca);}
@media (max-width: 700px) {
  .st-key-cabecalho > .st-key-ir_conta {margin-left: auto;}
  .st-key-ir_conta button {padding: .340rem .750rem !important;}
  .st-key-ir_conta button p {max-width: 96px;}
  .st-key-caixa_entrar, .st-key-caixa_criar, .st-key-caixa_dados {padding: 14px 16px 16px 16px;}
  .ete-codigo {font-size: 1.200rem;}
}
@media (prefers-reduced-motion: reduce) {*, *::before, *::after {animation: none !important; transition: none !important;} .ete-kpi, .ete-cartao, .ete-dia, .ete-troco .no {transform: none !important;}}
</style>
"""

ONDAS = ("<svg class='ondas' viewBox='0 0 1200 300' preserveAspectRatio='none' aria-hidden='true'><g fill='none' stroke='#FFFFFF' stroke-width='2'>"
         + "".join(f"<path d='M0 {40 + 36 * i}c150-{30 + 4 * i} 300-{30 + 4 * i} 450 0s300 {30 + 4 * i} 450 0 200-{20 + 3 * i} 300-10'/>" for i in range(7)) + "</g></svg>")
ARTE = ("<svg class='arte' viewBox='0 0 380 260' aria-hidden='true'><g fill='none' stroke='#8E8AC4' stroke-width='1.600'>"
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
STATIC_DIR = Path(__file__).parent / "static"            # logos made by scripts/build_platform_logos.py


@lru_cache(maxsize=16)
def imagem(nome: str, altura: int) -> str:
    """A logo of static/ as a data address: the picture travels inside the page. The Streamlit
    Community Cloud answered "Internal server error" for the files of app/static (14/11/2026), so
    the page does not depend on that service. Reduced to twice the height it is shown at (sharp on
    phones) and to a small palette: about 4 KB each."""
    from PIL import Image

    im = Image.open(STATIC_DIR / f"{nome}.png").convert("RGBA")
    im = im.resize((round(im.width * altura / im.height), altura), Image.LANCZOS)
    buffer = io.BytesIO()
    im.quantize(64, method=Image.Quantize.FASTOCTREE).save(buffer, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

_REDES = {
    "facebook": "<svg viewBox='0 0 24 24' width='18' height='18' aria-hidden='true'><path fill='currentColor' d='M13.5 21v-7.600h2.600l.400-3h-3V8.500c0-.900.300-1.500 1.600-1.500H16.700V4.300c-.300 0-1.200-.100-2.300-.100-2.300 0-3.900 1.400-3.900 4v2.200H8v3h2.500V21z'/></svg>",
    "whatsapp": "<svg viewBox='0 0 24 24' width='18' height='18' fill='none' stroke='currentColor' stroke-width='1.700' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
                "<path d='M4.200 19.800l1.100-3.900A8.300 8.300 0 1 1 8.300 19z'/><path d='M9.200 8.300c.300-.600.700-.600 1-.500l.800 1.700c.100.300 0 .500-.200.700l-.500.600c.500 1.100 1.400 2 2.500 2.500l.600-.500c.200-.200.400-.300.700-.200l1.700.800c.100.300.100.700-.500 1-.700.400-1.600.500-2.600.100a8.400 8.400 0 0 1-4.100-4.100c-.400-1-.300-1.900.100-2.600z' fill='currentColor' stroke='none'/></svg>",
    "linkedin": "<svg viewBox='0 0 24 24' width='17' height='17' aria-hidden='true'><path fill='currentColor' d='M5.200 8.800h3.100V19H5.200zM6.700 4a1.800 1.800 0 1 1 0 3.600 1.800 1.800 0 0 1 0-3.600zM10.300 8.800h3v1.400c.400-.800 1.500-1.700 3.100-1.700 3.300 0 3.900 2.200 3.900 5V19h-3.100v-4.900c0-1.200 0-2.700-1.700-2.700s-1.900 1.300-1.900 2.600V19h-3.100z'/></svg>",
    "email": "<svg viewBox='0 0 24 24' width='18' height='18' fill='none' stroke='currentColor' stroke-width='1.700' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'><rect x='3.500' y='5.500' width='17' height='13' rx='2.500'/><path d='M4 7l8 6 8-6'/></svg>",
}


def social(small: bool = False, light: bool = False) -> str:
    """Round buttons for Facebook, WhatsApp, LinkedIn and e-mail (they open in a new tab). `light`: for a light background."""
    items = [("facebook", CONTACTOS["facebook"], "Facebook"), ("whatsapp", CONTACTOS["whatsapp"], "WhatsApp " + CONTACTOS["telefone"]),
             ("linkedin", CONTACTOS["linkedin"], "LinkedIn"), ("email", "mailto:" + CONTACTOS["email"], t("Questões técnicas") + ": " + CONTACTOS["email"])]
    links = "".join(f"<a class='ete-rede' href='{href}' target='_blank' rel='noopener' title='{label}' aria-label='{label}'>{_REDES[k]}</a>" for k, href, label in items)
    return f"<div class='ete-redes{' pequenas' if small else ''}{' claras' if light else ''}'>{links}</div>"


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
    html(f"<div class='ete-marca'><img src='{imagem('ete', 96)}' alt='Eyes to Earth' width='44' height='44'>"
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
        f"<a href='{url}' target='_blank' rel='noopener' title='{name}'><img src='{imagem(key + '_' + suffix, 132 if key == 'oad' else 108)}' alt='{name}' height='{66 if key == 'oad' else 54}'></a>"
        for key, name, url in APOIOS) + "</div>"


def footer(notice: str, light_page: str = "") -> None:
    light = f"<p><a href='{light_page}'>{t('Versão leve do boletim')}</a>, {t('para quando há pouca rede.')}</p>" if light_page else ""
    html("<div class='ete-rodape'><div class='cols'>"
         f"<div><div class='nome'><img src='{imagem('ete', 96)}' alt='' width='46' height='46'>Eyes to Earth</div>"
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


def section(title: str, subtitle: str = "", eyebrow: str = "", anchor: str = "") -> None:
    ident = f" id='{anchor}'" if anchor else ""                 # a button on another page can open the page at this section
    html(f"<div class='ete-seccao'{ident}>" + (f"<div class='ete-olho'>{t(eyebrow)}</div>" if eyebrow else "") + f"<div class='titulo' role='heading' aria-level='2'>{t(title)}</div>"
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


def hero(level: str, title: str, colour: str, advice: str = "", valid_until: str = "", issued: str = "", colours: dict | None = None, day=None,
         nome: str = "") -> None:
    """The answer of the day, in plain words, with the level on a four-step scale. With `nome` (signed in), the greeting uses it."""
    scale = _scale(level, colours) if colours else ""
    foot = (f"<div class='pe'>{t('Válido até <b>{dia}</b>', dia=valid_until)}" + (f" · {t('emitido a {quando}', quando=issued)}" if issued else "") + "</div>") if valid_until else ""
    do = f"<div class='fazer'><span class='ic'>{icon('escudo', 22, '#FFFFFF')}</span><div><b>{t('O que fazer hoje')}</b><span>{t(advice)}</span></div></div>" if advice else ""
    html(f"<div class='ete-hero nv-{level}'>{ONDAS}<div class='esq'><div class='data'>{data_longa(day or agora())} · Marracuene</div>"
         f"<div class='grande' role='heading' aria-level='1'>{saudacao()}{', ' + html_escape(nome) if nome else ''}.<br><em>{t(ALERT_HEADLINE[level])}</em></div>"
         f"<p class='lead'>{L.titulo_boletim(title)}</p>{do}</div>"
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


# ----------------------------------------------------------------------------- the map of the water colour
# How each of the five steps reads in a sentence ("Em Marracuene, a água está ...")
FRASES_AGUA = {"muito clara": "muito mais clara do que o costume", "clara": "mais clara do que o costume", "habitual": "com a cor do costume",
               "turva": "mais turva do que o costume", "muito turva": "muito mais turva do que o costume"}


def water_reading(when: str, sentence: str, places: list[tuple[str, str, str]], old_note: str = "") -> None:
    """The reading of the map in one sentence, with the date of the image and a chip per section."""
    chips_html = "".join(f"<span class='ete-chip'>{dot(colour)}<b>{name}</b>&nbsp;· {t(label)}</span>" for name, label, colour in places)
    html(f"<div class='ete-leitura'><div class='quando'>{when}</div><div class='frase' role='heading' aria-level='2'>{sentence}</div>"
         f"<div class='trocos'>{chips_html}</div>" + (f"<div class='aviso-velho'>{old_note}</div>" if old_note else "") + "</div>")


def water_scale(steps: list[dict]) -> None:
    """The five colours of the water from clearer to muddier, named, and the grey of 'no reading'."""
    shown = [s for s in steps if s["valor"] <= 4]
    grey = next((s for s in steps if s["valor"] == 5), None)
    bars = "".join(f"<span style='background:{s['cor']}'></span>" for s in shown)
    names = "".join(f"<span>{t(s['nome'])}</span>" for s in shown)
    html(f"<div class='ete-olho'>{t('Cor da água')}</div>"
         f"<div class='ete-escala-agua' role='img' aria-label='{t('Escala de cor: da água mais clara à mais turva')}'>{bars}</div>"
         f"<div class='ete-escala-agua-nomes'>{names}</div>"
         f"<div class='ete-escala-agua-pontas'><span>← {t('mais clara')}</span><span>{t('mais lama')} →</span></div>"
         + (f"<div class='ete-sem-leitura'><i style='background:{grey['cor']}'></i><span>{t('Cinzento: sem leitura. Nuvens, sombras de árvores e de nuvens, plantas, folhas e a margem nunca contam.')}</span></div>" if grey else ""))


# ----------------------------------------------------------------------------- two pictures of the same place
def _uri(file) -> str:
    file = Path(file)
    kind = "jpeg" if file.suffix.lower() in (".jpg", ".jpeg") else "png"
    return f"data:image/{kind};base64," + base64.b64encode(file.read_bytes()).decode()


def _marks(ring: float | None, km: float | None) -> str:
    """The place in the middle of a square picture (a circle `ring` of the width across) and a 1 km bar (`km` of the width)."""
    return ((f"<span class='ete-anel' style='--d:{100 * ring:.2f}%'></span>" if ring else "")
            + (f"<span class='ete-escala-km' style='width:{100 * km:.2f}%'><b>1 km</b><i></i></span>" if km else ""))


def compare(left, right, left_label: str, right_label: str, key: str, start: int = 50, note: str = "", ring: float | None = None, km: float | None = None) -> None:
    """Two pictures of the same place on top of each other: drag the white bar (or tap) to slide from one
    to the other. Both must have the same frame. Sent once per visit: Streamlit keeps large pieces of a
    page in the browser and does not send them again on each click. With `ring`, a circle marks the
    place in the middle; with `km`, a 1 km bar (both as a share of the width)."""
    st.html(f"<div class='ete-comparar{' com-anel' if ring else ''}' id='cmp-{key}' style='--pos:{start}%'>"
         f"<img class='base' src='{_uri(left)}' alt='{left_label}'><img class='topo' src='{_uri(right)}' alt='{right_label}'>" + _marks(ring, km) +
         f"<span class='rotulo esquerda'>{left_label}</span><span class='rotulo direita'>{right_label}</span>"
         "<div class='linha'><span class='pega'></span></div>"                     # the arrows are drawn in CSS (st.html removes SVG)
         f"<input type='range' min='0' max='100' value='{start}' aria-label='{t('Arraste para comparar as duas imagens')}'></div>"
         + (f"<div class='ete-comparar-nota'>{note}</div>" if note else "")
         # Streamlit removes inline handlers (oninput) but runs scripts: the bar is wired here
         + f"<script>(() => {{const box = document.getElementById('cmp-{key}'); if (!box) return; const bar = box.querySelector('input');"
           "const move = () => box.style.setProperty('--pos', bar.value + '%'); bar.addEventListener('input', move); move();})();</script>",
         unsafe_allow_javascript=True)


# ----------------------------------------------------------------------------- a WhatsApp message, as it arrives on the phone
def whatsapp_preview(card_png: bytes | None, text: str, footer: str, buttons: list[str], hour: str) -> None:
    """The message as it looks in WhatsApp: the situation card on top, the text, the footer and the buttons."""
    image = f"<img src='data:image/png;base64,{base64.b64encode(card_png).decode()}' alt='{t('Cartão com a situação dos próximos 10 dias')}'>" if card_png else ""
    body = html_escape(text).replace("\n", "<br>")
    keys = "".join(f"<div class='botao'><span>↗</span>{html_escape(b)}</div>" for b in buttons)
    st.html(f"<div class='ete-wa'><div class='topo'><img src='{imagem('ete', 96)}' alt=''><div><b>Eyes to Earth</b><small>{t('conta oficial dos alertas')}</small></div></div>"
            f"<div class='conversa'><div class='bolha'>{image}<div class='texto'>{body}</div><div class='rodape'><span>{html_escape(footer)}</span><span>{hour}</span></div>"
            f"{keys}</div></div></div>")


def html_escape(text: str) -> str:
    import html as _html

    return _html.escape(str(text))


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
    html(f"<div class='ete-msg'>{text}<span class='hora'>{agora():%H:%M}</span></div>")


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
PRIORIDADE = {"alto": ("Prioridade alta", "#9A3412", "#FDEBD8"), "atencao": ("Atenção", "#8A5A00", "#FFF4D6"), "info": ("Sempre", "#615C9F", "#F0EFF8")}
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


def advice_card(titulo: str, itens: list[str], nivel: str = "info", olho: str = "", texto: str = "", porque: str = "") -> None:
    """One situation in one card: its priority (in words, not colour only), what it means, what to do and, at the foot, what the data show."""
    rotulo, cor, fundo = PRIORIDADE[nivel]
    lista = "".join(f"<li><span class='v'>{VISTO}</span><span>{t(i)}</span></li>" for i in itens)
    html(f"<div class='ete-conselho' style='--c:{cor};--f:{fundo}'><div class='topo'><span class='prio'>{t(rotulo)}</span>"
         + (f"<span class='ete-olho'>{t(olho)}</span>" if olho else "") + f"</div><div class='cab'>{t(titulo)}</div>"
         + (f"<p class='sentido'>{t(texto)}</p>" if texto else "") + (f"<ul>{lista}</ul>" if itens else "")
         + (f"<div class='porque'><b>{t('O que os dados mostram:')}</b><br>{porque}</div>" if porque else "") + "</div>")


# ----------------------------------------------------------------------------- a place
def anchor(name: str) -> None:
    """An invisible mark a search or a button can open the page at (a part of a section, without a title of its own)."""
    html(f"<div class='ete-ancora' id='{name}'></div>")


def zone_head(name: str, line: str, chips_html: str = "") -> None:
    """The head of the page of a place: its name (never translated), where it is, and a few chips."""
    html(f"<div class='ete-cabeca zona'>{ARTE}<div class='ete-olho'>{t('A sua zona')}</div><div class='titulo' role='heading' aria-level='1'>{html_escape(name)}</div>"
         f"<div class='sub'>{line}</div>" + (f"<div class='chips'>{chips_html}</div>" if chips_html else "") + "</div>")


def answers(items: list[dict]) -> None:
    """Short answers to the questions people ask first: each item has icone, pergunta, resposta, detalhe and cor (the stripe)."""
    cards = "".join(f"<div class='ete-resposta' style='--c:{i.get('cor') or MARE}'><div class='q'><span class='ic'>{icon(i['icone'], 18)}</span>{i['pergunta']}</div>"
                    f"<div class='r'>{i['resposta']}</div>" + (f"<div class='d'>{i['detalhe']}</div>" if i.get("detalhe") else "") + "</div>" for i in items)
    html(f"<div class='ete-respostas'>{cards}</div>")


def picture(file, alt: str, label: str = "", ring: float | None = None, km: float | None = None, note: str = "") -> None:
    """A square picture of a place with the place marked in the middle (and a 1 km bar), enlarged by the browser."""
    st.html(f"<div class='ete-foto'><img src='{_uri(file)}' alt='{html_escape(alt)}'>" + _marks(ring, km)          # st.html: Markdown would shrink the picture
            + (f"<span class='rotulo'>{label}</span>" if label else "") + "</div>" + (f"<div class='ete-foto-nota'>{note}</div>" if note else ""))


def facts(rows: list[tuple[str, str]]) -> str:
    """Label and value, one per line (HTML for inside a card)."""
    return "<ul class='ete-factos'>" + "".join(f"<li><span>{a}</span><b>{b}</b></li>" for a, b in rows) + "</ul>"


def curiosities(items: list[dict]) -> None:
    """A grid of curiosities, each opening with a figure in large type (a number, or two words) and a short line under
    it, then the title, the text and the source; all already translated and filled in. No icons, no emojis."""
    cards = "".join(f"<div class='ete-curiosidade'><div class='fig'>{i['figura']}</div><div class='leg'>{i['legenda']}</div><div class='cab'>{i['titulo']}</div>"
                    f"<p>{i['texto']}</p><div class='fonte'>{i['fonte']}</div></div>" for i in items)
    html(f"<div class='ete-curiosidades'>{cards}</div>")
