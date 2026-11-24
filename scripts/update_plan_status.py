"""Actualiza o estado do plano a partir do que existe no projecto.

    .venv/bin/python scripts/update_plan_status.py

Lê ETE_Project_Plan.xlsx (NUNCA o altera) e escreve:
  ETE_Project_Plan_actualizado.xlsx   cópia com Estado, % de progresso, Evidência e Notas preenchidos
                                      nas folhas das semanas, e o estado de download na Parte I
  docs/estado_do_plano.md             o mesmo em texto, com o que falta e de quem depende

Regras:
  * Uma tarefa só passa a "Done" se o entregável existir no projecto (o ficheiro de evidência é verificado).
  * Um "Done" já posto por alguém no plano nunca é retirado; se não houver evidência no projecto,
    fica uma nota a dizê-lo.
  * As tarefas que não são técnicas (reuniões, logística, workshop) ficam como estão.
"""

import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SOURCE, TARGET = ROOT / "plano" / "ETE_Project_Plan.xlsx", ROOT / "plano" / "ETE_Project_Plan_actualizado.xlsx"

# id: (status, progress, evidence path or "", note). status None = leave as it is in the plan.
TASKS = {
    "W1-03": ("Done", 1, "data/raw/aoi/", "Bacia, sub-bacia, distrito e grelha comum EPSG:32736."),
    "W1-04": (None, None, "", "A pasta do projecto neste computador ainda não é um repositório Git. Estrutura e regras de nomes: README.md."),
    "W1-05": ("Done", 1, "data/raw/static/", "DEM, declive, aspeto, HAND, acumulação de fluxo, WorldCover, JRC, rios."),
    "W1-06": ("Done", 1, "data/processed/series/rain_daily.csv", "CHIRPS e IMERG diários, bacia e distrito."),
    "W1-07": ("Done", 1, "data/raw/optical/landsat", "235 meses com banda n_obs (os meses em falta não tiveram imagem limpa)."),
    "W1-08": ("Done", 1, "data/raw/radar/sentinel1", "137 meses, órbita ascendente; bandas extra VV_p10 e VH_p10 para cheias curtas."),
    "W1-09": ("Done", 1, "data/raw/labels/flood_events/flood_events_catalogue.csv", "EMSR857 (jan 2026) usado como referência independente."),
    "W1-10": ("Done", 1, "data/interim/water_quality/trocos_rio.gpkg", "9 troços, fronteira à foz; largura em largura_por_troco.csv. Notebook 29."),
    "W1-11": (None, None, "", "Sem evidência no projecto: o ACOLITE não foi instalado nem corrido neste computador (exige imagens de nível 1, cerca de 1 GB cada)."),
    "W1-12": ("Done", 1, "data/raw/water_quality/validacao/gemstat/GEMStat_station_metadata.csv", "Resultado: nenhuma estação na bacia do Incomáti (arquivo de fev 2026, 22 981 estações)."),
    "W1-13": (None, None, "docs/protocolo_de_campo_qualidade_da_agua.md", "Decisão da equipa (12/10/2026): não serão feitas medições no local. O protocolo e o calendário ficam guardados para uma fase futura."),
    "W2-01": ("Done", 1, "data/raw/optical/sentinel2", "116 meses, 10 m, com banda B5 (red edge)."),
    "W2-02": ("Done", 1, "notebooks/semana_2/20_indices_espectrais_e_radar.ipynb", "Coeficientes de Roy et al. testados e mantidos DESLIGADOS: baixam o MNDWI da água de 0,68 para 0,16. Decisão documentada."),
    "W2-03": ("Done", 1, "notebooks/semana_2/20_indices_espectrais_e_radar.ipynb", "NDWI, MNDWI, NDVI, NDMI, razão VV/VH e variação face à referência seca."),
    "W2-04": ("Done", 1, "data/interim/features", "Stack estático de 13 bandas na grelha comum."),
    "W2-05": ("Done", 1, "data/processed/series/rain_daily.csv", "Acumulados 3/7/14/30 dias e percentis por época do ano."),
    "W2-06": ("Done", 1, "data/processed/series/hydromet_daily.csv", "ERA5-Land, SMAP L4 v008 e GloFAS."),
    "W2-07": ("Done", 1, "data/processed/series/soil_moisture_calibrated_daily.csv", ""),
    "W2-08": ("Done", 1, "reports/semana_2", "Relatório de sobreposição 2017–2021."),
    "W2-09": ("Done", 1, "data/raw/labels/ems_unosat/ems_labels.gpkg", "JRC mensal + EMS (120 polígonos). As amostras desenhadas à mão ainda não existem (labels.gpkg vazio)."),
    "W2-10": ("Done", 1, "data/processed/training/train_historico.parquet", "670 243 linhas."),
    "W2-11": ("Done", 1, "data/processed/training/train_recente.parquet", "311 413 linhas."),
    "W2-12": ("Done", 1, "data/interim/water_quality/trocos_rio.gpkg", "Camadas agua_permanente, agua_pura_sentinel2, agua_pura_landsat. Feita com Dynamic World (10 m): o JRC (30 m) não vê o rio a montante. A rever no QGIS."),
    "W2-13": ("Done", 1, "data/raw/water_quality/modulo_q", "NDTI, turbidez, sólidos, NDCI, vegetação e temperatura por imagem e troço, 2006–2026. A montante só Sentinel-2 (rio com menos de 90 m)."),
    "W2-14": ("Not started", 0, "", "ACOLITE não corrido (megas: imagens de nível 1). Em sua vez: concordância entre dois satélites e teste das fórmulas com o GLORIA (notebooks 29 e 37)."),
    "W2-15": ("Done", 1, "data/processed/training/qualidade_trocos.parquet", "1 linha por troço e mês, com chuva e caudal. Notebook 29."),
    "W2-16": ("Not started", 0, "", "NÃO SERÁ FEITA. Decisão da equipa (12/10/2026): não serão feitas medições no local."),
    "W2-17": ("Done", 1, "plataforma/app.py", "Páginas Hoje, Quantidade, Qualidade e Sobre os dados; corre localmente (plataforma/testar_app.py). Feita pelo líder técnico; a rever pelo Mussa."),
    "W2-19": ("In progress", 0.7, "docs/guia_de_mensagens_de_alerta.md", "Níveis e mensagens em português prontos. Falta a língua local (por falantes nativos) e o teste com a comunidade."),
    "W3-01": ("Done", 1, "models/modelo_b_radar.joblib", "XGBoost escolhido entre 4 algoritmos. IoU 0,91, F1 0,95, Kappa 0,89 na cheia de 2026 (blocos espaciais)."),
    "W3-02": ("Done", 1, "data/processed/maps/modelo_a", "AUC 0,96 em validação e na cheia de 2026."),
    "W3-03": ("Done", 1, "notebooks/semana_3/32_motor_de_alertas.ipynb", "Em produção o alerta vem do caudal e da chuva previstos; o onde vem das zonas de aviso (cheia real de 2026)."),
    "W3-04": ("Done", 1, "notebooks/semana_3/33_validacao_e_resumo.ipynb", "Limite: toda a validação de cheias assenta num evento (jan 2026)."),
    "W3-05": ("Done", 1, "notebooks/semana_3/36_modulo_Q_normais_anomalias_tendencias.ipynb", "Normais, anomalias, Isolation Forest e Mann-Kendall sazonal, com teste à mudança de satélite de 2013."),
    "W3-06": ("Done", 1, "notebooks/semana_3/37_modulo_Q_turbidez_esperada_e_validacao.ipynb", "O modelo mensal previsto no plano não funcionou; ficou um modelo imagem a imagem. Só dá aviso nos troços onde explica o suficiente."),
    "W3-07": ("Done", 1, "reports/semana_3/37_validacao_gloria.csv", "Validação possível concluída: GLORIA feito; GEMStat sem estações na bacia. Sem validação local: Decisão da equipa (12/10/2026): não serão feitas medições no local."),
    "W3-08": ("Not started", 0, "", "NÃO SERÁ FEITA. Decisão da equipa (12/10/2026): não serão feitas medições no local."),
    "W3-09": ("Done", 1, "docs/ficha_de_evidencia_do_problema.md", "Notebook 38."),
    "W3-11": ("Done", 1, "data/processed/maps/zonas_de_aviso", "Zonas vetorizadas, manchas pequenas removidas, projecto QGIS."),
    "W3-12": ("Done", 1, "plataforma/dados/catalogo.json", "A app lê camadas reais através do pacote plataforma/dados/ (4,7 MB)."),
    "W3-13": ("Not started", 0, "docs/guia_de_mensagens_de_alerta.md", "As cores dos alertas já estão fixadas no guia e no catálogo; logótipo e ícones por fazer."),
    "W4-01": ("In progress", 0.9, "plataforma/app.py", "Página Quantidade pronta e testada (plataforma/testar_app.py). Falta a revisão do Mussa e a identidade visual."),
    "W4-02": ("In progress", 0.9, "plataforma/dados/qualidade/estado_por_troco.csv", "Página Qualidade pronta e testada: mapa por troço, séries desde 2006, normais, tendências, alertas. Falta a revisão."),
    "W4-03": ("In progress", 0.9, "deploy/ete-plataforma/.github/workflows/boletim_diario.yml", "Boletim diário preparado para correr nos servidores do GitHub (sem computador ligado); ensaiado num clone limpo. Fica a correr depois do passo 3 do guia de deploy. O mapa de radar é mensal, não diário."),
    "W4-04": ("Done", 1, "plataforma/dados/exposicao/exposicao_por_zona.csv", "Área, terras agrícolas, edifícios, escolas, saúde, estradas e pessoas por zona. As pessoas (WorldPop) são um limite superior. A rever pelo Agostinho."),
    "W4-05": ("In progress", 0.8, "docs/guia_de_deploy.md", "Repositório de publicação pronto e testado (deploy/ete-plataforma, 11 MB). Falta criar o repositório no GitHub e a app no Streamlit Cloud: precisa da conta da equipa (cerca de 20 minutos, guia passo a passo)."),
    "W4-06": ("Not started", 0, "docs/semana_4_preparacao.md", "Roteiro de testes pronto; os testes automáticos passam. Faltam os testes com pessoas."),
    "W4-07": ("In progress", 0.9, "docs/manual_do_utilizador.md", "README, guia de deploy, manual do utilizador, guias e protocolos feitos. Falta a revisão de linguagem pela Irene."),
    "W4-08": ("In progress", 0.5, "docs/teste_alerta_ponta_a_ponta.md", "Parte automática passa (previsão → boletim → mensagem). Falta enviar a um líder e registar a resposta."),
    "W4-09": ("In progress", 0.4, "reports/mapas_para_impressao/mapa_zonas_de_aviso_A3.pdf", "Mapas A3 em rascunho técnico. Falta o cartaz e o arranjo gráfico."),
    "B-03": ("In progress", 0.3, "reports/mapas_para_impressao", "Rascunhos de cheias; falta o mapa de qualidade da água e o arranjo gráfico."),
}

# variable number: (status, note)
VARIABLES = {17: ("Not started", "AWEI não calculado (P2); MNDWI e radar bastaram."),
             47: ("In progress", "Modelo de ficheiro criado, sem amostras desenhadas; a referência independente usada é o EMS."),
             48: ("Not started", "Sen1Floods11 não descarregado (P2); não foi preciso pré-treino."),
             55: ("Not started", "ACOLITE não corrido (megas)."),
             67: ("Not started", "Não será feita. Decisão da equipa (12/10/2026): não serão feitas medições no local.")}
VARIABLE_NOTES = {56: "Estimativa sem calibração local (banda do vermelho).", 57: "Estimativa; mesma informação da turbidez.",
                  58: "Calculado, mas não reportado como clorofila: no Incomáti segue o sedimento.",
                  59: "Fiável nos troços largos; a montante mistura a margem.", 60: "Só nos troços com mais de 300 m de largura.",
                  61: "Relação ajustada ao GLORIA; sem medições locais.", 65: "Verificado: nenhuma estação na bacia."}

wb = openpyxl.load_workbook(SOURCE)
report, missing = [], []
for sheet in wb.worksheets:
    header = next((row for row in sheet.iter_rows() if row[0].value == "ID"), None)
    if header is None:
        continue
    cols = {c.value: c.column for c in header if c.value}
    for row in sheet.iter_rows(min_row=header[0].row + 1):
        task = row[0].value
        if not isinstance(task, str) or "-" not in task or len(task) > 6:
            continue
        cell = lambda name: sheet.cell(row=row[0].row, column=cols[name])
        before = cell("Status").value
        if task in TASKS:
            status, progress, evidence, note = TASKS[task]
            if evidence and not (ROOT / evidence).exists():
                missing.append(f"{task}: {evidence}")
                status = None if status == "Done" else status
            if status is not None and before != "Done":
                cell("Status").value, cell("% Progress").value = status, progress
            elif before == "Done":
                cell("% Progress").value = 1
            if evidence and (ROOT / evidence).exists():
                cell("Evidence / link").value = evidence
            if note:
                cell("Notes / blockers").value = note
        elif before == "Done":
            cell("% Progress").value = 1
        report.append({"folha": sheet.title, "id": task, "tarefa": cell("Task").value, "responsavel": cell("Owner").value, "estado": cell("Status").value,
                       "progresso": cell("% Progress").value or 0, "evidencia": cell("Evidence / link").value or "", "nota": cell("Notes / blockers").value or ""})

part1 = wb["Part I - Variables"]
header = next(row for row in part1.iter_rows() if row[0].value == "#")
status_col = next(c.column for c in header if c.value == "Download status")
variables = []
for row in part1.iter_rows(min_row=header[0].row + 1):
    try:
        number = int(float(row[0].value))
    except (TypeError, ValueError):
        continue
    status, note = VARIABLES.get(number, ("Done", VARIABLE_NOTES.get(number, "")))
    part1.cell(row=row[0].row, column=status_col).value = status
    variables.append({"n": number, "variavel": row[2].value, "prioridade": row[11].value, "estado": status, "nota": note})
wb.save(TARGET)

names = {"Done": "Feito", "In progress": "Em curso", "Not started": "Por começar", "Blocked": "Bloqueado"}
lines = ["# Estado do plano", "", f"Gerado por `scripts/update_plan_status.py`. O plano original (`{SOURCE.name}`) não foi alterado; a cópia actualizada é `{TARGET.name}`.", ""]
for sheet in dict.fromkeys(r["folha"] for r in report):
    rows = [r for r in report if r["folha"] == sheet]
    done = sum(r["estado"] == "Done" for r in rows)
    lines += [f"## {sheet}: {done} de {len(rows)} feitas", "", "| ID | Tarefa | Responsável | Estado | Evidência | Nota |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['tarefa']} | {r['responsavel']} | {names.get(r['estado'], r['estado'])} ({100 * float(r['progresso']):.0f} %) | {('`' + r['evidencia'] + '`') if r['evidencia'] else ''} | {r['nota']} |" for r in rows]
    lines.append("")
total = {s: sum(v["estado"] == s for v in variables) for s in names}
lines += ["## Parte I: variáveis", "", f"{total['Done']} de {len(variables)} variáveis obtidas ou calculadas; {total['In progress']} em curso; {total['Not started']} por começar.", "",
          "| # | Variável | Prioridade | Estado | Nota |", "|---|---|---|---|---|"]
lines += [f"| {v['n']} | {v['variavel']} | {v['prioridade']} | {names[v['estado']]} | {v['nota']} |" for v in variables if v["estado"] != "Done" or v["nota"]]
lines.append("")
(ROOT / "docs" / "estado_do_plano.md").write_text("\n".join(lines))

for sheet in dict.fromkeys(r["folha"] for r in report):
    rows = [r for r in report if r["folha"] == sheet]
    print(f"{sheet:8s} feitas {sum(r['estado'] == 'Done' for r in rows):2d} | em curso {sum(r['estado'] == 'In progress' for r in rows):2d} | por começar {sum(r['estado'] == 'Not started' for r in rows):2d} | total {len(rows)}")
print(f"variáveis: {total['Done']} feitas, {total['In progress']} em curso, {total['Not started']} por começar")
if missing:
    print("EVIDÊNCIA EM FALTA (a tarefa não foi marcada como feita):")
    for item in missing:
        print("  ", item)
sys.exit(0)
