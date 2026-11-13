"""Ver a base de dados `subscritores` (quem pediu os alertas no WhatsApp). Só para a equipa.

    .venv/bin/python scripts/ver_subscritores.py               # onde está a base, totais e últimas inscrições
    .venv/bin/python scripts/ver_subscritores.py --completo    # mostra os números inteiros
    .venv/bin/python scripts/ver_subscritores.py --excel       # ficheiro Excel com todas as variáveis, resumo e envios:
                                                                 #   data/private/subscritores_AAAA-MM-DD.xlsx
    .venv/bin/python scripts/ver_subscritores.py --exportar    # guarda uma cópia em data/private/subscritores_AAAA-MM-DD.csv

Usa a mesma base que a plataforma (definição ETE_SUBSCRITORES no .env: sqlite ou supabase).
Os números são dados pessoais: não partilhar o resultado nem a cópia exportada.
"""

import csv
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plataforma"))
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

import inscricoes as I  # noqa: E402

base = I.loja()
todos = base.listar()
activos = I.activas(todos)
completo = "--completo" in sys.argv
print(f"Base de dados: {base.nome}\nOnde:          {base.onde}\nTabela:        {I.TABELA}\n")
print(f"Subscritores activos: {len(activos)}   ·   removidos: {len(todos) - len(activos)}   ·   à espera das boas-vindas: "
      f"{sum(1 for r in activos if not r['boas_vindas_utc'])}\n")
if activos:
    print("Por lugar:   " + ", ".join(f"{lugar or 'outro / não sabe'} {n}" for lugar, n in Counter(r["lugar"] for r in activos).most_common()))
    for campo, titulo in (("sexo", "Por sexo:    "), ("faixa_etaria", "Por idade:   "), ("profissao", "Por ocupação:")):
        print(titulo + " " + ", ".join(f"{I.OPCOES[campo].get(v, I.NAO_DIZ)} {n}" for v, n in Counter(r[campo] for r in activos).most_common()))
    print("Por língua:  " + ", ".join(f"{l} {n}" for l, n in Counter(r["lingua"] for r in activos).most_common()) + "\n")
    print("Últimas inscrições:")
    for r in activos[-10:]:
        numero = I.mostrar_telefone(r["telefone"]) if completo else I.esconder_telefone(r["telefone"])
        print(f"  {r['criado_utc'][:10]}  {numero:18s}  {r['lugar'] or '-':22s}  {r['lingua']}  {r['nome']}  · alertas recebidos: {r['envios'] or 0}")
if "--exportar" in sys.argv:
    destino = ROOT / "data" / "private" / f"subscritores_{date.today()}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=I.CAMPOS)
        escritor.writeheader()
        escritor.writerows(todos)
    destino.chmod(0o600)
    print(f"\nCópia guardada em {destino.relative_to(ROOT)} (dados pessoais: não partilhar).")
if "--excel" in sys.argv:
    import relatorio_subscritores as R

    destino = R.exportar(todos, ROOT / "data" / "private" / f"subscritores_{date.today()}.xlsx", R.historico_de_envios(), base.onde)
    print(f"\nExcel guardado em {destino.relative_to(ROOT)} (dados pessoais: só para a equipa).")
