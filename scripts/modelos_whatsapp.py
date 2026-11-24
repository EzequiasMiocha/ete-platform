"""Escreve os modelos de mensagem do WhatsApp para submeter à Meta, a partir do próprio código.

    .venv/bin/python scripts/modelos_whatsapp.py

Cria docs/modelos_whatsapp.md: para cada modelo (boas-vindas, alerta, fim de alerta) e cada língua,
o nome exacto, a categoria, o cabeçalho (imagem), o texto com as variáveis {{1}}, {{2}}..., um exemplo
de cada variável (com os números de hoje), o rodapé e os dois botões. Assim o texto aprovado é sempre
igual ao que a plataforma envia. Se um texto mudar no código, corre-se de novo e submete-se outra vez.
Não precisa de internet.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plataforma"))

import alertas_whatsapp as A  # noqa: E402
import leitor  # noqa: E402

NOMES = {"boas_vindas": "ete_boas_vindas_v2", "alerta": "ete_alerta_cheia_v2", "fim": "ete_fim_alerta_v2"}
QUANDO = {"boas_vindas": "logo depois de a pessoa se inscrever na plataforma",
          "alerta": "quando o alerta é laranja ou vermelho (e de 2 em 2 dias enquanto durar, ou logo se subir)",
          "fim": "quando o nível desce abaixo de laranja"}
LINGUAS = {"pt": "Português (pt_PT)", "en": "English (en)", "fr": "Français (fr)"}


def boletim_recente() -> dict:
    """The newest bulletin at hand: the project's own or the one GitHub published (deploy/ete-plataforma)."""
    import json

    candidatos = [ROOT / "plataforma" / "dados" / "boletim" / "boletim.json", ROOT / "deploy" / "ete-plataforma" / "plataforma" / "dados" / "boletim" / "boletim.json"]
    lidos = [json.loads(f.read_text()) for f in candidatos if f.exists()]
    return {**max(lidos, key=lambda b: b.get("emitido_utc", "")), "seguro_mostrar": True} if lidos else {**leitor.boletim(), "seguro_mostrar": True}


def modelo(tipo: str, lingua: str) -> tuple[str, list[str]]:
    """The template body with {{n}} in place of the named gaps, and an example for each variable."""
    texto = A.TEXTOS_MENSAGEM[tipo][lingua]
    for n, nome in enumerate(A.PARAMETROS[tipo], start=1):
        texto = texto.replace("{" + nome + "}", "{{" + str(n) + "}}")
    assert not re.search(r"(?<!\{)\{[a-z_]+\}(?!\})", texto), f"variável sem número em {tipo}/{lingua}"
    boletim = boletim_recente()
    if tipo == "alerta":
        boletim["nivel_maximo_provavel"] = "laranja"
    pessoa = {"nome": "Ana Cossa", "lugar": "Machubo", "lingua": lingua, "profissao": "pescador"}
    catalogo = __import__("json").loads((A.DADOS / "catalogo.json").read_text())
    _, exemplos = A.mensagem(tipo, pessoa, boletim, leitor.serie("lugares_por_ordem"), catalogo.get("conselhos", {}), A.prevista_da_cor())
    return texto, exemplos


def main():
    base = (A.ligacoes("pt")[0].split("/?")[0] or "https://ete-platform.streamlit.app").rstrip("/")
    linhas = ["# Modelos de mensagem do WhatsApp para submeter à Meta", "",
              "Gerado por `scripts/modelos_whatsapp.py` a partir de `plataforma/alertas_whatsapp.py`. Não editar à mão.", "",
              "Todos os modelos: categoria **Utility**; cabeçalho **Imagem** (o cartão de situação do dia, 1200 x 628 px, enviado pela",
              "plataforma); rodapé fixo; dois botões **Visit website** com a parte final do endereço variável.", "",
              "O botão 1 abre a página do lugar de cada pessoa (por exemplo `?p=zona&lugar=Machubo&lang=pt`); a quem não escolheu",
              "lugar, abre a primeira página. Os exemplos abaixo são os de quem não escolheu lugar.", "",
              "| Modelo | Quando sai |", "|---|---|"] + [f"| `{NOMES[t]}` | {QUANDO[t]} |" for t in NOMES] + [""]
    for tipo, nome in NOMES.items():
        linhas += [f"## `{nome}`", "", f"Sai {QUANDO[tipo]}.", ""]
        for lingua, rotulo in LINGUAS.items():
            texto, exemplos = modelo(tipo, lingua)
            linhas += [f"### {rotulo}", "", "**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).", "",
                       "**Texto (Body):**", "", "```", texto, "```", "", "**Exemplos das variáveis** (com os números de hoje):", ""]
            linhas += [f"- `{{{{{n}}}}}` ({p}): {e}" for n, (p, e) in enumerate(zip(A.PARAMETROS[tipo], exemplos), start=1)]
            botao_1, botao_2 = A.BOTOES[lingua]
            linhas += ["", f"**Rodapé (Footer):** {A.RODAPE[lingua]}", "",
                       f"**Botão 1 (Visit website, dinâmico):** «{botao_1}» → `{base}/{{{{1}}}}` · exemplo: `{A.sufixos(lingua)[0]}`",
                       f"**Botão 2 (Visit website, dinâmico):** «{botao_2}» → `{base}/{{{{1}}}}` · exemplo: `{A.sufixos(lingua)[1]}`", ""]
    (ROOT / "docs" / "modelos_whatsapp.md").write_text("\n".join(linhas) + "\n")
    cartao = A.cartao(boletim_recente(), A.prevista_da_cor(), "pt")
    if cartao:
        (ROOT / "plataforma" / "dados" / "modelos" / "exemplo_cartao_whatsapp.png").write_bytes(cartao)
    print("escrito docs/modelos_whatsapp.md e o exemplo do cartão")


if __name__ == "__main__":
    main()
