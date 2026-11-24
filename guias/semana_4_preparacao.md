# Semana 4 (17 a 23 de Outubro de 2026): o que está pronto e o que falta

Projecto Eyes to Earth. Actualizado a 11 de Outubro de 2026, segundo `ETE_Project_Plan.xlsx`.
O estado de todas as tarefas do plano, semana a semana, está em `docs/estado_do_plano.md`.

## Estado por tarefa

| Tarefa | Responsável | O que já existe | O que falta |
|---|---|---|---|
| W4-01 Integrar os modelos na app (página Quantidade) | Mussa + Ezequias | `plataforma/app.py`: alerta do dia, mapa de zonas de aviso, suscetibilidade, água por radar, previsão de caudal, exposição. Corre localmente sem erros (`plataforma/testar_app.py`) | Revisão do Mussa; identidade visual (W3-13) |
| W4-02 Integrar o Módulo Q (página Qualidade) | Mussa + Ezequias | Mapa por troço da fronteira à foz, séries desde 2006, normais, tendências, alerta de qualidade, previsão para as manhãs | Revisão; decidir que parâmetros mostrar ao público |
| W4-03 Pipeline automático diário | Ezequias + Mussa | `scripts/run_daily_pipeline.py` e a tarefa agendada `.github/workflows/boletim_diario.yml`: o boletim corre todos os dias nos servidores do GitHub, sem computador ligado. Ensaiado num clone limpo do repositório | Activar no GitHub (passo 3 do guia de deploy); imagens semanais e Módulo Q mensal continuam no computador do projecto |
| W4-04 Análise de exposição | Agostinho | `plataforma/dados/exposicao/`: área, terras agrícolas, edifícios, escolas, saúde, estradas e pessoas por zona; lugares por ordem de alagamento | Rever os números; validar os nomes dos lugares |
| W4-05 Deploy | Mussa | Repositório de publicação pronto em `deploy/ete-plataforma/` (11 MB), com a aplicação, a página leve de reserva, o boletim automático e os testes automáticos. Guia passo a passo: `docs/guia_de_deploy.md` | Criar o repositório no GitHub, ligar o GitHub Pages e o Streamlit Cloud (cerca de 20 minutos, com a conta da equipa) |
| W4-06 Testes internos | Todos | Roteiro abaixo | Fazer os testes e registar as correcções |
| W4-07 Documentação técnica | Ezequias + Irene | `README.md`, `docs/guia_de_deploy.md`, `docs/manual_do_utilizador.md`, `plataforma/LEIA-ME.md`, `qgis/GUIA_QGIS.md`, notebooks comentados, guia de mensagens | Revisão de linguagem do manual pela Irene |
| W4-08 Teste do alerta de ponta a ponta | Mussa + Glads | `scripts/test_alert_end_to_end.py` e relatório `docs/teste_alerta_ponta_a_ponta.md`: a parte automática passa | Enviar a mensagem a um líder e registar a resposta |
| W4-09 Materiais para a comunidade | Nilza + Irene | Mapas A3 em `reports/mapas_para_impressao/`; textos em `docs/guia_de_mensagens_de_alerta.md` | Cartaz "o que fazer"; arranjo gráfico; língua local |

## Diferenças face ao plano, e porquê

- **O alerta diário** vem da previsão de caudal (51 cenários do GloFAS) e da chuva na bacia,
  não do radar. O alerta tem de chegar antes da água, e o radar só a vê depois. Em Janeiro de
  2026 as regras teriam dado laranja 4 a 5 dias antes do primeiro mapa de cheia.
- **O mapa de água por radar** (Modelo B) é mensal: actualizá-lo custa cerca de 120 MB por mês.
- **Onde avisar** vem das zonas de aviso (a cheia real de 2026), não do produto "risco × água".
- **Módulo Q a montante só desde 2017.** Da fronteira até perto de Manhiça o rio tem 50 a 80 m
  de largura, menos de três píxeis Landsat. Aí só o Sentinel-2 serve. Os 20 anos existem nos
  três troços de jusante.
- **Turbidez esperada pela chuva.** O modelo mensal do plano não funcionou. Ficou um modelo
  imagem a imagem, e o aviso "acima do explicado" só é dado nos troços onde o modelo explica
  o suficiente.
- **ACOLITE não foi corrido** (imagens de nível 1, cerca de 1 GB cada). A turbidez em FNU e
  os sólidos em mg/L são estimativas sem calibração local.
- **Clorofila-a não é reportada.** O índice NDCI, neste rio, segue o sedimento.

## Decisões que são da equipa

1. **Conta GitHub da equipa** para publicar (`docs/guia_de_deploy.md`). É o único passo que
   falta para a plataforma ficar pública.
2. **Quem actualiza as imagens** de cor da água (semanal) e o Módulo Q (mensal) no computador
   do projecto. A conta do Earth Engine está em "modo restrito" (poucos pedidos em simultâneo):
   ver https://developers.google.com/earth-engine/guides/noncommercial_tiers
3. **Quem envia a mensagem diária aos líderes** e por que canal.
4. **Condições de uso do Open-Meteo** para um serviço público.
5. **Texto dos conselhos do boletim**, a rever com a protecção civil local.
6. **Coordenação com o INGD, o INAM e a ARA-Sul** antes de o boletim ser público.
7. **Que números de qualidade mostrar ao público:** recomenda-se só as classes (normal,
   elevada, muito elevada) e as plantas sobre a água; os FNU e mg/L ficam para a página técnica.

## Roteiro para os testes internos (W4-06)

| Teste | Como | Resultado esperado |
|---|---|---|
| O pacote está completo | `python plataforma/leitor.py` | termina com `PACOTE COMPLETO` |
| A app não tem erros | `cd plataforma && python testar_app.py` | termina com `APLICAÇÃO SEM ERROS` |
| O sistema de previsão está são | `.venv/bin/python scripts/check_forecast_system.py` | termina com `TUDO CERTO` |
| A mensagem para os líderes | `.venv/bin/python scripts/test_alert_end_to_end.py` | todas as verificações "ok" |
| Sem internet | `scripts/run_daily_pipeline.py --offline` | boletim emitido a partir da cópia guardada, a dizer que é cópia |
| Dados antigos | abrir a app com um `boletim/estado.json` de há 2 dias | a app mostra "previsão indisponível", nunca verde |
| Mapas no sítio certo | na app, ligar as zonas de aviso e os troços sobre o mapa de base | seguem o rio, sem desvio |
| Linguagem | uma pessoa de fora da equipa lê a página "Hoje" | percebe o nível, onde e o que fazer, sem ajuda |
| Telemóvel | abrir a app num telemóvel com dados móveis | carrega em poucos segundos e lê-se sem ampliar |

## Limites a manter visíveis na plataforma

- Toda a validação de cheias assenta num evento (Janeiro de 2026).
- O acerto da previsão em tempo real ainda não foi medido: as previsões começaram a ser
  arquivadas a 11 de Outubro de 2026 para o medir mais tarde.
- A qualidade da água é a cor da água vista por satélite, comparada com o seu normal. Não há
  nenhuma estação pública de qualidade na bacia (GEMStat), e a equipa decidiu (12/10/2026) não
  fazer medições no local. O módulo de qualidade é, por isso, um indicador relativo: a
  plataforma mostra classes (normal, elevada, muito elevada), nunca valores como medições.
- Os nomes dos lugares não estão validados.
- As pessoas por zona (WorldPop 2020) são um limite superior. Usar os edifícios.
