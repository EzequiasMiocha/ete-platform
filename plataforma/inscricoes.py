"""Base de dados `subscritores`: quem quer receber os alertas no WhatsApp, em que número, onde vive e em que língua.

Uma só tabela, `subscritores`, com estas colunas:
  id               identificador da inscrição (12 letras e números)
  criado_utc       quando a pessoa se inscreveu
  nome             nome (opcional)
  telefone         número de WhatsApp em formato internacional, sem "+" (258841234567)
  lugar            bairro ou lugar escolhido (vazio = "outro lugar / não sei")
  lingua           pt, en ou fr
  sexo             mulher, homem ou vazio (prefere não dizer)
  faixa_etaria     menos_18, 18_29, 30_44, 45_59, 60_mais ou vazio
  profissao        agricultor, pescador, comerciante, ... (ver OPCOES) ou vazio
  consentimento    quando a pessoa marcou "Aceito"
  estado           activa ou removido
  boas_vindas_utc  quando recebeu a mensagem de boas-vindas (vazio = ainda não)
  removido_utc     quando pediu para sair
  ultimo_envio_utc quando recebeu o último alerta (ou fim de alerta)
  envios           quantos alertas (e fins de alerta) já recebeu
Sexo, idade e profissão são opcionais: servem para conhecer quem está a ser avisado e para juntar
um conselho próprio à mensagem (por exemplo, às pessoas com 60 anos ou mais).

Onde fica (escolhido pela definição ETE_SUBSCRITORES, no ficheiro .env ou nos segredos do Streamlit):
  "sqlite"    (por defeito) base de dados no computador: data/private/subscritores.db
              (outro caminho com ETE_SUBSCRITORES_DB). Para testes e para o computador do projecto.
  "supabase"  a mesma tabela numa base de dados na internet (Supabase, Postgres), com SUPABASE_URL e
              SUPABASE_SERVICE_KEY. É a que serve a plataforma publicada: lá o disco do servidor apaga-se.
              Criar a tabela com docs/subscritores.sql. A equipa vê a lista no painel do Supabase.
Para ver os subscritores: python scripts/ver_subscritores.py

Os números são dados pessoais:
  * nunca aparecem na plataforma, nunca vão para o repositório (GitHub) nem para o pacote `dados/`;
  * só se guarda o necessário; quem sai fica "removido" e deixa de receber no envio seguinte.
"""

from __future__ import annotations

import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

TABELA = "subscritores"
CAMPOS = ["id", "criado_utc", "nome", "telefone", "lugar", "lingua", "sexo", "faixa_etaria", "profissao", "consentimento", "estado",
          "boas_vindas_utc", "removido_utc", "ultimo_envio_utc", "envios"]
# answers offered in the form: code stored in the database -> words shown (in Portuguese; translated on screen)
OPCOES = {
    "sexo": {"mulher": "Mulher", "homem": "Homem"},
    "faixa_etaria": {"menos_18": "Menos de 18 anos", "18_29": "18 a 29 anos", "30_44": "30 a 44 anos", "45_59": "45 a 59 anos", "60_mais": "60 anos ou mais"},
    "profissao": {"agricultor": "Agricultor(a) / camponês(a)", "pescador": "Pescador(a)", "comerciante": "Comerciante / vendedor(a)", "estudante": "Estudante",
                  "professor": "Professor(a)", "saude": "Profissional de saúde", "funcionario": "Funcionário(a) público(a)",
                  "lider": "Líder comunitário(a) / autoridade local", "protecao_civil": "Protecção civil / INGD / bombeiros", "transporte": "Motorista / transportador(a)",
                  "domestico": "Trabalho doméstico", "desempregado": "Desempregado(a)", "reformado": "Reformado(a)", "outra": "Outra"},
}
NAO_DIZ = "Prefiro não dizer"
RAIZ = Path(__file__).resolve().parents[1]
BASE_LOCAL = RAIZ / "data" / "private" / "subscritores.db"


# ----------------------------------------------------------------------------- settings
def definicao(nome: str, defeito: str = "") -> str:
    """A setting from the environment or, inside the app, from Streamlit secrets."""
    if os.environ.get(nome):
        return os.environ[nome]
    try:
        import streamlit as st

        return str(st.secrets.get(nome, defeito))
    except Exception:
        return defeito


def agora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ----------------------------------------------------------------------------- phone numbers
def normalizar_telefone(texto: str) -> str | None:
    """A phone number in international form without '+' (258841234567), or None if it is not valid.

    Mozambique: 9 digits starting with 82 to 87, with or without +258 / 00258 in front.
    Other countries (family in South Africa, Eswatini...): must start with + or 00 and the country code."""
    if not texto:
        return None
    bruto = str(texto).strip()
    internacional = bruto.startswith(("+", "00"))
    digitos = re.sub(r"\D", "", bruto)
    if digitos.startswith("00"):
        digitos = digitos[2:]
    if len(digitos) == 9 and re.fullmatch(r"8[2-7]\d{7}", digitos):
        return "258" + digitos
    if digitos.startswith("258"):
        return digitos if re.fullmatch(r"2588[2-7]\d{7}", digitos) else None
    if internacional and 8 <= len(digitos) <= 15:
        return digitos
    return None


def mostrar_telefone(numero: str) -> str:
    """258841234567 -> +258 84 123 4567 (for messages to the person themselves, never on public pages)."""
    if numero.startswith("258") and len(numero) == 12:
        return f"+258 {numero[3:5]} {numero[5:8]} {numero[8:]}"
    return "+" + numero


def esconder_telefone(numero: str) -> str:
    """+258 84 *** 4567: enough to recognise a number without showing it whole."""
    texto = mostrar_telefone(numero)
    return texto[:-8] + "*** " + texto[-4:] if len(texto) > 10 else texto


# ----------------------------------------------------------------------------- the database
class BaseSQLite:
    """The `subscritores` table in a database file on this computer."""

    nome = "SQLite (neste computador)"

    def __init__(self, ficheiro: Path | str | None = None):
        self.ficheiro = Path(ficheiro or definicao("ETE_SUBSCRITORES_DB") or BASE_LOCAL)
        self.ficheiro.parent.mkdir(parents=True, exist_ok=True)
        with self._ligar() as ligacao:
            ligacao.execute(f"CREATE TABLE IF NOT EXISTS {TABELA} (" + ", ".join(f"{c} TEXT" + (" PRIMARY KEY" if c == "id" else " NOT NULL DEFAULT ''") for c in CAMPOS) + ")")
            existentes = {linha[1] for linha in ligacao.execute(f"PRAGMA table_info({TABELA})")}
            for coluna in CAMPOS:                         # a database made by an earlier version gets the new columns
                if coluna not in existentes:
                    ligacao.execute(f"ALTER TABLE {TABELA} ADD COLUMN {coluna} TEXT NOT NULL DEFAULT ''")
            ligacao.execute(f"CREATE INDEX IF NOT EXISTS {TABELA}_telefone ON {TABELA} (telefone)")
        try:
            os.chmod(self.ficheiro, 0o600)                 # only the owner of the computer account can read it
        except OSError:
            pass

    def _ligar(self):
        return sqlite3.connect(self.ficheiro, timeout=10)

    @property
    def onde(self) -> str:
        return str(self.ficheiro)

    def listar(self) -> list[dict]:
        with self._ligar() as ligacao:
            ligacao.row_factory = sqlite3.Row
            return [dict(linha) for linha in ligacao.execute(f"SELECT {', '.join(CAMPOS)} FROM {TABELA} ORDER BY criado_utc")]

    def adicionar(self, registo: dict) -> None:
        with self._ligar() as ligacao:
            ligacao.execute(f"INSERT INTO {TABELA} ({', '.join(CAMPOS)}) VALUES ({', '.join('?' for _ in CAMPOS)})", [registo.get(c, "") for c in CAMPOS])

    def actualizar(self, identificador: str, alteracoes: dict) -> None:
        colunas = [c for c in alteracoes if c in CAMPOS and c != "id"]
        with self._ligar() as ligacao:
            ligacao.execute(f"UPDATE {TABELA} SET {', '.join(f'{c} = ?' for c in colunas)} WHERE id = ?", [alteracoes[c] for c in colunas] + [identificador])


class BaseSupabase:
    """The `subscritores` table in a Supabase project (Postgres on the internet), through its REST API.
    Uses the service key, which stays on the server (Streamlit secrets, GitHub secrets, .env): the table
    has Row Level Security switched on and no public access (docs/subscritores.sql)."""

    nome = "Supabase (base de dados na internet)"

    def __init__(self, url: str | None = None, chave: str | None = None, sessao=None):
        self.url = (url or definicao("SUPABASE_URL")).rstrip("/")
        chave = chave or definicao("SUPABASE_SERVICE_KEY")
        if not self.url or not chave:
            raise RuntimeError("Faltam SUPABASE_URL e SUPABASE_SERVICE_KEY.")
        if sessao is None:
            import requests

            sessao = requests.Session()
        self.sessao = sessao
        self.cabecalhos = {"apikey": chave, "Authorization": f"Bearer {chave}", "Content-Type": "application/json"}

    @property
    def onde(self) -> str:
        return f"{self.url} (tabela {TABELA})"

    def _endereco(self, filtro: str = "") -> str:
        return f"{self.url}/rest/v1/{TABELA}{filtro}"

    def listar(self) -> list[dict]:
        resposta = self.sessao.get(self._endereco("?select=*&order=criado_utc"), headers=self.cabecalhos, timeout=30)
        resposta.raise_for_status()
        return [{c: (linha.get(c) or "") for c in CAMPOS} for linha in resposta.json()]

    def adicionar(self, registo: dict) -> None:
        self.sessao.post(self._endereco(), headers={**self.cabecalhos, "Prefer": "return=minimal"},
                         json=[{c: registo.get(c, "") for c in CAMPOS}], timeout=30).raise_for_status()

    def actualizar(self, identificador: str, alteracoes: dict) -> None:
        dados = {c: v for c, v in alteracoes.items() if c in CAMPOS and c != "id"}
        self.sessao.patch(self._endereco(f"?id=eq.{identificador}"), headers={**self.cabecalhos, "Prefer": "return=minimal"}, json=dados, timeout=30).raise_for_status()


def escolha() -> str:
    return definicao("ETE_SUBSCRITORES", "sqlite").strip().lower() or "sqlite"


def loja():
    """The `subscritores` database chosen in the settings."""
    return BaseSupabase() if escolha() == "supabase" else BaseSQLite()


def permanente() -> bool:
    """False when the list would be lost on restart (a database file on a cloud server's temporary disk)."""
    if escolha() == "supabase":
        return True
    return not str(RAIZ).startswith(("/mount/src", "/app"))      # Streamlit Community Cloud runs from /mount/src


# ----------------------------------------------------------------------------- actions used by the platform
def activas(registos: list[dict]) -> list[dict]:
    return [r for r in registos if r.get("estado") == "activa"]


def inscrever(telefone: str, lugar: str, lingua: str, nome: str = "", consentimento: bool = False, destino=None,
              sexo: str = "", faixa_etaria: str = "", profissao: str = "") -> tuple[str, str]:
    """Add a person. Returns (result, phone shown back): result is 'ok', 'ja_inscrito', 'actualizado',
    'numero_invalido' or 'sem_consentimento'. Sex, age group and occupation are optional codes from OPCOES."""
    if not consentimento:
        return "sem_consentimento", ""
    numero = normalizar_telefone(telefone)
    if not numero:
        return "numero_invalido", ""
    perfil = {"sexo": sexo if sexo in OPCOES["sexo"] else "", "faixa_etaria": faixa_etaria if faixa_etaria in OPCOES["faixa_etaria"] else "",
              "profissao": profissao if profissao in OPCOES["profissao"] else ""}
    destino = destino or loja()
    existente = next((r for r in activas(destino.listar()) if r["telefone"] == numero), None)
    if existente:
        novo = {"lugar": lugar, "lingua": lingua, **{k: v for k, v in perfil.items() if v}, **({"nome": nome.strip()[:60]} if nome.strip() else {})}
        mudancas = {k: v for k, v in novo.items() if existente.get(k, "") != v}
        if mudancas:
            destino.actualizar(existente["id"], mudancas)
            return "actualizado", mostrar_telefone(numero)
        return "ja_inscrito", mostrar_telefone(numero)
    destino.adicionar({"id": uuid.uuid4().hex[:12], "criado_utc": agora_utc(), "nome": nome.strip()[:60], "telefone": numero, "lugar": lugar,
                       "lingua": lingua, **perfil, "consentimento": agora_utc(), "estado": "activa", "boas_vindas_utc": "", "removido_utc": "",
                       "ultimo_envio_utc": "", "envios": "0"})
    return "ok", mostrar_telefone(numero)


def cancelar(telefone: str, destino=None) -> str:
    """Stop the messages to a number. Returns 'ok', 'nao_encontrado' or 'numero_invalido'."""
    numero = normalizar_telefone(telefone)
    if not numero:
        return "numero_invalido"
    destino = destino or loja()
    encontrados = [r for r in activas(destino.listar()) if r["telefone"] == numero]
    for registo in encontrados:
        destino.actualizar(registo["id"], {"estado": "removido", "removido_utc": agora_utc()})
    return "ok" if encontrados else "nao_encontrado"
