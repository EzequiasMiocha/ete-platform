"""Monta (ou actualiza) o repositório de publicação em deploy/ete-plataforma/ (GitHub: EzequiasMiocha/ete-platform).

    .venv/bin/python scripts/build_deploy_repo.py

O repositório tem a plataforma a funcionar SEM este computador e, desde 24/11/2026, o projecto inteiro organizado
para quem o quiser compreender:

  plataforma/          a aplicação Streamlit e o pacote de dados
  docs/                a página leve do boletim (GitHub Pages), a reserva da aplicação
  src/, scripts/, config/, models/   o código, os modelos e todos os scripts do projecto
  notebooks/, reports/, workshops/   os notebooks de investigação, as figuras e tabelas, os dois workshops
  documentation/, guias/             a documentação em inglês e os guias em português (docs/ do projecto)
  data/                só os dados pequenos de que o boletim precisa ou que descrevem o resto
  .github/workflows/   o boletim corre todos os dias nos servidores do GitHub (grátis), e os testes a cada alteração

O que NÃO vai: os 43 GB de imagens de satélite e dados pesados, credenciais, os inscritos (data/private), a lista de
participantes dos workshops, o ambiente jupyter_env, os zips de distribuicao/ e os planos de plano/ (têm os contactos de
um colega e o orçamento).

Regras de cópia:
  * código, modelos, camadas fixas, documentação e material do projecto: a versão deste projecto substitui a da pasta
  * o que o boletim diário escreve (histórico, previsões guardadas, boletim, página): só é
    copiado se ainda não existir na pasta, para não pôr dados velhos por cima de novos
  * séries de cor da água: fica a versão mais recente

Depois de correr, ver docs/guia_de_deploy.md para os passos no GitHub e no Streamlit.
"""

import json
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "deploy" / "ete-plataforma"
sys.path.insert(0, str(ROOT / "src"))

from ete import config  # noqa: E402

cfg = config.load_config()
name = cfg["project"]["aoi_name"]

SOURCE_WINS = [                       # (path in the project, path in the repository); folders are copied whole
    ("src/ete", "src/ete"), ("models", "models"),
    ("scripts/run_daily_pipeline.py", "scripts/run_daily_pipeline.py"), ("scripts/check_forecast_system.py", "scripts/check_forecast_system.py"),
    ("scripts/test_alert_end_to_end.py", "scripts/test_alert_end_to_end.py"), ("scripts/update_water_quality_scenes.py", "scripts/update_water_quality_scenes.py"),
    ("scripts/manter_acordada.py", "scripts/manter_acordada.py"),          # a visita que não deixa o Streamlit adormecer a aplicação
    ("plataforma/app.py", "plataforma/app.py"), ("plataforma/leitor.py", "plataforma/leitor.py"), ("plataforma/tema.py", "plataforma/tema.py"), ("plataforma/graficos.py", "plataforma/graficos.py"), ("plataforma/testar_app.py", "plataforma/testar_app.py"),
    ("plataforma/requirements.txt", "plataforma/requirements.txt"), ("plataforma/LEIA-ME.md", "plataforma/LEIA-ME.md"), ("plataforma/.streamlit", "plataforma/.streamlit"),
    ("plataforma/.streamlit/config.toml", ".streamlit/config.toml"),     # the Streamlit Cloud runs from the repository root and reads it there
    ("plataforma/idioma.py", "plataforma/idioma.py"), ("plataforma/textos.py", "plataforma/textos.py"), ("plataforma/static", "plataforma/static"),
    ("plataforma/inscricoes.py", "plataforma/inscricoes.py"), ("plataforma/alertas_whatsapp.py", "plataforma/alertas_whatsapp.py"),
    ("plataforma/testar_alertas.py", "plataforma/testar_alertas.py"), ("scripts/send_whatsapp_alerts.py", "scripts/send_whatsapp_alerts.py"),
    ("plataforma/conselhos.py", "plataforma/conselhos.py"), ("plataforma/relatorio_subscritores.py", "plataforma/relatorio_subscritores.py"),
    ("plataforma/previsao_mapa.py", "plataforma/previsao_mapa.py"), ("plataforma/cartao_whatsapp.py", "plataforma/cartao_whatsapp.py"),
    ("plataforma/pesquisa.py", "plataforma/pesquisa.py"), ("plataforma/curiosidades.py", "plataforma/curiosidades.py"),
    ("plataforma/contas.py", "plataforma/contas.py"), ("plataforma/testar_contas.py", "plataforma/testar_contas.py"), ("docs/contas.sql", "docs/contas.sql"),
    ("scripts/ver_subscritores.py", "scripts/ver_subscritores.py"), ("docs/subscritores.sql", "docs/subscritores.sql"),
    ("plataforma/dados/mapas", "plataforma/dados/mapas"), ("plataforma/dados/vetores", "plataforma/dados/vetores"), ("plataforma/dados/exposicao", "plataforma/dados/exposicao"),
    ("plataforma/dados/qualidade", "plataforma/dados/qualidade"), ("plataforma/dados/sobre", "plataforma/dados/sobre"), ("plataforma/dados/modelos", "plataforma/dados/modelos"),
    ("plataforma/dados/imagens", "plataforma/dados/imagens"), ("plataforma/dados/lugares", "plataforma/dados/lugares"),
    # the colour of the river at Marracuene on every Sentinel-2 day: the daily run starts the 30-day forecast from the latest one
    ("data/processed/water_colour/cor_marracuene_diaria.csv", "data/processed/water_colour/cor_marracuene_diaria.csv"),
    ("plataforma/dados/series/alertas_historicos.csv", "plataforma/dados/series/alertas_historicos.csv"),
    # the catalogue describes the fixed layers too, so it follows the project; its dated fields are kept (see below)
    ("plataforma/dados/catalogo.json", "plataforma/dados/catalogo.json"),
    ("data/raw/aoi", "data/raw/aoi"),
    ("data/processed/forecast/exposicao_por_zona.csv", "data/processed/forecast/exposicao_por_zona.csv"),
    (f"data/processed/maps/zonas_de_aviso/lugares_por_ordem_de_alagamento_{name}.csv", f"data/processed/maps/zonas_de_aviso/lugares_por_ordem_de_alagamento_{name}.csv"),
    ("data/processed/series/alertas_diarios.csv", "data/processed/series/alertas_diarios.csv"), ("data/processed/series/modelo_b_area_mensal.csv", "data/processed/series/modelo_b_area_mensal.csv"),
    ("data/processed/series/vegetacao_no_rio_mensal.csv", "data/processed/series/vegetacao_no_rio_mensal.csv"),
    ("documentation", "documentation"),            # the English documentation (scripts/build_documentation.py draws its figures)
    # The whole project, organised so anyone can follow it (user's decision, 24 Nov 2026). Not the 43 GB of data, not the
    # plan files in plano/ (they hold a colleague's contacts and the budget), not the zips in distribuicao/.
    ("README.md", "README.md"),                     # the map of the repository (English)
    ("docs", "guias"),                              # Portuguese guides; docs/ in the repository is the GitHub Pages page
    ("scripts", "scripts"), ("notebooks", "notebooks"), ("reports", "reports"), ("workshops", "workshops"),
    ("qgis", "qgis"), ("servidor", "servidor"), ("logos", "logos"),
    ("data/README.md", "data/README.md"), ("data/metadata", "data/metadata"), ("data/processed/series", "data/processed/series"),
    ("data/raw/tide", "data/raw/tide"), ("data/raw/labels/flood_events", "data/raw/labels/flood_events"),
    ("data/raw/places/osm_places.gpkg", "data/raw/places/osm_places.gpkg"),
    ("data/raw/places/postos_administrativos.geojson", "data/raw/places/postos_administrativos.geojson"),
    ("data/raw/water_quality/modulo_q", "data/raw/water_quality/modulo_q"),
    ("data/processed/training/train_historico_dicionario.csv", "data/processed/training/train_historico_dicionario.csv"),
    ("data/processed/training/train_historico.meta.json", "data/processed/training/train_historico.meta.json"),
    ("data/processed/training/train_recente_dicionario.csv", "data/processed/training/train_recente_dicionario.csv"),
    ("data/processed/training/train_recente.meta.json", "data/processed/training/train_recente.meta.json"),
]
# Files of earlier layouts of the repository, removed when the repository is rebuilt
REMOVED = ["GUIA_DE_DEPLOY.md", "MANUAL_DO_UTILIZADOR.md", "ALERTAS_WHATSAPP.md", "GUIA_SERVIDOR_PROPRIO.md", "GUIA_DOMINIO_CO_MZ.md"]
ONLY_IF_MISSING = [
    ("data/raw/forecast/history", "data/raw/forecast/history"), ("data/processed/forecast/latest", "data/processed/forecast/latest"),
    ("plataforma/dados/boletim", "plataforma/dados/boletim"), ("plataforma/dados/series", "plataforma/dados/series"),
    ("plataforma/pagina/index.html", "docs/index.html"), ("plataforma/pagina/boletim.json", "docs/boletim.json"),
]
NEWER_WINS = [("data/raw/water_quality", "data/raw/water_quality", "*.csv")]
# Never copied: caches, the workshop's local Python environment, the screenshot sessions and browser profile, the list of
# workshop participants (privacy), the zips handed out on the day, logs
SKIP = {"__pycache__", ".ipynb_checkpoints", "cache", "jupyter_env", "capturas", ".perfil_firefox", "participantes.csv"}
SKIP_SUFFIX = {".zip", ".log", ".pyc"}


def copy(source: Path, target: Path, only_if_missing: bool = False) -> int:
    if not source.exists():
        return 0
    if source.is_dir():
        return sum(copy(item, target / item.name, only_if_missing) for item in sorted(source.iterdir()) if item.name not in SKIP)
    if source.suffix in SKIP_SUFFIX:
        return 0
    if only_if_missing and target.exists():
        return 0
    if source.suffix == ".png" and "forecast" in source.parts:           # charts made by notebooks: not needed to run
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return 1


for old in REMOVED:
    (TARGET / old).unlink(missing_ok=True)
CATALOGUE = TARGET / "plataforma" / "dados" / "catalogo.json"
published = json.loads(CATALOGUE.read_text()) if CATALOGUE.exists() else None      # as the daily run left it
copied = sum(copy(ROOT / a, TARGET / b) for a, b in SOURCE_WINS)
copied += sum(copy(ROOT / a, TARGET / b, only_if_missing=True) for a, b in ONLY_IF_MISSING)
# The date and the forecast status in the catalogue belong to the daily run. When the published copy is newer,
# keep them; otherwise every publish would show an old forecast date until the next morning's run.
if published:
    new = json.loads(CATALOGUE.read_text())
    if published.get("gerado_utc", "") > new.get("gerado_utc", ""):
        new["gerado_utc"] = published["gerado_utc"]
        new["estado_da_previsao"] = published.get("estado_da_previsao", new.get("estado_da_previsao"))
        CATALOGUE.write_text(json.dumps(new, indent=1, ensure_ascii=False))
for a, b, pattern in NEWER_WINS:
    for source in sorted((ROOT / a).glob(pattern)):
        target = TARGET / b / source.name
        if not target.exists() or source.stat().st_mtime > target.stat().st_mtime:
            copied += copy(source, target)
# the most recent stored forecast, so the repository can issue a bulletin even with no connection
runs = sorted((ROOT / "data/raw/forecast/runs").iterdir()) if (ROOT / "data/raw/forecast/runs").exists() else []
if runs and not any((TARGET / "data/raw/forecast/runs").glob("*")):
    copied += copy(runs[-1], TARGET / "data/raw/forecast/runs" / runs[-1].name)

# configuration: same as the project, with the light page written straight to docs/ (GitHub Pages)
text = (ROOT / "config" / "config.yaml").read_text()
assert "  static_page: plataforma/pagina " in text
(TARGET / "config").mkdir(parents=True, exist_ok=True)
(TARGET / "config" / "config.yaml").write_text(text.replace("  static_page: plataforma/pagina ", "  static_page: docs               "))

# exact versions of what the daily bulletin imports, so the models load the same way in the cloud
RUNTIME = ["numpy", "pandas", "scipy", "scikit-learn", "xgboost-cpu", "joblib", "PyYAML", "requests", "geopandas", "rasterio", "shapely", "pyproj", "pyogrio",
           "python-dotenv", "pillow", "matplotlib", "streamlit", "folium", "streamlit-folium"]       # matplotlib: the situation card of the WhatsApp messages
lines = ["# Versões exactas com que os modelos foram treinados e a plataforma testada.", "# Gerado por scripts/build_deploy_repo.py; não editar à mão."]
lines += [f"{package}=={metadata.version(package)}" for package in RUNTIME]
(TARGET / "requirements.txt").write_text("\n".join(lines) + "\n")
app_packages = ["streamlit", "folium", "streamlit-folium", "pandas", "requests", "matplotlib"]
(TARGET / "plataforma" / "requirements.txt").write_text("# o que a aplicação precisa para correr (o boletim diário usa o requirements.txt da raiz)\n"
                                                         + "\n".join(f"{p}=={metadata.version(p)}" for p in app_packages) + "\n")

(TARGET / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\n.venv/\n.ipynb_checkpoints/\n.streamlit/secrets.toml\n# telefones das pessoas inscritas nos alertas: nunca no repositório\ndata/private/\n"
                                   "# ambiente Python local do Workshop 2, zips de distribuição, lista de participantes\njupyter_env/\n*.zip\nparticipantes.csv\n")
(TARGET / ".env.example").write_text("# Só é preciso para actualizar as imagens de cor da água (Earth Engine). O boletim diário não usa.\nEE_PROJECT=\n"
                                     "# Alertas no WhatsApp (ver ALERTAS_WHATSAPP.md)\nWHATSAPP_TOKEN=\nWHATSAPP_PHONE_ID=\n"
                                     "ETE_SUBSCRITORES=sqlite\nSUPABASE_URL=\nSUPABASE_SERVICE_KEY=\n")
python = f"{sys.version_info.major}.{sys.version_info.minor}"

(TARGET / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
(TARGET / ".github" / "workflows" / "boletim_diario.yml").write_text(f"""\
# Boletim diário do ETE: previsão, boletim, mensagem, pacote da plataforma e página leve.
# Corre todos os dias nos servidores do GitHub. Também se pode correr à mão: Actions > Boletim diário > Run workflow.
name: Boletim diário

on:
  schedule:
    - cron: "15 3 * * *"        # 03:15 UTC = 05:15 em Maputo
  workflow_dispatch:

permissions:
  contents: write               # o boletim é guardado no próprio repositório

concurrency:
  group: boletim-diario
  cancel-in-progress: false

jobs:
  boletim:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "{python}"
          cache: pip
      - name: Instalar
        run: pip install -r requirements.txt
      - name: Previsão, boletim, pacote, página e alertas no WhatsApp
        id: pipeline
        env:                      # segredos do repositório (Settings > Secrets and variables > Actions); sem eles, os alertas não saem
          WHATSAPP_TOKEN: ${{{{ secrets.WHATSAPP_TOKEN }}}}
          WHATSAPP_PHONE_ID: ${{{{ secrets.WHATSAPP_PHONE_ID }}}}
          ETE_SUBSCRITORES: supabase
          SUPABASE_URL: ${{{{ secrets.SUPABASE_URL }}}}
          SUPABASE_SERVICE_KEY: ${{{{ secrets.SUPABASE_SERVICE_KEY }}}}
        run: |
          set +e
          python scripts/run_daily_pipeline.py --sem-imagens
          echo "codigo=$?" >> "$GITHUB_OUTPUT"
      - name: Verificar o pacote
        run: python plataforma/leitor.py
      - name: Guardar no repositório
        run: |
          git config user.name "ete-boletim"
          git config user.email "ete-boletim@users.noreply.github.com"
          git add -A plataforma/dados docs data/raw/forecast data/processed/forecast
          git diff --cached --quiet || git commit -m "Boletim de $(date -u +%F)"
          git push
      - name: Falhar se o boletim não saiu
        if: steps.pipeline.outputs.codigo == '2'
        run: |
          echo "O pipeline terminou com erro (código 2). A página e a aplicação mostram 'previsão indisponível' ao fim de 36 horas."
          exit 1
""")
(TARGET / ".github" / "workflows" / "testes.yml").write_text(f"""\
# Testes a cada alteração: o pacote está completo e todas as páginas da aplicação abrem sem erros.
name: Testes

on:
  push:
    paths-ignore: ["docs/**", "data/**", "documentation/**", "plataforma/dados/boletim/**", "plataforma/dados/series/**",
                   "workshops/**", "notebooks/**", "reports/**", "guias/**", "qgis/**", "servidor/**", "logos/**", "README.md"]
  pull_request:
  workflow_dispatch:

jobs:
  testes:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "{python}"
          cache: pip
      - name: Instalar
        run: pip install -r requirements.txt
      - name: Pacote de dados completo
        run: python plataforma/leitor.py --sem-prazo
      - name: Todas as páginas da aplicação
        working-directory: plataforma
        run: python testar_app.py
      - name: Contas (senhas, sessões, recuperação)
        working-directory: plataforma
        run: python testar_contas.py
      - name: Alertas no WhatsApp
        working-directory: plataforma
        run: python testar_alertas.py
      - name: Mensagem de alerta de ponta a ponta
        run: python scripts/test_alert_end_to_end.py
""")
(TARGET / ".github" / "workflows" / "manter_acordada.yml").write_text(f"""\
# Mantém a plataforma acordada. O Streamlit gratuito adormece as aplicações que passam 12 horas sem visitas,
# e a primeira pessoa a seguir fica à espera. De 4 em 4 horas, o GitHub abre a plataforma num navegador
# (o Chrome que já vem nos servidores do GitHub) e, se estiver a dormir, acorda-a.
# Se a plataforma não abrir em 10 minutos, este processo falha e o GitHub avisa por email.
name: Manter a plataforma acordada

on:
  schedule:
    - cron: "40 */4 * * *"      # 00:40, 04:40, 08:40, 12:40, 16:40 e 20:40 UTC (mais 2 horas em Maputo)
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: manter-acordada
  cancel-in-progress: true

jobs:
  visitar:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          sparse-checkout: scripts      # só o script da visita: o repositório inteiro tem os workshops e os notebooks
      - name: Abrir a plataforma
        run: python3 scripts/manter_acordada.py --url "{cfg['publication']['app_url']}" --navegador chrome --minutos 10
""")


if not (TARGET / ".git").exists():
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=TARGET, check=True)
size = sum(f.stat().st_size for f in TARGET.rglob("*") if f.is_file() and ".git" not in f.parts) / 1e6
print(f"{copied} ficheiros copiados para {TARGET.relative_to(ROOT)} ({size:.1f} MB sem contar o histórico do Git)")
