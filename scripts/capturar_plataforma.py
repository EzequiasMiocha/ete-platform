"""Fotografar as páginas da plataforma, como se vêem num telemóvel e num computador.

    .venv/bin/python scripts/capturar_plataforma.py                          # servidor local em :8599, todas as páginas
    .venv/bin/python scripts/capturar_plataforma.py --paginas inicio agua --larguras 390
    .venv/bin/python scripts/capturar_plataforma.py --paginas "zona:Aldeia Verde"      # a página de um lugar
    .venv/bin/python scripts/capturar_plataforma.py --url https://ete-platform.streamlit.app --larguras 390

Usa o Firefox sem janela, comandado pelo geckodriver, com um perfil próprio dentro do projecto
(nunca o Firefox que está aberto). As imagens ficam em reports/plataforma/capturas/<data>/.
Cada página fotografada também diz quantas imagens não abriram e se há algo mais largo do que o ecrã.

Internet: no servidor local, só as letras do Google Fonts (cerca de 100 KB). Na aplicação publicada,
cerca de 4 MB na primeira página e menos de 1 MB em cada uma das seguintes.
"""

import argparse
import base64
import json
import os
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
PERFIL = ROOT / "reports" / "plataforma" / ".perfil_firefox"
ELEMENTO = "element-6066-11e4-a52e-4f735466cecf"       # a chave que o WebDriver usa para os elementos
PAGINAS = ["inicio", "agua", "cheias", "alertas", "sobre", "zona:Machubo"]          # zona:<lugar> é a página de um lugar

# Depois de a página carregar: imagens que não abriram e elementos mais largos do que o ecrã
VERIFICAR = """
const largura = document.documentElement.clientWidth;
const partidas = [...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.getAttribute('src').slice(0, 80));
const largos = [];
for (const e of document.querySelectorAll('[data-testid="stMain"] *')) {
  const r = e.getBoundingClientRect();
  let deslizante = false;                       // dentro de uma caixa que desliza de lado (de propósito), não conta
  for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
    const o = getComputedStyle(p).overflowX;
    if ((o === 'auto' || o === 'scroll' || o === 'hidden') && p.getBoundingClientRect().right <= largura + 2) { deslizante = true; break; }
  }
  if (!deslizante && r.width > 0 && r.right > largura + 2 && getComputedStyle(e).position !== 'fixed') {
    largos.push((e.getAttribute('data-testid') || e.className || e.tagName).toString().slice(0, 60) + ' ' + Math.round(r.right) + 'px');
  }
}
const principal = document.querySelector('[data-testid="stMain"]');
return {partidas, largos: [...new Set(largos)].slice(0, 12), altura: Math.max(document.body.scrollHeight, principal ? principal.scrollHeight : 0)};
"""


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Firefox:
    """Uma sessão WebDriver mínima (só o que é preciso para fotografar)."""

    def __init__(self, largura: int, altura: int = 900, escala: float = 1.0):
        self.escala = escala
        PERFIL.mkdir(parents=True, exist_ok=True)
        self.porta = porta_livre()
        ambiente = {"PATH": "/usr/bin:/bin:/snap/bin", "HOME": str(Path.home())}          # sem LD_LIBRARY_PATH do ambiente virtual
        self.driver = subprocess.Popen(["geckodriver", "--port", str(self.porta)], env=ambiente, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.base = f"http://127.0.0.1:{self.porta}"
        for _ in range(60):
            try:
                requests.get(self.base + "/status", timeout=1)
                break
            except requests.RequestException:
                time.sleep(0.5)
        opcoes = {"args": ["-headless", "-profile", str(PERFIL)], "prefs": {"layout.css.devPixelsPerPx": str(self.escala)}}
        r = requests.post(self.base + "/session", json={"capabilities": {"alwaysMatch": {"moz:firefoxOptions": opcoes}}}, timeout=120).json()
        if "sessionId" not in r.get("value", {}):
            self.driver.terminate()
            raise RuntimeError(f"O Firefox não arrancou: {r.get('value', {}).get('message', r)}. Se ficou um Firefox deste perfil aberto, feche-o primeiro.")
        self.sessao = f"{self.base}/session/{r['value']['sessionId']}"
        self.pid = r["value"]["capabilities"].get("moz:processID")
        self.tamanho(largura, altura)

    def tamanho(self, largura: int, altura: int) -> None:
        requests.post(self.sessao + "/window/rect", json={"width": largura, "height": altura}, timeout=30)

    def abrir(self, url: str) -> None:
        requests.post(self.sessao + "/url", json={"url": url}, timeout=180)

    def js(self, codigo: str):
        return requests.post(self.sessao + "/execute/sync", json={"script": codigo, "args": []}, timeout=60).json()["value"]

    def elemento(self, seletor: str) -> str:
        r = requests.post(self.sessao + "/element", json={"using": "css selector", "value": seletor}, timeout=30).json()["value"]
        return next(iter(r.values()))

    def dentro(self, elemento: str | None) -> None:
        """Passa a trabalhar dentro da moldura (elemento) ou volta à página de fora (None)."""
        if elemento is None:
            requests.post(self.sessao + "/frame/parent", json={}, timeout=30)
        else:
            requests.post(self.sessao + "/frame", json={"id": {ELEMENTO: elemento}}, timeout=30)

    def foto(self, destino: Path, elemento: str) -> None:
        dados = requests.get(f"{self.sessao}/element/{elemento}/screenshot", timeout=180).json()["value"]
        destino.write_bytes(base64.b64decode(dados))

    def fechar(self) -> None:
        try:
            requests.delete(self.sessao, timeout=20)
        except requests.RequestException:
            pass
        self.driver.terminate()
        if self.pid:                       # o Firefox deste perfil, se não fechou a tempo (nunca outro)
            try:
                os.kill(self.pid, 15)
            except ProcessLookupError:
                pass


def esperar_pela_aplicacao(ff: Firefox, limite: float = 90) -> None:
    """Espera que o Streamlit acabe de correr a página (e mais um pouco para as imagens e as letras)."""
    fim = time.time() + limite
    time.sleep(3)
    while time.time() < fim:
        estado = ff.js("const a = document.querySelector('[data-testid=\"stApp\"]'); return a ? a.getAttribute('data-test-script-state') : null;")
        if estado == "notRunning":
            break
        time.sleep(1)
    time.sleep(2.5)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", default="http://localhost:8599")
    p.add_argument("--paginas", nargs="*", default=PAGINAS)
    p.add_argument("--larguras", nargs="*", type=int, default=[390, 1280])
    p.add_argument("--lingua", default="pt")
    p.add_argument("--pasta", help="onde guardar (por omissão reports/plataforma/capturas/<data>)")
    p.add_argument("--clicar", nargs="*", default=[], help="textos de botões, separadores ou opções a carregar antes da fotografia, por ordem")
    p.add_argument("--sufixo", default="", help="acrescentado ao nome do ficheiro (por exemplo _passado)")
    a = p.parse_args()
    pasta = Path(a.pasta) if a.pasta else ROOT / "reports" / "plataforma" / "capturas" / datetime.now().strftime("%Y-%m-%d_%H%M")
    pasta.mkdir(parents=True, exist_ok=True)
    relatorio = {}
    for largura in a.larguras:
        # O Firefox sem janela não fica mais estreito do que 500 px: a página abre numa moldura com a largura
        # pedida, dentro de uma janela maior. Nos ecrãs estreitos, o dobro dos píxeis, como nos telemóveis.
        ff = Firefox(max(largura + 40, 520), escala=2.0 if largura < 700 else 1.0)
        try:
            for pagina in a.paginas:
                nome, _, lugar = pagina.partition(":")
                url = f"{a.url.rstrip('/')}/?p={nome}&lang={a.lingua}&convite=0" + (f"&lugar={quote(lugar)}" if lugar else "")
                ff.tamanho(max(largura + 40, 520), 1000)
                ff.abrir("data:text/html,<style>body{margin:0;background:%23888}</style>"
                         f"<iframe id='f' src='{url}' style='border:0;display:block;width:{largura}px;height:900px'></iframe>")
                moldura = ff.elemento("#f")
                ff.dentro(moldura)
                esperar_pela_aplicacao(ff)
                for texto in a.clicar:                       # carregar num botão, separador ou opção com este texto
                    alvo = json.dumps(texto)
                    ff.js("const t = " + alvo + "; const e = [...document.querySelectorAll('label[data-testid=\"stRadioOption\"], button, [data-testid=\"stTab\"]')]"
                          ".find(x => x.innerText.trim() === t || x.innerText.trim().startsWith(t)); if (e) e.click(); return !!e;")
                    esperar_pela_aplicacao(ff)
                altura = int(ff.js(VERIFICAR)["altura"])
                ff.dentro(None)
                altura = min(altura + 40, 16000)
                ff.tamanho(max(largura + 40, 520), altura + 60)
                ff.js(f"document.getElementById('f').style.height = '{altura}px';")
                time.sleep(2.5)
                ff.dentro(moldura)
                info = ff.js(VERIFICAR)
                ff.dentro(None)
                destino = pasta / f"{largura}_{pagina.replace(':', '_').replace(' ', '_')}{a.sufixo}.png"
                ff.foto(destino, moldura)
                relatorio[f"{largura}_{pagina}"] = info
                aviso = []
                if info["partidas"]:
                    aviso.append(f"{len(info['partidas'])} imagem(ns) partida(s)")
                if info["largos"]:
                    aviso.append(f"{len(info['largos'])} elemento(s) mais largo(s) do que o ecrã")
                print(f"{largura:>5} px  {pagina:<10} {info['altura']:>6} px de altura  {'; '.join(aviso) or 'ok'}", flush=True)
        finally:
            ff.fechar()
    (pasta / "relatorio.json").write_text(json.dumps(relatorio, indent=1, ensure_ascii=False))
    print(f"\nFotografias em {pasta}")


if __name__ == "__main__":
    main()
