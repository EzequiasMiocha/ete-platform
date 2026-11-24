"""Publicar a plataforma com um só comando: GitHub (e, a partir daí, o Streamlit Cloud e a página leve).

    .venv/bin/python scripts/publicar_plataforma.py                     # publica o que mudou no projecto
    .venv/bin/python scripts/publicar_plataforma.py -m "Página nova"    # com uma mensagem própria
    .venv/bin/python scripts/publicar_plataforma.py --verificar         # só remonta e verifica; não envia nada

O que faz, por ordem:
  1. Liga-se ao GitHub com a chave de publicação (~/.ssh/ete_github_deploy, nome curto «github-ete» em
     ~/.ssh/config). Na primeira vez descobre sozinho o repositório (a chave só abre um) e guarda-o.
  2. Traz o que está publicado, com os boletins que o GitHub guardou todos os dias.
  3. Remonta o pacote deploy/ete-plataforma a partir do projecto (scripts/build_deploy_repo.py).
  4. Verifica como o GitHub: o pacote de dados está completo e todas as páginas abrem nas três línguas.
     Se alguma coisa falhar, pára e não envia nada.
  5. Regista e envia. O Streamlit Cloud actualiza a aplicação sozinho (1 a 2 minutos).

Internet: só o que mudou (na primeira vez, cerca de 8 MB). Nunca envia o .env nem a lista de inscritos.
Com a internet fraca, desiste ao fim de algum tempo em vez de ficar pendurado, e diz o que aconteceu.
O pacote é gerado: as alterações fazem-se no projecto (plataforma/, src/, config/), não em deploy/.
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACOTE = ROOT / "deploy" / "ete-plataforma"           # a pasta do pacote neste computador
REPOSITORIO = "ete-platform"                          # o nome do repositório no GitHub (o do guia)
CHAVE = Path.home() / ".ssh" / "ete_github_deploy"
ALIAS = "github-ete"                                  # o «Host» de ~/.ssh/config que usa a chave de publicação
PY = sys.executable
SEM_REDE = ("tempo esgotado", "could not resolve", "timed out", "network is unreachable", "connection refused",
            "connection reset", "connection closed", "broken pipe")
MSG_SEM_REDE = "Não consegui falar com o GitHub (internet lenta ou em baixo). Nada foi enviado. Tente mais tarde."


def correr(comando, pasta=PACOTE, mostrar=False, limite=None):
    """Corre um comando. «limite»: segundos até desistir, para a internet fraca não deixar tudo pendurado."""
    try:
        r = subprocess.run(comando, cwd=pasta, capture_output=True, text=True, timeout=limite)
    except subprocess.TimeoutExpired:
        r = subprocess.CompletedProcess(comando, 124, "", f"tempo esgotado ao fim de {limite} s")
    if mostrar and (r.stdout or r.stderr):
        print((r.stdout + r.stderr).rstrip())
    return r


def git(*args, limite=None):
    return correr(["git", *args], limite=limite)


def parar(mensagem, codigo=1):
    print("\n" + mensagem)
    sys.exit(codigo)


def sem_internet(texto):
    return any(s in texto.lower() for s in SEM_REDE)


def repositorio_da_chave():
    """Pergunta ao GitHub que repositório esta chave abre. Devolve ('conta/repositorio' ou None, a resposta do GitHub)."""
    r = correr(["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", f"git@{ALIAS}"], limite=60)
    resposta = r.stdout + r.stderr
    m = re.search(r"Hi ([^!\s]+)!", resposta)
    if not m:
        return None, resposta
    nome = m.group(1)
    return (nome if "/" in nome else f"{nome}/{REPOSITORIO}"), resposta   # chave de conta: o repositório tem o nome do guia


def instrucoes_github():
    publica = CHAVE.with_suffix(".pub").read_text().strip() if CHAVE.with_suffix(".pub").exists() else "(chave em falta)"
    return f"""O GitHub ainda não aceita a chave de publicação. Com a conta da equipa, em https://github.com:
  1. New repository: nome «{REPOSITORIO}», Public, sem README nem .gitignore nem licença; Create repository.
  2. No repositório: Settings > Deploy keys > Add deploy key. Title: «computador do projecto».
     Key: cole esta linha inteira e marque «Allow write access»:
     {publica}
Depois volte a correr este comando."""


def explicar_recusa(erro):
    """O que dizer quando o GitHub recusa o envio («erro» é o que o git escreveu)."""
    e = erro.lower()
    if "read only" in e or "denied" in e:
        return ("O GitHub não deixa esta chave escrever. No repositório, em Settings > Deploy keys, apague a chave (Delete) "
                "e adicione-a de novo com «Allow write access» marcado. Depois volte a correr este comando.")
    if "gh007" in e or "email privacy" in e:
        return ("O GitHub recusou porque a sua conta esconde o e-mail que está nos registos. Em github.com, Settings > Emails, "
                "desmarque «Block command line pushes that expose my email» e volte a correr este comando.")
    if "fetch first" in e or "non-fast-forward" in e:
        return ("O envio foi recusado: o GitHub guardou um boletim entretanto. Volte a correr este comando "
                "(ele traz o boletim primeiro e publica a seguir).")
    if sem_internet(e):
        return MSG_SEM_REDE
    return ("O envio falhou (ver a mensagem acima) e nada mudou no GitHub. Volte a correr este comando; "
            "se falhar outra vez, peça ajuda técnica.")


def preparar_ligacao():
    """Devolve (o endereço do repositório, None), ou (None, «sem acesso» ou «sem internet»)."""
    if not CHAVE.exists():
        parar(f"Não encontrei a chave {CHAVE}. Ver docs/guia_de_deploy.md, passo 1 (como criar a chave noutro computador).")
    origem = git("remote", "get-url", "origin")
    if origem.returncode == 0:
        return origem.stdout.strip(), None
    repo, resposta = repositorio_da_chave()
    if not repo:
        return None, ("sem internet" if sem_internet(resposta) else "sem acesso")
    url = f"git@{ALIAS}:{repo}.git"
    git("remote", "add", "origin", url)
    print(f"Repositório encontrado e guardado: https://github.com/{repo}")
    return url, None


def estado_no_github():
    """'publicado' (o GitHub já tem o ramo main), 'vazio' (primeira publicação), 'sem acesso' ou 'sem internet'."""
    r = git("ls-remote", "--heads", "origin", "main", limite=90)
    if r.returncode:
        return "sem internet" if sem_internet(r.stderr) else "sem acesso"
    return "publicado" if r.stdout.strip() else "vazio"


def remontar_e_verificar():
    print("\n3. Remontar o pacote a partir do projecto")
    r = correr([PY, str(ROOT / "scripts" / "build_deploy_repo.py")], pasta=ROOT, mostrar=True)
    if r.returncode:
        parar("O pacote não se montou: nada foi enviado.")
    print("\n4. Verificar, como o GitHub")
    for nome, comando, pasta in [("pacote de dados completo", [PY, "plataforma/leitor.py", "--sem-prazo"], PACOTE),
                                 ("todas as páginas nas três línguas", [PY, "testar_app.py"], PACOTE / "plataforma")]:
        r = correr(comando, pasta=pasta)
        if r.returncode:
            print((r.stdout + r.stderr)[-1500:])
            parar(f"FALHOU: {nome}. Nada foi enviado. Corrija no projecto e volte a correr.")
        print(f"   ok  {nome}")


def main():
    p = argparse.ArgumentParser(description="Publica a plataforma ETE no GitHub (e daí no Streamlit Cloud).")
    p.add_argument("-m", "--mensagem", help="a mensagem do registo (por omissão, «Actualização da plataforma» e a data)")
    p.add_argument("--verificar", action="store_true", help="só remonta e verifica; não envia nada")
    a = p.parse_args()

    print("1. Ligação ao GitHub")
    url, motivo = preparar_ligacao()
    estado = estado_no_github() if url else motivo
    if estado in ("sem acesso", "sem internet"):
        if not a.verificar:
            parar(instrucoes_github() if estado == "sem acesso" else MSG_SEM_REDE)
        print(f"   {estado} (no modo verificar, segue só com a parte local)")
    else:
        print(f"   {url} ({'já publicado' if estado == 'publicado' else 'vazio: primeira publicação'})")

    if estado == "publicado":
        print("\n2. Trazer o que está publicado (com os boletins diários)")
        if git("fetch", "origin", limite=600).returncode:
            parar(MSG_SEM_REDE)
        locais = git("rev-list", "--count", "origin/main..HEAD").stdout.strip()
        if locais not in ("", "0"):
            git("branch", "-f", "copia-antes-de-publicar", "HEAD")
            print(f"   {locais} registo(s) locais por enviar: guardados no ramo copia-antes-de-publicar; o pacote é remontado na mesma")
        git("reset", "--hard", "origin/main")
    else:
        print("\n2. Nada para trazer do GitHub")

    remontar_e_verificar()
    if a.verificar:
        mudariam = git("status", "--short").stdout.strip().splitlines()
        parar(f"Verificação concluída: tudo certo. {len(mudariam)} ficheiro(s) mudariam em relação ao último registo. "
              "Nada foi enviado (modo verificar).", 0)

    print("\n5. Registar e enviar")
    git("add", "-A")
    if git("diff", "--cached", "--quiet").returncode != 0:
        mensagem = a.mensagem or f"Actualização da plataforma ({datetime.now():%Y-%m-%d %H:%M})"
        git("commit", "-q", "-m", mensagem)
        print(f"   registado: {mensagem.splitlines()[0]}")
    elif estado == "publicado" and git("rev-list", "--count", "origin/main..HEAD").stdout.strip() == "0":
        parar("Nada mudou: a plataforma publicada já está igual ao projecto.", 0)
    envio = git("push", "-u", "origin", "main", limite=1800)
    if envio.returncode:
        print(envio.stderr.strip()[-800:])
        parar(explicar_recusa(envio.stderr))
    repo = re.sub(r"^git@[^:]+:|\.git$", "", url)
    print(f"\nPublicado em https://github.com/{repo}")
    print("A aplicação no Streamlit Cloud actualiza-se sozinha em 1 a 2 minutos; a página leve, no GitHub Pages, também.")


if __name__ == "__main__":
    main()
