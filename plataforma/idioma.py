"""Línguas da plataforma ETE: português (original), inglês e francês.

O texto é escrito em português no código e traduzido no momento de o mostrar:

    t("Caudal do rio hoje")                         -> "River flow today" (em inglês)
    t("Válido até {dia}", dia="23/10")              -> "Valid until 23/10"

As traduções estão em `textos.py` (português -> inglês, francês). Um texto sem tradução aparece
em português, nunca em branco. Para encontrar os que faltam:

    ETE_REGISTAR_EM_FALTA=1 python testar_app.py    # escreve textos_em_falta.txt

Também aqui: datas e números escritos à maneira de cada língua, e a tradução do título do
boletim (que o pipeline diário escreve em português).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st

import textos

LINGUAS = {"pt": "PT", "en": "EN", "fr": "FR"}
NOMES = {"pt": "Português", "en": "English", "fr": "Français"}
_INDICE = {"en": 0, "fr": 1}
_TRADUZIDOS: dict[int, set] = {}


def _tabela() -> dict:
    """The translations as they are now. Looked up on every call, never kept: when textos.py changes
    and is reloaded by the running app, the new translations are used at once (keeping a reference
    made a server started before a change show part of the page in Portuguese)."""
    return textos.TEXTOS


def _traduzidos() -> set:
    tabela = _tabela()
    if id(tabela) not in _TRADUZIDOS:
        _TRADUZIDOS.clear()
        _TRADUZIDOS[id(tabela)] = {v for par in tabela.values() for v in par}
    return _TRADUZIDOS[id(tabela)]
_REGISTO = Path(__file__).resolve().parent / "textos_em_falta.txt"
_REGISTAR = bool(os.environ.get("ETE_REGISTAR_EM_FALTA"))


def lingua() -> str:
    try:
        valor = st.session_state.get("lingua", "pt")
    except Exception:                                     # outside a Streamlit run
        valor = "pt"
    return valor if valor in LINGUAS else "pt"


def _falta(texto: str) -> None:
    if _REGISTAR and re.search(r"[A-Za-zÀ-ÿ]{3}", texto) and texto not in _traduzidos():
        with _REGISTO.open("a", encoding="utf-8") as f:
            f.write(texto.replace("\n", "\\n") + "\n")


def t(texto, **valores):
    """The text in the reader's language. Values given by name fill the {gaps} after translating."""
    if not isinstance(texto, str):
        return texto
    lang = lingua()
    if lang != "pt" and texto:
        par = _tabela().get(texto)
        if par is None:
            _falta(texto)
        else:
            texto = par[_INDICE[lang]]
    return texto.format(**valores) if valores else texto


def nivel(level: str) -> str:
    """An alert level name (verde, amarelo...) in the reader's language."""
    return t(level)


def troco(nome: str) -> str:
    """A river-section name such as 'Q1 fronteira / Ressano Garcia': the code stays, the words are translated."""
    nome = str(nome)
    codigo, _, resto = nome.partition(" ")
    if re.fullmatch(r"Q\d|\d", codigo) and resto:
        return f"{codigo} {t(resto)}"
    return t(nome)


# ----------------------------------------------------------------------------- numbers and dates
def numero(valor, casas: int | None = 0) -> str:
    """A number written the local way: 1 234,5 (pt, fr) or 1,234.5 (en); a dash when there is no value."""
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return "–"
    if isinstance(valor, str):
        return valor
    texto = f"{valor:,.{casas}f}"
    if lingua() == "en":
        return texto
    inteiro_grande = abs(valor) >= 10000
    return texto.replace(",", " " if inteiro_grande else "").replace(".", ",")


_MESES = {"pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
          "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
          "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]}
_MESES_CURTOS = {"pt": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
                 "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                 "fr": ["janv", "févr", "mars", "avr", "mai", "juin", "juil", "août", "sept", "oct", "nov", "déc"]}
_DIAS = {"pt": ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"],
         "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
         "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]}
_DIAS_CURTOS = {"pt": ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"], "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "fr": ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]}


def meses() -> list[str]:
    return _MESES_CURTOS[lingua()]


def meses_longos() -> list[str]:
    return _MESES[lingua()]


def dia_curto(dia) -> str:
    return _DIAS_CURTOS[lingua()][pd.Timestamp(dia).weekday()]


def dia_mes(dia) -> str:
    """23 de outubro · 23 October · 23 octobre"""
    dia = pd.Timestamp(dia)
    mes = _MESES[lingua()][dia.month - 1]
    return f"{dia.day} de {mes}" if lingua() == "pt" else f"{dia.day} {mes}"


def dia_da_semana(dia) -> str:
    """Terça-feira, 13 de outubro · Tuesday, 13 October · Mardi 13 octobre"""
    dia = pd.Timestamp(dia)
    nome = _DIAS[lingua()][dia.weekday()]
    texto = f"{nome} {dia_mes(dia)}" if lingua() == "fr" else f"{nome}, {dia_mes(dia)}"
    return texto[0].upper() + texto[1:]


def data_longa(dia) -> str:
    """terça-feira, 13 de outubro de 2026 · Tuesday, 13 October 2026 · mardi 13 octobre 2026"""
    dia = pd.Timestamp(dia)
    nome = _DIAS[lingua()][dia.weekday()]
    if lingua() == "pt":
        return f"{nome}, {dia_mes(dia)} de {dia.year}"
    return f"{nome}, {dia_mes(dia)} {dia.year}" if lingua() == "en" else f"{nome} {dia_mes(dia)} {dia.year}"


def mes_ano(mes: str) -> str:
    """'2026-01' -> Janeiro de 2026 · January 2026 · Janvier 2026"""
    nome = _MESES[lingua()][int(mes[5:7]) - 1]
    texto = f"{nome} de {mes[:4]}" if lingua() == "pt" else f"{nome} {mes[:4]}"
    return texto[0].upper() + texto[1:]


# ----------------------------------------------------------------------------- the bulletin headline (written in Portuguese by the daily pipeline)
_TITULOS = [
    (re.compile(r"Nível (\w+) nos próximos (\d+) dias: nenhum cenário prevê cheia no Incomáti em Marracuene\."),
     "Nível {0} nos próximos {1} dias: nenhum cenário prevê cheia no Incomáti em Marracuene."),
    (re.compile(r"Nível VERDE como cenário mais provável, mas há possibilidade de nível (\w+) por volta de ([\d/]+) \((\d+) % dos cenários\)\."),
     "Nível VERDE como cenário mais provável, mas há possibilidade de nível {0} por volta de {1} ({2} % dos cenários)."),
    (re.compile(r"Nível (\w+) previsto a partir de ([\d/]+)\. O caudal mais alto é esperado a ([\d/]+): cerca de ([\d\s ]+) m³/s\."),
     "Nível {0} previsto a partir de {1}. O caudal mais alto é esperado a {2}: cerca de {3} m³/s."),
]


def titulo_boletim(texto: str) -> str:
    if lingua() == "pt":
        return texto
    for padrao, modelo in _TITULOS:
        achado = padrao.fullmatch(texto.strip())
        if achado:
            partes = [t(p.lower()).upper() if p.isalpha() and p.isupper() else p for p in achado.groups()]
            return t(modelo).format(*partes)
    return t(texto)
