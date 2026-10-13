"""Gráficos da plataforma ETE (Altair).

Regras seguidas em todos:
  * as cores de alerta só são usadas para alertas, e a palavra aparece sempre (legenda ou rótulo);
  * as séries usam uma ordem fixa de cores (azul, laranja, verde-água), no máximo três de cada vez;
  * um só eixo por gráfico; tocar ou passar o rato num ponto mostra o valor;
  * datas em números (dia/mês), para não aparecerem meses em inglês.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]        # fixed order; never more than three series at once
INK, MUTED, GRID, BAND = "#14212E", "#5A6B7D", "#E6EBF1", "#D6DEE8"
LEVELS = ["verde", "amarelo", "laranja", "vermelho"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _base(chart, height: int = 270):
    return (chart.properties(height=height, background="white").configure_view(stroke=None)
            .configure_axis(grid=True, gridColor=GRID, domainColor=GRID, tickColor=GRID, labelColor=MUTED, titleColor=MUTED, labelFontSize=11, titleFontSize=11, titlePadding=8)
            .configure_legend(orient="bottom", title=None, labelColor=INK, labelFontSize=12, symbolType="circle"))


def _limits(limits: dict, colours: dict, top: float, labels: bool = True):
    """Alert limits as dashed lines; only those near the plotted range, so a low river is not
    squashed flat under a far-away limit. Returns (layers, limits left out)."""
    shown = {k: v for k, v in limits.items() if v <= 3 * top}
    if not shown:
        return [], limits
    frame = pd.DataFrame({"limite": list(shown), "valor": list(shown.values()), "rotulo": [f"limite {k}: {v:.0f}" for k, v in shown.items()]})
    scale = alt.Scale(domain=list(colours), range=list(colours.values()))
    rules = alt.Chart(frame).mark_rule(strokeDash=[5, 4], strokeWidth=1.6).encode(y="valor:Q", color=alt.Color("limite:N", scale=scale, legend=None), tooltip=["rotulo:N"])
    text = alt.Chart(frame).mark_text(align="left", dx=4, dy=-6, fontSize=11, color=INK).encode(y="valor:Q", x=alt.value(0), text="rotulo:N")
    return ([rules, text] if labels else [rules]), {k: v for k, v in limits.items() if k not in shown}


def forecast(scenarios: pd.DataFrame, limits: dict, colours: dict, chosen_day=None, height: int = 280):
    """Forecast discharge: middle scenario (line), 10-90 % range (band), alert limits (dashed),
    and the chosen day marked. Returns (chart, limits not drawn)."""
    frame = pd.DataFrame({"dia": pd.to_datetime(scenarios.index), "mediana": scenarios.median(axis=1).to_numpy(),
                          "baixo": scenarios.quantile(0.1, axis=1).to_numpy(), "alto": scenarios.quantile(0.9, axis=1).to_numpy()})
    x = alt.X("dia:T", title=None, axis=alt.Axis(format="%d/%m", tickCount=min(len(frame), 11)))
    tip = [alt.Tooltip("dia:T", title="Dia", format="%d/%m"), alt.Tooltip("mediana:Q", title="Cenário central (m³/s)", format=".0f"),
           alt.Tooltip("baixo:Q", title="Mínimo provável", format=".0f"), alt.Tooltip("alto:Q", title="Máximo provável", format=".0f")]
    layers = [alt.Chart(frame).mark_area(opacity=0.2, color=SERIES[0]).encode(x=x, y=alt.Y("baixo:Q", title="Caudal (m³/s)"), y2="alto:Q"),
              alt.Chart(frame).mark_line(strokeWidth=2.2, color=SERIES[0]).encode(x=x, y="mediana:Q"),
              alt.Chart(frame).mark_point(size=75, filled=True, color=SERIES[0], stroke="white", strokeWidth=2).encode(x=x, y="mediana:Q", tooltip=tip)]
    if chosen_day is not None:
        mark = frame[frame["dia"] == pd.Timestamp(chosen_day)]
        layers.append(alt.Chart(mark).mark_rule(color=INK, strokeWidth=1, opacity=0.5).encode(x="dia:T"))
        layers.append(alt.Chart(mark).mark_point(size=170, filled=False, color=INK, strokeWidth=2).encode(x="dia:T", y="mediana:Q"))
    rules, left_out = _limits(limits, colours, float(frame["alto"].max()))
    return _base(alt.layer(*layers, *rules), height), left_out


def rain(daily: pd.DataFrame, today):
    """Basin rain day by day: what fell (blue) and what is forecast (lighter)."""
    frame = pd.DataFrame({"dia": pd.to_datetime(daily.index), "chuva": daily.iloc[:, 0].to_numpy()}).dropna()
    frame["tipo"] = ["prevista" if d >= pd.Timestamp(today) else "já caída" for d in frame["dia"]]
    chart = alt.Chart(frame).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("dia:T", title=None, axis=alt.Axis(format="%d/%m", tickCount=12)), y=alt.Y("chuva:Q", title="Chuva média na bacia (mm por dia)"),
        color=alt.Color("tipo:N", scale=alt.Scale(domain=["já caída", "prevista"], range=[SERIES[0], "#9ec5f4"])),
        tooltip=[alt.Tooltip("dia:T", title="Dia", format="%d/%m/%Y"), alt.Tooltip("chuva:Q", title="Chuva (mm)", format=".1f"), alt.Tooltip("tipo:N", title="")])
    return _base(chart, 250)


def history(frame: pd.DataFrame, limits: dict, colours: dict, height: int = 250, month_axis: bool = True):
    data = pd.DataFrame({"dia": pd.to_datetime(frame["data"]), "caudal": frame["caudal_m3s"]}).dropna()
    line = alt.Chart(data).mark_line(strokeWidth=1.7, color=SERIES[0]).encode(
        x=alt.X("dia:T", title=None, axis=alt.Axis(format="%m/%Y" if month_axis else "%d/%m", tickCount=8)), y=alt.Y("caudal:Q", title="Caudal (m³/s)"),
        tooltip=[alt.Tooltip("dia:T", title="Dia", format="%d/%m/%Y"), alt.Tooltip("caudal:Q", title="Caudal (m³/s)", format=".0f")])
    rules, _ = _limits(limits, colours, float(data["caudal"].max()), labels=False)
    return _base(alt.layer(line, *rules), height)


def year_detail(frame: pd.DataFrame, limits: dict, colours: dict):
    """One hydrological year, day by day: the river (line) and the alert of each day (coloured band under it)."""
    data = pd.DataFrame({"dia": pd.to_datetime(frame["data"]), "caudal": frame["caudal_m3s"], "alerta": frame["alerta"]}).dropna(subset=["caudal"])
    scale = alt.Scale(domain=LEVELS, range=[colours[k] for k in LEVELS])
    x = alt.X("dia:T", title=None, axis=alt.Axis(format="%d/%m", tickCount=12))
    line = alt.Chart(data).mark_line(strokeWidth=1.8, color=SERIES[0]).encode(x=x, y=alt.Y("caudal:Q", title="Caudal (m³/s)"),
                                                                              tooltip=[alt.Tooltip("dia:T", title="Dia", format="%d/%m/%Y"), alt.Tooltip("caudal:Q", title="Caudal (m³/s)", format=".0f"),
                                                                                       alt.Tooltip("alerta:N", title="Alerta")])
    strip = alt.Chart(data).mark_tick(thickness=3, size=14).encode(x=x, y=alt.value(262), color=alt.Color("alerta:N", scale=scale, legend=alt.Legend(title=None, orient="bottom")),
                                                                    tooltip=[alt.Tooltip("dia:T", title="Dia", format="%d/%m/%Y"), alt.Tooltip("alerta:N", title="Alerta")])
    rules, _ = _limits(limits, colours, float(data["caudal"].max()), labels=False)
    return _base(alt.layer(line, *rules, strip), 290)


def alert_days(yearly: pd.DataFrame, colours: dict):
    """Days at each alert level per hydrological year (stacked; the level names are in the legend)."""
    long = yearly.reset_index().melt("ano", var_name="alerta", value_name="dias")
    order = ["amarelo", "laranja", "vermelho"]
    chart = alt.Chart(long).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, stroke="white", strokeWidth=1).encode(
        x=alt.X("ano:O", title="Ano hidrológico (de outubro a setembro)", axis=alt.Axis(labelAngle=0)), y=alt.Y("dias:Q", title="Dias"),
        color=alt.Color("alerta:N", scale=alt.Scale(domain=order, range=[colours[k] for k in order]), sort=order),
        order=alt.Order("nivel:Q"), tooltip=[alt.Tooltip("ano:O", title="Ano"), alt.Tooltip("alerta:N", title="Alerta"), alt.Tooltip("dias:Q", title="Dias")]
    ).transform_calculate(nivel="indexof(['amarelo','laranja','vermelho'], datum.alerta)")
    return _base(chart, 270)


def level_calendar(monthly: pd.DataFrame, colours: dict):
    """Highest alert of each month, year by year: one small square per month."""
    scale = alt.Scale(domain=LEVELS, range=[colours[k] for k in LEVELS])
    chart = alt.Chart(monthly).mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        x=alt.X("mes_nome:O", sort=MESES, title=None, axis=alt.Axis(labelAngle=0, orient="top")), y=alt.Y("ano:O", title=None),
        color=alt.Color("alerta:N", scale=scale, legend=alt.Legend(title=None, orient="bottom")),
        tooltip=[alt.Tooltip("ano:O", title="Ano"), alt.Tooltip("mes_nome:O", title="Mês"), alt.Tooltip("alerta:N", title="Alerta mais alto"), alt.Tooltip("caudal:Q", title="Caudal máximo (m³/s)", format=".0f")])
    return _base(chart, 22 * monthly["ano"].nunique() + 50).configure_axis(grid=False, domain=False, ticks=False, labelColor=MUTED, labelFontSize=11)


def flood_area(frame: pd.DataFrame):
    data = pd.DataFrame({"mes": pd.to_datetime(frame["month"]), "area": frame["cheia_distrito_km2"]}).dropna()
    chart = alt.Chart(data).mark_bar(color=SERIES[0]).encode(x=alt.X("mes:T", title=None, axis=alt.Axis(format="%Y", tickCount=11)), y=alt.Y("area:Q", title="Água fora do habitual no distrito (km²)"),
                                                             tooltip=[alt.Tooltip("mes:T", title="Mês", format="%m/%Y"), alt.Tooltip("area:Q", title="Área (km²)", format=".0f")])
    return _base(chart, 230)


def turbidity_heatmap(daily: pd.DataFrame):
    """Chance of water more turbid than usual, per morning and reach: one hue, darker = more likely."""
    long = daily.rename_axis("dia").reset_index().melt("dia", var_name="troco", value_name="prob")
    long["dia"] = pd.to_datetime(long["dia"]).dt.strftime("%d/%m")
    long["pct"] = (100 * long["prob"]).round(0)
    order = list(dict.fromkeys(long["dia"]))
    base = alt.Chart(long).encode(x=alt.X("dia:O", sort=order, title=None, axis=alt.Axis(labelAngle=0, orient="top")), y=alt.Y("troco:N", title=None))
    cells = base.mark_rect(stroke="white", strokeWidth=2, cornerRadius=4).encode(
        color=alt.Color("prob:Q", scale=alt.Scale(domain=[0, 1], range=["#cde2fb", "#0d366b"]), legend=None),
        tooltip=[alt.Tooltip("troco:N", title="Troço"), alt.Tooltip("dia:O", title="Dia"), alt.Tooltip("pct:Q", title="Probabilidade (%)")])
    text = base.mark_text(fontSize=11, fontWeight="bold").encode(text=alt.Text("pct:Q", format=".0f"), color=alt.condition("datum.prob > 0.5", alt.value("white"), alt.value(INK)))
    return _base(alt.layer(cells, text), 46 * daily.shape[1] + 44).configure_axis(grid=False, domain=False, ticks=False, labelColor=MUTED, labelFontSize=11)


def quality(series: pd.DataFrame, normals: pd.DataFrame | None, value: str, title: str):
    """Monthly values of one section. For the colour index, the grey band is the usual range for
    each month of the year and the dashed line its normal value."""
    frame = series[["month", value]].dropna().assign(dia=lambda d: pd.to_datetime(d["month"]))
    x = alt.X("dia:T", title=None, axis=alt.Axis(format="%Y", tickCount=10))
    y = alt.Y(f"{value}:Q", title=title, scale=alt.Scale(zero=False))
    layers = []
    if normals is not None and len(normals):
        usual = series[["month", "mes"]].assign(dia=lambda d: pd.to_datetime(d["month"])).join(normals, on="mes").dropna(subset=["mediana"])
        usual = usual[usual["dia"] >= frame["dia"].min()]
        layers.append(alt.Chart(usual).mark_area(color=BAND, opacity=0.6).encode(x=x, y=alt.Y("p25:Q", title=title, scale=alt.Scale(zero=False)), y2="p75:Q"))
        layers.append(alt.Chart(usual).mark_line(color=MUTED, strokeDash=[4, 3], strokeWidth=1.2).encode(x=x, y="mediana:Q"))
    tip = [alt.Tooltip("dia:T", title="Mês", format="%m/%Y"), alt.Tooltip(f"{value}:Q", title=title, format=".3f")]
    layers.append(alt.Chart(frame).mark_line(color=SERIES[0], strokeWidth=1, opacity=0.45).encode(x=x, y=y))
    layers.append(alt.Chart(frame).mark_point(color=SERIES[0], filled=True, size=36 if len(frame) <= 130 else 18).encode(x=x, y=y, tooltip=tip))
    return _base(alt.layer(*layers), 280)


def compare(wide: pd.DataFrame):
    """Up to three sections on one axis, colours in a fixed order."""
    names = list(wide.columns)[:3]
    long = wide[names].rename_axis("dia").reset_index().melt("dia", var_name="troco", value_name="ndti").dropna()
    chart = alt.Chart(long).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=22, filled=True)).encode(
        x=alt.X("dia:T", title=None, axis=alt.Axis(format="%Y", tickCount=9)), y=alt.Y("ndti:Q", title="Índice de cor (mais alto = mais turva)", scale=alt.Scale(zero=False)),
        color=alt.Color("troco:N", scale=alt.Scale(domain=names, range=SERIES[:len(names)]), sort=names),
        tooltip=[alt.Tooltip("troco:N", title="Troço"), alt.Tooltip("dia:T", title="Mês", format="%m/%Y"), alt.Tooltip("ndti:Q", title="Índice de cor", format=".3f")])
    return _base(chart, 290)


def climatology(normals: pd.DataFrame):
    frame = normals.reset_index().assign(nome=lambda d: [MESES[int(m) - 1] for m in d["mes"]])
    x = alt.X("nome:O", sort=MESES, title=None, axis=alt.Axis(labelAngle=0))
    band = alt.Chart(frame).mark_area(color=BAND, opacity=0.65).encode(x=x, y=alt.Y("p25:Q", title="Índice de cor", scale=alt.Scale(zero=False)), y2="p75:Q")
    line = alt.Chart(frame).mark_line(color=SERIES[0], strokeWidth=2, point=alt.OverlayMarkDef(size=45, filled=True)).encode(
        x=x, y="mediana:Q", tooltip=[alt.Tooltip("nome:O", title="Mês"), alt.Tooltip("mediana:Q", title="Normal", format=".3f"),
                                     alt.Tooltip("p25:Q", title="Habitual: de", format=".3f"), alt.Tooltip("p75:Q", title="Habitual: até", format=".3f")])
    return _base(alt.layer(band, line), 220)


def buildings_by_place(places: pd.DataFrame, colours: dict):
    """Buildings around each named place that lie inside the flooded zone (largest first)."""
    data = places[places["edificios_alagados"] > 0].nlargest(12, "edificios_alagados")
    colours = {k: v for k, v in colours.items() if k in set(data["categoria"])}          # legend only for what is drawn
    chart = alt.Chart(data).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        y=alt.Y("lugar:N", sort="-x", title=None), x=alt.X("edificios_alagados:Q", title="Edifícios dentro da zona de aviso (raio de 500 m)"),
        color=alt.Color("categoria:N", scale=alt.Scale(domain=list(colours), range=list(colours.values()))),
        tooltip=[alt.Tooltip("lugar:N", title="Lugar"), alt.Tooltip("categoria:N", title="Situação"), alt.Tooltip("edificios_alagados:Q", title="Edifícios na zona")])
    return _base(chart, 26 * len(data) + 60)
