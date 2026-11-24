# Publicação: ponto de situação do ETE (semanas 1 e 2)

Imagens em inglês (por esta ordem, como carrossel): 1_capa.png, 2_radar_cheia.png, 3_caudal_20_anos.png,
4_terreno.png, 5_trocos_do_rio.png. Versão em português das imagens: pt/. Refazer com: `.venv/bin/python scripts/build_social_posts.py`

Páginas a identificar (escrever @ e escolher a página oficial na lista):
- IAU-OAD: LinkedIn "IAU Office of Astronomy for Development" (linkedin.com/company/iau-office-of-astronomy-for-development);
  Facebook "@astro4dev" (facebook.com/astro4dev)
- DARA: LinkedIn "DARA Project" (linkedin.com/company/dara-project). O site da DARA não indica página no Facebook:
  no Facebook, escrever o nome por extenso e o site dara-project.org.
- Líder técnico: @Ezequias Miocha (perfil pessoal; escrever @ e escolher o perfil na lista).

---

## English (main text: LinkedIn and Facebook)

🛰️ Eyes to Earth (ETE): watching over the Incomati River

In January 2026 the Incomati brought Marracuene its largest flood in 20 years. Eyes to Earth (ETE) uses satellites and machine learning to monitor the river's water quality and warn communities before the water arrives.

We have finished our first two weeks, focused on data. This work was led by our Technical Lead, @Ezequias Miocha, who designed and built the data pipeline:

📡 20 years of satellite imagery (Landsat, Sentinel-1, Sentinel-2), rainfall, soil moisture, temperature and river discharge, all on one common grid.
🌧️ Sentinel-1 radar sees through clouds: during the January 2026 flood it showed more than 200 km² of new water in our study area, checked against the official Copernicus EMS map.
⛰️ Terrain layers (elevation, height above the river, slope, land cover) that show where water goes first.
💧 The river split into 9 sections, from the border at Ressano Garcia to the mouth, to follow water turbidity from space.

Next: training and testing the flood-detection and water-quality models.

Thank you to the IAU Office of Astronomy for Development (@IAU-OAD) and DARA – Development in Africa with Radio Astronomy (@DARA) for their support.

#EyesToEarth #Mozambique #EarthObservation #MachineLearning #Floods #WaterQuality #Sentinel1 #Copernicus #Astro4Dev #DARA

---

## Português (opcional)

🛰️ Eyes to Earth (ETE): os olhos no rio Incomáti

Em janeiro de 2026, o Incomáti trouxe a maior cheia dos últimos 20 anos a Marracuene. O projecto Eyes to Earth (ETE) usa satélites e Machine Learning para monitorizar a qualidade da água do rio e avisar as comunidades antes que a água chegue.

Concluímos as duas primeiras semanas de trabalho, dedicadas aos dados. Esta fase foi liderada pelo nosso Líder Técnico, @Ezequias Miocha, que concebeu e construiu todo o processamento dos dados:

📡 Juntámos 20 anos de imagens de satélite (Landsat, Sentinel-1 e Sentinel-2), chuva, humidade do solo, temperatura e caudal do rio, tudo na mesma grelha.
🌧️ O radar Sentinel-1 vê através das nuvens: na cheia de janeiro de 2026 detectámos mais de 200 km² de água nova na área de estudo, e comparámos o resultado com o mapa oficial do Copernicus EMS.
⛰️ Preparámos o terreno: altitude, altura acima do rio, declive e ocupação do solo, que mostram para onde a água vai primeiro.
💧 Dividimos o rio em 9 troços, da fronteira em Ressano Garcia até à foz, para seguir a turbidez da água por satélite.

Próximo passo: treinar e testar os modelos de detecção de cheias e de qualidade da água.

Um agradecimento ao IAU Office of Astronomy for Development (@IAU-OAD) e à DARA (Development in Africa with Radio Astronomy) (@DARA) pelo apoio.

#EyesToEarth #Moçambique #Marracuene #RioIncomati #ObservaçãoDaTerra #MachineLearning #Cheias #QualidadeDaÁgua #Sentinel1 #Copernicus #Astro4Dev #DARA

---

## Se publicar a partir do seu perfil pessoal

Troque a frase do líder técnico por esta (falar de si próprio na primeira pessoa soa mais natural):

EN: "As Technical Lead, I led this first phase and built the data pipeline:"
PT: "Como Líder Técnico, liderei esta primeira fase e construí o processamento dos dados:"
