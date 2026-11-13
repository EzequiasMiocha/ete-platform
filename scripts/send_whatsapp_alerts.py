"""Alertas de cheia no WhatsApp para as pessoas inscritas (corre depois do boletim; o pipeline diário já o chama).

    .venv/bin/python scripts/send_whatsapp_alerts.py            # decide e envia
    .venv/bin/python scripts/send_whatsapp_alerts.py --ensaio   # mostra o que faria, sem enviar nem gravar nada

Com WHATSAPP_TOKEN e WHATSAPP_PHONE_ID definidos (ficheiro .env ou segredos do GitHub), envia pela API
oficial do WhatsApp. Sem eles, prepara o "envio assistido": uma página em data/private/caixa_de_saida/
com um botão por pessoa. Explicação completa e textos dos modelos para a Meta: docs/alertas_whatsapp.md.
Custo de internet: poucos KB por mensagem.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plataforma"))
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

import yaml  # noqa: E402

import alertas_whatsapp as A  # noqa: E402


class Ensaio:
    """Shows each message instead of sending it."""
    modo = "ensaio"

    def enviar(self, numero, tipo, lingua, texto, parametros):
        print(f"--- {tipo} · {lingua} · +{numero[:6]}…\n{texto}\n")
        return True, ""

    def concluir(self):
        return ""


def opcoes() -> dict:
    cfg = yaml.safe_load((ROOT / "config" / "config.yaml").read_text()).get("whatsapp", {})
    return {"niveis": cfg.get("niveis_que_avisam", ["laranja", "vermelho"]), "lembrar_dias": cfg.get("lembrar_a_cada_dias", 2)}


def correr(ensaio: bool = False) -> dict:
    return A.executar(**opcoes(), envio=Ensaio() if ensaio else None, gravar_estado=not ensaio)


if __name__ == "__main__":
    resumo = correr("--ensaio" in sys.argv)
    print(json.dumps(resumo, indent=1, ensure_ascii=False))
