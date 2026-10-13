# Pacote de dados da plataforma ETE

Esta pasta é tudo o que a aplicação precisa. Não é preciso ter os 43 GB de dados do
projecto, nem o Earth Engine, nem os modelos.

| O quê | Onde |
|---|---|
| Dados (cerca de 4 MB) | `dados/` |
| Funções de leitura, testadas | `leitor.py` |
| Aplicação Streamlit (Início, Cheias, Mapa, Água do rio, Histórico, Lugares, Como funciona) | `app.py` (páginas), `tema.py` (paleta, estilo, cartões, botões de anterior e seguinte), `graficos.py` (gráficos); teste sem navegador: `testar_app.py` |
| Versões anteriores da aplicação | `arquivo/` |
| Exemplo mínimo anterior | `app_exemplo.py` |

## Começar

```bash
python plataforma/leitor.py          # verifica o pacote: deve terminar com PACOTE COMPLETO
pip install -r plataforma/requirements.txt
cd plataforma && streamlit run app.py
python testar_app.py                 # corre todas as páginas: deve terminar com APLICAÇÃO SEM ERROS
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
| `qualidade/` | Módulo Q: estado por troço, série mensal desde 2006, normais, tendências | mensal |
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
