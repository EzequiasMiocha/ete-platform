"""Peças visuais da plataforma ETE: estilo, cartões, gráficos e mapas.

Regras seguidas em todos os gráficos:
  * as cores de alerta (verde, amarelo, laranja, vermelho) só são usadas para alertas, e vêm
    sempre com a palavra ao lado;
  * as séries usam uma ordem fixa de cores (azul, laranja, verde-água), no máximo três de cada vez;
  * um só eixo por gráfico; passar o dedo ou o rato sobre um ponto mostra o valor;
  * datas escritas em números (dia/mês), para não aparecerem meses em inglês.
"""

from __future__ import annotations

from contextlib import contextmanager

import altair as alt
import pandas as pd
import streamlit as st

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]        # fixed order; never more than three series at once
INK, MUTED, GRID = "#1c2833", "#566573", "#e5e8e8"
NEUTRAL_BAND = "#d5dbdb"
ALERT_TEXT = {"verde": "white", "amarelo": "#1c2833", "laranja": "white", "vermelho": "white"}
ALERT_ICON = {"verde": "🟢", "amarelo": "🟡", "laranja": "🟠", "vermelho": "🔴"}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

CSS = """
<style>
  .block-container {padding-top: 1.2rem; padding-bottom: 2.5rem; max-width: 1080px;}
  h1 {font-size: 1.45rem !important; margin-bottom: 0 !important;}
  h2 {font-size: 1.2rem !important;} h3 {font-size: 1.05rem !important;}
  .ete-sub {color: #566573; font-size: .9rem; margin: 0 0 .6rem 0;}
  .ete-alerta {border-radius: 12px; padding: 18px 20px; margin: .4rem 0 1rem 0;}
  .ete-alerta .nivel {font-size: 1.7rem; font-weight: 700; line-height: 1.15;}
  .ete-alerta .texto {font-size: 1.02rem; margin-top: .3rem;}
  .ete-dias {display: flex; gap: 6px; flex-wrap: wrap; margin: .2rem 0 .6rem 0;}
  .ete-dia {border-radius: 8px; padding: 6px 4px; min-width: 52px; text-align: center; font-size: .82rem; line-height: 1.2;}
  .ete-dia b {display: block; font-size: .95rem;}
  .ete-cartao {background: #f8f9f9; border: 1px solid #e5e8e8; border-radius: 10px; padding: 12px 14px; margin-bottom: .6rem;}
  .ete-chip {display: inline-block; border-radius: 999px; padding: 3px 11px; margin: 2px 4px 2px 0; font-size: .85rem; border: 1px solid #d5d8dc; background: white;}
  .ete-ponto {display: inline-block; width: .7em; height: .7em; border-radius: 50%; margin-right: .4em; vertical-align: middle;}
  .ete-rodape {color: #566573; font-size: .8rem; border-top: 1px solid #e5e8e8; margin-top: 2rem; padding-top: .7rem;}
  div[data-testid="stMetricValue"] {font-size: 1.35rem;}
  @media (max-width: 640px) {
    .block-container {padding-left: .8rem; padding-right: .8rem;}
    .ete-alerta .nivel {font-size: 1.4rem;}
  }
</style>
"""


# ----------------------------------------------------------------------------- pieces of the page
@contextmanager
def guard(what: str):
    """Error boundary: a broken section says so and the rest of the page still shows."""
    try:
        yield
    except Exception:                                        # pragma: no cover - last line of defence
        st.warning(f"Não foi possível mostrar: {what}.")


def alert_banner(level: str, title: str, colour: str) -> None:
    st.markdown(f"<div class='ete-alerta' style='background:{colour};color:{ALERT_TEXT[level]}'>"
                f"<div class='nivel'>Alerta {level.upper()}</div><div class='texto'>{title}</div></div>", unsafe_allow_html=True)


def unavailable_banner() -> None:
    st.markdown("<div class='ete-alerta' style='background:#566573;color:white'><div class='nivel'>Previsão indisponível</div>"
                "<div class='texto'>Não há um boletim válido das últimas 36 horas. Isto não quer dizer que não há perigo. "
                "Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul.</div></div>", unsafe_allow_html=True)


def day_strip(days: list[dict], colours: dict) -> None:
    """The next days as coloured tiles: date, and the alert word under it (never colour alone)."""
    tiles = "".join(f"<div class='ete-dia' style='background:{colours[d['alerta']]};color:{ALERT_TEXT[d['alerta']]}'>"
                    f"<b>{pd.Timestamp(d['data']).strftime('%d/%m')}</b>{d['alerta']}</div>" for d in days)
    st.markdown(f"<div class='ete-dias'>{tiles}</div>", unsafe_allow_html=True)


def chips(items: list[tuple[str, str, str]]) -> None:
    """Small labelled pills: (name, state, colour of the dot)."""
    html = "".join(f"<span class='ete-chip'><span class='ete-ponto' style='background:{colour}'></span><b>{name}</b>: {state}</span>" for name, state, colour in items)
    st.markdown(html, unsafe_allow_html=True)


def legend(items: list[dict]) -> None:
    chips([(str(i["nome"]), "", i["cor"]) for i in items]) if False else st.markdown(
        " ".join(f"<span class='ete-chip'><span class='ete-ponto' style='background:{i['cor']}'></span>{i['nome']}</span>" for i in items), unsafe_allow_html=True)


def footer(text: str) -> None:
    st.markdown(f"<div class='ete-rodape'>{text}</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------- charts
def _base(chart: alt.Chart, height: int = 260) -> alt.Chart:
    return (chart.properties(height=height).configure_view(stroke=None)
            .configure_axis(grid=True, gridColor=GRID, domainColor=GRID, tickColor=GRID, labelColor=MUTED, titleColor=MUTED, labelFontSize=11, titleFontSize=11)
            .configure_legend(orient="bottom", title=None, labelColor=INK, labelFontSize=12))


def _limit_layers(limits: dict, colours: dict, top: float, labels: bool = True):
    """Alert limits as dashed lines with their name, only those near the plotted range (so a low
    river is not squashed flat under a far-away limit). Returns (layers, limits left out)."""
    shown = {k: v for k, v in limits.items() if v <= 3 * top}
    frame = pd.DataFrame({"limite": list(shown), "valor": list(shown.values()), "rotulo": [f"limite {k}: {v:.0f}" for k, v in shown.items()]})
    if frame.empty:
        return [], limits
    scale = alt.Scale(domain=list(colours), range=list(colours.values()))
    rules = alt.Chart(frame).mark_rule(strokeDash=[5, 4], strokeWidth=1.5).encode(y="valor:Q", color=alt.Color("limite:N", scale=scale, legend=None), tooltip=["rotulo:N"])
    text = alt.Chart(frame).mark_text(align="left", dx=4, dy=-6, fontSize=11, color=INK).encode(y="valor:Q", x=alt.value(0), text="rotulo:N")
    return ([rules, text] if labels else [rules]), {k: v for k, v in limits.items() if k not in shown}


def forecast_chart(scenarios: pd.DataFrame, limits: dict, colours: dict):
    """Forecast discharge: the middle scenario as a line, the 10-90 % range as a band, the alert
    limits as dashed lines. Returns (chart, limits not drawn)."""
    frame = pd.DataFrame({"dia": pd.to_datetime(scenarios.index), "mediana": scenarios.median(axis=1).to_numpy(),
                          "baixo": scenarios.quantile(0.1, axis=1).to_numpy(), "alto": scenarios.quantile(0.9, axis=1).to_numpy()})
    x = alt.X("dia:T", title=None, axis=alt.Axis(format="%d/%m", tickCount=min(len(frame), 11)))
    tip = [alt.Tooltip("dia:T", title="Dia", format="%d/%m"), alt.Tooltip("mediana:Q", title="Cenário central (m³/s)", format=".0f"),
           alt.Tooltip("baixo:Q", title="Mínimo provável", format=".0f"), alt.Tooltip("alto:Q", title="Máximo provável", format=".0f")]
    band = alt.Chart(frame).mark_area(opacity=0.18, color=SERIES[0]).encode(x=x, y=alt.Y("baixo:Q", title="Caudal (m³/s)"), y2="alto:Q")
    line = alt.Chart(frame).mark_line(strokeWidth=2, color=SERIES[0]).encode(x=x, y="mediana:Q")
    dots = alt.Chart(frame).mark_point(size=70, filled=True, color=SERIES[0], stroke="white", strokeWidth=2).encode(x=x, y="mediana:Q", tooltip=tip)
    rules, left_out = _limit_layers(limits, colours, float(frame["alto"].max()))
    return _base(alt.layer(band, line, dots, *rules)), left_out


def history_chart(history: pd.DataFrame, limits: dict, colours: dict):
    frame = pd.DataFrame({"dia": pd.to_datetime(history["data"]), "caudal": history["caudal_m3s"]})
    x = alt.X("dia:T", title=None, axis=alt.Axis(format="%m/%Y", tickCount=8))
    line = alt.Chart(frame).mark_line(strokeWidth=1.6, color=SERIES[0]).encode(
        x=x, y=alt.Y("caudal:Q", title="Caudal (m³/s)"), tooltip=[alt.Tooltip("dia:T", title="Dia", format="%d/%m/%Y"), alt.Tooltip("caudal:Q", title="Caudal (m³/s)", format=".0f")])
    rules, _ = _limit_layers(limits, colours, float(frame["caudal"].max()), labels=False)      # the names go in a legend under the chart: they overlap here
    return _base(alt.layer(line, *rules), 240)


def turbidity_heatmap(daily: pd.DataFrame):
    """Chance of water more turbid than usual, per morning and river reach: one hue, darker = more likely."""
    long = daily.rename_axis("dia").reset_index().melt("dia", var_name="troco", value_name="prob")
    long["dia"] = pd.to_datetime(long["dia"]).dt.strftime("%d/%m")
    long["pct"] = (100 * long["prob"]).round(0)
    order = list(dict.fromkeys(long["dia"]))
    base = alt.Chart(long).encode(x=alt.X("dia:O", sort=order, title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("troco:N", title=None))
    cells = base.mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        color=alt.Color("prob:Q", scale=alt.Scale(domain=[0, 1], range=["#cde2fb", "#0d366b"]), legend=None),
        tooltip=[alt.Tooltip("troco:N", title="Troço"), alt.Tooltip("dia:O", title="Dia"), alt.Tooltip("pct:Q", title="Probabilidade (%)")])
    text = base.mark_text(fontSize=11).encode(text=alt.Text("pct:Q", format=".0f"), color=alt.condition("datum.prob > 0.5", alt.value("white"), alt.value(INK)))
    return _base(alt.layer(cells, text), 44 * daily.shape[1] + 40).configure_axis(grid=False, domain=False, ticks=False, labelColor=MUTED, labelFontSize=11)


def quality_chart(series: pd.DataFrame, normals: pd.DataFrame | None, value: str, title: str):
    """Monthly values of one river section. For the colour index, the grey band is the usual
    range for each month of the year and the dashed line its normal value."""
    frame = series[["month", value]].dropna().assign(dia=lambda d: pd.to_datetime(d["month"]))
    x = alt.X("dia:T", title=None, axis=alt.Axis(format="%Y", tickCount=10))
    y = alt.Y(f"{value}:Q", title=title, scale=alt.Scale(zero=False))
    layers = []
    if normals is not None and len(normals):
        usual = series[["month", "mes"]].assign(dia=lambda d: pd.to_datetime(d["month"])).join(normals, on="mes").dropna(subset=["mediana"])
        usual = usual[usual["dia"] >= frame["dia"].min()]
        layers.append(alt.Chart(usual).mark_area(color=NEUTRAL_BAND, opacity=0.55).encode(x=x, y=alt.Y("p25:Q", title=title, scale=alt.Scale(zero=False)), y2="p75:Q"))
        layers.append(alt.Chart(usual).mark_line(color=MUTED, strokeDash=[4, 3], strokeWidth=1.2).encode(x=x, y="mediana:Q"))
    tip = [alt.Tooltip("dia:T", title="Mês", format="%m/%Y"), alt.Tooltip(f"{value}:Q", title=title, format=".3f")]
    layers.append(alt.Chart(frame).mark_line(color=SERIES[0], strokeWidth=1, opacity=0.45).encode(x=x, y=y))
    layers.append(alt.Chart(frame).mark_point(color=SERIES[0], filled=True, size=34 if len(frame) <= 130 else 18).encode(x=x, y=y, tooltip=tip))
    return _base(alt.layer(*layers), 270)


def compare_chart(wide: pd.DataFrame):
    """Up to three river sections on one axis, colours in a fixed order."""
    names = list(wide.columns)[:3]
    long = wide[names].rename_axis("dia").reset_index().melt("dia", var_name="troco", value_name="ndti").dropna()
    chart = alt.Chart(long).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=22, filled=True)).encode(
        x=alt.X("dia:T", title=None, axis=alt.Axis(format="%Y", tickCount=9)), y=alt.Y("ndti:Q", title="Índice de cor (mais alto = mais turva)", scale=alt.Scale(zero=False)),
        color=alt.Color("troco:N", scale=alt.Scale(domain=names, range=SERIES[:len(names)]), sort=names),
        tooltip=[alt.Tooltip("troco:N", title="Troço"), alt.Tooltip("dia:T", title="Mês", format="%m/%Y"), alt.Tooltip("ndti:Q", title="Índice de cor", format=".3f")])
    return _base(chart, 280)


def climatology_chart(normals: pd.DataFrame):
    """The usual value of each month of the year in one section: band = usual range, line = normal."""
    frame = normals.reset_index().assign(nome=lambda d: [MESES[int(m) - 1] for m in d["mes"]])
    x = alt.X("nome:O", sort=MESES, title=None, axis=alt.Axis(labelAngle=0))
    band = alt.Chart(frame).mark_area(color=NEUTRAL_BAND, opacity=0.6).encode(x=x, y=alt.Y("p25:Q", title="Índice de cor", scale=alt.Scale(zero=False)), y2="p75:Q")
    line = alt.Chart(frame).mark_line(color=SERIES[0], strokeWidth=2, point=alt.OverlayMarkDef(size=45, filled=True)).encode(
        x=x, y="mediana:Q", tooltip=[alt.Tooltip("nome:O", title="Mês"), alt.Tooltip("mediana:Q", title="Normal", format=".3f"),
                                     alt.Tooltip("p25:Q", title="Habitual: de", format=".3f"), alt.Tooltip("p75:Q", title="Habitual: até", format=".3f")])
    return _base(alt.layer(band, line), 220)
