"""Contas da plataforma: quem quiser guarda os seus dados (nome completo, lugar, número de WhatsApp,
língua) e entra com um nome de utilizador e uma senha. A conta é opcional: os alertas, os mapas e os
conselhos continuam abertos a todos, sem entrar.

Duas tabelas, na mesma base de dados das inscrições (inscricoes.py: SQLite neste computador, Supabase
na plataforma publicada, escolhida pela definição ETE_SUBSCRITORES; criar no Supabase com docs/contas.sql):
  contas    id, criado_utc, utilizador, nome, telefone, lugar, lingua, senha, recuperacao, falhas,
            bloqueado_ate, ultimo_acesso_utc, estado
  sessoes   token, conta, criado_utc, expira_utc

Segurança:
  * a senha nunca é guardada: guarda-se uma impressão digital feita com scrypt (16 MiB de memória, sal
    aleatório para cada conta), que não deixa voltar à senha; a comparação é feita em tempo constante;
  * depois de 5 tentativas erradas, a conta fica fechada 10 minutos; a mensagem de erro nunca diz se
    o que falhou foi o nome ou a senha;
  * o código de recuperação, mostrado uma só vez, também só fica guardado como impressão digital;
  * «manter a sessão iniciada»: o aparelho guarda um bilhete aleatório de 32 bytes (cookie, 30 dias);
    na base fica só a sua impressão digital, e sair apaga-o;
  * o nome só aceita letras, espaços, hífens, apóstrofos e pontos (nada que possa ser código numa página),
    e o nome de utilizador só letras sem acentos, algarismos, ponto, hífen e sublinhado.

    python testar_contas.py      # os testes destas regras
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import inscricoes

CAMPOS_CONTA = ["id", "criado_utc", "utilizador", "nome", "telefone", "lugar", "lingua", "senha", "recuperacao", "falhas", "bloqueado_ate",
                "ultimo_acesso_utc", "estado"]
CAMPOS_SESSAO = ["token", "conta", "criado_utc", "expira_utc"]
PUBLICOS = ["id", "criado_utc", "utilizador", "nome", "telefone", "lugar", "lingua"]       # what may stay in the browser session
TENTATIVAS, MINUTOS_FECHADA, DIAS_DE_SESSAO = 5, 10, 30
SCRYPT = {"n": 2 ** 14, "r": 8, "p": 5}               # 16 MiB, p = 5: one of the OWASP settings for scrypt
LETRAS_DO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"     # no 0/O, 1/I: easy to copy from a piece of paper
COMUNS = {"12345678", "123456789", "1234567890", "87654321", "11111111", "00000000", "password", "password1", "senha123", "senha1234",
          "qwerty123", "qwertyui", "abc12345", "abcd1234", "iloveyou", "marracuene", "incomati", "mocambique", "moçambique", "maputo123"}


# ----------------------------------------------------------------------------- where the tables are
class TabelaSQLite:
    """A table in the database file on this computer (the same file as the sign-ups)."""

    def __init__(self, nome: str, campos: list[str], chave: str, unicos: tuple[str, ...] = (), indices: tuple[str, ...] = (), ficheiro=None):
        self.nome, self.campos, self.chave = nome, campos, chave
        self.ficheiro = Path(ficheiro or inscricoes.definicao("ETE_SUBSCRITORES_DB") or inscricoes.BASE_LOCAL)
        self.ficheiro.parent.mkdir(parents=True, exist_ok=True)
        with self._ligar() as ligacao:
            ligacao.execute(f"CREATE TABLE IF NOT EXISTS {nome} (" + ", ".join(f"{c} TEXT" + (" PRIMARY KEY" if c == chave else " NOT NULL DEFAULT ''") for c in campos) + ")")
            existentes = {linha[1] for linha in ligacao.execute(f"PRAGMA table_info({nome})")}
            for coluna in campos:
                if coluna not in existentes:
                    ligacao.execute(f"ALTER TABLE {nome} ADD COLUMN {coluna} TEXT NOT NULL DEFAULT ''")
            for coluna in unicos:
                ligacao.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {nome}_{coluna} ON {nome} ({coluna})")
            for coluna in indices:
                ligacao.execute(f"CREATE INDEX IF NOT EXISTS {nome}_{coluna} ON {nome} ({coluna})")
        try:
            self.ficheiro.chmod(0o600)
        except OSError:
            pass

    def _ligar(self):
        return sqlite3.connect(self.ficheiro, timeout=10)

    def procurar(self, campo: str, valor: str) -> list[dict]:
        with self._ligar() as ligacao:
            ligacao.row_factory = sqlite3.Row
            return [dict(r) for r in ligacao.execute(f"SELECT {', '.join(self.campos)} FROM {self.nome} WHERE {campo} = ?", [valor])]

    def listar(self) -> list[dict]:
        with self._ligar() as ligacao:
            ligacao.row_factory = sqlite3.Row
            return [dict(r) for r in ligacao.execute(f"SELECT {', '.join(self.campos)} FROM {self.nome}")]

    def adicionar(self, registo: dict) -> None:
        with self._ligar() as ligacao:
            ligacao.execute(f"INSERT INTO {self.nome} ({', '.join(self.campos)}) VALUES ({', '.join('?' for _ in self.campos)})",
                            [registo.get(c, "") for c in self.campos])

    def actualizar(self, identificador: str, alteracoes: dict) -> None:
        colunas = [c for c in alteracoes if c in self.campos and c != self.chave]
        if colunas:
            with self._ligar() as ligacao:
                ligacao.execute(f"UPDATE {self.nome} SET {', '.join(f'{c} = ?' for c in colunas)} WHERE {self.chave} = ?",
                                [alteracoes[c] for c in colunas] + [identificador])

    def apagar(self, campo: str, valor: str) -> None:
        with self._ligar() as ligacao:
            ligacao.execute(f"DELETE FROM {self.nome} WHERE {campo} = ?", [valor])


class TabelaSupabase:
    """The same table in the Supabase project of the sign-ups, through its REST API, with the service key
    (it stays on the server). Row Level Security is on and there is no public access (docs/contas.sql)."""

    def __init__(self, nome: str, campos: list[str], chave: str, sessao=None, **_):
        self.nome, self.campos, self.chave = nome, campos, chave
        self.url = inscricoes.definicao("SUPABASE_URL").rstrip("/")
        segredo = inscricoes.definicao("SUPABASE_SERVICE_KEY")
        if not self.url or not segredo:
            raise RuntimeError("Faltam SUPABASE_URL e SUPABASE_SERVICE_KEY.")
        if sessao is None:
            import requests

            sessao = requests.Session()
        self.sessao = sessao
        self.cabecalhos = {"apikey": segredo, "Authorization": f"Bearer {segredo}", "Content-Type": "application/json"}

    def _endereco(self, filtro: str = "") -> str:
        return f"{self.url}/rest/v1/{self.nome}{filtro}"

    def procurar(self, campo: str, valor: str) -> list[dict]:
        resposta = self.sessao.get(self._endereco(f"?{campo}=eq.{quote(valor, safe='')}&select=*"), headers=self.cabecalhos, timeout=30)
        resposta.raise_for_status()
        return [{c: (linha.get(c) or "") for c in self.campos} for linha in resposta.json()]

    def listar(self) -> list[dict]:
        resposta = self.sessao.get(self._endereco("?select=*"), headers=self.cabecalhos, timeout=30)
        resposta.raise_for_status()
        return [{c: (linha.get(c) or "") for c in self.campos} for linha in resposta.json()]

    def adicionar(self, registo: dict) -> None:
        self.sessao.post(self._endereco(), headers={**self.cabecalhos, "Prefer": "return=minimal"},
                         json=[{c: registo.get(c, "") for c in self.campos}], timeout=30).raise_for_status()

    def actualizar(self, identificador: str, alteracoes: dict) -> None:
        dados = {c: v for c, v in alteracoes.items() if c in self.campos and c != self.chave}
        if dados:
            self.sessao.patch(self._endereco(f"?{self.chave}=eq.{quote(identificador, safe='')}"), headers={**self.cabecalhos, "Prefer": "return=minimal"},
                              json=dados, timeout=30).raise_for_status()

    def apagar(self, campo: str, valor: str) -> None:
        self.sessao.delete(self._endereco(f"?{campo}=eq.{quote(valor, safe='')}"), headers=self.cabecalhos, timeout=30).raise_for_status()


def tabelas():
    """(contas, sessoes) in the database chosen in the settings (the same as the sign-ups)."""
    classe = TabelaSupabase if inscricoes.escolha() == "supabase" else TabelaSQLite
    return (classe("contas", CAMPOS_CONTA, "id", unicos=("utilizador",), indices=("telefone",)),
            classe("sessoes", CAMPOS_SESSAO, "token", indices=("conta",)))


def permanente() -> bool:
    """False on a cloud server without the database on the internet: the accounts would be lost on restart."""
    return inscricoes.permanente()


# ----------------------------------------------------------------------------- checks
def agora() -> datetime:
    return datetime.now(timezone.utc)


def normalizar_utilizador(texto: str) -> str:
    return str(texto or "").strip().lower()


def erro_no_utilizador(utilizador: str) -> str | None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,29}", utilizador):
        return "utilizador_invalido"
    return None


def limpar_nome(nome: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(nome or "")).strip())


def erro_no_nome(nome: str) -> str | None:
    """A full name: at least two words of two letters or more (name and surname), made only of letters,
    spaces, hyphens, apostrophes and dots, starting with a letter."""
    nome = limpar_nome(nome)
    if not 5 <= len(nome) <= 80 or not nome[0].isalpha() or re.search(r"[^\w .'’-]|[\d_]", nome):
        return "nome_invalido"
    if len([p for p in nome.split(" ") if sum(letra.isalpha() for letra in p) >= 2]) < 2:
        return "nome_incompleto"
    return None


def erro_na_senha(senha: str, utilizador: str = "", repetida: str | None = None) -> str | None:
    senha = str(senha or "")
    if repetida is not None and senha != repetida:
        return "senhas_diferentes"
    if len(senha) < 8:
        return "senha_curta"
    if len(senha) > 128:
        return "senha_longa"
    if senha.lower() in COMUNS or len(set(senha)) <= 2 or (utilizador and utilizador in senha.lower()):
        return "senha_fraca"
    return None


# ----------------------------------------------------------------------------- secrets kept only as fingerprints
def impressao(segredo: str) -> str:
    sal = secrets.token_bytes(16)
    digital = hashlib.scrypt(segredo.encode("utf-8"), salt=sal, dklen=32, maxmem=64 * 1024 * 1024, **SCRYPT)
    return "scrypt${n}${r}${p}${sal}${dig}".format(**SCRYPT, sal=base64.b64encode(sal).decode(), dig=base64.b64encode(digital).decode())


def confere(segredo: str, guardada: str) -> bool:
    try:
        nome, n, r, p, sal, digital = guardada.split("$")
        if nome != "scrypt":
            return False
        calculada = hashlib.scrypt(str(segredo).encode("utf-8"), salt=base64.b64decode(sal), n=int(n), r=int(r), p=int(p), dklen=32, maxmem=64 * 1024 * 1024)
        return hmac.compare_digest(calculada, base64.b64decode(digital))
    except (ValueError, TypeError):
        return False


_FALSA = impressao("senha que ninguém tem")             # compared when the user does not exist, so both answers take as long


def novo_codigo() -> str:
    """A recovery code such as K7QX-M2PA-9TRD (60 bits), easy to copy from paper."""
    letras = "".join(secrets.choice(LETRAS_DO_CODIGO) for _ in range(12))
    return f"{letras[:4]}-{letras[4:8]}-{letras[8:]}"


def _codigo_limpo(codigo: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(codigo or "").upper())


def _digital_do_bilhete(bilhete: str) -> str:
    return hashlib.sha256(str(bilhete).encode("utf-8")).hexdigest()


def publica(conta: dict) -> dict:
    """The fields of an account that may be kept in the browser session (never the fingerprints)."""
    return {c: conta.get(c, "") for c in PUBLICOS}


def _activa(contas, utilizador: str) -> dict | None:
    return next((c for c in contas.procurar("utilizador", utilizador) if c.get("estado") == "activa"), None)


def _fechada(conta: dict, quando: datetime) -> int:
    """Minutes the account stays closed after too many wrong attempts (0 = open)."""
    try:
        fim = datetime.fromisoformat(conta.get("bloqueado_ate") or "")
    except ValueError:
        return 0
    return max(0, int((fim - quando).total_seconds() // 60) + 1) if fim > quando else 0


def _tentativa_errada(contas, conta: dict, quando: datetime) -> str:
    falhas = int(conta.get("falhas") or 0) + 1
    if falhas >= TENTATIVAS:
        contas.actualizar(conta["id"], {"falhas": "0", "bloqueado_ate": (quando + timedelta(minutes=MINUTOS_FECHADA)).isoformat(timespec="seconds")})
        return "fechada"
    contas.actualizar(conta["id"], {"falhas": str(falhas)})
    return "errado"


# ----------------------------------------------------------------------------- what the platform does with accounts
def criar(utilizador: str, nome: str, senha: str, repetida: str, lugar: str = "", telefone: str = "", lingua: str = "pt",
          consentimento: bool = False, base=None) -> tuple[str, dict]:
    """Open an account. Returns (result, {"conta": public fields, "codigo": recovery code shown once}).
    Results: ok, sem_consentimento, utilizador_invalido, utilizador_existe, nome_invalido, nome_incompleto,
    telefone_invalido, senhas_diferentes, senha_curta, senha_longa, senha_fraca."""
    if not consentimento:
        return "sem_consentimento", {}
    utilizador = normalizar_utilizador(utilizador)
    nome = limpar_nome(nome)
    erro = erro_no_utilizador(utilizador) or erro_no_nome(nome) or erro_na_senha(senha, utilizador, repetida)
    if erro:
        return erro, {}
    numero = ""
    if str(telefone or "").strip():
        numero = inscricoes.normalizar_telefone(telefone) or ""
        if not numero:
            return "telefone_invalido", {}
    contas, _ = base or tabelas()
    if contas.procurar("utilizador", utilizador):
        return "utilizador_existe", {}
    codigo = novo_codigo()
    registo = {"id": secrets.token_hex(8), "criado_utc": agora().isoformat(timespec="seconds"), "utilizador": utilizador, "nome": nome, "telefone": numero,
               "lugar": str(lugar or "")[:80], "lingua": lingua if lingua in ("pt", "en", "fr") else "pt", "senha": impressao(senha),
               "recuperacao": impressao(_codigo_limpo(codigo)), "falhas": "0", "bloqueado_ate": "", "ultimo_acesso_utc": agora().isoformat(timespec="seconds"),
               "estado": "activa"}
    try:
        contas.adicionar(registo)
    except Exception:
        if contas.procurar("utilizador", utilizador):     # created at the same moment by someone else
            return "utilizador_existe", {}
        raise
    return "ok", {"conta": publica(registo), "codigo": codigo}


def entrar(utilizador: str, senha: str, base=None, quando: datetime | None = None) -> tuple[str, dict]:
    """Sign in. Results: ok (with the public fields), errado (never says what was wrong), fechada (with minutes)."""
    quando = quando or agora()
    contas, _ = base or tabelas()
    conta = _activa(contas, normalizar_utilizador(utilizador))
    if conta is None:
        confere(str(senha), _FALSA)
        return "errado", {}
    minutos = _fechada(conta, quando)
    if minutos:
        return "fechada", {"minutos": minutos}
    if not confere(str(senha), conta.get("senha", "")):
        resultado = _tentativa_errada(contas, conta, quando)
        return resultado, ({"minutos": MINUTOS_FECHADA} if resultado == "fechada" else {})
    contas.actualizar(conta["id"], {"falhas": "0", "bloqueado_ate": "", "ultimo_acesso_utc": quando.isoformat(timespec="seconds")})
    return "ok", {"conta": publica(conta)}


def recuperar(utilizador: str, codigo: str, nova: str, repetida: str, base=None, quando: datetime | None = None) -> tuple[str, dict]:
    """A new password with the recovery code; the code is then replaced by a new one (shown once).
    Results: ok (with the new code), errado, fechada, and the password checks of criar()."""
    quando = quando or agora()
    contas, sessoes = base or tabelas()
    utilizador = normalizar_utilizador(utilizador)
    conta = _activa(contas, utilizador)
    if conta is None:
        confere(_codigo_limpo(codigo), _FALSA)
        return "errado", {}
    minutos = _fechada(conta, quando)
    if minutos:
        return "fechada", {"minutos": minutos}
    if not confere(_codigo_limpo(codigo), conta.get("recuperacao", "")):
        resultado = _tentativa_errada(contas, conta, quando)
        return resultado, ({"minutos": MINUTOS_FECHADA} if resultado == "fechada" else {})
    erro = erro_na_senha(nova, utilizador, repetida)
    if erro:
        return erro, {}
    codigo_novo = novo_codigo()
    contas.actualizar(conta["id"], {"senha": impressao(nova), "recuperacao": impressao(_codigo_limpo(codigo_novo)), "falhas": "0", "bloqueado_ate": ""})
    sessoes.apagar("conta", conta["id"])                 # every device signs in again with the new password
    return "ok", {"codigo": codigo_novo}


def _conta_por_id(contas, identificador: str) -> dict | None:
    return next((c for c in contas.procurar("id", identificador) if c.get("estado") == "activa"), None)


def mudar_senha(identificador: str, actual: str, nova: str, repetida: str, base=None) -> str:
    """ok, errado (the current password is wrong), or the password checks of criar(). Other devices are signed out."""
    contas, sessoes = base or tabelas()
    conta = _conta_por_id(contas, identificador)
    if conta is None or not confere(str(actual), conta.get("senha", "")):
        return "errado"
    erro = erro_na_senha(nova, conta.get("utilizador", ""), repetida)
    if erro:
        return erro
    contas.actualizar(identificador, {"senha": impressao(nova)})
    sessoes.apagar("conta", identificador)
    return "ok"


def actualizar_dados(identificador: str, nome: str, lugar: str, telefone: str, lingua: str, base=None) -> tuple[str, dict]:
    """Change the name, place, phone or language. Returns (ok | nome_invalido | nome_incompleto | telefone_invalido, public fields)."""
    contas, _ = base or tabelas()
    conta = _conta_por_id(contas, identificador)
    if conta is None:
        return "errado", {}
    nome = limpar_nome(nome)
    erro = erro_no_nome(nome)
    if erro:
        return erro, {}
    numero = ""
    if str(telefone or "").strip():
        numero = inscricoes.normalizar_telefone(telefone) or ""
        if not numero:
            return "telefone_invalido", {}
    alteracoes = {"nome": nome, "lugar": str(lugar or "")[:80], "telefone": numero, "lingua": lingua if lingua in ("pt", "en", "fr") else "pt"}
    contas.actualizar(identificador, alteracoes)
    return "ok", publica({**conta, **alteracoes})


def apagar(identificador: str, senha: str, base=None) -> str:
    """Delete the account and its sessions for good (the password confirms it). ok or errado."""
    contas, sessoes = base or tabelas()
    conta = _conta_por_id(contas, identificador)
    if conta is None or not confere(str(senha), conta.get("senha", "")):
        return "errado"
    sessoes.apagar("conta", identificador)
    contas.apagar("id", identificador)
    return "ok"


# ----------------------------------------------------------------------------- staying signed in on a device
def abrir_sessao(identificador: str, base=None, dias: int = DIAS_DE_SESSAO) -> str:
    """A new random ticket for the device (only its fingerprint is stored). Returns the ticket."""
    _, sessoes = base or tabelas()
    bilhete = secrets.token_urlsafe(32)
    sessoes.adicionar({"token": _digital_do_bilhete(bilhete), "conta": identificador, "criado_utc": agora().isoformat(timespec="seconds"),
                       "expira_utc": (agora() + timedelta(days=dias)).isoformat(timespec="seconds")})
    return bilhete


def bilhete_valido(bilhete) -> bool:
    """A ticket made by abrir_sessao: 43 URL-safe characters (anything else is not looked up)."""
    return isinstance(bilhete, str) and re.fullmatch(r"[A-Za-z0-9_-]{40,60}", bilhete) is not None


def conta_da_sessao(bilhete: str, base=None) -> dict | None:
    """The public fields of the account of a device ticket, or None if it is unknown, expired or the account is gone."""
    if not bilhete_valido(bilhete):
        return None
    contas, sessoes = base or tabelas()
    digital = _digital_do_bilhete(bilhete)
    sessao = next(iter(sessoes.procurar("token", digital)), None)
    if sessao is None:
        return None
    try:
        valida = datetime.fromisoformat(sessao["expira_utc"]) > agora()
    except ValueError:
        valida = False
    conta = _conta_por_id(contas, sessao["conta"]) if valida else None
    if conta is None:
        sessoes.apagar("token", digital)
        return None
    return publica(conta)


def fechar_sessao(bilhete: str, base=None) -> None:
    if bilhete:
        _, sessoes = base or tabelas()
        sessoes.apagar("token", _digital_do_bilhete(bilhete))
