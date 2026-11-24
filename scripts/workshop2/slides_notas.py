"""Notas do orador dos slides do Workshop 2 que são texto fixo.

As notas com números das respostas de referência (que mudam se os dados mudarem) estão em slides.py.
Papéis: MODERADORA e FACILITADOR 1 a 7 (os nomes ficam no manual dos facilitadores).
"""

NOTAS_FIXAS = {
    "capa": """MODERADORA (Armenia Machava), 08:15. Este slide fica no ecrã durante o registo (08:00–08:15).

Boas-vindas: "Bom dia a todos e sejam bem-vindos ao segundo workshop do projecto EYES TO EARTH. Hoje vamos falar de Inteligência Artificial: a mesma tecnologia que está no vosso telemóvel, mas usada para vigiar o rio Incomáti e avisar as pessoas antes de uma cheia."

Agradecer o apoio do IAU Office of Astronomy for Development (IAU-OAD) e do DARA. Apresentar a equipa em 1 minuto: só nome e função (a apresentação longa foi feita no Workshop 1).

Regras da casa: telemóveis em silêncio; pode-se interromper para perguntar; perguntas escritas num papel também valem (a moderadora recolhe-as).""",
    "missao": """MODERADORA, cerca de 1 minuto.

"Hoje temos uma missão. No fim do dia, cada par vai ter treinado a sua própria Inteligência Artificial: um programa que olha para uma imagem de satélite e diz onde está a água da cheia. E vão saber dizer onde ele acerta e onde erra, porque uma máquina que não sabe onde erra é perigosa."

Formar os pares já agora (10 estudantes, 5 pares), se ainda não estiverem formados no registo. Juntar quem já programou com quem nunca programou.""",
    "inquerito": """MODERADORA, 08:20–08:25.

Colocar aqui o QR code e o link do questionário OAD pré-workshop (substituir o quadro claro). Ter cópias em papel para quem não tiver telemóvel ou dados.

A equipa circula pela sala para ajudar. Ninguém avança sem submeter. O questionário mede o conhecimento inicial: é o mesmo que respondem às 13:45, para medir o que aprenderam (Resultado do plano OAD).""",
    "revisao-regra": """FACILITADOR 1, cerca de 2 minutos.

"No Workshop 1 usámos uma REGRA para encontrar a água. A regra é uma conta: o índice MNDWI compara a luz verde com a luz infravermelha de onda curta (SWIR). A água devolve um pouco de verde e quase nenhum SWIR, por isso o resultado fica positivo. Se for maior do que zero, dizemos 'é água'.

Com esta regra medimos a cheia de Janeiro de 2026: o rio chegou a 2 987 metros cúbicos por segundo no dia 19 de Janeiro, a maior cheia em 20 anos. Na imagem de 24 de Janeiro, a planície tinha cerca de 20 244 hectares de água nova, mais ou menos 28 000 campos de futebol."

Ponto-chave: uma regra é escrita por uma pessoa e é igual para todos os dias.""",
    "m1": """FACILITADOR 1. Módulo 1: 25 minutos de conteúdo + 5 minutos de dúvidas (08:35–09:05).

Fazer a pergunta e ouvir 2 ou 3 respostas, sem corrigir. Respostas que costumam aparecer: "tem uma fotografia guardada", "compara os olhos". Chegar à ideia: ninguém escreveu no telemóvel a regra "a cara do João tem o nariz assim". O telemóvel viu várias fotografias da sua cara quando configurou o desbloqueio, e APRENDEU a reconhecê-la. Isso é Inteligência Artificial.

Objectivo do módulo: no fim, cada estudante sabe explicar a diferença entre escrever uma regra e aprender com exemplos, e dá 3 exemplos de IA no dia-a-dia.""",
    "m1-regras": """FACILITADOR 1, cerca de 3 minutos. É o slide mais importante do módulo.

"Há duas maneiras de pôr um computador a fazer uma tarefa.

A primeira é a programação clássica: uma pessoa pensa e escreve as regras, passo a passo. O computador recebe as regras e os dados, e dá as respostas. Foi o que fizemos no Workshop 1: escrevemos a regra 'MNDWI maior do que zero é água'.

A segunda é o Machine Learning, em português 'aprendizagem automática'. Aqui damos ao computador EXEMPLOS com as RESPOSTAS certas: este píxel é água, este não é. O computador procura sozinho a regra que liga os exemplos às respostas. O resultado chama-se MODELO: são as regras que o computador descobriu."

Analogia: a receita de bolo (regras escritas) contra a avó que aprendeu a cozinhar a provar muitos bolos (exemplos).

Atenção ao vocabulário, que volta na prática: exemplo, resposta certa (rótulo), modelo, treinar (aprender), prever.""",
    "m1-ia-ml-dl": """FACILITADOR 1, cerca de 3 minutos.

"Estas três palavras aparecem muito nas notícias. Uma está dentro da outra, como caixas.

A caixa maior é a Inteligência Artificial: qualquer computador que faz uma tarefa que antes só uma pessoa sabia fazer.

Dentro dela está o Machine Learning: a IA que aprende com exemplos. É o que vamos fazer hoje, com um método chamado Random Forest (floresta aleatória).

Dentro do Machine Learning está o Deep Learning, a 'aprendizagem profunda'. Usa redes neuronais: muitas camadas de pequenas contas, inspiradas (de longe) nos neurónios do cérebro. É muito poderoso, mas precisa de muitíssimos exemplos: o reconhecimento facial aprendeu com milhões de caras e o ChatGPT com uma enorme quantidade de texto."

Se perguntarem "o Random Forest é Deep Learning?": não. É Machine Learning clássico: funciona bem com poucos exemplos, é rápido e conseguimos ver como decide.""",
    "m1-aprende": """FACILITADOR 1, cerca de 2 minutos.

"Ninguém deu a uma criança a regra 'um cão tem quatro patas, pêlo e ladra'. Ela viu muitos cães. Um adulto disse: 'olha, um cão'. E um dia, na rua, apontou para um cão que nunca tinha visto e disse 'cão!'. Aprendeu com exemplos e com a resposta certa.

A máquina faz o mesmo, com duas diferenças. Primeira: precisa de muitos mais exemplos do que uma criança. Segunda: só sabe o que viu. Se só viu cães pretos, pode não reconhecer um cão branco. Guardem esta frase: vamos vê-la acontecer na prática, quando o modelo treinado com 2026 encontrar um ano diferente."

Vocabulário para a prática: os exemplos com a resposta certa chamam-se DADOS DE TREINO; a resposta certa chama-se RÓTULO.""",
    "m1-actividade": """FACILITADOR 1. Actividade em pares, 5 minutos (3 para pensar, 2 para corrigir em conjunto).

Cada par escreve no papel "R" (regra) ou "E" (exemplos) para cada tarefa.

Respostas:
1. Regra: o troco é uma conta exacta (pago menos preço).
2. Exemplos: ninguém consegue escrever a regra de uma voz; reconhecemo-la por a termos ouvido muitas vezes.
3. Regra: a ordem alfabética tem regras claras.
4. Exemplos: o spam muda todos os dias; aprende-se com mensagens marcadas.
5. Regra: 1 km = 1000 m.
6. Exemplos: a água muda de cor (barrenta, escura, limpa); uma regra fixa falha, como vimos em 2021 e 2024.

Ideia a retirar: quando há uma fórmula exacta, escreve-se a regra. Quando o problema é "reconhecer" algo que muda muito, o Machine Learning ganha.""",
    "m1-gancho": """FACILITADOR 1, 2 minutos; depois 5 minutos de dúvidas do Módulo 1 (09:00–09:05).

Fazer a pergunta de verificação a um estudante ao acaso (não a quem já falou).
Resposta esperada: "Uma regra é escrita por uma pessoa e é sempre igual. Um modelo é treinado: o computador aprende a regra a partir de exemplos com a resposta certa. Se os exemplos mudarem, o modelo muda."

Transição para o Módulo 2 (Facilitador 2): "E como é que o computador aprende, exactamente? É isso que o próximo módulo mostra.\"""",
    "m2": """FACILITADOR 2. Módulo 2: cerca de 43 minutos de conteúdo e actividades + 7 de dúvidas (09:05–09:55). É o centro do dia: cada palavra deste módulo aparece na prática.

Fazer a pergunta e ouvir 2 ou 3 respostas. Chegar a: "mostraram-lhe milhares de imagens de raio-X de malas, já marcadas por agentes: esta tem uma arma, esta não tem. O computador aprendeu a diferença sozinho." Isso é aprendizagem supervisionada.

Mapa do módulo:
1. O que é um modelo e o que são os dados (exemplos, características, rótulos).
2. Os três tipos de aprendizagem: supervisionada (classificação e regressão), não supervisionada (agrupamento) e por reforço.
3. Como se treina: errar, medir o erro, corrigir.
4. Quatro algoritmos de classificação: árvore de decisão, Random Forest, k vizinhos, rede neuronal.
Duas actividades em pares: "Que tipo de aprendizagem é?" e "Sejam uma árvore de decisão".""",
    "m2-tipos": """FACILITADOR 2, cerca de 2 minutos. É o mapa de todo o módulo: voltar a ele no fim.

"Há três grandes maneiras de uma máquina aprender.

SUPERVISIONADA: damos exemplos COM a resposta certa, como um professor que corrige. Há dois casos: se a resposta é uma categoria (água ou não água, arma ou sem arma), chama-se CLASSIFICAÇÃO. Se a resposta é um número (o caudal em m³/s, uma nota de 0 a 20), chama-se REGRESSÃO.

NÃO SUPERVISIONADA: damos exemplos SEM resposta. A máquina procura grupos de coisas parecidas: é o AGRUPAMENTO. Existe, mas no nosso projecto não a usámos.

POR REFORÇO: a máquina experimenta, recebe pontos quando acerta e perde quando erra, como num jogo. É assim que se treinam programas que jogam xadrez ou robôs que aprendem a andar."

Na prática fazemos só a supervisionada, a que o projecto usou: classificação (Temas 1, 2 e 3) e regressão (Tema 4).""",
    "m2-classificacao": """FACILITADOR 2, cerca de 1,5 minutos. Dados reais: os píxeis dos pontos que a equipa marcou na cheia de 2026.

"Cada ponto é um píxel. A posição vem de duas pistas: o NIR (eixo horizontal) e o SWIR (eixo vertical). A cor é o rótulo: azul é água, laranja é não água.

A água fica toda no canto de baixo, à esquerda: absorve o infravermelho, por isso tem NIR e SWIR baixos. A terra e as plantas reflectem o infravermelho e ficam espalhadas pelo resto.

TREINAR UMA CLASSIFICAÇÃO é encontrar a FRONTEIRA que melhor separa as duas cores. Aqui é uma linha recta. Depois, para um píxel novo (a estrela), o modelo só vê de que lado da fronteira ele cai: está do lado azul, logo diz 'água'."

Com as 5 bandas da prática, a fronteira não se consegue desenhar (são 5 dimensões), mas a ideia é a mesma. Cada algoritmo traça a fronteira à sua maneira: a árvore faz cortes direitos, a rede neuronal faz curvas.""",
    "m2-treinar": """FACILITADOR 2, cerca de 1,5 minutos. Como é que o computador encontra a melhor recta?

"Não acerta à primeira. Começa com uma recta qualquer (passo 0, a mais clara, que até desce). Mede o erro: é enorme. Depois corrige a recta um bocadinho na direcção que faz o erro descer. Mede outra vez. Corrige outra vez. Depois de 10 passos já está quase certa; ao fim de 60 passos o erro já não desce.

É como afinar o volume de um rádio: rodar um pouco, ouvir, rodar mais um pouco.

O gráfico da direita é a CURVA DE TREINO: o erro a descer a cada passo. Aparece em todos os livros de Machine Learning. As redes neuronais (o Deep Learning) aprendem exactamente assim, com milhões de números em vez de dois."

Palavra técnica, se perguntarem: 'descida do gradiente'.""",
    "m2-nao-supervisionada": """FACILITADOR 2, cerca de 2,5 minutos. Dados reais: 1 500 píxeis da imagem da cheia de 2026, sem nenhum rótulo.

"E se não tivermos rótulos? À esquerda estão os píxeis como o computador os recebe: só números, todos cinzentos. Ninguém disse o que é água.

À direita, o K-means juntou-os em 3 grupos de píxeis parecidos. O grupo azul (NIR e SWIR baixos) é, de facto, a água; os outros dois são tipos diferentes de terra. Mas o computador não sabe os nomes: chamou-lhes grupo 1, 2 e 3. Somos nós que olhamos e dizemos 'o grupo 1 é água'."

Outros usos do agrupamento: juntar os clientes de uma loja por hábitos de compra; juntar músicas parecidas (as listas automáticas do Spotify); juntar notícias sobre o mesmo assunto; encontrar transacções bancárias estranhas, que não se parecem com nenhum grupo (fraude).

Dizer no fim: "No projecto EYES TO EARTH não usámos aprendizagem não supervisionada. Porquê? Porque tínhamos rótulos: os mapas oficiais das cheias feitos por especialistas (Copernicus EMS) e 20 anos de mapas de água (JRC). Com rótulos, a máquina aprende exactamente o que queremos. Os grupos não têm nome: alguém teria de dizer, em cada imagem, qual é a água, e a plataforma corre sozinha todos os dias."

Se perguntarem: na imagem da cheia o K-means separa bem a água, porque ela é muito diferente da terra; numa imagem de seca, junta ao rio terra húmida e sombras.""",
    "m2-reforco": """FACILITADOR 2, cerca de 1,5 minutos. Só para conhecer: não o usamos na prática.

"No terceiro tipo não há rótulos nem grupos. Há um AGENTE (um programa, um robô) que faz uma ACÇÃO num AMBIENTE (um jogo, o mundo). O ambiente responde com uma RECOMPENSA: pontos se correu bem, menos pontos se correu mal. O agente repete milhões de vezes e aprende as acções que dão mais pontos. É como treinar um cão com biscoitos.

O exemplo mais famoso: o AlphaGo venceu o campeão mundial de Go em 2016; a versão seguinte, AlphaGo Zero, aprendeu só a jogar contra si própria. Também se treinam assim robôs que aprendem a andar e drones, primeiro em simulação."

Porque não usamos? Precisa de um ambiente onde se possa errar milhões de vezes sem estragar nada (um jogo ou um simulador). Com um rio verdadeiro não se pode experimentar.""",
    "m2-actividade-tipos": """FACILITADOR 2. Actividade em pares, 4 minutos (2 para responder, 2 para corrigir).

Respostas:
1. Temperatura máxima de amanhã: REGRESSÃO (um número, em graus).
2. Mensagens de WhatsApp "burla" ou "normal": CLASSIFICAÇÃO (supervisionada: precisa de mensagens já marcadas).
3. Clientes em grupos parecidos, sem saber os grupos: AGRUPAMENTO (não supervisionada).
4. Robô que aprende a andar caindo e levantando-se: POR REFORÇO.
5. Scanner "arma" ou "sem arma": CLASSIFICAÇÃO.
6. Caudal do Incomáti daqui a 3 dias: REGRESSÃO.
7. Píxeis em grupos parecidos: AGRUPAMENTO (não supervisionada).
8. Nota a partir das horas de estudo: REGRESSÃO.

Truque para a turma: "a resposta é uma categoria? Classificação. Um número? Regressão. Não há resposta, só grupos? Agrupamento. Há pontos e tentativas? Reforço." """,
    "m2-algoritmos": """FACILITADOR 2, cerca de 1 minuto. Apresentar os quatro; os próximos slides mostram cada um.

"Para a mesma tarefa de classificação há muitos algoritmos. Vamos conhecer quatro, todos usados na prática:
- ÁRVORE DE DECISÃO: perguntas de sim ou não. Fácil de ler.
- RANDOM FOREST: muitas árvores a votar. Robusto e rápido.
- K VIZINHOS MAIS PRÓXIMOS: procura os exemplos mais parecidos e segue a maioria.
- REDE NEURONAL: camadas de neurónios artificiais. É a base do Deep Learning.

Qual é o melhor? Depende! Na Aula 2 da prática usamos a floresta aleatória e vemos que um modelo que passa num exame pode falhar noutro ano." """,
    "m2-arvore": """FACILITADOR 2, cerca de 2 minutos.

"Como é que o computador transforma exemplos em regras? Uma das maneiras mais simples é a ÁRVORE DE DECISÃO: uma série de perguntas de sim ou não, como no jogo das 20 perguntas.

Vamos seguir um píxel do rio: MNDWI maior do que 0? Sim: é água. Agora um píxel de uma machamba: MNDWI maior do que 0? Não. NIR maior do que 0,25? Sim: é vegetação.

O mais importante: NÓS não escrevemos estas perguntas. O computador experimentou muitas perguntas possíveis e ficou com as que melhor separam os exemplos. Os números (0, 0,25) também foram escolhidos por ele."

Esta é uma árvore pequena (2 perguntas). Na Aula 1 da prática, os estudantes treinam uma árvore com os pontos da cheia de 2026 e vêem a pergunta que ela escolheu: «SWIR ≤ 0,04 é água».""",
    "m2-knn": """FACILITADOR 2, cerca de 1,5 minutos. Os mesmos 24 píxeis.

"O método dos K VIZINHOS MAIS PRÓXIMOS é o mais fácil de explicar: 'diz-me com quem andas, dir-te-ei quem és'. Para um píxel novo (a estrela), procura os k exemplos mais parecidos, que no gráfico são os que estão mais perto. Aqui k = 5: três são vegetação e dois são solo. A maioria ganha: vegetação.

Este método quase não treina: guarda os exemplos e mede distâncias quando chega um caso novo. Por isso é rápido a aprender e lento a prever quando há milhões de exemplos.

E o k importa: com k = 1 segue um só vizinho, mesmo que seja um caso estranho (decora o ruído); com k muito grande, a maioria da turma toda ganha sempre."

Nos testes da equipa, os k vizinhos com k = 5 ficam entre os melhores no exame de 2026.""",
    "m3": """FACILITADOR 5. Módulo 3: 27 minutos + 3 de dúvidas (10:05–10:35). É a ponte para a prática, que o mesmo facilitador conduz.

Ouvir 2 ou 3 respostas. Chegar a: "faz-lhe perguntas NOVAS, que ele não viu, e vê se ele acerta". É exactamente o que fazemos com um modelo: o exame com dados que nunca viu.

Mapa do módulo: o caminho completo do treino; treino e teste; os rótulos e o exame do nosso rio; a matriz de confusão e as notas; subajuste e sobreajuste.""",
    "m3-fluxo": """FACILITADOR 5, cerca de 2 minutos.

"Este é o caminho de qualquer projecto de Machine Learning, do filtro de spam à nossa plataforma:
1. Uma pergunta clara: onde está a água? Quanto caudal vai haver?
2. Dados: as imagens de satélite, as séries de caudal e chuva.
3. Rótulos (na supervisionada): os pontos marcados, o caudal medido.
4. Características: as pistas (bandas, índices, chuva).
5. Dividir: uma parte para estudar (treino) e outra fechada à chave para o exame (teste).
6. Treinar: modelo.fit(X, y).
7. Avaliar: as notas no teste.
8. Usar: modelo.predict com dados novos.

Se a nota do teste for má, volta-se atrás: mais exemplos, outras pistas, outro algoritmo. Na prática vão fazer este caminho todo, três vezes." """,
    "m3-rotulos": """FACILITADOR 5, cerca de 1,5 minutos.

"O primeiro ingrediente são os RÓTULOS: a resposta certa. Nesta imagem da cheia de Janeiro de 2026, a equipa marcou 15 pontos de água (círculos azuis) e 15 de não água (quadrados laranja). Cada ponto vale um quadradinho de 5 por 5 píxeis, ou seja 25 exemplos.

Na prática, cada par vai marcar os seus próprios pontos, com uma 'lupa' para ver de perto.

Dois cuidados:
1. Variedade. Se só mostrarmos água castanha, o modelo pode não reconhecer água escura. Marquem água de vários tipos e terra de vários tipos.
2. Rigor. Um ponto em cima de uma nuvem, ou na borda entre água e terra, é um rótulo duvidoso. Rótulos errados ensinam coisas erradas: é a regra número 1 do Machine Learning."

Curiosidade: o mapa mundial de água e terra que o projecto ETE usa (Dynamic World, da Google) foi treinado com dezenas de milhares de imagens marcadas à mão por pessoas.""",
    "m3-matriz": """FACILITADOR 5, cerca de 2 minutos. Números do modelo da equipa no exame EMS (339 409 píxeis).

"Quando comparamos a resposta do modelo com a resposta certa, só há quatro possibilidades. Dois acertos: disse água e era água; disse terra e era terra. E dois erros diferentes:
- FALSO ALARME: disse água, mas era terra. Num sistema de avisos, gera alarmes falsos e as pessoas deixam de acreditar.
- ÁGUA PERDIDA: disse terra, mas era água. Num sistema de avisos, é o erro mais perigoso: não avisa quem está em perigo.

O nosso modelo quase não dá falsos alarmes (29 píxeis). Perde alguma água (9 657 píxeis, a laranja no mapa), sobretudo nas bordas da cheia, onde um píxel de 30 metros é metade água e metade terra, ou onde a água é pouco funda e está entre a vegetação."

Na prática (Aula 2), cada par vê esta mesma tabela para o seu modelo. Os cientistas chamam a esta tabela "matriz de confusão".""",
    "m3-iou": """FACILITADOR 5, cerca de 2 minutos. Fazer a conta no quadro.

"O círculo cinzento é a água que o modelo previu: 80 hectares. O círculo vermelho é a água verdadeira: 100 hectares. Eles sobrepõem-se em 70 hectares: é a INTERSECÇÃO, a água que o modelo acertou.

A UNIÃO é tudo o que está pintado, cinzento ou vermelho: 80 + 100, menos os 70 que contámos duas vezes = 110.

IoU = 70 ÷ 110 = 0,64. Se os dois mapas fossem iguais, a intersecção seria igual à união e o IoU seria 1."

Porque é uma boa nota para mapas de cheia: não se deixa enganar pela muita terra seca que há à volta (ao contrário do acerto). Esta mesma conta aparece no teste do aluno (pergunta 10).""",
    "m3-ajuste": """FACILITADOR 5, cerca de 2,5 minutos. Dados inventados: os mesmos 16 pontos nos três quadros.

"Três modelos para os mesmos pontos.
- À esquerda, uma recta: simples demais. Não apanha a forma dos pontos. Erra nos exemplos e vai errar nos casos novos. É o SUBAJUSTE.
- Ao meio, uma curva que apanha a forma geral, sem perseguir cada ponto. Erra um pouco nos exemplos, mas vai acertar nos novos. É o BOM AJUSTE.
- À direita, uma curva que passa por TODOS os pontos, incluindo o ruído. Nos exemplos não erra nada. Mas entre os pontos faz loucuras, e com um ponto novo vai errar muito. É o SOBREAJUSTE: decorou.

É como estudar para um teste: quem não estuda (subajuste) chumba; quem decora as respostas do livro sem perceber (sobreajuste) também chumba quando as perguntas mudam." """,
    "m3-decorar": """FACILITADOR 5, cerca de 1,5 minutos. Números reais do modelo da equipa (15 + 15 pontos, 100 árvores).

"Este é o modelo que a equipa treinou com 30 pontos na imagem da cheia. Nos exemplos que estudou, acerta 100%: perfeito! Mas isso não prova nada. No exame, com mapas da cheia feitos por especialistas e que o modelo nunca viu, acerta 97%. É uma óptima nota, mas é ESTA a nota verdadeira.

Quando a diferença entre as duas notas é muito grande (por exemplo, 100% no treino e 70% no exame), o modelo decorou os exemplos em vez de aprender a regra geral. Chama-se sobreajuste, em inglês 'overfitting'."

Curiosidade para quem perguntar: se baralharmos os píxeis dos próprios pontos e usarmos uma parte para testar, também dá 100%, porque píxeis vizinhos do mesmo ponto são quase iguais. É como copiar no exame. Por isso o exame tem de vir de outro sítio.""",
    "m3-verificacao": """FACILITADOR 5. 1 minuto; depois 3 minutos de dúvidas do Módulo 3 (10:32–10:35).

Fazer a pergunta e esperar. No modo de apresentação, a resposta aparece no clique seguinte.

Resposta esperada: "Não. 100% nos exemplos de treino pode querer dizer que decorou. Tem de ser testado com dados que nunca viu e com rótulos que não foram feitos pelo próprio modelo (a regra de ouro)."

Dúvidas frequentes:
- "Quantos exemplos são precisos?" Depende da dificuldade. Para água e terra, dezenas de pontos já chegam; para reconhecer caras, são precisos milhões.
- "O modelo pode piorar?" Sim, se lhe dermos rótulos errados.
- "O Random Forest pensa?" Não. Faz contas e votações; não percebe o que é a água.

A seguir: Módulo 4, a qualidade da água, com o Facilitador 3.""",
    "m4": """FACILITADOR 3. Módulo 4: 22 minutos + 3 de dúvidas (10:35–11:00).

Ouvir 2 ou 3 respostas. Chegar a: a cor castanha vem da terra (sedimentos) que a água da chuva arrasta; quanto mais castanha, mais sedimentos. Isso é a TURBIDEZ, um dos sinais de qualidade da água. Mas atenção: a cor não diz tudo. Uma água transparente pode ter bactérias.

Objectivo do módulo: os estudantes sabem o que o satélite consegue ver na água, o que NÃO consegue, e porque é que a plataforma nunca diz "água própria para beber".""",
    "m4-o-que-ve": """FACILITADOR 3, cerca de 3 minutos.

"O satélite não mergulha na água: só vê a luz que sai da superfície. Mas essa luz diz bastante:
- TURBIDEZ: a água com terra (sedimentos) fica castanha. Reflecte mais luz vermelha do que verde. É o que o satélite mede melhor, e o que a plataforma ETE mostra.
- CLOROFILA-A: as algas têm clorofila, como as plantas, e deixam a água esverdeada. Há um índice para isso (NDCI), mas no Incomáti a lama confunde-o: quando a água está barrenta, o índice sobe mesmo sem algas. Por isso a plataforma NÃO diz que há algas sem confirmação no terreno.
- PLANTAS FLUTUANTES: os jacintos-de-água cobrem partes do rio e vêem-se como vegetação em cima da água, sobretudo onde o rio é largo.
- TEMPERATURA: o Landsat tem uma banda térmica (infravermelho térmico), com píxeis de 100 metros: só serve para troços largos."

Honestidade: no projecto, os números absolutos (por exemplo turbidez em FNU) ainda não foram confirmados com medições no rio. Por isso a plataforma compara cada troço com o seu próprio normal (próximos slides).""",
    "m4-cor": """FACILITADOR 3, cerca de 3 minutos.

"É o mesmo sítio, a foz do Incomáti, em duas datas. Na época seca, a água do rio é escura. Na cheia, o rio leva tanta terra que se vê uma enorme mancha castanha a entrar no mar: é a 'pluma' de sedimentos.

O satélite mede esta cor com um índice, o NDTI. É parecido com o NDWI do Workshop 1, mas compara o vermelho com o verde: a terra na água reflecte muita luz vermelha. Quanto maior o NDTI, mais barrenta a água.

A água barrenta não é só um problema de cor: tapa a luz para as plantas e os peixes, entope os filtros das estações de tratamento e costuma trazer o que a chuva lavou dos campos e das casas."

Pergunta: "Em que época do ano esperam a água mais barrenta?" (Na época das chuvas, de Dezembro a Março.)""",
    "m4-trocos": """FACILITADOR 3, cerca de 2 minutos.

"A plataforma não olha para o rio inteiro de uma vez. Dividimos o Incomáti em 9 troços de cerca de 37 quilómetros, desde a fronteira com a África do Sul, em Ressano Garcia, até à foz, depois de Marracuene. Q8 é o troço de Marracuene.

Para cada troço e cada mês desde 2006, juntámos todas as imagens dos satélites Landsat e Sentinel-2 sem nuvens: mais de 8 000 medições. E medimos a cor da água, as plantas em cima da água e a temperatura.

Uma regra importante: cada troço só se compara consigo mesmo. A água perto da foz é naturalmente mais barrenta, por causa da maré. Por isso perguntamos 'este mês está pior do que o normal DESTE troço nesta ÉPOCA?'"

Nota técnica: nos troços estreitos do norte (Q1 a Q6, 50 a 80 m de largura) só o Sentinel-2 (10 m) serve; o Landsat (30 m) só é usado nos troços largos (Q7 a Q9). Os troços Q3 e Q6 têm fiabilidade reduzida.""",
    "m4-anomalias": """FACILITADOR 3, cerca de 3 minutos.

"Cada barra é um mês. Primeiro calculámos o 'normal' de cada mês: por exemplo, como costuma estar a água em Fevereiro em Marracuene, olhando para todos os fevereiros. Depois, para cada mês, vemos quanto ficou acima ou abaixo desse normal. Isso é uma ANOMALIA.

Barras castanhas para cima: água mais barrenta do que o habitual. Barras azuis para baixo: mais limpa. As grandes barras azuis de 2016 coincidem com a seca do El Niño: pouca chuva, pouca terra arrastada para o rio.

É assim que a plataforma decide se a água de um troço está 'normal', 'elevada' ou 'muito elevada': sempre em comparação com o próprio troço."

E as tendências de 20 anos? Pergunta frequente. Resposta honesta: ainda não há uma tendência confirmada. Os satélites mudaram (Landsat 5 e 7, depois Landsat 8 e 9, depois Sentinel-2) e cada um vê as cores de forma um pouco diferente. Numa década com um só satélite (Sentinel-2, desde 2017) alguns troços do norte parecem estar a ficar mais barrentos, mas isso ainda tem de ser confirmado no terreno.""",
    "m4-nao-mede": """FACILITADOR 3, cerca de 2 minutos. Mensagem de saúde pública: dizer devagar.

"O satélite vê a cor. Não vê o pH, o oxigénio, os nutrientes (adubos), os metais nem as bactérias e os vírus. Uma água pode estar transparente e cheia de bactérias. Por isso, a plataforma EYES TO EARTH nunca diz que a água é boa para beber. Diz apenas se a cor está normal ou fora do normal.

E o que fazer com a água do rio? Ferver, ou tratar com uma solução de cloro como a Certeza, sempre. Depois de uma cheia, ainda mais: a cheia lava latrinas, campos e lixo para o rio. A página 'Conselhos' da plataforma explica como tratar a água em casa."

Ligação ao projecto: a plataforma dá conselhos por tipo de pessoa (famílias, agricultores, pescadores, escolas...) sempre que encontra um problema. Para medir pH, oxigénio ou bactérias são precisas amostras de água analisadas em laboratório.""",
    "m4-actividade": """FACILITADOR 3. Actividade em pares, 5 minutos (2 para responder, 3 para corrigir); depois 3 minutos de dúvidas do Módulo 4 (10:57–11:00).

Respostas:
1. VERDADE: a turbidez muda a cor da água (mais vermelho), e o satélite vê a cor.
2. MITO: a turbidez é só a cor; a água pode ter bactérias, metais ou adubos. Tratar sempre a água do rio.
3. MITO: as bactérias são demasiado pequenas e não mudam a cor; só se medem em laboratório.
4. VERDADE: a água perto da foz é naturalmente mais barrenta (maré); compara-se cada troço com o seu próprio normal da mesma época.
5. MITO: sem a maré, o modelo de turbidez não acertava, por mais árvores que tivesse (ROC-AUC 0,44).
6. VERDADE: as nuvens tapam o rio; nesse dia não há medição óptica (o radar Sentinel-1 vê através das nuvens, mas não vê a cor da água).

A afirmação 2 é também a pergunta de verificação do módulo.""",
    "m5": """FACILITADOR 4. Módulo 5: 18 minutos + 2 de dúvidas (11:00–11:20). Inclui a demonstração ao vivo da plataforma.

Ouvir respostas: rádio, megafone, chefes de bairro, WhatsApp, SMS, igreja ou mesquita... Todas são boas. A plataforma EYES TO EARTH junta satélites, previsões e IA para saber MAIS CEDO, e avisa por WhatsApp quem se inscreveu. Mas os canais oficiais e da comunidade continuam essenciais.

Antes do módulo: abrir ete-platform.streamlit.app no portátil do projector uns minutos antes (se ninguém a visitou há muito tempo, pode demorar a acordar). O boletim corre sozinho todas as manhãs. Ter as capturas de ecrã dos slides seguintes como plano B.""",
    "m5-dado-alerta": """FACILITADOR 4, cerca de 2 minutos.

"A plataforma faz cinco coisas, todos os dias:
1. Olha para os satélites: onde está a água agora. O radar Sentinel-1 vê através das nuvens; o Sentinel-2 e o Landsat vêem a cor.
2. Junta as previsões: quanta chuva vai cair na bacia e quanta água o rio vai trazer nos próximos 10 dias (serviço europeu GloFAS).
3. Os modelos e as regras comparam esses números com 20 anos de história do rio: é normal ou é perigoso?
4. Dá um nível de alerta: verde, amarelo, laranja ou vermelho.
5. Avisa: mostra na página e envia mensagem por WhatsApp a quem se inscreveu, com conselhos do que fazer."

Nota para a equipa: o boletim corre sozinho todas as manhãs, nos servidores do GitHub, e a plataforma está publicada em ete-platform.streamlit.app.""",
    "m5-gatilhos": """FACILITADOR 4, cerca de 2 minutos.

"O nível de alerta não é decidido pela IA: é decidido por REGRAS claras, que qualquer pessoa pode verificar. Usamos dois gatilhos:
1. O CAUDAL: quantos metros cúbicos de água passam por segundo no rio em Marracuene, segundo a previsão. Os limites (164, 376 e 970) foram calculados com 25 anos de história do rio (1997–2021): passam-se poucas vezes por ano, ou de anos a anos.
2. A CHUVA ANÓMALA: quando a chuva dos últimos 7 dias na bacia fica muito acima do que é normal nessa época.

Vejam o gráfico da cheia de Janeiro de 2026: o rio passou o amarelo, depois o laranja, e a 19 de Janeiro chegou a quase 3 000 m³/s, três vezes o limite vermelho. Com estas regras e as previsões, o alerta laranja teria saído 4 a 5 dias antes do primeiro mapa da cheia."

Porque é que o alerta usa regras e não a IA? Porque um alerta tem de ser explicável e previsível. A IA entra antes: nos mapas de água, na previsão do caudal e da turbidez. A página "Modelos" da plataforma explica isto.

Nota: esta conclusão foi testada só com a cheia de 2026 (um evento). É dito na plataforma.""",
    "m5-niveis": """FACILITADOR 4, cerca de 2 minutos.

"Quatro cores, como um semáforo com mais um passo. Cada cor tem o seu nome escrito, para quem não distingue bem as cores.

Porque é que o WhatsApp só manda mensagem em laranja e vermelho? Porque se mandássemos uma mensagem todos os dias, as pessoas deixavam de ler. É o mesmo problema dos falsos alarmes do Módulo 2: um sistema que grita 'lobo' sem lobo perde a confiança. Por isso também se envia uma mensagem quando o perigo passa ('fim do alerta')."

Os conselhos exactos de cada nível estão na plataforma (páginas Alertas e Água); os deste slide são um resumo. Em caso de cheia, as indicações das autoridades (INGD, administração do distrito) estão sempre acima da plataforma.""",
    "m5-paginas": """FACILITADOR 4, cerca de 1 minuto (antes da demonstração ao vivo).

"A plataforma tem três grandes partes, como pede o projecto:
- QUANTIDADE: a página Cheias (previsão do caudal para 10 dias, onde a água chega primeiro, o rio visto do espaço e vinte anos de cheias).
- QUALIDADE: a página Água, com a cor da água hoje, os conselhos e o rio inteiro em 9 troços.
- ALERTAS: a inscrição para receber avisos no WhatsApp, só em laranja ou vermelho.

A página O projecto mostra os modelos de IA, as notas que tiveram nos testes, e o que se tentou e não funcionou. É a mesma honestidade que vamos praticar hoje."

As imagens são capturas de ecrã (plano B se não houver Internet).""",
    "m5-demo": """FACILITADOR 4, 5 minutos: a demonstração ao vivo, no projector, em ete-platform.streamlit.app.

Percurso (cerca de 1 minuto por página):
1. INÍCIO: ler em voz alta o nível de hoje e o que quer dizer. Mostrar o selector de língua (PT, EN, FR).
2. PESQUISA: escrever o nome de um bairro na barra com a lupa (por exemplo Machubo) e abrir a página do lugar.
3. CHEIAS: o gráfico do caudal previsto, com a faixa dos cenários, e o mapa «Onde a água chega primeiro». Perguntar: "passa algum limite nos próximos dias?"
4. ÁGUA: a cor da água hoje em Marracuene: mais clara ou mais turva do que o costume?
5. ALERTAS: mostrar o formulário (sem inscrever ninguém ao vivo) e o exemplo de mensagem.

Plano B sem Internet: usar esta captura e as do slide anterior, e descrever cada página.
Se o boletim tiver mais de 36 horas, o Início mostra "previsão indisponível": explicar que é honesto (a plataforma não inventa uma previsão quando não a tem).

Durante a prática, a plataforma fica aberta no projector para quem a quiser explorar.""",
    "m5-oficiais": """FACILITADOR 4, 1 minuto.

"A plataforma EYES TO EARTH é uma ajuda a mais, feita por cientistas, com modelos que podem errar e que dizem quando podem errar. As decisões de evacuação são das autoridades: o INGD (Instituto Nacional de Gestão e Redução do Risco de Desastres), a ARA-Sul (que gere as águas e as barragens do sul), a administração do distrito. Se a plataforma e um aviso oficial disserem coisas diferentes, segue-se o aviso oficial."

Depois: actividade "Que alerta daria?" e 5 minutos de dúvidas do Módulo 4.""",
    "m5-actividade": """FACILITADOR 4. Actividade em pares, 4 minutos; depois 2 minutos de dúvidas do Módulo 5 (11:18–11:20).

Respostas:
A · 120 m³/s: VERDE (abaixo de 164).
B · 250 m³/s: AMARELO (acima de 164, abaixo de 376).
C · 600 m³/s: LARANJA (acima de 376, abaixo de 970).
D · 1 500 m³/s: VERMELHO (acima de 970). Para comparar: o pico de Janeiro de 2026 foi 2 987 m³/s.
E · AMARELO, mas com atenção: a previsão tem incerteza e o máximo provável (450) passa o limite laranja. É por isso que a página Cheias mostra a PROBABILIDADE de passar cada limite e não um só número. Boa discussão: "é melhor avisar cedo e às vezes errar, ou avisar tarde e ter a certeza?"

Transição para o intervalo: "Depois do matabicho, vamos treinar a nossa própria IA. Quando voltarem, o Jupyter Notebook já está aberto em cada computador.\"""",
    "intervalo": """MODERADORA anuncia; LOGÍSTICA serve o matabicho (11:20–11:40).

Durante o intervalo, o Facilitador 6 passa por cada computador: o Jupyter Notebook está aberto na pasta Workshop_2/2_pratica? O notebook 0_verificar_computador.ipynb diz "PRONTO"? O notebook Aula_1_ensinar_com_exemplos.ipynb está aberto? O carregador está ligado?

Os padrinhos sentam-se já junto do seu par para o início da prática.""",
    "resultados-2024": """FACILITADOR 5, 1 minuto. A imagem que resume o dia.

"Em Janeiro de 2024, a correcção da imagem deixou a água quase sem luz verde (0,007) e com um pouco de SWIR (0,018). Para a regra MNDWI, que compara o verde com o SWIR, o resultado ficou negativo: 'não é água'. O rio desapareceu do mapa. A nossa IA, treinada só com a cheia de 2026, olhou para várias pistas ao mesmo tempo (o NIR muito baixo, o NDVI negativo) e encontrou 96% do rio.

Lição: nunca confiar num número sem olhar para a imagem. E é por isso que a IA ajuda: combina muitas pistas que nós não conseguimos escrever à mão."

Nota técnica: o NDWI (verde contra NIR) também encontra o rio em 2024 (91%), mas falha em 2021. Nenhuma regra única funciona em todos os anos.""",
    "licoes": """MODERADORA com o FACILITADOR 5, 13:40–13:45.

Pedir a 4 estudantes diferentes que leiam cada uma das lições em voz alta. Depois perguntar à sala: "Qual destas vos surpreendeu mais?"

Anunciar o par vencedor do quiz relâmpago.

Perguntas e respostas abertas (5 minutos), se houver tempo: a moderadora lê também as perguntas escritas que recolheu durante o dia.""",
    "inquerito-final": """MODERADORA, 13:45–14:00.

13:45–13:52 Questionário OAD pós-workshop (o mesmo do início, para medir o conhecimento adquirido). Ninguém sai sem submeter. Ter cópias em papel.
13:52–13:56 Formulário curto de avaliação do workshop.
13:56–14:00 Entrega dos certificados (chamar cada estudante pelo nome) e foto de grupo.

Trocar os quadros claros pelos QR codes e links reais antes do workshop. Os certificados estão em Workshop_2/0_facilitadores/certificados (um PDF por participante, gerado a partir da lista de presenças).""",
    "obrigado": """MODERADORA, fim às 14:00.

Agradecer aos estudantes, às escolas e famílias, à equipa ETE, ao IAU Office of Astronomy for Development (IAU-OAD) e ao DARA.

Trocar "[endereço da plataforma]" e "[contacto do projecto]" pelos reais antes do workshop.

Lembrar a equipa: recolher as folhas de presenças, os questionários em papel e as fotografias para o relatório OAD.""",
    # ---------- notas dos slides divididos e dos slides novos (versão de 104 slides) ----------
    "dia-manha": """MODERADORA, 30 segundos (com o slide seguinte, 1 minuto ao todo).

Ler só as horas grandes: "Até às 11:20 vamos perceber como uma máquina aprende: cinco módulos curtos, com actividades em pares e um quiz a meio da manhã."

O Módulo 2 (50 minutos) é o centro do dia, com os tipos de aprendizagem e os algoritmos. A moderadora avisa cada facilitador quando faltam 5 minutos.

Quem conduz (para a equipa): registo, Logística e Facilitador 6; abertura e revisão, Moderadora e Facilitador 1; Módulo 1, Facilitador 1; Módulo 2, Facilitador 2; quiz, Moderadora; Módulo 3, Facilitador 5; Módulo 4, Facilitador 3; Módulo 5, Facilitador 4.""",
    "dia-tarde": """MODERADORA, 30 segundos.

"Depois do matabicho, das 11:40 às 13:25, cada par treina os seus modelos no computador, no Jupyter Notebook. Às 13:25 cada par mostra o resultado. Às 14:00 terminamos, com os certificados."

Quem conduz (para a equipa): intervalo, Logística; prática, Facilitador 5, com um padrinho por par (Facilitadores 1, 2, 3, 4 e 7) e o Facilitador 6 nos problemas técnicos; apresentações, Facilitador 5; encerramento, Moderadora.""",
    "revisao-luz": """FACILITADOR 1, 08:25–08:35: cerca de 8 minutos para os quatro slides de revisão (este, cerca de 3 minutos) e 2 minutos de perguntas.

Os participantes do Workshop 2 são estudantes pré-universitários: muitos não estiveram no Workshop 1. Esta revisão é para eles.

"No primeiro workshop aprendemos que um satélite, a 700 km de altura, é como uma máquina fotográfica que vê mais cores do que nós. Vê o azul, o verde e o vermelho, como os nossos olhos, mas também o infravermelho, que nós não vemos. Cada imagem é uma tabela enorme de números: cada quadradinho, o píxel, é um pedaço de chão de 30 por 30 metros.

A água tem uma 'impressão digital': absorve quase todo o infravermelho. Nesta imagem, o rio é a fita escura que serpenteia até ao mar."

Pergunta rápida à sala: "Onde está o rio nesta imagem?" (Alguém aponta.)""",
    "revisao-2021": """FACILITADOR 1, cerca de 1,5 minutos. Este slide e o seguinte são o GANCHO do dia.

"Mas as regras têm um problema. À esquerda está a fotografia do satélite e à direita o que a regra viu, a azul.

Em Janeiro de 2021, depois das chuvas do ciclone Eloise, a água estava tão barrenta que a regra NDWI só encontrou metade do rio: 51%."

Nota para a equipa: o quadro do plano diz que "o NDWI falhou com água barrenta (2021) e com água muito escura (2022 e 2024)". Nos nossos dados, em 2022 e 2024 quem falhou foi o MNDWI (o NDWI funcionou); em 2021 falhou o NDWI. Estes dois slides já estão corrigidos.

Números (percentagem do rio permanente encontrado, rótulos JRC): 2021 NDWI 51%, MNDWI 77%; 2024 MNDWI 0%, NDWI 91%; 2022 MNDWI 66%, NDWI 93%.""",
    "revisao-2024": """FACILITADOR 1, cerca de 1,5 minutos.

"Em Janeiro de 2024, por um efeito da correcção da imagem, a água ficou muito escura e a regra MNDWI não encontrou o rio de todo: 0%. O rio estava lá!

Uma regra fixa é como uma pessoa que só reconhece a água quando ela tem uma cor certa. Hoje vamos tentar outra coisa: em vez de escrevermos a regra, vamos dar exemplos ao computador e deixá-lo aprender."

Transição: "É isto a Inteligência Artificial. Vamos ver o que é, no Módulo 1." """,
    "m1-telemovel": """FACILITADOR 1, cerca de 2 minutos.

Antes de mostrar o slide, perguntar: "Quem usou Inteligência Artificial hoje de manhã?" Normalmente ninguém levanta a mão. Depois mostrar o slide: quase todos usaram.

Explicar dois em detalhe, sempre com a ideia de APRENDER COM EXEMPLOS:
- Filtro de spam: milhões de pessoas carregaram em "isto é spam". Cada clique é um exemplo com a resposta certa. O filtro aprendeu que "GANHOU um PRÉMIO, clique aqui!!!" costuma ser lixo. Na prática vão fazer o mesmo com a água: dar exemplos com a resposta certa.
- Desbloqueio facial: quando configurou o telemóvel, ele fotografou a sua cara de vários ângulos. São os exemplos.

Os outros dois: o assistente de voz aprendeu com muitas horas de voz gravada e escrita; o tradutor com textos traduzidos por pessoas.""",
    "m1-todos-os-dias": """FACILITADOR 1, cerca de 1 minuto.

"E não é só no telemóvel." Cada um aprendeu com exemplos: as recomendações de vídeos e de música com aquilo que milhões de pessoas viram ou ouviram até ao fim; os mapas com as viagens de muitos telemóveis; o ChatGPT com uma enorme quantidade de textos; na saúde, com raios-X já analisados por médicos.

Pergunta rápida: "Qual destes usaram esta semana?" """,
    "m1-seguranca": """FACILITADOR 1, cerca de 1,5 minutos. Tom: informar e fazer pensar, sem pormenores técnicos de armas.

- Aeroportos: as máquinas de raios-X da bagagem mostram uma imagem; em vários aeroportos, um programa de IA treinado com milhares de imagens de malas assinala objectos perigosos (armas, facas, explosivos). Quem decide abrir a mala é sempre um agente. Ponto: a IA ajuda, a pessoa decide.
- Câmaras: o reconhecimento facial é a mesma tecnologia do desbloqueio do telemóvel, mas aplicada a desconhecidos na rua. Erra mais com algumas pessoas do que com outras (depende dos exemplos com que aprendeu) e levanta questões de privacidade.""",
    "m1-armas": """FACILITADOR 1, cerca de 1,5 minutos.

Drones e armas autónomas: já há drones e sistemas militares que usam IA para reconhecer veículos ou pessoas. Desde 2014, os países discutem nas Nações Unidas (em Genebra) regras para as "armas autónomas letais"; muitos defendem que uma pessoa tem de ter sempre o controlo da decisão.

Pergunta para debate (1 minuto, em pares): "Quem deve tomar a decisão final: a máquina ou uma pessoa? Porquê?" Ouvir 2 respostas.

Ligação ao nosso projecto: o nosso modelo encontra água, mas quem decide avisar as pessoas e o que fazer são as autoridades (INGD, ARA-Sul) e as próprias pessoas. A plataforma mostra sempre onde o modelo pode errar.""",
    "m2-modelo": """FACILITADOR 2, cerca de 1 minuto.

"Em Machine Learning, chamamos MODELO à 'caixa' que recebe as pistas e dá uma resposta. Do lado de fora é sempre igual: entra uma lista de números, sai uma resposta.

Dentro da caixa há números (pesos, perguntas, limites). TREINAR é ajustar esses números com exemplos até as respostas ficarem certas. Depois do treino, a caixa fica fixa e usamo-la em casos novos: é PREVER."

Vocabulário que volta em todo o dia: modelo, treinar (aprender), prever.""",
    "m2-modelo-exemplos": """FACILITADOR 2, cerca de 1 minuto.

"Três exemplos. Os números de um píxel entram, sai 'água' ou 'não água'. A imagem de raio-X de uma mala entra, sai 'arma' ou 'sem arma'. O caudal de hoje e a chuva entram, sai o caudal daqui a 3 dias."

Pergunta à sala: "Que outro modelo conhecem? O que entra e o que sai?" (Por exemplo, o filtro de spam: entra a mensagem, sai "spam" ou "normal".)""",
    "m2-dados": """FACILITADOR 2, cerca de 1,5 minutos.

"O segundo ingrediente são as CARACTERÍSTICAS, em inglês 'features': as pistas que o modelo usa para decidir. Para o computador, um píxel não é uma cor: é uma linha de números.

Olhem para a tabela, são píxeis reais de Marracuene de Outubro de 2025. A água (primeira linha) tem pouca luz em tudo, e quase nenhuma no SWIR. A vegetação (segunda) tem o NIR muito alto: as folhas reflectem o infravermelho. O solo nu (terceira) sobe devagar até ao SWIR.

Na prática vamos usar 5 características: as 5 bandas (azul, verde, vermelho, NIR e SWIR). O modelo vai descobrir sozinho quais são as mais úteis."

Pergunta rápida: "Se só pudesse olhar para UMA coluna para encontrar a água, qual escolhia?" (O SWIR: na água é quase 0.)

Se perguntarem pelo terreno: no projecto ETE vimos que o terreno pode fazer o modelo 'decorar' onde costuma haver água, em vez de olhar para a imagem do dia. Por isso, na prática, não usamos o terreno.""",
    "m2-python": """FACILITADOR 2, cerca de 1 minuto. Vocabulário em Python que aparece na prática.

"No computador, a tabela das pistas chama-se X e a coluna dos rótulos chama-se y. Treinar é uma linha: modelo.fit(X, y), quer dizer 'aprende com estes exemplos'. Prever é outra: modelo.predict(X_novo), quer dizer 'dá-me a resposta para estes casos novos'."

É igual para todos os algoritmos do dia: a árvore, o Random Forest, os k vizinhos, a rede neuronal e a recta da regressão. No K-means (sem rótulos) só há fit(X), sem y: vamos ver porquê.""",
    "m2-supervisionada": """FACILITADOR 2, cerca de 1 minuto.

"Na aprendizagem SUPERVISIONADA damos ao computador exemplos COM a resposta certa, o RÓTULO, como um professor que corrige os exercícios. Há dois casos, conforme o tipo de resposta: se é uma categoria (água ou não água), chama-se CLASSIFICAÇÃO; se é um número (o caudal em m³/s), chama-se REGRESSÃO."

Os rótulos são feitos por pessoas. Sem rótulos não há aprendizagem supervisionada.""",
    "m2-supervisionada-exemplos": """FACILITADOR 2, cerca de 1,5 minutos.

Ler a tabela linha a linha e perguntar à sala, antes de ler a última coluna: "isto dá uma categoria ou um número?"

- Spam, scanner do aeroporto, desbloqueio facial e mapa de água: a resposta é uma categoria. Classificação.
- Preço de uma casa e caudal do rio: a resposta é um número. Regressão.

Em todos há RÓTULOS feitos por pessoas: mensagens marcadas como spam, malas verificadas por agentes, fotografias do dono, píxeis marcados por nós, casas vendidas com o preço conhecido, caudais medidos no passado.""",
    "m2-floresta": """FACILITADOR 2, cerca de 1,5 minutos.

"Uma árvore sozinha pode enganar-se, sobretudo com casos estranhos. Por isso usamos uma FLORESTA: muitas árvores.

Para decidir sobre um píxel, todas as árvores votam. Aqui, 5 árvores dizem água e 2 dizem terra: ganha a água. E a parte dos votos dá-nos a PROBABILIDADE: 5 em 7 é 0,71. Com 100 árvores, se 96 disserem água, a probabilidade é 0,96."

Na Aula 2 da prática, os estudantes comparam uma floresta de 100 árvores com uma só árvore.""",
    "m2-floresta-porque": """FACILITADOR 2, cerca de 1 minuto.

"Cada árvore estuda uma parte diferente dos exemplos, escolhida ao acaso. Por isso se chama 'floresta aleatória', Random Forest. É como um júri num concurso: um jurado pode errar, mas a maioria de muitos jurados raramente erra."

O número de árvores é um HIPERPARÂMETRO: um botão que nós escolhemos antes de treinar (a palavra volta no Módulo 3). Na Aula 2 usam 100 árvores e, num exercício, experimentam uma só: o acerto no teste cai muito.""",
    "m2-actividade": """FACILITADOR 2. Actividade em pares, 6 minutos ao todo: 4 para escrever e testar as perguntas (este slide) e 2 para a votação (slide seguinte).

Os 8 píxeis são reais (Sentinel-2, Marracuene, Outubro de 2025).

Uma árvore possível:
- Pergunta 1: "SWIR menor do que 0,1?" Sim: ÁGUA (píxeis 1, 2, 3).
- Pergunta 2: "NIR maior do que SWIR?" Sim: VEGETAÇÃO (4, 5, 6). Não: SOLO (7, 8).

Outras árvores também servem (por exemplo "NIR maior do que 0,25?"). Pedir a 2 pares que leiam as suas perguntas: são árvores diferentes que acertam nos 8 exemplos. Isso também é verdade para o computador: há muitas regras possíveis, e por isso usamos uma floresta.""",
    "m2-actividade-votar": """FACILITADOR 2, 2 minutos; depois 7 minutos de dúvidas do Módulo 2 (09:48–09:55).

X é um píxel de água barrenta da cheia de Janeiro de 2026; Y é solo nu. Com a árvore do slide anterior: X é água (SWIR 0,010) e Y é solo (NIR 0,164 menor do que SWIR 0,317).

Votação: cada par diz em voz alta o que a sua árvore responde para X e para Y. Contar os votos no quadro: é exactamente o que faz o Random Forest. Se algum par errar o X (por ter usado só o NIR, por exemplo), melhor ainda: a floresta corrige-o.""",
    "quiz": """MODERADORA, 09:55–10:05 (10 minutos). Quiz sobre os Módulos 1 e 2: 5 perguntas, uma por slide.

Cada par tem 3 cartões: A, B e C. Em cada pergunta: ler em voz alta, contar até 5 e todos levantam o cartão ao mesmo tempo. Depois clicar: a resposta aparece no slide. Anotar os pontos de cada par num papel (1 ponto por resposta certa). O par vencedor é anunciado no encerramento.

Respostas: 1 B, 2 B, 3 B, 4 A, 5 A.""",
    "quiz-1": """MODERADORA, cerca de 1,5 minutos. Ler, contar até 5, cartões no ar; depois clicar para mostrar a resposta.

Resposta: B. A aprendizagem supervisionada aprende com exemplos e com as respostas certas (os rótulos). A) é a programação clássica, como a regra do Workshop 1; C) é a não supervisionada.""",
    "quiz-2": """MODERADORA, cerca de 1,5 minutos.

Resposta: B, regressão, porque a resposta é um número (m³/s). Se muitos erraram, repetir o truque: "a resposta é um número? Regressão. Uma categoria? Classificação." """,
    "quiz-3": """MODERADORA, cerca de 1,5 minutos.

Resposta: B, os rótulos: são as respostas certas, marcadas por especialistas. Por isso o projecto usou aprendizagem supervisionada. As pistas são as cores (as bandas) de cada píxel; o algoritmo é o método, por exemplo a floresta aleatória.""",
    "quiz-4": """MODERADORA, cerca de 1,5 minutos.

Resposta: A, classificação: a resposta é uma categoria e há malas marcadas por pessoas (os rótulos).""",
    "quiz-5": """MODERADORA, cerca de 1,5 minutos. Somar os pontos de cada par.

Resposta: A, água: ganha a maioria dos vizinhos, 4 contra 1.

Transição: "Já sabemos como as máquinas aprendem. Mas como sabemos se aprenderam BEM? É o Módulo 3, com o Facilitador 5." """,
    "m3-divisao": """FACILITADOR 5, cerca de 1,5 minutos.

"Na escola há duas fases: estudar e fazer o exame. No Machine Learning é igual.

TREINO: o modelo estuda os exemplos com a resposta certa. Em Python, isto é uma linha: modelo.fit(X, y). X são as características (a tabela de números) e y são os rótulos (1 = água, 0 = não água). 'fit' quer dizer 'ajustar': o modelo ajusta-se aos exemplos.

TESTE: damos ao modelo dados que ele nunca viu, sem lhe dizer a resposta. Ele PREVÊ: modelo.predict(...). Depois comparamos com a resposta certa e damos a nota.

Se o professor desse no exame as mesmas perguntas do caderno de exercícios, a nota não diria se o aluno aprendeu ou se decorou."

A barra mostra a divisão habitual: cerca de 70% dos dados para treinar e 30% para o teste, que fica "fechado à chave" até ao fim. Estas duas linhas de código aparecem na prática: os estudantes vão reconhecê-las.""",
    "m3-futuro": """FACILITADOR 5, cerca de 1 minuto.

"Quando o tempo importa, como nas previsões do rio, o teste é o FUTURO: treina-se com 2006 a 2018 e testa-se com 2019 a 2026, anos que o modelo nunca viu. Misturar os dias ao acaso seria copiar: um dia e o seguinte são quase iguais, e o modelo veria no treino o dia ao lado do dia do exame."

É assim na Aula 4 da prática. Na previsão do tempo é igual: uma previsão só se avalia com dias que ainda não tinham acontecido quando ela foi feita.""",
    "m3-regra-de-ouro": """FACILITADOR 5, cerca de 1,5 minutos. Ler a regra de ouro em voz alta e pedir à turma que a repita.

"A regra de ouro do teste: nunca dar a nota a um modelo com rótulos que ele próprio fez. Se o modelo fizer o mapa e depois o corrigirmos com o mesmo mapa, tira sempre 20, e não aprendemos nada.

O nosso exame vem de fora: o Copernicus EMS, o serviço europeu que faz mapas de emergência quando há cheias, sismos ou incêndios. Em Janeiro de 2026 fizeram mapas da cheia do Incomáti, com outras imagens de satélite. A azul, as amostras de água; a laranja, as de não água. O nosso modelo nunca viu estes mapas." """,
    "m3-exame-erro": """FACILITADOR 5, cerca de 1 minuto. Uma lição de honestidade científica.

"Até o exame tinha um erro. O EMS marca a água DA CHEIA, mas não o rio de sempre. Algumas amostras de 'não água' ficaram em cima do leito do rio. Quando corrigimos o nosso modelo com elas, quase todos os 'falsos alarmes' estavam no rio: o modelo tinha razão e o exame não! Corrigimos o exame com o arquivo JRC, que guarda 38 anos de água vista pelo Landsat (1984–2021)."

Números: 4 419 píxeis passaram de "não água" a "água"; sem a correcção, 2 883 dos 2 901 falsos alarmes estavam no rio.

Mensagem: um exame também pode errar. Quando o modelo e o exame discordam, vale a pena ir ver quem tem razão.""",
    "m3-notas": """FACILITADOR 5, cerca de 2,5 minutos. Todas as notas vão de 0 a 1; quanto mais perto de 1, melhor. Valores do modelo da equipa no exame EMS.

- ACERTO: a mais fácil. 0,97 = 97 em cada 100 píxeis certos. Cuidado: se 95% da imagem fosse terra, um modelo que dissesse sempre "terra" teria 95% de acerto sem servir para nada.
- IoU (Intersection over Union, "sobreposição"): pega no mapa de água do modelo e no mapa verdadeiro e vê quanto se sobrepõem. É a nota mais usada para mapas de cheia. Próximo slide.
- F1: equilibra os dois erros (falsos alarmes e água perdida). Só é alta se os dois forem baixos.
- KAPPA: corrige a sorte. 0 = tão bom como atirar uma moeda ao ar; acima de 0,8 = muito bom.
- ROC-AUC: olha para as probabilidades. 1 = o modelo dá sempre mais probabilidade de água à água do que à terra; 0,5 = ao calhas.

Mensagem honesta: nesta imagem limpa, a regra MNDWI do Workshop 1 ainda tem IoU 0,99, melhor do que o modelo (0,96). Não é vergonha: numa imagem fácil, uma boa regra chega. A IA mostra o seu valor quando a água muda (2021, 2022, 2024), como os pares vão ver na Aula 2, quando levam o modelo a outro ano.""",
    "m3-hiperparametros": """FACILITADOR 5, cerca de 2 minutos.

"Há dois tipos de números num modelo. Os PARÂMETROS são aprendidos com os exemplos: os pesos da recta, as perguntas da árvore. Os HIPERPARÂMETROS são escolhidos por nós ANTES de treinar: quantas árvores, que profundidade, que k, quantos grupos, a partir de que probabilidade dizemos 'água'.

Como se escolhem? Como no gráfico anterior: experimenta-se e vê-se o erro no TESTE (ou numa parte de validação), nunca no treino."

Na prática, os pares mudam três hiperparâmetros numa só linha e comparam o resultado no teste: o número de árvores (Aula 2), o K do K-means (Aula 3) e a profundidade da árvore (Aula 4).""",
}
