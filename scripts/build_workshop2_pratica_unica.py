"""Gera e testa a prática única do Workshop 2: um notebook para os alunos e o mesmo, resolvido, para os facilitadores.

    .venv/bin/python scripts/build_workshop2_pratica_unica.py

Escreve:
  Workshop_2/2_pratica_unica/Pratica_agua_turva.ipynb e cor_do_rio_e_mare.csv            (alunos: copiar só esta pasta)
  Workshop_2/0_facilitadores/pratica_unica/Pratica_agua_turva_FACILITADOR.ipynb e o csv  (resolvido, já corrido)

Testa como no dia: o notebook dos alunos em branco não pode dar nenhum erro e o dos facilitadores tem de dar «Certo!» em tudo.
Os textos estão em scripts/workshop2/pratica_unica.py. Não editem os notebooks à mão.
"""

import re
import shutil
import sys
from pathlib import Path

import nbformat
import pandas as pd
from nbclient import NotebookClient
from nbformat.v4 import new_notebook
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from workshop2.pratica_unica import RESPOSTAS, TITULO, fazer  # noqa: E402

WS2 = ROOT / "workshops" / "Workshop_2"
ORIGEM = WS2 / "2_pratica/dados/cor_do_rio_e_mare.csv"
ALUNOS = WS2 / "2_pratica_unica"
FAC = WS2 / "0_facilitadores/pratica_unica"
EMOJIS = re.compile("[\U0001F300-\U0001FAFF☀-➿️]")
N_VERIFICACOES = 11                         # as células verificar(...)


def referencia():
    """As mesmas contas do notebook: os números das notas dos facilitadores."""
    rio = pd.read_csv(ORIGEM)
    tr, te = rio[rio["ano"] <= 2022], rio[rio["ano"] >= 2023]
    sem, com = ["caudal_m3s", "chuva_7d_mm", "mes"], ["caudal_m3s", "chuva_7d_mm", "mes", "altura_da_mare_m"]
    criar = {"arvore": lambda: DecisionTreeClassifier(max_depth=3, random_state=42),
             "floresta": lambda: RandomForestClassifier(n_estimators=100, random_state=42),
             "boosting": lambda: GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=42)}
    nota = lambda P: {k: accuracy_score(te["turva"], f().fit(tr[P], tr["turva"]).predict(te[P])) for k, f in criar.items()}
    modelo = criar["boosting"]().fit(tr[com], tr["turva"])
    p, v = modelo.predict(te[com]), te["turva"].to_numpy()
    faixa = pd.cut(rio["altura_da_mare_m"], [-5, -0.5, 0.5, 5])
    probs = [float(modelo.predict_proba(pd.DataFrame({"caudal_m3s": [20], "chuva_7d_mm": [5], "mes": [6], "altura_da_mare_m": [m]})[com])[0, 1])
             for m in (-1, 0, 0.7)]
    exemplo = rio[(rio["data"] == "2026-01-24") & (rio["troco"] == "foz")].iloc[0]
    contexto = {"manhas": int(rio["data"].nunique()), "inicio": rio["data"].min(), "fim": rio["data"].max(),
                "por_ano": {str(a): int(n) for a, n in rio.groupby("ano")["data"].nunique().items()},
                "medianas": {k: float(v) for k, v in tr.groupby("troco")["ndti"].median().items()},
                "exemplo": {k: (exemplo[k].item() if hasattr(exemplo[k], "item") else exemplo[k])
                            for k in ("data", "troco", "caudal_m3s", "chuva_7d_mm", "altura_da_mare_m", "turva")}}
    return {**contexto, "n": len(rio), "turva": float(rio["turva"].mean()), "n_treino": len(tr), "n_teste": len(te), "sempre": float(te["turva"].mean()),
            "sem": nota(sem), "com": nota(com), "falsos": int(((v == 0) & (p == 1)).sum()), "perdidas": int(((v == 1) & (p == 0)).sum()),
            "mare": rio.groupby(faixa, observed=False)["turva"].mean().tolist(), "prob": probs}


def escrever(celulas, destino):
    nb = new_notebook(cells=celulas, metadata={"kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
                                               "language_info": {"name": "python"}})
    for i, c in enumerate(nb.cells):
        c["id"] = f"celula-{i:03d}"
    nbformat.validate(nb)
    destino.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, destino)
    return nb


def correr(nb, pasta):
    NotebookClient(nb, timeout=300, kernel_name="python3", allow_errors=True, resources={"metadata": {"path": str(pasta)}}).execute()
    erros, partes = [], []
    for i, c in enumerate(nb.cells):
        for o in c.get("outputs", []):
            if o.output_type == "error":
                erros.append(f"célula {i}: {o.ename}: {o.evalue[:150]}")
            elif o.output_type == "stream":
                partes.append(o.text)
                if o.name == "stderr":
                    erros.append(f"célula {i} (aviso): {o.text.strip()[:150]}")
    return erros, "".join(partes)


def main():
    R = referencia()
    ALUNOS.mkdir(parents=True, exist_ok=True)
    FAC.mkdir(parents=True, exist_ok=True)
    shutil.copy(ORIGEM, ALUNOS / ORIGEM.name)
    shutil.copy(ORIGEM, FAC / ORIGEM.name)
    aluno_f, fac_f = ALUNOS / "Pratica_agua_turva.ipynb", FAC / "Pratica_agua_turva_FACILITADOR.ipynb"
    aluno = escrever(fazer(False, R), aluno_f)
    resolvido = escrever(fazer(True, R), fac_f)
    falhas = [f"{f.name}: tem emojis" for f in (aluno_f, fac_f) if EMOJIS.search(f.read_text(encoding="utf-8"))]

    teste = nbformat.read(aluno_f, as_version=4)
    erros, texto = correr(teste, ALUNOS)
    falhas += [f"alunos em branco: {e}" for e in erros]
    if "PRONTO" not in texto or "Certo!" in texto:
        falhas.append("alunos em branco: devia dizer PRONTO e nenhum Certo!")
    print(f"Alunos, em branco: {len(erros)} erros; {texto.count('Ainda não')} «Ainda não», {texto.count('Falta responder')} «Falta responder»")

    erros, texto = correr(resolvido, FAC)
    falhas += [f"facilitador: {e}" for e in erros]
    esperado = N_VERIFICACOES + len(RESPOSTAS)
    if texto.count("Certo!") != esperado or "Ainda não" in texto:
        falhas.append(f"facilitador: {texto.count('Certo!')} Certo! (esperava {esperado}), {texto.count('Ainda não')} Ainda não")
    nbformat.write(resolvido, fac_f)
    print(f"Facilitador, resolvido: {len(erros)} erros; {texto.count('Certo!')} «Certo!», {texto.count('Ainda não')} «Ainda não»")
    print(f"{TITULO}: {len(aluno.cells)} células (alunos), {len(resolvido.cells)} (facilitador)")
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in R.items() if k in ("n", "n_treino", "n_teste", "sempre", "falsos", "perdidas")})
    print("sem maré", {k: round(100 * v, 1) for k, v in R["sem"].items()}, "| com maré", {k: round(100 * v, 1) for k, v in R["com"].items()})
    print("probabilidades (-1, 0, 0,7 m):", [round(100 * p) for p in R["prob"]])
    if falhas:
        print("\nFALHAS:")
        for f in falhas:
            print(" -", f)
        return 1
    print("\nPRÁTICA ÚNICA SEM ERROS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
