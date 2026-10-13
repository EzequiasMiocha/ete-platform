"""Teste da aplicação sem abrir o navegador: corre cada página e falha se houver algum erro.

    cd plataforma && python testar_app.py
"""

import sys

from streamlit.testing.v1 import AppTest

failures = 0
for page in ("Hoje", "Quantidade (cheias)", "Qualidade (água do rio)", "Sobre os dados"):
    app = AppTest.from_file("app.py", default_timeout=180).run()
    app.sidebar.radio[0].set_value(page).run()
    errors = [str(e.value) for e in app.exception]
    failures += len(errors)
    print(f"{'ok   ' if not errors else 'FALHA'} {page}: {len(app.subheader)} secções, {len(app.dataframe)} tabelas")
    for error in errors:
        print("      ", error[:300])
# safety rule: with an old bulletin the first page must say "indisponível" and must not show an alert level
import leitor  # noqa: E402

leitor.HORAS_ATE_DESATUALIZADO = -1                     # pretend the bulletin is too old
app = AppTest.from_file("app.py", default_timeout=180).run()
shown = " ".join(str(m.value) for m in app.markdown)
safe = any("indisponível" in str(e.value) for e in app.error) and "Alerta VERDE" not in shown and not app.exception
failures += 0 if safe else 1
print(f"{'ok   ' if safe else 'FALHA'} boletim antigo: a página diz 'previsão indisponível' e não mostra nível")
print("APLICAÇÃO SEM ERROS" if not failures else f"{failures} ERRO(S)")
sys.exit(1 if failures else 0)
