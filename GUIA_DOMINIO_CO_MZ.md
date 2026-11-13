# Domínio eyestoearth.co.mz: registo e ligação ao servidor

Estado em 16/10/2026: **eyestoearth.co.mz está livre** no registo oficial `.mz` (whois.nic.mz).

## 1. Registar o domínio

O espaço `.mz` (incluindo `.co.mz`) é gerido pelo **CIUEM** (Centro de Informática da Universidade
Eduardo Mondlane). O registo faz-se através de um agente de registo, por ordem de chegada: quem
regista primeiro fica com o nome.

- **Quem pode registar `.co.mz`**: qualquer pessoa ou entidade, de Moçambique ou de fora. Não é
  preciso entregar documentos; pedem nome do titular, email, telefone, morada e país.
- **Onde**: num agente de registo moçambicano (por exemplo, a MozOut indica preços a partir de
  2 500 MT por ano para `.co.mz`) ou num registador internacional (Netim, INWX e outros, em geral
  mais caros). Comparar o preço do primeiro ano **e o da renovação**.
- **Quanto tempo**: de 1 a 10 anos. Sugestão: pelo menos 2 anos e **renovação automática**.
- **Em nome de quem**: do projecto ou da instituição que o acolhe, com um email da equipa que não
  dependa de uma só pessoa. Um domínio que caduca deixa a plataforma e as ligações das mensagens de
  WhatsApp sem funcionar, e outra pessoa pode registá-lo.
- **Quanto demora**: normalmente fica activo minutos depois de confirmado o pagamento.

Confirmar no próprio agente as condições do dia: as regras do `.mz` estão no Regulamento do Uso do
Domínio .MZ (Decreto n.º 82/2020).

## 2. Ligar o domínio ao servidor (DNS)

Depois de alugar o servidor (ver `docs/guia_servidor_proprio.md`), no painel do agente de registo,
na zona DNS de `eyestoearth.co.mz`:

| Tipo | Nome | Valor | TTL |
|---|---|---|---|
| A | `@` (o próprio eyestoearth.co.mz) | IP do servidor (por exemplo 203.0.113.10) | 3600 |
| A | `www` | o mesmo IP | 3600 |
| AAAA | `@` e `www` | IPv6 do servidor, **só se** o servidor tiver IPv6 | 3600 |
| CAA (opcional) | `@` | `0 issue "letsencrypt.org"` | 3600 |

Se o agente pedir "servidores de nomes", deixar os do próprio agente e criar os registos acima no
painel dele. A mudança pode levar de minutos a algumas horas a chegar a todo o lado.

## 3. Verificar

No computador do projecto:

```bash
.venv/bin/python scripts/verificar_dominio.py --ip IP_DO_SERVIDOR
```

Diz, passo a passo: se o domínio está registado, para onde aponta, se `http://` leva a `https://`,
se o certificado HTTPS é válido, e se a plataforma, a página leve e o logótipo respondem. Cada passo
que falha diz o que fazer.

## 4. Instalar no servidor

O domínio e o email do certificado já estão em `servidor/dominio.conf`, por isso os comandos são curtos:

```bash
bash scripts/enviar_para_servidor.sh root@IP_DO_SERVIDOR      # do computador do projecto (cerca de 12 MB)
ssh root@IP_DO_SERVIDOR
sudo bash /opt/ete/servidor/instalar.sh                       # no servidor
```

O instalador avisa se o DNS ainda não aponta para o servidor (sem isso o HTTPS não pode ser
emitido). Actualizações seguintes, do computador do projecto: `bash scripts/enviar_para_servidor.sh`.

## Endereços finais

| O quê | Endereço |
|---|---|
| Plataforma | https://eyestoearth.co.mz |
| Página leve do boletim | https://eyestoearth.co.mz/leve/ |
| Alertas no WhatsApp | https://eyestoearth.co.mz/?p=alertas |
| Partilhar já em inglês ou francês | https://eyestoearth.co.mz/?lang=en · ?lang=fr |

Estes endereços já estão na configuração (`config/config.yaml`, secção `publication`): aparecem
nas mensagens de WhatsApp e no rodapé da plataforma a partir do próximo boletim.
