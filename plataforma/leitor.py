"""Leitura do pacote de dados da plataforma ETE (pasta `dados/` ao lado deste ficheiro).

Só precisa de pandas. A aplicação deve ler tudo através destas funções, para que uma mudança no
pacote se corrija num só sítio.

    python plataforma/leitor.py        # verifica o pacote e mostra um resumo
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DADOS = Path(__file__).resolve().parent / "dados"
HORAS_ATE_DESATUALIZADO = 36


def catalogo() -> dict:
    return json.loads((DADOS / "catalogo.json").read_text())


def camada(identificador: str) -> dict:
    """A entrada do catálogo de uma camada (título, ficheiro, legenda, limites)."""
    return next(c for c in catalogo()["camadas"] if c["id"] == identificador)


def caminho(relativo: str) -> Path:
    return DADOS / relativo


def boletim() -> dict:
    """O boletim de hoje, com a chave extra `seguro_mostrar`.

    `seguro_mostrar` é False quando a previsão está indisponível ou foi emitida há mais de 36 horas.
    Nesse caso a aplicação deve mostrar um aviso e NUNCA o nível verde."""
    dados = json.loads((DADOS / "boletim" / "boletim.json").read_text())
    estado = json.loads((DADOS / "boletim" / "estado.json").read_text())
    emitido = datetime.fromisoformat(estado["emitido_utc"])
    horas = (datetime.now(timezone.utc) - emitido).total_seconds() / 3600
    dados["estado"] = estado
    dados["horas_desde_a_emissao"] = round(horas, 1)
    dados["seguro_mostrar"] = estado.get("estado") == "ok" and horas <= HORAS_ATE_DESATUALIZADO
    dados["texto"] = (DADOS / "boletim" / "boletim.md").read_text()
    return dados


def tabela(nome: str) -> pd.DataFrame:
    """Uma tabela do boletim: previsao_alertas, cenarios_caudal, chuva_bacia, turbidez, turbidez_diaria."""
    ficheiro = DADOS / camada("boletim")["tabelas"][nome]
    return pd.read_csv(ficheiro, index_col=0) if ficheiro.exists() else pd.DataFrame()


def serie(identificador: str) -> pd.DataFrame:
    """Uma série do catálogo (tipo `serie` ou `tabela`), por exemplo `caudal_e_chuva`."""
    return pd.read_csv(DADOS / camada(identificador)["ficheiro"])


def geojson(identificador: str) -> dict:
    return json.loads((DADOS / camada(identificador)["ficheiro"]).read_text())


def imagem(identificador: str, mes: str | None = None) -> tuple[Path, list[list[float]]]:
    """Ficheiro PNG e cantos [[sul, oeste], [norte, leste]] de uma camada de imagem.
    Para camadas mensais, `mes` é "AAAA-MM" (por omissão, o mais recente)."""
    entrada = camada(identificador)
    ficheiro = entrada["ficheiro"]
    if entrada["tipo"] == "imagem_mensal":
        ficheiro = ficheiro.format(mes=mes or entrada["meses"][-1])
    return DADOS / ficheiro, entrada["cantos"]


def imagem_leve(identificador: str, mes: str | None = None) -> Path | None:
    """A imagem pequena de uma camada (com os nomes dos lugares), ou None se o pacote não a tiver.
    Para camadas mensais, `mes` é "AAAA-MM" (por omissão, o mais recente)."""
    entrada = camada(identificador)
    leve = entrada.get("mapa_leve")
    if not leve:
        return None
    ficheiro = DADOS / (leve.format(mes=mes or entrada["meses"][-1]) if entrada["tipo"] == "imagem_mensal" else leve)
    return ficheiro if ficheiro.is_file() else None


def verificar() -> list[str]:
    """Problemas encontrados no pacote (lista vazia = tudo certo)."""
    problemas = []
    for entrada in catalogo()["camadas"]:
        if entrada["tipo"] == "imagem_mensal":
            ficheiros = [entrada[k].format(mes=m) for m in entrada["meses"] for k in ("ficheiro", "mapa_leve") if entrada.get(k)]
        else:                                  # every file an entry points to: the main one, pictures that go with it, pairs of photographs
            ficheiros = [entrada[k] for k in ("ficheiro", "recorte", "sobreposicao", "foto", "foto_recorte", "mapa_leve", "imagem", "fundo", "letras", "meses") if entrada.get(k)]
            ficheiros += [par[lado]["ficheiro"] for par in entrada.get("pares", []) for lado in ("antes", "depois")]
            if entrada["tipo"] == "lugares" and (DADOS / entrada["ficheiro"]).is_file():       # the pictures of every place
                ficheiros += [f for r in json.loads((DADOS / entrada["ficheiro"]).read_text())["lugares"] for f in r["ficheiros"].values()]
            if not ficheiros:
                problemas.append(f"{entrada['id']}: não diz que ficheiro usa")
        ficheiros += list(entrada.get("tabelas", {}).values())
        for f in ficheiros:
            if not (DADOS / f).exists():
                problemas.append(f"{entrada['id']}: falta {f}")
        for campo in ("titulo", "descricao"):
            if not entrada.get(campo):
                problemas.append(f"{entrada['id']}: sem {campo}")
    return problemas


if __name__ == "__main__":
    b = boletim()
    print("camadas:", len(catalogo()["camadas"]))
    print("boletim:", b["titulo"])
    print("seguro mostrar:", b["seguro_mostrar"], f"(emitido há {b['horas_desde_a_emissao']} h)")
    print("turbidez:", tabela("turbidez")["estado"].to_dict())
    print("água, mês mais recente:", imagem("agua_mensal")[0].name)
    problemas = verificar()
    print("\n".join(problemas) if problemas else "PACOTE COMPLETO")
    raise SystemExit(1 if problemas else 0)
