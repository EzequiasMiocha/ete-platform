"""Gráficos da plataforma ETE (Altair), na língua de quem lê.

Regras seguidas em todos:
  * as cores de alerta só são usadas para alertas, e a palavra aparece sempre (legenda ou rótulo);
  * as séries usam uma ordem fixa de cores (verde-água, violeta, rosa), no máximo três de cada vez,
    escolhidas para não se confundirem com as cores de alerta nem com as classes da água;
  * um só eixo por gráfico; tocar ou passar o rato num ponto mostra o valor;
  * datas em números (dia/mês) e meses escritos por nós, para não aparecerem na língua do navegador;
  * todo o texto passa por t(): títulos, legendas, dicas e os valores das categorias.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

import idioma as L
from idioma import t

# Fixed order; never more than three series at once. Marine blue first (the water; close to the Copernicus marine service),
# then pink and violet: checked with the data-viz validator (light mode, all pairs, colour-blind safe; the pink needs the legend).
SERIES = ["#1F5F8F", "#E07A9F", "#8C6BB1"]
INK, MUTED, GRID, BAND = "#212529", "#6C6E74", "#ECECF2", "#E4E3EC"
SURFACE, QUIET, SOFT_SERIES = "#FFFFFF", "#C9CBD6", "#A9C4DC"
FONT = "'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif"
_AXIS = dict(grid=True, gridColor=GRID, domainColor=GRID, tickColor=GRID, labelColor=MUTED, titleColor=MUTED, labelFontSize=11, titleFontSize=11, titlePadding=10,
             titleFontWeight=600, labelPadding=6, tickSize=4)
_LEGEND = dict(orient="bottom", title=None, labelColor=INK, labelFontSize=12, symbolType="circle", symbolSize=90, padding=6)
LEVELS = ["verde", "amarelo", "laranja", "vermelho"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _base(chart, height: int = 270):
    return (chart.properties(height=height, background=SURFACE, padding={"left": 4, "right": 18, "top": 8, "bottom": 4}).configure(font=FONT).configure_view(stroke=None)
            .configure_axis(**_AXIS).configure_legend(**_LEGEND))


def _levels(colours: dict, keys=LEVELS) -> alt.Scale:
    """Colour scale for alert levels, with the level names in the reader's language."""
    return alt.Scale(domain=[t(k) for k in keys], range=[colours[k] for k in keys])


def _dec() -> str:
    """The reader's decimal mark, for number labels drawn by Vega."""
    return "." if L.lingua() == "en" else ","


def _limits(limits: dict, colours: dict, top: float, labels: bool = True):
    """Alert limits as dashed lines; only those near the plotted range, so a low river is not
    squashed flat under a far-away limit. Returns (layers, limits left out)."""
    shown = {k: v for k, v in limits.items() if v <= 3 * top}
    if not shown:
        return [], limits
    frame = pd.DataFrame({"limite": [t(k) for k in shown], "valor": list(shown.values()),
                          "rotulo": [t("limite {nivel}: {valor}", nivel=t(k), valor=L.numero(v)) for k, v in shown.items()]})
    rules = alt.Chart(frame).mark_rule(strokeDash=[5, 4], strokeWidth=1.6).encode(y="valor:Q", color=alt.Color("limite:N", scale=_levels(colours, list(colours)), legend=None),
                                                                                 tooltip=[alt.Tooltip("rotulo:N", title=" ")])
    text = alt.Chart(frame).mark_text(align="left", dx=4, dy=-6, fontSize=11, color=INK).encode(y="valor:Q", x=alt.value(0), text="rotulo:N")
    return ([rules, text] if labels else [rules]), {k: v for k, v in limits.items() if k not in shown}


def forecast(scenarios: pd.DataFrame, limits: dict, colours: dict, chosen_day=None, height: int = 280):
    """Forecast discharge: middle scenario (line), 10-90 % range (band), alert limits (dashed),
    and the chosen day marked. Returns (chart, limits not drawn)."""
    frame = pd.DataFrame({"dia": pd.to_datetime(scenarios.index), "mediana": scenarios.median(axis=1).to_numpy(),
                          "baixo": scenarios.quantile(0.1, axis=1).to_numpy(), "alto": scenarios.quantile(0.9, axis=1).to_numpy()})
    x = alt.X("dia:T", title=None, axis=alt.Axis(format="%d/%m", tickCount=min(len(frame), 11)))
    tip = [alt.Tooltip("dia:T", title=t("Dia"), format="%d/%m"), alt.Tooltip("mediana:Q", title=t("Cenário central (m³/s)"), format=".0f"),
           alt.Tooltip("baixo:Q", title=t("Mínimo provável"), format=".0f"), alt.Tooltip("alto:Q", title=t("Máximo provável"), format=".0f")]
    layers = [alt.Chart(frame).mark_area(opacity=0.14, color=SERIES[0]).encode(x=x, y=alt.Y("baixo:Q", title=t("Caudal (m³/s)")), y2="alto:Q"),
              alt.Chart(frame).mark_line(strokeWidth=2.4, color=SERIES[0], interpolate="monotone").encode(x=x, y="mediana:Q"),
              alt.Chart(frame).mark_point(size=75, filled=True, color=SERIES[0], stroke="white", strokeWidth=2).encode(x=x, y="mediana:Q", tooltip=tip)]
    if chosen_day is not None:
        mark = frame[frame["dia"] == pd.Timestamp(chosen_day)]
        layers.append(alt.Chart(mark).mark_rule(color=INK, strokeWidth=1, opacity=0.5).encode(x="dia:T"))
        layers.append(alt.Chart(mark).mark_point(size=170, filled=False, color=INK, strokeWidth=2).encode(x="dia:T", y="mediana:Q"))
    rules, left_out = _limits(limits, colours, float(frame["alto"].max()))
    return _base(alt.layer(*layers, *rules), height), left_out


def rain(daily: pd.DataFrame, today):
    """Basin rain day by day: what fell (dark) and what is forecast (lighter)."""
    fell, coming = t("já caída"), t("prevista")
    frame = pd.DataFrame({"dia": pd.to_datetime(daily.index), "chuva": daily.iloc[:, 0].to_numpy()}).dropna()
    frame["tipo"] = [coming if d >= pd.Timestamp(today) else fell for d in frame["dia"]]
    chart = alt.Chart(frame).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("dia:T", title=None, axis=alt.Axis(format="%d/%m", tickCount=12)), y=alt.Y("chuva:Q", title=t("Chuva média na bacia (mm por dia)")),
        color=alt.Color("tipo:N", scale=alt.Scale(domain=[fell, coming], range=[SERIES[0], SOFT_SERIES])),
        tooltip=[alt.Tooltip("dia:T", title=t("Dia"), format="%d/%m/%Y"), alt.Tooltip("chuva:Q", title=t("Chuva (mm)"), format=".1f"), alt.Tooltip("tipo:N", title=" ")])
    return _base(chart, 250)


def history(frame: pd.DataFrame, limits: dict, colours: dict, height: int = 250, month_axis: bool = True):
    data = pd.DataFrame({"dia": pd.to_datetime(frame["data"]), "caudal": frame["caudal_m3s"]}).dropna()
    line = alt.Chart(data).mark_line(strokeWidth=1.7, color=SERIES[0]).encode(
        x=alt.X("dia:T", title=None, axis=alt.Axis(format="%m/%Y" if month_axis else "%d/%m", tickCount=8)), y=alt.Y("caudal:Q", title=t("Caudal (m³/s)")),
        tooltip=[alt.Tooltip("dia:T", title=t("Dia"), format="%d/%m/%Y"), alt.Tooltip("caudal:Q", title=t("Caudal (m³/s)"), format=".0f")])
    rules, _ = _limits(limits, colours, float(data["caudal"].max()), labels=False)
    return _base(alt.layer(line, *rules), height)


def year_detail(frame: pd.DataFrame, limits: dict, colours: dict):
    """One hydrological year, day by day: the river (line) and the alert of each day (coloured band under it)."""
    data = pd.DataFrame({"dia": pd.to_datetime(frame["data"]), "caudal": frame["caudal_m3s"],
                         "alerta": frame["alerta"].map(lambda v: t(v) if isinstance(v, str) else v)}).dropna(subset=["caudal"])
    x = alt.X("dia:T", title=None, axis=alt.Axis(format="%d/%m", tickCount=12))
    line = alt.Chart(data).mark_line(strokeWidth=1.8, color=SERIES[0]).encode(
        x=x, y=alt.Y("caudal:Q", title=t("Caudal (m³/s)")),
        tooltip=[alt.Tooltip("dia:T", title=t("Dia"), format="%d/%m/%Y"), alt.Tooltip("caudal:Q", title=t("Caudal (m³/s)"), format=".0f"), alt.Tooltip("alerta:N", title=t("Alerta"))])
    strip = alt.Chart(data).mark_tick(thickness=3, size=14).encode(
        x=x, y=alt.value(262), color=alt.Color("alerta:N", scale=_levels(colours), legend=alt.Legend(title=None, orient="bottom")),
        tooltip=[alt.Tooltip("dia:T", title=t("Dia"), format="%d/%m/%Y"), alt.Tooltip("alerta:N", title=t("Alerta"))])
    rules, _ = _limits(limits, colours, float(data["caudal"].max()), labels=False)
    return _base(alt.layer(line, *rules, strip), 290)


def alert_days(yearly: pd.DataFrame, colours: dict):
    """Days at each alert level per hydrological year (stacked; the level names are in the legend)."""
    order = ["amarelo", "laranja", "vermelho"]
    long = yearly.reset_index().melt("ano", var_name="alerta", value_name="dias")
    long["nivel"] = long["alerta"].map(order.index)
    long["alerta"] = long["alerta"].map(t)
    chart = alt.Chart(long).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, stroke="white", strokeWidth=1).encode(
        x=alt.X("ano:O", title=t("Ano hidrológico (de outubro a setembro)"), axis=alt.Axis(labelAngle=0, labelOverlap="parity")), y=alt.Y("dias:Q", title=t("Dias")),   # on a phone every other year
        color=alt.Color("alerta:N", scale=_levels(colours, order), sort=[t(k) for k in order]),
        order=alt.Order("nivel:Q"), tooltip=[alt.Tooltip("ano:O", title=t("Ano")), alt.Tooltip("alerta:N", title=t("Alerta")), alt.Tooltip("dias:Q", title=t("Dias"))])
    return _base(chart, 270)


def level_calendar(monthly: pd.DataFrame, colours: dict):
    """Highest alert of each month, year by year: one small square per month."""
    data = monthly.assign(alerta=monthly["alerta"].map(t), mes_nome=monthly["mes"].map(lambda m: L.meses()[int(m) - 1]))
    chart = alt.Chart(data).mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        x=alt.X("mes_nome:O", sort=L.meses(), title=None, axis=alt.Axis(labelAngle=0, orient="top")), y=alt.Y("ano:O", title=None),
        color=alt.Color("alerta:N", scale=_levels(colours), legend=alt.Legend(title=None, orient="bottom")),
        tooltip=[alt.Tooltip("ano:O", title=t("Ano")), alt.Tooltip("mes_nome:O", title=t("Mês")), alt.Tooltip("alerta:N", title=t("Alerta mais alto")),
                 alt.Tooltip("caudal:Q", title=t("Caudal máximo (m³/s)"), format=".0f")])
    return _base(chart, 22 * monthly["ano"].nunique() + 50).configure_axis(grid=False, domain=False, ticks=False, labelColor=MUTED, labelFontSize=11)


def flood_area(frame: pd.DataFrame):
    data = pd.DataFrame({"mes": pd.to_datetime(frame["month"]), "area": frame["cheia_distrito_km2"]}).dropna()
    chart = alt.Chart(data).mark_bar(color=SERIES[0], cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        x=alt.X("mes:T", title=None, axis=alt.Axis(format="%Y", tickCount=11)), y=alt.Y("area:Q", title=t("Água fora do habitual no distrito (km²)")),
        tooltip=[alt.Tooltip("mes:T", title=t("Mês"), format="%m/%Y"), alt.Tooltip("area:Q", title=t("Área (km²)"), format=".0f")])
    return _base(chart, 230)


def turbidity_heatmap(daily: pd.DataFrame):
    """Chance of water more turbid than usual, per morning and reach: one hue, darker = more likely."""
    long = daily.rename_axis("dia").reset_index().melt("dia", var_name="troco", value_name="prob")
    long["troco"] = long["troco"].map(L.troco)
    long["dia"] = pd.to_datetime(long["dia"]).dt.strftime("%d/%m")
    long["pct"] = (100 * long["prob"]).round(0)
    order = list(dict.fromkeys(long["dia"]))
    base = alt.Chart(long).encode(x=alt.X("dia:O", sort=order, title=None, axis=alt.Axis(labelAngle=0, orient="top")), y=alt.Y("troco:N", title=None))
    cells = base.mark_rect(stroke="white", strokeWidth=2, cornerRadius=4).encode(
        color=alt.Color("prob:Q", scale=alt.Scale(domain=[0, 1], range=["#EEEDF6", "#4E4A8C"]), legend=None),
        tooltip=[alt.Tooltip("troco:N", title=t("Troço")), alt.Tooltip("dia:O", title=t("Dia")), alt.Tooltip("pct:Q", title=t("Probabilidade (%)"))])
    text = base.mark_text(fontSize=11, fontWeight="bold").encode(text=alt.Text("pct:Q", format=".0f"), color=alt.condition("datum.prob > 0.5", alt.value("white"), alt.value(INK)))
    return _base(alt.layer(cells, text), 46 * daily.shape[1] + 44).configure_axis(grid=False, domain=False, ticks=False, labelColor=MUTED, labelFontSize=11)


def quality(series: pd.DataFrame, normals: pd.DataFrame | None, value: str, title: str):
    """Monthly values of one section. For the colour index, the grey band is the usual range for
    each month of the year and the dashed line its normal value."""
    title = t(title)
    frame = series[["month", value]].dropna().assign(dia=lambda d: pd.to_datetime(d["month"]))
    x = alt.X("dia:T", title=None, axis=alt.Axis(format="%Y", tickCount=10))
    y = alt.Y(f"{value}:Q", title=title, scale=alt.Scale(zero=False))
    layers = []
    if normals is not None and len(normals):
        usual = series[["month", "mes"]].assign(dia=lambda d: pd.to_datetime(d["month"])).join(normals, on="mes").dropna(subset=["mediana"])
        usual = usual[usual["dia"] >= frame["dia"].min()]
        layers.append(alt.Chart(usual).mark_area(color=BAND, opacity=0.6).encode(x=x, y=alt.Y("p25:Q", title=title, scale=alt.Scale(zero=False)), y2="p75:Q"))
        layers.append(alt.Chart(usual).mark_line(color=MUTED, strokeDash=[4, 3], strokeWidth=1.2).encode(x=x, y="mediana:Q"))
    tip = [alt.Tooltip("dia:T", title=t("Mês"), format="%m/%Y"), alt.Tooltip(f"{value}:Q", title=title, format=".3f")]
    layers.append(alt.Chart(frame).mark_line(color=SERIES[0], strokeWidth=1, opacity=0.45).encode(x=x, y=y))
    layers.append(alt.Chart(frame).mark_point(color=SERIES[0], filled=True, size=36 if len(frame) <= 130 else 18).encode(x=x, y=y, tooltip=tip))
    return _base(alt.layer(*layers), 280)


def compare(wide: pd.DataFrame):
    """Up to three sections on one axis, colours in a fixed order."""
    wide = wide.rename(columns=L.troco)
    names = list(wide.columns)[:3]
    long = wide[names].rename_axis("dia").reset_index().melt("dia", var_name="troco", value_name="ndti").dropna()
    chart = alt.Chart(long).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=22, filled=True)).encode(
        x=alt.X("dia:T", title=None, axis=alt.Axis(format="%Y", tickCount=9)), y=alt.Y("ndti:Q", title=t("Índice de cor (mais alto = mais turva)"), scale=alt.Scale(zero=False)),
        color=alt.Color("troco:N", scale=alt.Scale(domain=names, range=SERIES[:len(names)]), sort=names),
        tooltip=[alt.Tooltip("troco:N", title=t("Troço")), alt.Tooltip("dia:T", title=t("Mês"), format="%m/%Y"), alt.Tooltip("ndti:Q", title=t("Índice de cor"), format=".3f")])
    return _base(chart, 290)


def climatology(normals: pd.DataFrame):
    frame = normals.reset_index().assign(nome=lambda d: [L.meses()[int(m) - 1] for m in d["mes"]])
    x = alt.X("nome:O", sort=L.meses(), title=None, axis=alt.Axis(labelAngle=0))
    band = alt.Chart(frame).mark_area(color=BAND, opacity=0.65).encode(x=x, y=alt.Y("p25:Q", title=t("Índice de cor"), scale=alt.Scale(zero=False)), y2="p75:Q")
    line = alt.Chart(frame).mark_line(color=SERIES[0], strokeWidth=2, point=alt.OverlayMarkDef(size=45, filled=True)).encode(
        x=x, y="mediana:Q", tooltip=[alt.Tooltip("nome:O", title=t("Mês")), alt.Tooltip("mediana:Q", title=t("Normal"), format=".3f"),
                                     alt.Tooltip("p25:Q", title=t("Habitual: de"), format=".3f"), alt.Tooltip("p75:Q", title=t("Habitual: até"), format=".3f")])
    return _base(alt.layer(band, line), 220)


def buildings_by_place(places: pd.DataFrame, colours: dict):
    """Buildings around each named place that lie inside the flooded zone (largest first)."""
    data = places[places["edificios_alagados"] > 0].nlargest(12, "edificios_alagados").copy()
    colours = {k: v for k, v in colours.items() if k in set(data["categoria"])}          # legend only for what is drawn
    data["categoria"] = data["categoria"].map(t)
    chart = alt.Chart(data).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        y=alt.Y("lugar:N", sort="-x", title=None), x=alt.X("edificios_alagados:Q", title=t("Edifícios dentro da zona de aviso (raio de 500 m)")),
        color=alt.Color("categoria:N", scale=alt.Scale(domain=[t(k) for k in colours], range=list(colours.values())), legend=alt.Legend(columns=1)),   # one per line: fits a phone
        tooltip=[alt.Tooltip("lugar:N", title=t("Lugar")), alt.Tooltip("categoria:N", title=t("Situação")), alt.Tooltip("edificios_alagados:Q", title=t("Edifícios na zona"))])
    return _base(chart, 26 * len(data) + 60 + 18 * max(len(colours) - 1, 0))


# ----------------------------------------------------------------------------- machine learning and monitoring
def ranked_bars(frame: pd.DataFrame, label: str, value: str, title: str, chosen: str | None = None, domain=(0, 1), reference: float | None = None):
    """Horizontal bars in the order given. The chosen row is in the main colour, the others in a
    quiet one; an optional dashed line marks a reference value (for example chance)."""
    title = t(title)
    data = frame[[label, value]].dropna().copy()
    chosen_word, compared_word = t("escolhido"), t("comparado")
    data["tipo"] = [chosen_word if chosen is not None and chosen in str(name) else compared_word for name in data[label]]
    data[label] = [L.troco(v) if isinstance(v, str) else v for v in data[label]]
    data["rotulo"] = [L.numero(v, 2) for v in data[value]]
    y = alt.Y(f"{label}:N", sort=list(data[label]), title=None, axis=alt.Axis(labelLimit=260))
    x = alt.X(f"{value}:Q", title=title, scale=alt.Scale(domain=list(domain), nice=False),
              axis=alt.Axis(labelExpr=f"replace(format(datum.value, '.1f'), '.', '{_dec()}')", tickMinStep=0.1))
    bars = alt.Chart(data).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, clip=True).encode(
        y=y, x=x, x2=alt.datum(domain[0]),
        color=alt.Color("tipo:N", scale=alt.Scale(domain=[chosen_word, compared_word], range=[SERIES[0], QUIET]), legend=alt.Legend(title=None, orient="bottom") if chosen else None),
        tooltip=[alt.Tooltip(f"{label}:N", title=" "), alt.Tooltip("rotulo:N", title=title)])
    text = alt.Chart(data).mark_text(align="left", dx=5, fontSize=11, color=INK).encode(y=y, x=x, text="rotulo:N")
    layers = [bars, text]
    if reference is not None:
        layers.append(alt.Chart(pd.DataFrame({"v": [reference]})).mark_rule(strokeDash=[4, 3], color=MUTED).encode(x="v:Q"))
    # a fixed step per row keeps the bars the same size however many rows there are
    return (alt.layer(*layers).properties(height=alt.Step(32), background=SURFACE, padding={"left": 6, "right": 34, "top": 10, "bottom": 8}).configure(font=FONT)
            .configure_view(stroke=None).configure_axis(**_AXIS).configure_scale(bandPaddingInner=0.34).configure_legend(**_LEGEND))


def lead_skill(frame: pd.DataFrame):
    """Our discharge model against simply repeating today's value, by days ahead (two series)."""
    names = [t("modelo próprio"), t("repetir o valor de hoje")]
    long = frame.rename(columns={"nse_modelo": names[0], "nse_persistencia": names[1]}).melt("dias_a_frente", names, "quem", "nse")
    chart = alt.Chart(long).mark_line(strokeWidth=2.2, point=alt.OverlayMarkDef(size=60, filled=True)).encode(
        x=alt.X("dias_a_frente:O", title=t("Dias à frente"), axis=alt.Axis(labelAngle=0)), y=alt.Y("nse:Q", title=t("Acerto (NSE: 1 = perfeito)"), scale=alt.Scale(domain=[0, 1])),
        color=alt.Color("quem:N", scale=alt.Scale(domain=names, range=SERIES[:2]), sort=names),
        tooltip=[alt.Tooltip("quem:N", title=" "), alt.Tooltip("dias_a_frente:O", title=t("Dias à frente")), alt.Tooltip("nse:Q", title="NSE", format=".2f")])
    return _base(chart, 250)


def monitoring_matrix(year: pd.DataFrame, colours: dict, order: list[str]):
    """One year of monitoring: every river section (rows, border at the top) in every month
    (columns), coloured by the state of the water against its normal."""
    data = year.assign(mes_nome=[L.meses()[m - 1] for m in year["mes_do_ano"]], nome=year["nome"].map(L.troco), classe=year["classe"].map(t),
                       fonte=year["fonte"].map(lambda v: t(v) if isinstance(v, str) else v))
    classes = [c for c in ("normal", "elevada", "muito elevada", "sem dados") if c in colours]
    chart = alt.Chart(data).mark_rect(stroke="white", strokeWidth=4, cornerRadius=7).encode(
        x=alt.X("mes_nome:O", sort=L.meses(), title=None, axis=alt.Axis(labelAngle=0, orient="top")),
        y=alt.Y("nome:N", sort=[L.troco(o) for o in order], title=None, axis=alt.Axis(labelLimit=220)),
        color=alt.Color("classe:N", scale=alt.Scale(domain=[t(c) for c in classes], range=[colours[c] for c in classes]), legend=alt.Legend(title=None, orient="bottom", columns=2)),
        tooltip=[alt.Tooltip("nome:N", title=t("Troço")), alt.Tooltip("month:N", title=t("Mês")), alt.Tooltip("classe:N", title=t("Estado")),
                 alt.Tooltip("ndti:Q", title=t("Índice de cor"), format=".3f"), alt.Tooltip("fonte:N", title=t("Satélite")),
                 alt.Tooltip("caudal_m3s:Q", title=t("Caudal do mês (m³/s)"), format=".0f")])
    return _base(chart, 36 * len(order) + 70).configure_axis(grid=False, domain=False, ticks=False, labelColor=MUTED, labelFontSize=11)


def river_profile(profile: pd.DataFrame, order: list[str]):
    """The colour of the water along the river, border to mouth, in the dry and in the rainy season."""
    names = [t("época seca"), t("época chuvosa")]
    data = profile.assign(epoca=profile["epoca"].map(t), nome=profile["nome"].map(L.troco))
    chart = alt.Chart(data).mark_line(strokeWidth=2.2, point=alt.OverlayMarkDef(size=70, filled=True)).encode(
        x=alt.X("troco:N", sort=order, title=t("Da fronteira (Q1) à foz (Q9)"), axis=alt.Axis(labelAngle=0)),
        y=alt.Y("ndti:Q", title=t("Índice de cor (mais alto = mais turva)"), scale=alt.Scale(zero=False)),
        color=alt.Color("epoca:N", scale=alt.Scale(domain=names, range=SERIES[:2]), sort=names),
        tooltip=[alt.Tooltip("nome:N", title=t("Troço")), alt.Tooltip("epoca:N", title=" "), alt.Tooltip("ndti:Q", title=t("Índice de cor (mediana)"), format=".3f"),
                 alt.Tooltip("meses:Q", title=t("Meses medidos"))])
    return _base(chart, 260)


def colour_forecast(forecast: pd.DataFrame, steps: list[float], colours: list[str], names: list[str], chosen: tuple | None = None):
    """The colour of the river at Marracuene in the coming 30 mornings: the most likely value (line), the
    band where 8 days out of 10 fell in the tests, over the five colour steps of the map (background).
    `chosen` = (first day, last day) of the week shown on the map, marked."""
    data = forecast.reset_index().rename(columns={"index": "date"})
    data["date"] = pd.to_datetime(data["date"])
    low = float(min(data["p10"].min(), steps[0]) - 0.03)
    high = float(max(data["p90"].max(), steps[-1]) + 0.03)
    edges = [low] + list(steps) + [high]
    first, last = data["date"].min() - pd.Timedelta(hours=12), data["date"].max() + pd.Timedelta(hours=12)
    bands = pd.DataFrame({"de": edges[:-1], "ate": edges[1:], "degrau": [t(n) for n in names], "x0": first, "x1": last})
    background = alt.Chart(bands).mark_rect(opacity=0.30).encode(
        x=alt.X("x0:T", title=None, axis=alt.Axis(format="%d/%m", labelOverlap="parity")), x2="x1:T",
        y=alt.Y("de:Q", scale=alt.Scale(domain=[low, high], nice=False), title=t("Cor da água em Marracuene (índice)")), y2="ate:Q",
        color=alt.Color("degrau:N", scale=alt.Scale(domain=[t(n) for n in names], range=colours), legend=None))
    labels = alt.Chart(bands.assign(meio=(bands["de"] + bands["ate"]) / 2)).mark_text(align="right", dx=-6, fontSize=10, fontWeight=600, color=INK).encode(
        x="x1:T", y="meio:Q", text="degrau:N")
    band = alt.Chart(data).mark_area(opacity=0.22, color=INK).encode(x="date:T", y="p10:Q", y2="p90:Q")
    line = alt.Chart(data).mark_line(color=INK, strokeWidth=2.2).encode(
        x="date:T", y="ndti_q8:Q",
        tooltip=[alt.Tooltip("date:T", title=t("Dia"), format="%d/%m"), alt.Tooltip("classe:N", title=t("Cor prevista")),
                 alt.Tooltip("ndti_q8:Q", title=t("Índice"), format=".3f")])
    layers = [background, labels, band, line]
    if chosen:
        week = pd.DataFrame({"de": [pd.Timestamp(chosen[0]) - pd.Timedelta(hours=12)], "ate": [pd.Timestamp(chosen[1]) + pd.Timedelta(hours=12)]})
        layers.append(alt.Chart(week).mark_rect(fillOpacity=0, stroke=INK, strokeWidth=1.6, strokeDash=[4, 3]).encode(x="de:T", x2="ate:T"))
    return _base(alt.layer(*layers), 250)


def same_month(summary: pd.DataFrame, month: int, chosen: str, steps: list[float], colours: list[str], names: list[str], forecast: float | None = None,
               forecast_year: int | None = None):
    """The colour of the river at Marracuene in the same month of every year (one point per year, in the
    colour of its step), the chosen year ringed, and this year's forecast as a hollow point."""
    data = summary[summary.index.str[5:7].astype(int) == month].dropna(subset=["ndti_marracuene"]).copy()
    data["ano"] = data.index.str[:4].astype(int)
    data["degrau"] = [t(names[int(sum(v >= s for s in steps))]) for v in data["ndti_marracuene"]]
    data["escolhido"] = data.index == chosen
    values = list(data["ndti_marracuene"]) + ([forecast] if forecast is not None else [])
    low, high = min(values + [steps[0]]) - 0.03, max(values + [steps[-1]]) + 0.03
    edges = [low] + list(steps) + [high]
    years = list(range(int(data["ano"].min()) if len(data) else 2017, max(int(data["ano"].max()) if len(data) else 2026, forecast_year or 0) + 1))
    bands = pd.DataFrame({"de": edges[:-1], "ate": edges[1:], "nome": [t(n) for n in names], "x0": years[0] - 0.5, "x1": years[-1] + 0.5})
    scale_x = alt.Scale(domain=[years[0] - 0.5, years[-1] + 0.5], nice=False)
    background = alt.Chart(bands).mark_rect(opacity=0.28).encode(
        x=alt.X("x0:Q", scale=scale_x, title=None, axis=alt.Axis(values=years, format="d", labelOverlap="parity")), x2="x1:Q",
        y=alt.Y("de:Q", scale=alt.Scale(domain=[low, high], nice=False), title=t("Cor da água em Marracuene (índice)")), y2="ate:Q",
        color=alt.Color("nome:N", scale=alt.Scale(domain=[t(n) for n in names], range=colours), legend=None))
    points = alt.Chart(data).mark_circle(size=150, stroke="white", strokeWidth=1.5, opacity=1).encode(
        x=alt.X("ano:Q", scale=scale_x), y="ndti_marracuene:Q",
        color=alt.Color("degrau:N", scale=alt.Scale(domain=[t(n) for n in names], range=colours), legend=None),
        tooltip=[alt.Tooltip("ano:Q", title=t("Ano"), format="d"), alt.Tooltip("degrau:N", title=t("Cor da água")),
                 alt.Tooltip("caudal_m3s:Q", title=t("Caudal médio (m³/s)"), format=".0f")])
    ring = alt.Chart(data[data["escolhido"]]).mark_point(size=420, shape="circle", filled=False, color=INK, strokeWidth=2.2).encode(x=alt.X("ano:Q", scale=scale_x), y="ndti_marracuene:Q")
    layers = [background, points, ring]
    if forecast is not None and forecast_year:
        guess = pd.DataFrame({"ano": [forecast_year], "valor": [forecast], "texto": [t("previsão")]})
        layers.append(alt.Chart(guess).mark_point(size=260, shape="diamond", filled=False, color=INK, strokeWidth=2, strokeDash=[3, 2]).encode(
            x=alt.X("ano:Q", scale=scale_x), y="valor:Q", tooltip=[alt.Tooltip("texto:N", title=" ")]))
        layers.append(alt.Chart(guess).mark_text(dy=-16, fontSize=11, fontWeight=600, color=INK).encode(x=alt.X("ano:Q", scale=scale_x), y="valor:Q", text="texto:N"))
    return _base(alt.layer(*layers), 230)
