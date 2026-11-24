"""Corre a aula prática do Workshop 1 como um aluno e confirma que tudo funciona.

    .venv/bin/python scripts/test_workshop.py

Cada notebook corre numa cópia temporária da sua pasta (os mapas PNG que cria não sujam o material).
Verifica:
  - os notebooks de introdução, o guiado e o quadro da turma correm sem erros;
  - as 10 soluções correm sem erros e o verificador dá ✅ em todas as respostas (nenhum ❌);
  - os 10 notebooks dos estudantes, por preencher, param no primeiro ✏️ com a mensagem amigável;
  - o teste do aluno dá 20 valores com as respostas certas.
Guarda as versões executadas das soluções e do notebook guiado em 0_facilitadores/.
"""

import re
import shutil
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(__file__).resolve().parents[1]
AULA = ROOT / "workshops" / "Pratica_Workshop_1"
sys.path.insert(0, str(ROOT / "scripts"))
from workshop.extras import PERGUNTAS  # noqa: E402


def correr(notebook: Path, dados: Path | None = None, guardar: Path | None = None, alterar=None):
    """Corre o notebook numa pasta temporária (com a pasta de dados ao lado). Devolve (nb, erro)."""
    nb = nbformat.read(notebook, as_version=4)
    if alterar:
        alterar(nb)
    with tempfile.TemporaryDirectory() as tmp:
        if dados is not None and dados.exists():
            shutil.copytree(dados, Path(tmp) / "dados")
        cliente = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": tmp}})
        erro = None
        try:
            cliente.execute()
        except CellExecutionError as e:
            erro = e
    if guardar:
        guardar.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(nb, guardar)
    return nb, erro


def texto(nb) -> str:
    partes = []
    for c in nb.cells:
        for o in c.get("outputs", []):
            if o.get("output_type") == "stream":
                partes.append(o["text"])
            elif o.get("output_type") == "error":
                partes.append(f"{o['ename']}: {o['evalue']}")
    return "\n".join(partes)


def main() -> int:
    falhas = []

    def ok(condicao, nome, detalhe=""):
        print(("  OK    " if condicao else "  FALHA ") + nome + (f"  ({detalhe})" if detalhe and not condicao else ""))
        if not condicao:
            falhas.append(nome)

    print("1. Introdução ao Python")
    for nb_path in sorted((AULA / "1_introducao_python").glob("*.ipynb")):
        _, erro = correr(nb_path)
        ok(erro is None, nb_path.name, str(erro)[-300:] if erro else "")

    print("2. Aula guiada (2026)")
    nb, erro = correr(AULA / "2_aula_guiada/aula_guiada_cheia_2026.ipynb", dados=AULA / "2_aula_guiada/dados",
                      guardar=AULA / "0_facilitadores/aula_guiada_executada.ipynb")
    saida = texto(nb)
    ok(erro is None, "aula_guiada_cheia_2026.ipynb corre sem erros", str(erro)[-300:] if erro else "")
    nova = re.search(r"Água NOVA\s*:\s*(\d+) ha", saida)
    ok(nova is not None, "a aula guiada imprime a água nova", saida[-500:])
    if nova:
        print(f"        água nova 2026: {nova.group(1)} ha")

    completo = AULA / "0_facilitadores/aula_guiada_COMPLETA_facilitador.ipynb"
    nb, erro = correr(completo, dados=AULA / "2_aula_guiada/dados", guardar=completo)
    ok(erro is None and "Água NOVA" in texto(nb), "versão completa do facilitador corre e fica guardada com resultados",
       str(erro)[-300:] if erro else "")

    print("3. Exercícios: soluções e versões dos estudantes")
    for pasta in sorted((AULA / "3_exercicios").glob("ano_*")):
        ano = pasta.name[4:]
        sol = AULA / f"0_facilitadores/solucoes/solucao_{ano}.ipynb"
        nb, erro = correr(sol, dados=pasta / "dados", guardar=sol)
        saida = texto(nb)
        certos, errados = saida.count("✅"), saida.count("❌")
        ok(erro is None and certos == 5 and errados == 0, f"solução {ano}: {certos} ✅, {errados} ❌",
           str(erro)[-300:] if erro else saida[-400:])
        linha = re.search(r"QUADRO DA TURMA -> (.*)", saida)
        if linha:
            print("        " + linha.group(1))
        nb, erro = correr(pasta / f"exercicio_{ano}.ipynb", dados=pasta / "dados")
        mensagem = str(erro) if erro else ""
        ok(erro is not None and "AssertionError" in mensagem and "Volte à célula anterior" in mensagem,
           f"estudante {ano}: pára no primeiro ✏️ com a mensagem amigável", mensagem[-300:] or "não parou")
        ok("Ainda falta preencher" in texto(nb), f"estudante {ano}: o verificador avisa o que falta")

    print("4. Quadro da turma")
    for nb_path, dados in [(AULA / "3_exercicios/quadro_da_turma.ipynb", None),
                           (AULA / "0_facilitadores/solucoes/quadro_da_turma_preenchido.ipynb", None)]:
        _, erro = correr(nb_path, dados=dados, guardar=nb_path if "preenchido" in nb_path.name else None)
        ok(erro is None, nb_path.name, str(erro)[-300:] if erro else "")

    print("5. Teste do aluno")

    def responder_tudo(nb):
        for i, (_, certa, tipo, _) in enumerate(PERGUNTAS, start=1):
            valor = repr(certa) if tipo == "numero" else f'"{certa}"'
            for c in nb.cells:
                if c.cell_type == "code" and c.source.startswith(f"resposta_{i} = ..."):
                    c.source = c.source.replace(f"resposta_{i} = ...", f"resposta_{i} = {valor}", 1)

    nb, erro = correr(AULA / "4_teste_do_aluno/teste_do_aluno.ipynb", alterar=responder_tudo)
    saida = texto(nb)
    ok(erro is None and "Nota: 20 valores" in saida and saida.count("✅") == len(PERGUNTAS),
       "teste com as respostas certas dá 20 valores", saida[-400:])
    nb, erro = correr(AULA / "4_teste_do_aluno/teste_do_aluno.ipynb")
    ok(erro is None and "Ainda não respondeu" in texto(nb), "teste por responder corre sem erros")

    print()
    print("TUDO CERTO" if not falhas else f"{len(falhas)} FALHAS: " + "; ".join(falhas))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
