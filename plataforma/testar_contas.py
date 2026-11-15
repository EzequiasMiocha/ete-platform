"""Testes das contas (contas.py), sem o navegador e numa base de dados temporária.

    cd plataforma && python testar_contas.py

Verifica: as regras do nome completo, do nome de utilizador e da senha; que a senha nunca fica guardada
(só a impressão digital); entrar, e a resposta igual para um nome ou uma senha errados; a conta fechada
10 minutos depois de 5 tentativas erradas; o código de recuperação (uma vez só); mudar a senha; manter a
sessão num aparelho (o bilhete, a validade, sair); mudar os dados; apagar a conta.
"""

import os
import sqlite3
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

BASE = Path(tempfile.mkdtemp()) / "contas_teste.db"
os.environ["ETE_SUBSCRITORES_DB"] = str(BASE)
os.environ["ETE_SUBSCRITORES"] = "sqlite"

import contas as C

falhas = 0


def verificar(nome: str, condicao: bool, detalhe: str = "") -> None:
    global falhas
    falhas += 0 if condicao else 1
    print(f"{'ok   ' if condicao else 'FALHA'} {nome}" + (f"  ({detalhe})" if detalhe and not condicao else ""))


# the rules
verificar("nome completo aceite", C.erro_no_nome("Ezequias Miocha") is None and C.erro_no_nome("Maria-José da Silva Cossa") is None)
verificar("um só nome pede o apelido", C.erro_no_nome("Ezequias") == "nome_incompleto")
verificar("nome com algarismos ou código é recusado", C.erro_no_nome("Ana 123 Cossa") == "nome_invalido" and C.erro_no_nome("<b>Ana</b> Cossa") == "nome_invalido")
verificar("nome de utilizador: letras, algarismos, ponto, hífen", C.erro_no_utilizador("ezequias.m") is None and C.erro_no_utilizador("ez") == "utilizador_invalido"
          and C.erro_no_utilizador("eze quias") == "utilizador_invalido" and C.erro_no_utilizador("joão") == "utilizador_invalido")
verificar("senha curta, comum ou com o nome é recusada", C.erro_na_senha("abc123") == "senha_curta" and C.erro_na_senha("12345678") == "senha_fraca"
          and C.erro_na_senha("ezequias2026", "ezequias") == "senha_fraca" and C.erro_na_senha("aaaaaaaaaa") == "senha_fraca")
verificar("senhas diferentes são recusadas", C.erro_na_senha("Rio-Incomati-26", "", "Rio-Incomati-27") == "senhas_diferentes")

# creating an account
resultado, dados = C.criar("Ezequias.M", "Ezequias  Miocha", "Rio-Incomati-26", "Rio-Incomati-26", "Machubo", "84 123 4567", "pt", consentimento=False)
verificar("sem aceitar, não cria", resultado == "sem_consentimento")
resultado, dados = C.criar("Ezequias.M", "Ezequias  Miocha", "Rio-Incomati-26", "Rio-Incomati-26", "Machubo", "84 123 4567", "pt", consentimento=True)
verificar("cria a conta", resultado == "ok" and dados["conta"]["utilizador"] == "ezequias.m" and dados["conta"]["nome"] == "Ezequias Miocha"
          and dados["conta"]["telefone"] == "258841234567", str(resultado))
codigo = dados.get("codigo", "")
verificar("o código de recuperação tem 12 letras e algarismos", len(codigo.replace("-", "")) == 12, codigo)
verificar("a sessão do navegador não leva a senha nem o código", "senha" not in dados["conta"] and "recuperacao" not in dados["conta"])
with sqlite3.connect(BASE) as ligacao:
    guardada = ligacao.execute("SELECT senha, recuperacao FROM contas").fetchone()
verificar("a base não guarda a senha nem o código, só a impressão digital", "Rio-Incomati-26" not in "".join(guardada) and codigo not in "".join(guardada)
          and guardada[0].startswith("scrypt$") and guardada[1].startswith("scrypt$"))
verificar("o mesmo nome de utilizador não se repete", C.criar("ezequias.m", "Outra Pessoa", "Outra-senha-99", "Outra-senha-99", consentimento=True)[0] == "utilizador_existe")
verificar("número de WhatsApp errado é recusado", C.criar("ana.cossa", "Ana Cossa", "Outra-senha-99", "Outra-senha-99", telefone="12 34", consentimento=True)[0] == "telefone_invalido")

# signing in
verificar("entra com a senha certa (sem ligar a maiúsculas no utilizador)", C.entrar("EZEQUIAS.M", "Rio-Incomati-26")[0] == "ok")
errada, inexistente = C.entrar("ezequias.m", "senha-errada-1"), C.entrar("ninguem.aqui", "senha-errada-1")
verificar("utilizador ou senha errados dão a mesma resposta", errada[0] == inexistente[0] == "errado")
for _ in range(3):
    C.entrar("ezequias.m", "senha-errada-1")
resultado, extra = C.entrar("ezequias.m", "senha-errada-1")
verificar("à 5.ª tentativa errada a conta fecha 10 minutos", resultado == "fechada" and extra.get("minutos") == 10, f"{resultado} {extra}")
verificar("fechada, nem a senha certa entra", C.entrar("ezequias.m", "Rio-Incomati-26")[0] == "fechada")
verificar("passados os 10 minutos, entra outra vez", C.entrar("ezequias.m", "Rio-Incomati-26", quando=C.agora() + timedelta(minutes=11))[0] == "ok")

# staying signed in on a device
conta_id = C.entrar("ezequias.m", "Rio-Incomati-26")[1]["conta"]["id"]
bilhete = C.abrir_sessao(conta_id)
verificar("o bilhete do aparelho abre a conta", (C.conta_da_sessao(bilhete) or {}).get("utilizador") == "ezequias.m")
with sqlite3.connect(BASE) as ligacao:
    guardados = [linha[0] for linha in ligacao.execute("SELECT token FROM sessoes")]
verificar("a base guarda só a impressão digital do bilhete", bilhete not in guardados and len(guardados) == 1)
verificar("um bilhete inventado não abre nada", C.conta_da_sessao("bilhete-inventado") is None and C.conta_da_sessao("") is None)
C.fechar_sessao(bilhete)
verificar("sair apaga o bilhete", C.conta_da_sessao(bilhete) is None)
velho = C.abrir_sessao(conta_id, dias=-1)
verificar("um bilhete fora do prazo não abre", C.conta_da_sessao(velho) is None)

# recovery, password change, data change, deletion
outro_bilhete = C.abrir_sessao(conta_id)
verificar("código de recuperação errado não muda a senha", C.recuperar("ezequias.m", "AAAA-BBBB-CCCC", "Nova-senha-Rio1", "Nova-senha-Rio1")[0] == "errado")
resultado, extra = C.recuperar("ezequias.m", codigo.lower().replace("-", " "), "Nova-senha-Rio1", "Nova-senha-Rio1")
verificar("com o código certo escolhe uma senha nova (e recebe um código novo)", resultado == "ok" and extra.get("codigo") and extra["codigo"] != codigo, resultado)
verificar("a senha nova fecha as sessões antigas", C.conta_da_sessao(outro_bilhete) is None)
verificar("o código antigo já não serve", C.recuperar("ezequias.m", codigo, "Outra-nova-Rio2", "Outra-nova-Rio2")[0] == "errado")
verificar("entra com a senha nova", C.entrar("ezequias.m", "Nova-senha-Rio1")[0] == "ok")
verificar("mudar a senha pede a senha actual", C.mudar_senha(conta_id, "senha-errada", "Mais-uma-Rio3", "Mais-uma-Rio3") == "errado"
          and C.mudar_senha(conta_id, "Nova-senha-Rio1", "Mais-uma-Rio3", "Mais-uma-Rio3") == "ok")
resultado, publica = C.actualizar_dados(conta_id, "Ezequias Arlindo Miocha", "Macaneta", "+258 85 765 4321", "en")
verificar("muda o nome, o lugar, o número e a língua", resultado == "ok" and publica["nome"] == "Ezequias Arlindo Miocha" and publica["lugar"] == "Macaneta"
          and publica["telefone"] == "258857654321" and publica["lingua"] == "en", resultado)
verificar("apagar pede a senha", C.apagar(conta_id, "senha-errada") == "errado")
bilhete = C.abrir_sessao(conta_id)
verificar("apaga a conta e as sessões", C.apagar(conta_id, "Mais-uma-Rio3") == "ok" and C.entrar("ezequias.m", "Mais-uma-Rio3")[0] == "errado"
          and C.conta_da_sessao(bilhete) is None)
with sqlite3.connect(BASE) as ligacao:
    restam = ligacao.execute("SELECT COUNT(*) FROM contas").fetchone()[0], ligacao.execute("SELECT COUNT(*) FROM sessoes").fetchone()[0]
verificar("da conta apagada não fica nada na base", restam == (0, 0), str(restam))

print("CONTAS SEM ERROS" if not falhas else f"{falhas} ERRO(S)")
sys.exit(1 if falhas else 0)
