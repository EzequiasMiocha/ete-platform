"""Visita a plataforma publicada com um navegador a sério, para o Streamlit Community Cloud não a pôr a dormir.

O Streamlit gratuito adormece as aplicações que passam 12 horas sem visitas, e a primeira pessoa a seguir
fica à espera enquanto a aplicação acorda. O GitHub corre esta visita de 4 em 4 horas
(.github/workflows/manter_acordada.yml). Se encontrar a plataforma a dormir, carrega no botão que a acorda.
Se a plataforma não abrir no tempo dado, termina com erro: o GitHub avisa o dono do repositório por email,
e assim a equipa fica a saber que a plataforma está em baixo.

Um pedido simples (curl) não chega: só conta como visita um navegador que abre a aplicação.

Uso:
    python scripts/manter_acordada.py                          # Chrome (nos servidores do GitHub)
    python scripts/manter_acordada.py --navegador firefox --perfil reports/plataforma/.perfil_firefox
Só usa a biblioteca padrão do Python e o chromedriver ou geckodriver já instalado.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://ete-platform.streamlit.app/"

# o que a página mostra: o botão de acordar, a aplicação aberta, ou o Streamlit a preparar a aplicação
ESTADO = """
const corpo = document.body ? document.body.innerText : '';
const quadro = document.querySelector('iframe[title="streamlitApp"]');
let app = '';
try { app = quadro && quadro.contentDocument && quadro.contentDocument.body ? quadro.contentDocument.body.innerText : ''; } catch (e) {}
const direto = document.querySelector('[data-testid="stApp"]');
if (direto) app += ' ' + direto.innerText;
const botao = [...document.querySelectorAll('button')].find(b => /get this app back up/i.test(b.innerText));
if (botao) { botao.click(); return 'a dormir: carreguei no botão para a acordar'; }
if (app.includes('Eyes to Earth')) return 'aberta';
if (/oven/i.test(corpo)) return 'o Streamlit está a preparar a aplicação (in the oven)';
if (/waking up/i.test(corpo)) return 'a acordar (waking up)';
if (/longer than normal/i.test(corpo)) return 'a demorar mais do que o normal (taking longer than normal)';
if (/error|oh no/i.test(corpo + app)) return 'erro: ' + (corpo + ' ' + app).replace(/\\s+/g, ' ').slice(0, 200);
return 'a carregar';
"""


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Navegador:
    """Uma sessão WebDriver mínima, sem bibliotecas de fora."""

    def __init__(self, navegador: str, perfil: str | None):
        porta = porta_livre()
        if navegador == "chrome":
            exe = shutil.which("chromedriver") or str(Path(os.environ.get("CHROMEWEBDRIVER", "")) / "chromedriver")
            comando, ambiente = [exe, f"--port={porta}"], None
            opcoes = {"browserName": "chrome", "goog:chromeOptions": {
                "args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,900"]}}
        else:
            comando = [shutil.which("geckodriver") or "geckodriver", "--port", str(porta)]
            ambiente = {"PATH": "/usr/bin:/bin:/snap/bin", "HOME": str(Path.home())}       # sem as bibliotecas do ambiente virtual
            opcoes = {"browserName": "firefox", "moz:firefoxOptions": {"args": ["-headless"] + (["-profile", str(Path(perfil).resolve())] if perfil else [])}}
            if perfil:
                Path(perfil).mkdir(parents=True, exist_ok=True)
        self.processo = subprocess.Popen(comando, env=ambiente, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.raiz = f"http://127.0.0.1:{porta}"
        for _ in range(60):
            try:
                self._pedido("GET", "/status")
                break
            except OSError:
                time.sleep(0.5)
        resposta = self._pedido("POST", "/session", {"capabilities": {"alwaysMatch": opcoes}})
        if "sessionId" not in resposta.get("value", {}):
            self.processo.terminate()
            raise RuntimeError(f"O navegador não arrancou: {resposta.get('value')}")
        self.sessao = f"/session/{resposta['value']['sessionId']}"

    def _pedido(self, metodo: str, caminho: str, corpo: dict | None = None, espera: float = 120) -> dict:
        dados = None if corpo is None else json.dumps(corpo).encode()
        pedido = urllib.request.Request(self.raiz + caminho, data=dados, method=metodo, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=espera) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as erro:              # o WebDriver responde aos erros com um corpo em JSON
            return json.loads(erro.read() or b"{}")

    def abrir(self, url: str) -> None:
        self._pedido("POST", self.sessao + "/url", {"url": url}, espera=300)

    def js(self, codigo: str):
        return self._pedido("POST", self.sessao + "/execute/sync", {"script": codigo, "args": []}).get("value")

    def fechar(self) -> None:
        try:
            self._pedido("DELETE", self.sessao, espera=20)
        except OSError:
            pass
        self.processo.terminate()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--url", default=URL)
    p.add_argument("--navegador", choices=["chrome", "firefox"], default="chrome")
    p.add_argument("--perfil", help="pasta do perfil do Firefox (só com --navegador firefox)")
    p.add_argument("--minutos", type=float, default=10, help="quanto tempo esperar até a plataforma abrir")
    a = p.parse_args()

    inicio = time.time()
    linhas, ultimo, estado = [], None, "sem resposta"
    navegador = Navegador(a.navegador, a.perfil)
    try:
        navegador.abrir(a.url)
        while time.time() - inicio < a.minutos * 60:
            estado = navegador.js(ESTADO) or "a carregar"
            if estado != ultimo:
                linha = f"{time.time() - inicio:5.0f} s  {estado}"
                print(linha, flush=True)
                linhas.append(linha)
                ultimo = estado
            if estado == "aberta":
                time.sleep(10)                                # deixar a página correr um pouco, como uma visita normal
                break
            time.sleep(5)
    finally:
        navegador.fechar()

    aberta = estado == "aberta"
    final = (f"A plataforma está acordada: abriu em {time.time() - inicio - 10:.0f} s." if aberta
             else f"A plataforma NÃO abriu em {a.minutos:.0f} minutos. Último estado: {estado}. "
                  "Veja os registos em share.streamlit.io (Manage app) e reinicie a aplicação (Reboot app).")
    print(final)
    resumo = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumo:
        with open(resumo, "a", encoding="utf-8") as f:
            f.write(f"### {final}\n\n```\n" + "\n".join(linhas) + "\n```\n")
    return 0 if aberta else 1


if __name__ == "__main__":
    sys.exit(main())
