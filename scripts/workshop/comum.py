"""Peças comuns aos notebooks da aula prática do Workshop 1 (geradas por build_workshop_notebooks.py)."""

import base64
import json
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(__file__).resolve().parents[2]
AULA = ROOT / "workshops" / "Pratica_Workshop_1"
HA_CAMPO = 0.714          # campo de futebol de 105 m x 68 m = 7 140 m²


def fmt(valor, casas=0):
    """Número à portuguesa: espaço nos milhares e vírgula nas decimais (20 244 ou 0,09)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", " ").replace(".", ",")


def md(texto: str):
    return new_markdown_cell(texto.strip("\n"))


def code(texto: str):
    return new_code_cell(texto.strip("\n"))


def escrever(celulas, destino: Path, titulo: str = "") -> Path:
    nb = new_notebook(cells=celulas)
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["colab"] = {"name": titulo or destino.name, "provenance": []}
    destino.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, destino)
    return destino


LEGENDA = """
| Sinal | Quer dizer |
| --- | --- |
| ▶️ | Corra a célula: clique nela e prima **Shift + Enter** |
| ✏️ | Edite: troque os `...` pela sua resposta e corra outra vez |
| ✍️ | Responda por escrito, na célula de texto logo abaixo (duplo clique para escrever) |
| ✅ | A célula verifica a sua resposta |
"""

# Célula 0: as ferramentas da aula. Igual no notebook guiado e nos exercícios, para os estudantes
# reconhecerem o mesmo código. Só precisa de numpy e matplotlib (já existem no Google Colab).
FERRAMENTAS = r'''
# Célula 0 · ferramentas da aula: corra sem mudar nada ▶️
import os                          # os: trabalhar com pastas e ficheiros
import glob                        # glob: procurar ficheiros pelo nome
import numpy as np                 # numpy: contas com tabelas de números (uma imagem é uma tabela)
import matplotlib.pyplot as plt    # matplotlib: desenhar imagens e gráficos

BANDAS = ["azul", "verde", "vermelho", "nir", "swir"]


def encontrar(nome):
    """Procura um ficheiro de dados: ao lado do notebook, na pasta dados/, no Colab e no Google Drive."""
    for sitio in [nome, os.path.join("dados", nome), "/content/" + nome, "/content/dados/" + nome]:
        if os.path.exists(sitio):
            return sitio
    no_colab = os.getcwd().startswith("/content")
    bases = ["/content/drive/MyDrive"] if no_colab else [".", "..", "../.."]
    for base in bases:
        achados = glob.glob(os.path.join(base, "**", nome), recursive=True)
        if achados:
            return achados[0]
    try:
        from google.colab import files            # só existe no Google Colab
        print("Não encontrei", nome, "- escolha esse ficheiro no seu computador:")
        files.upload()
        if os.path.exists(nome):
            return nome
    except ImportError:
        pass
    raise FileNotFoundError(f"Não encontrei {nome}. Coloque-o na pasta 'dados' ao lado deste notebook.")


def carregar(nome):
    """Abre um ficheiro .npz e devolve um dicionário com as bandas em reflectância (0 a 1)."""
    z = np.load(encontrar(nome))
    img = {banda: z[banda] / 10000 for banda in BANDAS}   # guardámos números inteiros: dividir por 10 000
    img["nuvem"] = z["nuvem"]       # True onde há nuvem, sombra ou falta de dados
    img["zona"] = z["zona"]         # True dentro do distrito de Marracuene e fora do mar
    for chave in ["data", "satelite", "epoca", "data_pico"]:
        img[chave] = str(z[chave])
    for chave in ["caudal_m3s", "caudal_pico_m3s", "resolucao_m"]:
        img[chave] = float(z[chave])
    return img


def cor_natural(img, brilho=0.15):
    """Junta vermelho, verde e azul numa imagem a cores, como a veríamos de um avião."""
    rgb = np.dstack([img["vermelho"], img["verde"], img["azul"]])
    return np.clip(rgb / brilho, 0, 1)


def falsa_cor(img, brilho=0.35):
    """NIR no canal vermelho: a vegetação fica vermelha e a água fica quase preta."""
    rgb = np.dstack([img["nir"], img["vermelho"], img["verde"]])
    return np.clip(rgb / brilho, 0, 1)


print("Ferramentas prontas.")
'''


def verificador(respostas: dict) -> str:
    """Célula com as respostas de referência (codificadas, para não se lerem sem querer) e a função verificar()."""
    pacote = base64.b64encode(json.dumps(respostas, ensure_ascii=False).encode()).decode()
    return f'''
# Célula 0b · verificador de respostas: corra sem mudar nada ▶️
import base64, json
_RESPOSTAS = json.loads(base64.b64decode("{pacote}").decode())


def verificar(chave, valor):
    """Compara a sua resposta com a de referência, com uma pequena margem."""
    if valor is ...:
        print("✏️ Ainda falta preencher esta resposta (troque os ... por uma conta).")
        return False
    referencia, margem, dica = _RESPOSTAS[chave]
    if abs(float(valor) - referencia) <= margem:
        print(f"✅ Certo! {{chave}} = {{float(valor):.2f}}")
        return True
    print(f"❌ Ainda não ({{chave}} = {{float(valor):.2f}}). Dica: {{dica}}")
    return False


def preenchido(*valores):
    """Pára com uma mensagem simples se ainda houver ... por preencher numa célula anterior."""
    assert all(v is not ... for v in valores), "✏️ Volte à célula anterior e troque os ... pela sua resposta."


print("Verificador pronto.")
'''


ERROS_COMUNS = """
## Se aparecer um erro

Leia **a última linha** da mensagem vermelha. Quase sempre é um destes:

| Última linha do erro | O que quer dizer | O que fazer |
| --- | --- | --- |
| `NameError: name 'np' is not defined` | Saltou a Célula 0 | Corra a Célula 0 e depois as outras, por ordem |
| `NameError: name 'seca' is not defined` | Saltou a célula que carrega os dados | Corra as células por ordem, de cima para baixo |
| `AssertionError: ✏️ Volte à célula anterior...` | Ficaram `...` por preencher | Complete a célula ✏️ anterior |
| `FileNotFoundError: Não encontrei ...npz` | O ficheiro de dados não está ao lado do notebook | Ponha a pasta `dados` ao lado do notebook, ou carregue o ficheiro quando o Colab pedir |
| `SyntaxError` | Falta um parêntese, uma aspa ou uma vírgula | Compare a sua linha com o exemplo logo acima |
| `IndentationError` | Os espaços no início da linha estão errados | Use 4 espaços dentro de `if`, `for` e `def` |

Se nada resultar: menu **Ambiente de execução → Reiniciar e executar tudo** (Colab) ou **Kernel → Restart & Run All** (Jupyter).
"""
