"""Teste dos alertas no WhatsApp, sem enviar nada nem tocar na lista verdadeira de inscritos.

    cd plataforma && python testar_alertas.py

Simula uma cheia do princípio ao fim (verde, laranja, laranja no dia seguinte, lembrete, vermelho,
verde) com inscritos de teste, e verifica: quem recebe o quê e quando; que cada alerta diz pelo
menos dois lugares, com o lugar da pessoa primeiro quando está em risco; que nada sai com um
boletim antigo; e que nenhum número de telefone fica no registo dos envios.
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import alertas_whatsapp as A
import inscricoes as I
import leitor

failures = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global failures
    failures += 0 if ok else 1
    print(f"{'ok   ' if ok else 'FALHA'} {name}" + (f"  ({detail})" if detail and not ok else ""))


class Gravador:
    """Collects the messages instead of sending them."""
    modo = "teste"

    def __init__(self):
        self.enviadas = []

    def enviar(self, numero, tipo, lingua, texto, parametros):
        self.enviadas.append((numero, tipo, lingua, texto, parametros))
        return True, ""

    def concluir(self):
        return ""


# ----------------------------------------------------------------------------- phone numbers
for escrito, esperado in [("84 123 4567", "258841234567"), ("+258 84 123 4567", "258841234567"), ("00258841234567", "258841234567"), ("258871234567", "258871234567"),
                          ("+27 82 123 4567", "27821234567"), ("12345", None), ("81 123 4567", None), ("", None), ("84 123 456", None)]:
    check(f"número '{escrito}'", I.normalizar_telefone(escrito) == esperado, f"deu {I.normalizar_telefone(escrito)}")

# ----------------------------------------------------------------------------- sign-up and leaving (temporary file)
pasta = Path(tempfile.mkdtemp())
loja = I.BaseSQLite(pasta / "subscritores.db")
check("inscrever sem consentimento é recusado", I.inscrever("84 123 4567", "Machubo", "pt", consentimento=False, destino=loja)[0] == "sem_consentimento")
check("inscrever número errado é recusado", I.inscrever("123", "Machubo", "pt", consentimento=True, destino=loja)[0] == "numero_invalido")
check("inscrever", I.inscrever("84 123 4567", "Machubo", "pt", "Ana", True, destino=loja)[0] == "ok")
check("o mesmo número outra vez não duplica", I.inscrever("+258841234567", "Machubo", "pt", consentimento=True, destino=loja)[0] == "ja_inscrito" and len(loja.listar()) == 1)
check("mudar de lugar actualiza", I.inscrever("841234567", "Mecaline", "en", consentimento=True, destino=loja)[0] == "actualizado" and loja.listar()[0]["lugar"] == "Mecaline")
I.inscrever("85 765 4321", "", "fr", consentimento=True, destino=loja)
I.inscrever("86 000 1111", "Pateque", "pt", consentimento=True, destino=loja)
check("sair", I.cancelar("86 000 1111", destino=loja) == "ok" and len(I.activas(loja.listar())) == 2)
check("sair com número desconhecido", I.cancelar("87 999 9999", destino=loja) == "nao_encontrado")



class SupabaseFalso:
    """Answers like Supabase's REST API, keeping the rows in memory."""

    def __init__(self):
        self.linhas, self.pedidos = [], []

    class R:
        def __init__(self, dados=None):
            self.dados, self.ok = dados, True

        def raise_for_status(self):
            pass

        def json(self):
            return self.dados

    def get(self, url, headers, timeout):
        self.pedidos.append(("GET", url, headers))
        return self.R([dict(l) for l in self.linhas])

    def post(self, url, headers, json, timeout):
        self.pedidos.append(("POST", url, headers))
        self.linhas += json
        return self.R()

    def patch(self, url, headers, json, timeout):
        self.pedidos.append(("PATCH", url, headers))
        ident = url.split("id=eq.")[1]
        for linha in self.linhas:
            if linha["id"] == ident:
                linha.update(json)
        return self.R()


falso = SupabaseFalso()
nuvem = I.BaseSupabase("https://exemplo.supabase.co", "chave-de-teste", sessao=falso)
check("Supabase: inscrever", I.inscrever("84 222 3333", "Machubo", "pt", consentimento=True, destino=nuvem)[0] == "ok")
check("Supabase: o mesmo número não duplica", I.inscrever("842223333", "Machubo", "pt", consentimento=True, destino=nuvem)[0] == "ja_inscrito" and len(falso.linhas) == 1)
check("Supabase: sair", I.cancelar("84 222 3333", destino=nuvem) == "ok" and falso.linhas[0]["estado"] == "removido")
check("Supabase: usa a tabela subscritores e a chave em cada pedido",
      all("/rest/v1/subscritores" in url and h["apikey"] == "chave-de-teste" for _, url, h in falso.pedidos))

# ----------------------------------------------------------------------------- a flood from start to end
base = leitor.boletim()
lugares = leitor.serie("lugares_por_ordem")
A.ESTADO = pasta / "avisos_whatsapp.json"                     # never touch the real record


def boletim(nivel: str, valido: bool = True) -> dict:
    dias = [{**d, "alerta": nivel if i >= 2 else "verde"} for i, d in enumerate(base["previsao_diaria"])]
    return {**base, "nivel_maximo_provavel": nivel, "seguro_mostrar": valido, "previsao_diaria": dias}


def correr(nivel: str, valido: bool = True, dias_depois: float = 0):
    if dias_depois and A.ESTADO.exists():                   # pretend the last message was sent N days ago
        estado = json.loads(A.ESTADO.read_text())
        estado["enviado_utc"] = (datetime.now(timezone.utc) - timedelta(days=dias_depois)).isoformat(timespec="seconds")
        A.ESTADO.write_text(json.dumps(estado))
    gravador = Gravador()
    resumo = A.executar(loja=loja, envio=gravador, boletim=boletim(nivel, valido))
    return resumo, gravador.enviadas


resumo, enviadas = correr("verde")
check("verde: só boas-vindas aos novos", [t for _, t, *_ in enviadas] == ["boas_vindas", "boas_vindas"], str([t for _, t, *_ in enviadas]))
check("boas-vindas na língua de cada um", {l for _, _, l, *_ in enviadas} == {"en", "fr"})
resumo, enviadas = correr("verde")
check("verde no dia seguinte: nada", enviadas == [])
resumo, enviadas = correr("laranja", valido=False)
check("laranja com boletim antigo: nada", enviadas == [] and resumo["decisao"] == "nada")
resumo, enviadas = correr("laranja")
check("laranja: alerta a todos", [t for _, t, *_ in enviadas] == ["alerta", "alerta"], resumo["motivo"])
texto_en = next(texto for _, _, l, texto, _ in enviadas if l == "en")
# Mecaline floods only in a large flood: at orange it is not named; at red it comes first, marked as the person's place
check("alerta laranja em inglês diz ORANGE e só lugares que alagam primeiro", "ORANGE" in texto_en and "Mecaline" not in texto_en, texto_en)
check("sem endereço da plataforma, a mensagem não mostra traços", "—" not in texto_en, texto_en)
for _, _, _, texto, parametros in enviadas:
    nomes = parametros[2].split(", ")
    check("alerta com pelo menos dois lugares", len(nomes) >= 2, parametros[2])
    check("parâmetros do modelo sem mudanças de linha", all("\n" not in p for p in parametros))
base_dicas = I.BaseSQLite(pasta / "dicas.db")
I.inscrever("84 777 0001", "Machubo", "pt", consentimento=True, destino=base_dicas, sexo="mulher", faixa_etaria="60_mais", profissao="agricultor")
I.inscrever("84 777 0002", "Machubo", "fr", consentimento=True, destino=base_dicas, profissao="pescador")
I.inscrever("84 777 0003", "Machubo", "pt", consentimento=True, destino=base_dicas, sexo="nao-existe", faixa_etaria="99")
check("respostas desconhecidas ficam vazias", base_dicas.listar()[2]["sexo"] == "" and base_dicas.listar()[2]["faixa_etaria"] == "")
textos = {p["telefone"]: A.mensagem("alerta", p, boletim("laranja"), lugares, {"laranja": "Preparação."})[0] for p in base_dicas.listar()}
check("60 anos ou mais: conselho para combinar ajuda (a idade vem antes da profissão)", "combine já com um vizinho" in textos["258847770001"] and "gado" not in textos["258847770001"])
check("pescador, em francês: não ir ao rio de barco", "en bateau" in textos["258847770002"])
check("sem perfil: só o conselho do nível", textos["258847770003"].count("Preparação.") == 1 and "vizinho" not in textos["258847770003"])
envios_antes = {p["id"]: int(p["envios"] or 0) for p in loja.listar()}
resumo, enviadas = correr("laranja")
check("laranja no dia seguinte: sem repetir", enviadas == [], resumo["motivo"])
check("cada pessoa tem o número de alertas recebidos e a data do último",
      all(int(p["envios"]) >= 1 and p["ultimo_envio_utc"] for p in I.activas(loja.listar())), str([(p["envios"], p["ultimo_envio_utc"][:10]) for p in loja.listar()]))
I.inscrever("82 555 0000", "Machubo", "pt", consentimento=True, destino=loja)
resumo, enviadas = correr("laranja")
check("quem se inscreve durante o alerta recebe boas-vindas e o alerta", [t for _, t, *_ in enviadas] == ["boas_vindas", "alerta"], str([t for _, t, *_ in enviadas]))
resumo, enviadas = correr("laranja", dias_depois=2.1)
check("laranja passados 2 dias: lembrete", len(enviadas) == 3 and resumo["motivo"].startswith("lembrete"), resumo["motivo"])
resumo, enviadas = correr("vermelho")
check("vermelho: alerta logo (subiu)", len(enviadas) == 3 and "VERMELHO" in enviadas[0][3] + enviadas[1][3] + enviadas[2][3], resumo["motivo"])
texto_en = next(texto for _, _, l, texto, _ in enviadas if l == "en")
check("alerta vermelho põe o lugar da pessoa primeiro", "flood: Mecaline (where you live)," in texto_en, texto_en)
resumo, enviadas = correr("verde")
check("verde depois do alerta: fim de alerta", [t for _, t, *_ in enviadas] == ["fim"] * 3, str([t for _, t, *_ in enviadas]))
resumo, enviadas = correr("verde")
check("verde outra vez: nada", enviadas == [])

registo = A.ESTADO.read_text()
numeros = [r["telefone"] for r in loja.listar()]
check("o registo dos envios não tem números de telefone", not any(n in registo or n[3:] in registo for n in numeros))
check("o resumo não tem números de telefone", not any(n in json.dumps(resumo) for n in numeros))

print("ALERTAS SEM ERROS" if not failures else f"{failures} ERRO(S)")
sys.exit(1 if failures else 0)
