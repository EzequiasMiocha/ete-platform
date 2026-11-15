# Pacote de dados da plataforma ETE

Esta pasta é tudo o que a aplicação precisa. Não é preciso ter os 43 GB de dados do
projecto, nem o Earth Engine, nem os modelos.

| O quê | Onde |
|---|---|
| Dados (cerca de 11 MB, dos quais 3 MB são as imagens dos lugares) | `dados/` |
| Funções de leitura, testadas | `leitor.py` |
| Aplicação Streamlit: cinco páginas lidas de cima para baixo, sem separadores (Início, Qualidade da água, Cheias, Alertas, O projecto), mais a página de cada lugar («A sua zona», `?p=zona&lugar=Machubo`), aberta pela barra de pesquisa que está em todas as páginas; os endereços antigos (`?p=mapa`, `?p=conselhos`...) abrem a página que agora tem esse conteúdo | `app.py` (páginas), `tema.py` (sistema de desenho com as cores do copernicus.eu: roxo #615C9F, fundo claro, sem emojis; tipografia Fraunces e Plus Jakarta Sans, barra de navegação fixa, cartões, tabelas em HTML, botões de anterior e seguinte), `graficos.py` (gráficos); teste sem navegador: `testar_app.py` |
| Pesquisa (lugares e perguntas, sem ligar a acentos nem a pequenos erros) e curiosidades (com as fontes; os números vêm do pacote) | `pesquisa.py`, `curiosidades.py` |
| Contas opcionais (nome de utilizador e senha; a senha só como impressão digital scrypt; 5 tentativas e 10 minutos fechada; código de recuperação; sessão de 30 dias num cookie; tabelas `contas` e `sessoes` na base das inscrições, no Supabase com `docs/contas.sql`); página `?p=conta`; teste: `testar_contas.py` | `contas.py` |
| Línguas (português, inglês, francês) | `idioma.py` (troca de língua, datas, números) e `textos.py` (as traduções, português → inglês, francês) |
| Logótipos (ETE, IAU-OAD, DARA) nas cores da paleta | `static/`, feitos a partir de `logos/` por `scripts/build_platform_logos.py` |
| Versões anteriores da aplicação | `arquivo/` |
| Exemplo mínimo anterior | `app_exemplo.py` |

## Começar

```bash
python plataforma/leitor.py          # verifica o pacote: deve terminar com PACOTE COMPLETO
pip install -r plataforma/requirements.txt
cd plataforma && streamlit run app.py
python testar_app.py                 # corre todas as páginas nas três línguas: deve terminar com APLICAÇÃO SEM ERROS
```

## O que há em `dados/`

| Pasta | Conteúdo | Muda |
|---|---|---|
| `catalogo.json` | lista de todas as camadas: título, ficheiro, legenda, cores, limites | todos os dias |
| `boletim/` | boletim de hoje (`boletim.json`, `boletim.md`), estado e tabelas | todos os dias |
| `series/` | caudal e chuva, alertas desde 2015, área de água, cor da água, vegetação no rio | todos os dias |
| `exposicao/` | o que está em cada zona de aviso; lugares por ordem de alagamento | raramente |
| `vetores/` | zonas de aviso, lugares, distrito, troços do rio (GeoJSON) | raramente |
| `mapas/` | suscetibilidade e água por mês (PNG transparente + cantos no catálogo) | mensal |
| `mapas/cor_da_agua*.png` | cor da água (turbidez) da imagem limpa mais recente: mapa leve, recorte de Marracuene e camada transparente; leitura por troço em `catalogo.json` (`cor_da_agua_mapa`) | semanal |
| `qualidade/` | Módulo Q: estado por troço, série mensal desde 2006, normais, tendências, meses invulgares, resumo | mensal |
| `modelos/` | fichas dos modelos de machine learning e tabelas dos testes | quando os modelos mudam |
| `lugares/` | para cada lugar, três imagens de um quadrado de 6 km (antes da cheia de 2026, durante a cheia ou o radar onde havia nuvens, zonas de aviso) e `lugares.json` com o troço do rio mais perto; feitas por `src/ete/place_images.py`, sem descarregar nada (cerca de 3 MB) | quando houver uma nova cheia fotografada |
| `pipeline.json` | resumo da última execução do pipeline diário | todos os dias |

Tudo está em latitude/longitude (EPSG:4326). Os mapas em PNG põem-se sobre o mapa de base com
os cantos `[[sul, oeste], [norte, leste]]` que estão no catálogo.

## Regras que a aplicação tem de cumprir

1. **Nunca mostrar verde com dados em falta ou antigos.** Usar `leitor.boletim()["seguro_mostrar"]`.
   Se for `False`, mostrar "previsão indisponível" e remeter para os avisos oficiais.
2. **Mostrar sempre o aviso** de `catalogo.json` (`aviso`): o produto é experimental e não
   substitui o INGD, o INAM e a ARA-Sul.
3. **Mostrar o campo `limites`** de cada camada junto do mapa ou do gráfico.
4. **Qualidade:** dizer "cor da água" ou "mais turva do que o habitual". Os valores em FNU e
   mg/L são estimativas sem calibração: só na página técnica e com a palavra "estimada". Não
   dizer que a água é ou não é segura, não falar em algas. Os troços com `fiabilidade`
   `reduzida` mostram-se a cinzento ou com aviso.
5. **Pessoas por zona** (`pessoas_worldpop_2020`): é uma estimativa por cima. Preferir o número
   de edifícios; se as pessoas forem mostradas, dizer "até cerca de".
6. **Nomes de lugares:** ainda não foram validados no terreno (coluna `validado` vazia).
7. Ler os títulos, as cores e as legendas do catálogo, sem os escrever à mão no código.

## Quem atualiza o quê

| Comando | Quando | Internet |
|---|---|---|
| `scripts/run_daily_pipeline.py` | todos os dias (cron, 06:00) | poucos KB; uma vez por semana, centenas de KB |
| `scripts/export_platform_package.py` | depois de treinar modelos ou de fazer novos mapas mensais | nenhuma |

Para publicar a aplicação num serviço como o Streamlit Community Cloud, esta pasta tem de ir
no repositório (é pequena de propósito) e o servidor que corre o pipeline tem de a enviar
depois de cada execução.

## Línguas

A plataforma está escrita em português; cada texto passa por `t()` e aparece na língua escolhida
no selector **PT | EN | FR** (ou no endereço, por exemplo `?lang=en&p=agua`). Para acrescentar ou
corrigir uma tradução, editar `textos.py`. Um texto sem tradução aparece em português. Para ver
os que faltam: `ETE_REGISTAR_EM_FALTA=1 python testar_app.py` (escreve `textos_em_falta.txt`;
nomes de lugares e frases montadas a partir de peças já traduzidas também aparecem lá e podem
ser ignorados). A mensagem para WhatsApp e o boletim completo ficam sempre em português.

## Alertas no WhatsApp

As pessoas inscrevem-se na plataforma (janela de convite na primeira visita, página **Alertas**,
botão na barra do topo). Todas as manhãs, com alerta laranja ou vermelho, recebem uma mensagem com
o nível, pelo menos dois lugares que podem alagar e a ligação para a plataforma; e outra quando o
perigo passa. Base de dados `subscritores` (SQLite no computador, Supabase na plataforma publicada): `inscricoes.py`; ver quem está inscrito: `python scripts/ver_subscritores.py`; decidir e enviar: `alertas_whatsapp.py`;
teste: `python testar_alertas.py`. Como ligar o envio automático, criar a base no Supabase
e os textos dos modelos para a Meta: `docs/alertas_whatsapp.md`. Os números de telefone
nunca vão para o pacote `dados/` nem para o repositório.

## Conselhos sobre a água

A secção **O que fazer com a água**, na página da qualidade da água (e o resumo na primeira página),
diz o que fazer, para cada público: famílias, agricultores e criadores, pescadores, escolas, unidades de
saúde, quem trata e distribui água, autoridades e líderes. `conselhos.py` detecta as situações a
partir dos dados do dia (água mais turva, água turva prevista, alerta de cheia, depois da cheia,
rio com pouca água para a época, plantas sobre a água) e escolhe os conselhos. Os textos seguem as
orientações da OMS e da UNICEF; editar só em `conselhos.py` (e as traduções em `textos.py`).
