"""Verifica, passo a passo, se o domínio da plataforma está pronto e a funcionar.

    .venv/bin/python scripts/verificar_dominio.py                   # o domínio de servidor/dominio.conf
    .venv/bin/python scripts/verificar_dominio.py --ip 1.2.3.4      # e confirma que aponta para este servidor
    .venv/bin/python scripts/verificar_dominio.py --dominio outro.co.mz

Passos: 1 registado no registo .mz (CIUEM)  2 DNS aponta para o servidor  3 http leva a https
4 certificado HTTPS válido  5 plataforma responde  6 página leve  7 logótipo.
Cada passo que falha diz o que fazer. Internet: poucos KB. Só usa a biblioteca padrão do Python.
"""

import argparse
import socket
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OK, FALHA, AVISO = "  ✓", "  ✗", "  !"


def configurado() -> str:
    for linha in (ROOT / "servidor" / "dominio.conf").read_text().splitlines():
        if linha.startswith("DOMINIO="):
            return linha.split("=", 1)[1].strip()
    return ""


def whois(dominio: str) -> str:
    with socket.create_connection(("whois.nic.mz", 43), timeout=20) as s:
        s.sendall((dominio + "\r\n").encode())
        dados = b""
        while bloco := s.recv(4096):
            dados += bloco
    return dados.decode("utf-8", "replace")


def pedir(url: str, seguir: bool = True):
    """(status, final URL, body start) without following redirects when seguir=False."""
    class SemSeguir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    abrir = urllib.request.build_opener() if seguir else urllib.request.build_opener(SemSeguir)
    try:
        with abrir.open(urllib.request.Request(url, headers={"User-Agent": "ete-verificador"}), timeout=20) as r:
            return r.status, r.geturl(), r.read(400).decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, url, "", dict(e.headers or {})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dominio", default=configurado())
    parser.add_argument("--ip", default="", help="IP do servidor, para confirmar que o DNS aponta para ele")
    args = parser.parse_args()
    d = args.dominio
    print(f"Domínio: {d}\n")
    falhas = 0

    print("1. Registo do domínio (whois.nic.mz)")
    try:
        resposta = whois(d)
        if "does not exist" in resposta or "No Object Found" in resposta:
            print(f"{FALHA} Ainda não está registado. Registe {d} num agente de registo .mz (ver docs/guia_dominio_co_mz.md).")
            return 1
        campos = {l.split(":", 1)[0].strip(): l.split(":", 1)[1].strip() for l in resposta.splitlines() if ":" in l}
        expira = campos.get("Registry Expiry Date", "")
        print(f"{OK} Registado · agente: {campos.get('Registrar', '?')} · expira: {expira[:10] or '?'}")
        servidores = [l.split(":", 1)[1].strip() for l in resposta.splitlines() if l.startswith("Name Server")]
        print(f"{OK if servidores else AVISO} Servidores de nomes: {', '.join(servidores) or 'nenhum indicado'}")
        if expira:
            dias = (datetime.fromisoformat(expira.replace("Z", "+00:00")) - datetime.now(timezone.utc)).days
            if dias < 45:
                print(f"{AVISO} O domínio expira daqui a {dias} dias: renove já (e active a renovação automática).")
    except OSError as erro:
        print(f"{AVISO} Não foi possível consultar o registo ({erro}); continua.")

    print("\n2. DNS: para onde aponta o domínio")
    ips = {}
    for nome in (d, "www." + d):
        try:
            ips[nome] = sorted({r[4][0] for r in socket.getaddrinfo(nome, 443, socket.AF_INET)})
            certo = not args.ip or args.ip in ips[nome]
            print(f"{OK if certo else FALHA} {nome} → {', '.join(ips[nome])}" + ("" if certo else f" (devia ser {args.ip})"))
            falhas += not certo
        except socket.gaierror:
            print(f"{FALHA} {nome} não aponta para lado nenhum. No painel do domínio crie um registo A: "
                  f"'{'@' if nome == d else 'www'}' → IP do servidor. Pode demorar algumas horas a propagar.")
            falhas += 1
    if d not in ips:
        return 1

    print("\n3. http:// leva para https://")
    try:
        status, _, _, cabecalhos = pedir(f"http://{d}/", seguir=False)
        destino = cabecalhos.get("Location", "")
        bom = status in (301, 302, 308) and destino.startswith("https://")
        print(f"{OK if bom else AVISO} HTTP {status}" + (f" → {destino}" if destino else "") + ("" if bom else " (o certbot do servidor/instalar.sh trata disto)"))
    except OSError as erro:
        print(f"{FALHA} O servidor não responde na porta 80 ({erro}). Está ligado? O firewall deixa passar HTTP?")
        falhas += 1

    print("\n4. Certificado HTTPS")
    try:
        contexto = ssl.create_default_context()
        with socket.create_connection((d, 443), timeout=20) as s, contexto.wrap_socket(s, server_hostname=d) as tls:
            cert = tls.getpeercert()
        fim = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        emissor = dict(x[0] for x in cert["issuer"]).get("organizationName", "?")
        dias = (fim - datetime.now(timezone.utc)).days
        print(f"{OK} Válido, emitido por {emissor}, até {fim:%d/%m/%Y} ({dias} dias; renova-se sozinho)")
    except (OSError, ssl.SSLError, ValueError) as erro:
        print(f"{FALHA} Sem HTTPS válido ({type(erro).__name__}). No servidor: sudo certbot --nginx -d {d} -d www.{d}")
        return 1

    for numero, titulo, caminho, esperado in ((5, "Plataforma", "/_stcore/health", "ok"), (6, "Página leve do boletim", "/leve/", ""),
                                             (7, "Logótipo", "/app/static/ete.png", "")):
        print(f"\n{numero}. {titulo}")
        try:
            status, _, corpo, _ = pedir(f"https://{d}{caminho}")
            bom = status == 200 and (not esperado or esperado in corpo)
            print(f"{OK if bom else FALHA} https://{d}{caminho} → HTTP {status}")
            if not bom:
                falhas += 1
                print("     No servidor: systemctl status ete-plataforma · journalctl -u ete-plataforma -n 50")
        except OSError as erro:
            print(f"{FALHA} {erro}")
            falhas += 1

    print("\n" + ("TUDO A FUNCIONAR: https://" + d if not falhas else f"{falhas} passo(s) por resolver"))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
