"""Testa todas as aulas do Workshop 2: corre cada notebook do princípio ao fim e diz se há erros.

Correr na pasta Workshop_2, com o Python do ambiente:

    jupyter_env/bin/python testar_aulas.py

Os notebooks originais não são alterados: o teste trabalha numa cópia temporária, que apaga no fim.
Demora cerca de 1 minuto e não usa a Internet.

O que é verificado:
- todos os notebooks correm sem erros e sem avisos (alunos, preparação, teste do aluno e aulas resolvidas);
- o 0_verificar_computador diz "PRONTO PARA AS AULAS";
- nas práticas resolvidas, todas as verificações dizem «Certo!» (nenhum «Ainda não»);
- a Prática 1 resolvida funciona com o ano de cada par (2014, 2021, 2022, 2024 e 2025).
"""

import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import nbformat
    from nbclient import NotebookClient
except ImportError:
    sys.exit("Este Python não tem o Jupyter. Corram com o Python do ambiente:  jupyter_env/bin/python testar_aulas.py")

AQUI = Path(__file__).resolve().parent
PASTAS = ["2_pratica_unica", "0_facilitadores/pratica_unica", "2_pratica", "1_preparacao_python", "3_teste_do_aluno",
          "0_facilitadores/aulas_resolvidas"]
ANOS_DOS_PARES = [2014, 2021, 2022, 2024, 2025]
PRATICA_1 = "0_facilitadores/aulas_resolvidas/1_Pratica_a_agua_no_vosso_ano_RESOLVIDA.ipynb"


def correr(nb, pasta):
    """Corre o notebook na pasta dele e devolve (erros, avisos, texto mostrado, número de figuras)."""
    cliente = NotebookClient(nb, kernel_name="python3", timeout=600, allow_errors=True,
                             resources={"metadata": {"path": str(pasta)}})
    cliente.execute(stderr=subprocess.DEVNULL)      # esconde as mensagens internas do kernel no terminal
    erros, avisos, texto, figuras = [], [], [], 0
    for i, celula in enumerate(nb.cells):
        for saida in celula.get("outputs", []):
            if saida.output_type == "error":
                erros.append(f"célula {i}: {saida.ename}: {saida.evalue[:200]}")
            elif saida.output_type == "stream":
                texto.append(saida.text)
                if saida.name == "stderr":
                    avisos.append(f"célula {i}: {saida.text.strip()[:200]}")
            else:
                dados = saida.get("data", {})
                figuras += "image/png" in dados
                texto.append(dados.get("text/plain", ""))
    return erros, avisos, "\n".join(texto), figuras


def main():
    print("Python em uso:", sys.executable)
    problemas, n = [], 0
    with tempfile.TemporaryDirectory(prefix="teste_workshop2_") as tmp:
        copia = Path(tmp) / "Workshop_2"
        shutil.copytree(AQUI, copia, ignore=shutil.ignore_patterns("jupyter_env", ".ipynb_checkpoints", "*.pdf", "*.zip"))
        for pasta in PASTAS:
            if not (copia / pasta).is_dir():
                print(f"\n(sem a pasta {pasta}: não testada)")
                continue
            print(f"\n{pasta}/")
            for caminho in sorted((copia / pasta).glob("*.ipynb")):
                t0 = time.time()
                nb = nbformat.read(caminho, as_version=4)
                erros, avisos, texto, figuras = correr(nb, caminho.parent)
                falhas = erros + avisos
                if caminho.name == "0_verificar_computador.ipynb" and "PRONTO PARA AS AULAS" not in texto:
                    falhas.append("não disse PRONTO PARA AS AULAS")
                if ("RESOLVIDA" in caminho.name or "FACILITADOR" in caminho.name) and "Pratica" in caminho.name:
                    if "Ainda não" in texto or "Certo!" not in texto:
                        falhas.append(f"verificações: {texto.count('Certo!')} Certo!, {texto.count('Ainda não')} Ainda não")
                n += 1
                estado = "ERRO " if falhas else "OK   "
                extra = f", {texto.count('Certo!')} Certo!" if "Certo!" in texto else ""
                fig = f"{figuras} figura" + ("" if figuras == 1 else "s")
                print(f"  {estado} {caminho.name}  ({time.time() - t0:.0f} s, {fig}{extra})")
                for f in falhas:
                    print("        ", f)
                problemas += [f"{pasta}/{caminho.name}: {f}" for f in falhas]

        if (copia / PRATICA_1).exists():
            print("\nPrática 1 resolvida com o ano de cada par:")
            for ano in ANOS_DOS_PARES:
                nb = nbformat.read(copia / PRATICA_1, as_version=4)
                for celula in nb.cells:
                    if celula.cell_type == "code" and celula.source.lstrip().startswith("ANO = "):
                        celula.source = re.sub(r"ANO = \d+", f"ANO = {ano}", celula.source, count=1)
                erros, avisos, texto, _ = correr(nb, (copia / PRATICA_1).parent)
                falhas = erros + avisos
                if "Ainda não" in texto or "Certo!" not in texto:
                    falhas.append(f"verificações: {texto.count('Certo!')} Certo!, {texto.count('Ainda não')} Ainda não")
                regra = next((linha.strip() for linha in texto.splitlines() if "<=" in linha), "")
                print(f"  {'ERRO ' if falhas else 'OK   '} {ano}  ({texto.count('Certo!')} Certo!, primeira regra: {regra})")
                for f in falhas:
                    print("        ", f)
                problemas += [f"Prática 1 com {ano}: {f}" for f in falhas]

    print()
    if problemas:
        print(f"HÁ PROBLEMAS EM {len(problemas)} SÍTIOS:")
        for p in problemas:
            print("  -", p)
        return 1
    print(f"TODAS AS AULAS CORREM SEM ERROS ({n} notebooks, e a Prática 1 com os {len(ANOS_DOS_PARES)} anos dos pares).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
