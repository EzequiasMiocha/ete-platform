"""Daily operation (production): run the forecast, check it, write the bulletin, keep an archive.

One call does everything:

    from ete import config, operations
    result = operations.run_daily(config.load_config())

Files written to data/processed/forecast/latest/ (what the platform reads) and to
data/processed/forecast/archive/<date>/ (kept for later verification):

    previsao_alertas.csv   one row per day: discharge scenarios, rain, alert levels
    cenarios_caudal.csv    the 51 discharge scenarios
    chuva_bacia.csv        observed and forecast basin rain
    turbidez.csv           per river reach: measured state and forecast summary (turbidez_diaria.csv: probability per day)
    boletim.md / .json     the bulletin, for people and for the platform
    estado.json            when the data was fetched, whether it is fresh, any problem found

Safety rule: if the data cannot be fetched or fails the checks, the bulletin says
"previsão indisponível". It never shows "verde" for lack of data.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import __version__, alerts, forecast, forecast_models, places
from .alerts import LEVELS
from .config import path

ADVICE = {
    "verde": "Sem sinais de cheia nos próximos dias. Não é precisa nenhuma ação especial.",
    "amarelo": "Atenção. Acompanhe os próximos boletins. Quem vive ou trabalha nas zonas baixas junto ao rio "
               "deve rever para onde ir e o que levar se a água subir.",
    "laranja": "Preparação. Proteja documentos, alimentos e bens em local alto; leve o gado para terreno elevado; "
               "evite atravessar o rio e as zonas baixas. Siga as indicações do INGD e das autoridades locais.",
    "vermelho": "Cheia provável ou em curso nas zonas baixas junto ao Incomáti. Siga de imediato as ordens das "
                "autoridades, incluindo a de sair de casa. Não atravesse zonas alagadas a pé nem de carro.",
}
TURBIDITY_ADVICE = ("A água do rio deve ser sempre tratada antes de beber (ferver, ou cloro). Com turbidez elevada, "
                    "deixe primeiro a água assentar e filtre-a por um pano limpo: a água barrenta é mais difícil de desinfetar.")
DISCLAIMER = ("Boletim experimental do projeto Eyes to Earth. Não substitui os avisos oficiais do INGD, do INAM e da "
              "ARA-Sul. A turbidez é um indicador da cor da água visto por satélite: não mede se a água é segura.")


# ----------------------------------------------------------------------------- checks
def check_forecast(cfg: dict, fc: dict) -> list[str]:
    """Problems that make a forecast unusable. An empty list means it passed."""
    problems = []
    today = pd.Timestamp(fc["date"])
    q = fc["discharge"]
    days = pd.date_range(today, periods=cfg["forecast"]["horizon_days"] + 1)
    window = q.reindex(days)
    if window.notna().sum(axis=1).min() < 30:
        problems.append("menos de 30 cenários de caudal em pelo menos um dia do horizonte")
    values = window.to_numpy()
    if np.nanmin(values, initial=0) < 0 or np.nanmax(values, initial=0) > 50_000:
        problems.append("caudal fora do intervalo plausível (0 a 50 000 m³/s)")
    rain = fc["rain"].reindex(pd.date_range(today - pd.Timedelta(days=6), today + pd.Timedelta(days=cfg["forecast"]["rain_skill_days"])))
    if rain.isna().any():
        problems.append("faltam dias na chuva observada ou prevista")
    elif (rain < 0).any() or (rain > 500).any():
        problems.append("chuva fora do intervalo plausível (0 a 500 mm/dia)")
    return problems


# ----------------------------------------------------------------------------- exposure (static, cached)
def exposure(cfg: dict) -> pd.DataFrame:
    """What lies in each warning zone inside the district (computed once and cached)."""
    file = path(cfg, "forecast", "exposicao_por_zona.csv")
    if not file.exists():
        zones = alerts.warning_zones(cfg)
        alerts.exposure_by_zone(cfg, zones["raster"]).round(1).to_csv(file)
    return pd.read_csv(file, index_col=0)


# ----------------------------------------------------------------------------- bulletin
def _turbidity_skill_text(cfg: dict) -> str:
    """One sentence on how often the turbidity forecast ranks a turbid day above a normal one."""
    try:
        skill = forecast_models.turbidity_skill(cfg)["auc"]
        own = float(skill[[i for i in skill.index if "5 dias" in i][0]])
        other = [float(skill[i]) for i in skill.index if "Landsat antes" in i]
    except (OSError, KeyError, IndexError, ValueError):
        return ""
    num = lambda v: f"{v:.2f}".replace(".", ",")
    text = f"A previsão dá maior probabilidade ao dia turvo em mais de {int(own * 10)} de cada 10 comparações entre um dia turvo e um dia normal (AUC {num(own)}, em anos que o modelo não viu"
    return text + (f"; {num(other[0])} noutro satélite e noutros anos). " if other else "). ")


# the message for community leaders is plain text: no emojis (one emoji makes a phone send an SMS in many more parts)


def whatsapp_message(data: dict) -> str:
    """The bulletin as a short text message for the community leaders' channel (WhatsApp or SMS).
    Plain words, the level first, what to do, where, until when, and who to listen to."""
    if "nivel_maximo_provavel" not in data:
        return ("ETE - Rio Incomáti, Marracuene\nHoje não foi possível fazer a previsão.\n"
                "Siga os avisos do INGD, do INAM e da ARA-Sul.")
    day = lambda text: pd.Timestamp(text).strftime("%d/%m")
    level = data["nivel_maximo_provavel"]
    lines = [f"ETE - Rio Incomáti, Marracuene ({day(data['emitido_utc'][:10])})", f"ALERTA {level.upper()} até {day(data['valido_ate'])}"]
    if level != "verde":
        lines.append(f"Dia mais crítico: {day(data['dia_mais_critico'])}")
    if data.get("nivel_maximo_possivel") not in (None, level):
        lines.append(f"Pode chegar a {data['nivel_maximo_possivel'].upper()} (menos provável).")
    lines += ["", data["conselho"]]
    first, large = data.get("lugares_que_alagam_primeiro") or [], data.get("lugares_em_cheia_grande") or []
    if first:
        lines += ["", "Alagam primeiro: " + ", ".join(first[:8]) + "."]
    if large:
        lines.append("Em cheia grande: " + ", ".join(large[:8]) + ".")
    turbid = [t["troco"] for t in data.get("turbidez", []) if t.get("previsao") == "provável" or t.get("estado") in ("elevada", "muito elevada")]
    if turbid:
        lines += ["", "Água do rio mais turva do que o habitual. Deixe assentar, filtre por um pano limpo e ferva ou use cloro antes de beber."]
    lines += ["", "Aviso experimental. Não substitui o INGD, o INAM e a ARA-Sul."]
    return "\n".join(lines)


def build_bulletin(cfg: dict, fc: dict, outlook: pd.DataFrame, turbidity: pd.DataFrame | None,
                   model_c: pd.DataFrame | None, status: dict) -> tuple[dict, str]:
    """The bulletin as a dictionary (for the platform) and as Markdown text (for people)."""
    f = cfg["forecast"]
    today = outlook.iloc[0]
    # most critical day = the highest discharge among the days at the highest level
    worst = lambda col: outlook[outlook[col] == outlook[col].max()].sort_values("caudal_mediana").iloc[-1]
    peak, possible = worst("nivel"), worst("nivel_possivel")
    first_day = outlook.index[outlook["nivel"] == outlook["nivel"].max()][0]
    level, level_possible = LEVELS[int(peak["nivel"])], LEVELS[int(possible["nivel_possivel"])]
    day = lambda ts: pd.Timestamp(ts).strftime("%d/%m")
    num = lambda v: f"{v:,.0f}".replace(",", " ")           # 12 345 instead of 12,345
    exp = exposure(cfg)
    # amarelo and laranja: the places that flood first; vermelho: the whole extent of the reference flood
    worst_level = int(max(peak["nivel"], possible["nivel_possivel"]))
    names = places.names_for_bulletin(cfg)
    zone = None if worst_level == 0 else exp.iloc[1] if worst_level == 3 else exp.iloc[0]

    if peak["nivel"] == 0 and possible["nivel_possivel"] == 0:
        headline = f"Nível VERDE nos próximos {f['horizon_days']} dias: nenhum cenário prevê cheia no Incomáti em Marracuene."
    elif peak["nivel"] == 0:
        headline = (f"Nível VERDE como cenário mais provável, mas há possibilidade de nível {level_possible.upper()} "
                    f"por volta de {day(possible.name)} ({100 * possible['prob_' + level_possible]:.0f} % dos cenários).")
    else:
        headline = (f"Nível {level.upper()} previsto a partir de {day(first_day)}. O caudal mais alto é esperado a "
                    f"{day(peak.name)}: cerca de {num(peak['caudal_mediana'])} m³/s.")
    short = (f"ETE Incomáti {day(fc['date'])}: alerta {level.upper()}"
             + (f" (possível {level_possible.upper()})" if level_possible != level else "")
             + f" até {day(outlook.index[-1])}. " + ADVICE[level].split(".")[0] + ". Não substitui avisos oficiais do INGD.")

    data = {
        "emitido_utc": status["emitido_utc"], "valido_ate": str(outlook.index[-1].date()), "desatualizado": status["desatualizado"],
        "nivel_hoje": LEVELS[int(today["nivel"])], "nivel_maximo_provavel": level, "dia_mais_critico": str(pd.Timestamp(peak.name).date()),
        "nivel_maximo_possivel": level_possible, "titulo": headline, "mensagem_curta": short,
        "conselho": ADVICE[level], "lugares_que_alagam_primeiro": names.get("alaga primeiro", []) if zone is not None else [], "lugares_em_cheia_grande": names.get("alaga em cheia grande", []) if worst_level == 3 else [], "zona_a_avisar": None if zone is None else {"nome": zone.name, **{k: float(v) for k, v in zone.items()}},
        "previsao_diaria": [{"data": str(i.date()), "alerta": r["alerta"], "alerta_possivel": r["alerta_possivel"],
                             "caudal_mediana_m3s": round(float(r["caudal_mediana"]), 1), "caudal_p10_m3s": round(float(r["caudal_p10"]), 1),
                             "caudal_p90_m3s": round(float(r["caudal_p90"]), 1), "prob_laranja": round(float(r["prob_laranja"]), 2),
                             "chuva_7d_mm": None if pd.isna(r["chuva_7d_mm"]) else round(float(r["chuva_7d_mm"]), 1)}
                            for i, r in outlook.iterrows()],
        "turbidez": [] if turbidity is None else [{"troco": i, **{k: (round(float(v), 2) if isinstance(v, float) else v) for k, v in r.items()}}
                                                  for i, r in turbidity.iterrows()],
        "aviso": DISCLAIMER, "fontes": "Caudal: GloFAS v4 (Copernicus EMS) via Open-Meteo. Chuva: ECMWF IFS via Open-Meteo. "
                                       "Turbidez: Sentinel-2 (Copernicus). Terreno: Copernicus DEM, MERIT Hydro, JRC.",
        "estado": status,
    }

    lines = ["# Boletim ETE - Rio Incomáti, Marracuene", "",
             f"**Emitido:** {status['emitido_utc'][:16].replace('T', ' ')} UTC · **Válido até:** {day(outlook.index[-1])}"
             + (" · **ATENÇÃO: DADOS DESATUALIZADOS**" if status["desatualizado"] else ""), "",
             f"## {headline}", "", f"**O que fazer:** {ADVICE[level]}", ""]
    if zone is not None:
        first, large = names.get("alaga primeiro", []), names.get("alaga em cheia grande", [])
        if first:
            lines += [f"**Lugares que alagam primeiro** (na cheia de 2026, cerca de 4 dias depois do alerta): {', '.join(first)}.", ""]
        if large and worst_level == 3:
            lines += [f"**Lugares atingidos numa cheia grande** (em 2026, cerca de 10 dias depois do alerta): {', '.join(large)}.", ""]
        if first or large:
            lines += ["Os nomes vêm de mapas públicos e indicam a zona à volta de cada lugar (500 m), não limites oficiais de bairros.", ""]
        lines += [f"**Onde:** {zone.name}, no mapa de zonas de aviso (onde a água chegou na cheia de janeiro de 2026). "
                  f"No distrito, essa zona tem cerca de {num(zone['area_km2'])} km², dos quais {num(zone['area_agricola_km2'])} km² de terras agrícolas, "
                  f"{num(zone['edificios'])} edifícios e {num(zone['estradas_km'])} km de estradas e caminhos.", ""]
    lines += ["## Previsão para os próximos dias", "",
              "| Dia | Alerta | Alerta possível | Caudal previsto (m³/s) | Cenários acima do limite laranja | Chuva 7 dias na bacia (mm) |",
              "|---|---|---|---|---|---|"]
    for i, r in outlook.iterrows():
        rain = "-" if pd.isna(r["chuva_7d_mm"]) else f"{r['chuva_7d_mm']:.0f}"
        lines.append(f"| {day(i)} | {r['alerta']} | {r['alerta_possivel']} | {r['caudal_mediana']:.0f} ({r['caudal_p10']:.0f} a {r['caudal_p90']:.0f}) "
                     f"| {100 * r['prob_laranja']:.0f} % | {rain} |")
    lines += ["", f"Limites de caudal: amarelo {status['limites_caudal']['amarelo']:.0f}, laranja {status['limites_caudal']['laranja']:.0f}, "
                  f"vermelho {status['limites_caudal']['vermelho']:.0f} m³/s. \"Alerta\" é o nível previsto por pelo menos metade dos 51 cenários; "
                  f"\"alerta possível\" por pelo menos {100 * f['probability']['possivel']:.0f} %.", ""]
    if model_c is not None and len(model_c):
        values = ", ".join(f"{day(i)}: {v:.0f}" for i, v in model_c["caudal_modelo_c"].items())
        lines += [f"**Segunda opinião (modelo próprio, só com a chuva já caída):** {values} m³/s.", ""]
    if turbidity is not None and len(turbidity):
        daily = turbidity.attrs.get("daily", pd.DataFrame())
        lines += ["## Qualidade da água: turbidez (cor da água vista por satélite)", "",
                  f"| Troço do rio | Estado nos últimos 20 dias | Manhãs com água mais turva nos próximos {f['horizon_days']} dias | Dias mais prováveis |", "|---|---|---|---|"]
        for i, r in turbidity.iterrows():
            if r["previsao"] == "sem previsão":
                outlook_text, when = "sem previsão (medição pouco fiável neste troço)", "-"
            else:
                likely = daily.index[daily[i] >= 0.5] if i in daily else []
                outlook_text = f"{r['dias_elevada']} ({r['previsao']})"
                when = ", ".join(day(d) for d in likely[:6]) or "-"
            images = f"{r['estado']} ({r['medicoes_em_20_dias']} {'imagem' if r['medicoes_em_20_dias'] == 1 else 'imagens'})" if r["medicoes_em_20_dias"] else r["estado"]
            lines.append(f"| {i} | {images} | {outlook_text} | {when} |")
        used = sorted({d for d in turbidity.get("medicao_usada", pd.Series(dtype=str)) if d})
        start = (f"A previsão parte da última medição por satélite ({day(pd.Timestamp(used[-1]))})." if used
                 else "Não há medição por satélite nos últimos 30 dias: a previsão usa só o caudal e a maré e é menos certa.")
        lines += ["", start + " É para a manhã (cerca das 9h30), a hora a que os satélites observam o rio. A cor da água muda com o caudal "
                      "e também com a maré, por isso varia de dia para dia mesmo sem chuva. \"Mais turva\" quer dizer entre os 25 % de dias "
                      "mais turvos desse troço.", "", TURBIDITY_ADVICE, ""]
    lines += ["## Confiança e limites", "",
              f"- Previsão de caudal: {status['cenarios']} cenários do GloFAS; dados obtidos em {status['dados_obtidos_utc'][:16].replace('T', ' ')} UTC"
              + (" (cópia guardada: sem ligação no momento da emissão)" if status["fonte"] == "cache" else "") + ".",
              f"- A chuva prevista só é usada como gatilho até {f['rain_skill_days']} dias à frente.",
              "- Turbidez: índice de cor da água (NDTI) medido por satélite; dois satélites independentes concordam (correlação 0,92 no mesmo dia). "
              + _turbidity_skill_text(cfg) +
              "É um indicador relativo: não há medições no rio para o converter em unidades de turbidez.",
              "- Os limites dos alertas foram calculados com dados até 2021 e testados em 2022-2026.", "", f"*{DISCLAIMER}*", ""]
    return data, "\n".join(lines)


# ----------------------------------------------------------------------------- run
def run_daily(cfg: dict, offline: bool = False) -> dict:
    """Fetch (or reuse) today's forecast, check it, and write the bulletin and tables."""
    f = cfg["forecast"]
    now = datetime.now(timezone.utc)
    status = {"emitido_utc": now.isoformat(timespec="seconds"), "versao_codigo": __version__, "fonte": "online", "problemas": []}
    fc = None
    if not offline:
        try:
            forecast.update_history(cfg)
            fc = forecast.fetch_forecast(cfg)
        except Exception as err:
            status["problemas"].append(f"sem ligação aos serviços de previsão: {type(err).__name__}")
    if fc is None:
        last = forecast.latest_run(cfg)
        if last is None:
            raise RuntimeError("no forecast could be fetched and no earlier run is stored")
        fc, status["fonte"] = forecast.load_run(cfg, last), "cache"
        fetched = datetime.fromtimestamp((path(cfg, "forecast_raw", "runs", last, mkdir=False) / "discharge_ensemble.json").stat().st_mtime, timezone.utc)
        fc["fetched_utc"] = fetched.isoformat(timespec="seconds")
    age_hours = (now - datetime.fromisoformat(fc["fetched_utc"])).total_seconds() / 3600
    limits = forecast.load_limits(cfg)
    status.update({"data_da_previsao": str(fc["date"]), "dados_obtidos_utc": fc["fetched_utc"], "idade_dos_dados_horas": round(age_hours, 1),
                   "desatualizado": bool(age_hours > f["stale_after_hours"]), "cenarios": int(fc["discharge"].shape[1]),
                   "limites_caudal": limits["discharge_m3s"], "limites_calculados_em": limits["created_utc"]})
    status["problemas"] += check_forecast(cfg, fc)

    latest = path(cfg, "forecast", "latest")
    if any(p for p in status["problemas"] if not p.startswith("sem ligação")):
        status["estado"] = "previsao_indisponivel"
        text = ("# Boletim ETE - Rio Incomáti, Marracuene\n\n## Previsão indisponível\n\nOs dados de hoje não passaram nas verificações: "
                + "; ".join(status["problemas"]) + ".\n\nConsulte os avisos oficiais do INGD, do INAM e da ARA-Sul.\n")
        (latest / "boletim.md").write_text(text)
        (latest / "boletim.json").write_text(json.dumps({"titulo": "Previsão indisponível", "estado": status}, indent=1, ensure_ascii=False))
        (latest / "mensagem_whatsapp.txt").write_text(whatsapp_message({}))
        (latest / "estado.json").write_text(json.dumps(status, indent=1, ensure_ascii=False))
        return {"status": status, "bulletin": text}

    outlook = forecast.alert_outlook(cfg, fc, limits)
    model_c = turbidity = None
    try:
        model_c = forecast_models.predict_discharge(cfg, fc)
    except Exception as err:
        status["problemas"].append(f"modelo próprio de caudal indisponível: {type(err).__name__}")
    try:
        turbidity = forecast_models.turbidity_outlook(cfg, fc)
    except Exception as err:
        status["problemas"].append(f"previsão de turbidez indisponível: {type(err).__name__}")
    colour = None
    try:                                     # the colour of the water at Marracuene for 30 days (feeds the forecast maps of the page)
        from . import water_colour_model
        colour = water_colour_model.forecast_reach(cfg, fc)
    except Exception as err:
        status["problemas"].append(f"previsão da cor da água a 30 dias indisponível: {type(err).__name__}")
    status["estado"] = "ok" if not status["desatualizado"] else "desatualizado"
    data, text = build_bulletin(cfg, fc, outlook, turbidity, model_c, status)

    table = outlook.join(model_c) if model_c is not None and len(model_c) else outlook.assign(caudal_modelo_c=np.nan)
    table.round(3).to_csv(latest / "previsao_alertas.csv")
    fc["discharge"].round(2).rename_axis("date").to_csv(latest / "cenarios_caudal.csv")
    fc["rain"].round(2).rename_axis("date").to_csv(latest / "chuva_bacia.csv")
    if colour is not None and len(colour):
        colour.round(4).to_csv(latest / "cor_prevista.csv")
    if turbidity is not None and len(turbidity):
        turbidity.round(3).to_csv(latest / "turbidez.csv")
        if len(turbidity.attrs.get("daily", [])):
            turbidity.attrs["daily"].round(3).rename_axis("date").to_csv(latest / "turbidez_diaria.csv")
    (latest / "boletim.md").write_text(text)
    (latest / "boletim.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    (latest / "mensagem_whatsapp.txt").write_text(whatsapp_message(data))
    (latest / "estado.json").write_text(json.dumps(status, indent=1, ensure_ascii=False))
    archive = path(cfg, "forecast", "archive", str(fc["date"]))
    for file in latest.iterdir():
        shutil.copy2(file, archive / file.name)
    return {"status": status, "outlook": table, "turbidity": turbidity, "bulletin": text, "data": data, "forecast": fc}


# ----------------------------------------------------------------------------- verification
def verification(cfg: dict) -> pd.DataFrame:
    """Compare the archived forecasts with what the service later reported as observed.

    One row per archived run and lead time: forecast median, later value, error, and whether the
    alert level was right. Empty until at least one archived forecast day lies in the past.
    """
    history = forecast.load_history(cfg)["q"].dropna()
    limits = forecast.load_limits(cfg)["discharge_m3s"]
    level = lambda q: int(q >= limits["amarelo"]) + int(q >= limits["laranja"]) + int(q >= limits["vermelho"])
    folder = path(cfg, "forecast", "archive", mkdir=False)
    rows = []
    for run in sorted(folder.iterdir()) if folder.exists() else []:
        file = run / "previsao_alertas.csv"
        if not file.exists():
            continue
        table = pd.read_csv(file, index_col=0, parse_dates=True)
        for day, r in table.iterrows():
            if r["dias_a_frente"] > 0 and day in history.index and day < history.index.max() - pd.Timedelta(days=3):
                observed = float(history[day])
                rows.append({"emitido": run.name, "dia": day.date(), "dias_a_frente": int(r["dias_a_frente"]),
                             "previsto_mediana": r["caudal_mediana"], "observado": observed, "erro": r["caudal_mediana"] - observed,
                             "dentro_do_intervalo": bool(r["caudal_p10"] <= observed <= r["caudal_p90"]),
                             "nivel_previsto": int(r["nivel_caudal"]), "nivel_observado": level(observed)})
    return pd.DataFrame(rows)
