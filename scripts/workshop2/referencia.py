"""Respostas de referência do Workshop 2, calculadas com o MESMO código dos notebooks (FERRAMENTAS_IA).

    .venv/bin/python -m workshop2.referencia      (a partir da pasta scripts/)

Escreve Workshop_2/0_facilitadores/resultados_de_referencia.json com tudo o que os notebooks, os slides
e o manual citam: o modelo da equipa (pontos de exemplos_da_equipa.json), as notas no teste EMS, as regras
do Workshop 1, cada ano antes e depois de "ensinar" o modelo, o efeito do terreno e a rede neuronal.
"""

import json

import numpy as np

from .comum import ANOS_TESTE, DADOS_SLIDES, FAC, PRATICA, ferramentas_namespace

N_ARVORES = 100


def calcular():
    f = ferramentas_namespace()
    dados = PRATICA / "dados"
    import os
    os.chdir(dados)                                      # as ferramentas procuram os ficheiros aqui
    ex = json.loads((dados / "exemplos_da_equipa.json").read_text())
    extra = dict(np.load(DADOS_SLIDES / "camadas_extra.npz"))
    cheia, seca = f["carregar"]("incomati_2026_cheia.npz"), f["carregar"](str(DADOS_SLIDES / "incomati_2026_seca.npz"))
    CAR = f["BANDAS"] + f["INDICES"]
    RFC = f["RandomForestClassifier"]
    X, y = f["exemplos"](cheia, ex["2026"]["agua"], ex["2026"]["nao_agua"], CAR)
    modelo = RFC(n_estimators=N_ARVORES, random_state=0, n_jobs=-1).fit(X, y)
    p = f["prever"](modelo, cheia, CAR)
    ems = extra["ems_2026"]
    teste = (ems >= 0) & ~cheia["nuvem"]
    verdade = ems[teste]
    r = {"n_pontos_agua": len(ex["2026"]["agua"]), "n_pontos_terra": len(ex["2026"]["nao_agua"]),
         "pixeis_treino": int(len(y)), "pixeis_treino_agua": int(y.sum()),
         "acerto_treino": float((modelo.predict(X) == y).mean()),
         "pixeis_teste_ems": int(teste.sum()), "pixeis_teste_ems_agua": int(verdade.sum())}
    r["ems_modelo"] = f["notas"](verdade, (p[teste] > 0.5).astype(int), p[teste])
    r["ems_mndwi"] = f["notas"](verdade, (cheia["mndwi"][teste] > 0).astype(int), np.nan_to_num(cheia["mndwi"][teste]))
    r["ems_ndwi"] = f["notas"](verdade, (cheia["ndwi"][teste] > 0).astype(int), np.nan_to_num(cheia["ndwi"][teste]))
    prev = (p[teste] > 0.5).astype(int)
    r["ems_contagens"] = {"agua_certa": int(((verdade == 1) & (prev == 1)).sum()), "terra_certa": int(((verdade == 0) & (prev == 0)).sum()),
                          "falso_alarme": int(((verdade == 0) & (prev == 1)).sum()), "agua_perdida": int(((verdade == 1) & (prev == 0)).sum())}
    r["importancias"] = dict(zip(CAR, modelo.feature_importances_.round(3).tolist()))
    zona_vista = cheia["zona"] & ~cheia["nuvem"]
    r["agua_prevista_ha"] = float(((p > 0.5) & zona_vista).sum() * 0.09)
    r["agua_prevista_seca_ha"] = float(((f["prever"](modelo, seca, CAR) > 0.5) & seca["zona"] & ~seca["nuvem"]).sum() * 0.09)

    # o "teste batoteiro": dividir os mesmos píxeis ao acaso dá uma nota quase perfeita
    rng = np.random.default_rng(0)
    idx = rng.permutation(len(y))
    meio = len(y) * 7 // 10
    m2 = RFC(n_estimators=N_ARVORES, random_state=0, n_jobs=-1).fit(X[idx[:meio]], y[idx[:meio]])
    r["acerto_divisao_ao_acaso"] = float((m2.predict(X[idx[meio:]]) == y[idx[meio:]]).mean())

    # cada ano: antes (só 2026) e depois de ensinar (2026 + 5 + 5 pontos desse ano)
    va, vt = extra["verif_agua"], extra["verif_terra"]
    r["anos"] = {}
    for ano in ANOS_TESTE:
        img = f["carregar"](f"incomati_{ano}_chuvosa.npz")
        ok = ~img["nuvem"]
        pa = f["prever"](modelo, img, CAR)
        Xa, ya = f["exemplos"](img, ex[str(ano)]["agua"], ex[str(ano)]["nao_agua"], CAR)
        m3 = RFC(n_estimators=N_ARVORES, random_state=0, n_jobs=-1).fit(np.concatenate([X, Xa]), np.concatenate([y, ya]))
        pd_ = f["prever"](m3, img, CAR)
        p26 = f["prever"](m3, cheia, CAR)
        r["anos"][str(ano)] = {
            "data": img["data"], "satelite": img["satelite"], "caudal": img["caudal_m3s"],
            "nuvem_pct": float(100 * img["nuvem"][img["zona"]].mean()),
            "antes_rio": float(100 * (pa[va & ok] > 0.5).mean()), "antes_terra": float(100 * (pa[vt & ok] > 0.5).mean()),
            "depois_rio": float(100 * (pd_[va & ok] > 0.5).mean()), "depois_terra": float(100 * (pd_[vt & ok] > 0.5).mean()),
            "mndwi_rio": float(100 * (img["mndwi"][va & ok] > 0).mean()), "mndwi_terra": float(100 * (img["mndwi"][vt & ok] > 0).mean()),
            "ndwi_rio": float(100 * (img["ndwi"][va & ok] > 0).mean()), "ndwi_terra": float(100 * (img["ndwi"][vt & ok] > 0).mean()),
            "depois_ems_2026": f["notas"](verdade, (p26[teste] > 0.5).astype(int)),
        }

    # e se juntarmos o terreno?
    CT = CAR + f["TERRENO"]
    f["juntar_terreno"](cheia, extra)
    f["juntar_terreno"](seca, extra)
    Xt, yt = f["exemplos"](cheia, ex["2026"]["agua"], ex["2026"]["nao_agua"], CT)
    mt = RFC(n_estimators=N_ARVORES, random_state=0, n_jobs=-1).fit(Xt, yt)
    pt = f["prever"](mt, cheia, CT)
    r["terreno_ems"] = f["notas"](verdade, (pt[teste] > 0.5).astype(int), pt[teste])
    r["terreno_importancias"] = dict(zip(CT, mt.feature_importances_.round(3).tolist()))
    r["terreno_agua_na_seca_ha"] = float(((f["prever"](mt, seca, CT) > 0.5) & seca["zona"] & ~seca["nuvem"]).sum() * 0.09)

    # extra: uma rede neuronal pequena (a ideia do deep learning) com os mesmos exemplos
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    rede = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(16, 16), max_iter=800, random_state=0)).fit(X, y)
    pr = rede.predict_proba(f["tabela"](cheia, CAR))[:, 1].reshape(cheia["verde"].shape)
    r["rede_ems"] = f["notas"](verdade, (pr[teste] > 0.5).astype(int), pr[teste])
    img24 = f["carregar"]("incomati_2024_chuvosa.npz")
    pr24 = rede.predict_proba(f["tabela"](img24, CAR))[:, 1].reshape(cheia["verde"].shape)
    r["rede_2024_rio"] = float(100 * (pr24[va & ~img24["nuvem"]] > 0.5).mean())

    # Parte C: quatro algoritmos de classificação, os mesmos exemplos, o mesmo exame
    r["algoritmos"] = {}
    img21 = f["carregar"]("incomati_2021_chuvosa.npz")
    for nome, m in algoritmos().items():
        m.fit(X, y)
        pm = f["prever"](m, cheia, CAR)
        p21 = f["prever"](m, img21, CAR)
        p24 = f["prever"](m, img24, CAR)
        r["algoritmos"][nome] = {**f["notas"](verdade, (pm[teste] > 0.5).astype(int)),
                                 "rio_2021": float(100 * (p21[va & ~img21["nuvem"]] > 0.5).mean()),
                                 "rio_2024": float(100 * (p24[va & ~img24["nuvem"]] > 0.5).mean())}

    # Parte E: K-means, sem rótulos. Os grupos de "água" são os que, no exame, têm sobretudo água
    from sklearn.cluster import KMeans
    from .comum import K_GRUPOS
    valido = (cheia["zona"] & ~cheia["nuvem"]).ravel()
    tab = f["tabela"](cheia, CAR)
    r["kmeans"] = {}
    for k in [2, 3, K_GRUPOS, 6]:
        km = make_pipeline(StandardScaler(), KMeans(n_clusters=k, n_init=3, random_state=0)).fit(tab[valido])
        g = km.predict(tab).reshape(cheia["verde"].shape)
        agua = [int(c) for c in range(k) if verdade[g[teste] == c].mean() > 0.5]
        tamanhos = np.bincount(g.ravel()[valido], minlength=k)
        r["kmeans"][str(k)] = {**f["notas"](verdade, np.isin(g[teste], agua).astype(int)), "grupos_agua": agua,
                               "pct_por_grupo": (100 * tamanhos / tamanhos.sum()).round(1).tolist()}

    r["regressao"] = regressao()
    r["avancado"] = avancado()
    return r


def avancado():
    """Parte H: corre as MESMAS células de código do notebook 5_nivel_avancado.ipynb e devolve RESULTADOS."""
    import os
    import tempfile
    from pathlib import Path

    import matplotlib
    matplotlib.use("Agg")
    from .avancado import codigo_das_analises
    antes = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.symlink(PRATICA / "dados", Path(tmp) / "dados")     # o notebook procura os dados em dados/
        os.chdir(tmp)
        ns = {}
        try:
            for fonte in codigo_das_analises():
                exec(fonte.replace("plt.show()", "plt.close('all')"), ns)
        finally:
            os.chdir(antes)
    return json.loads(json.dumps(ns["RESULTADOS"], default=float))


def algoritmos():
    """Os quatro classificadores da Parte C (iguais aos do notebook)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeClassifier
    return {"Árvore de decisão": DecisionTreeClassifier(random_state=0),
            "k vizinhos (k = 5)": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)),
            "Random Forest (100 árvores)": RandomForestClassifier(n_estimators=N_ARVORES, random_state=0, n_jobs=-1),
            "Rede neuronal (16 + 16)": make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(16, 16), max_iter=800, random_state=0))}


def regressao():
    """Parte F: prever o caudal daqui a HORIZONTE dias. Treino até 2018, exame 2019-2026 (o futuro)."""
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.tree import DecisionTreeRegressor
    from .comum import HORIZONTE, PISTAS_CAUDAL, ULTIMO_ANO_TREINO
    d = pd.read_csv(PRATICA / "dados/caudal_e_chuva_diarios.csv", parse_dates=["data"])
    d["caudal_daqui_a_3_dias"] = d["caudal_m3s"].shift(-HORIZONTE)
    d = d.dropna()
    treino, exame = d[d["data"].dt.year <= ULTIMO_ANO_TREINO], d[d["data"].dt.year > ULTIMO_ANO_TREINO]
    alvo = "caudal_daqui_a_3_dias"
    out = {"dias_treino": int(len(treino)), "dias_exame": int(len(exame)),
           "max_treino": float(treino["caudal_m3s"].max()), "max_exame": float(exame["caudal_m3s"].max())}
    lin = LinearRegression().fit(treino[PISTAS_CAUDAL], treino[alvo])
    p = lin.predict(exame[PISTAS_CAUDAL])
    out["linear"] = {"MAE": float(mean_absolute_error(exame[alvo], p)), "R2": float(r2_score(exame[alvo], p)),
                     "coeficientes": dict(zip(PISTAS_CAUDAL, lin.coef_.round(3).tolist())), "intercepto": float(lin.intercept_)}
    so_chuva = PISTAS_CAUDAL[1:]
    l2 = LinearRegression().fit(treino[so_chuva], treino[alvo])
    p2 = l2.predict(exame[so_chuva])
    out["so_chuva"] = {"MAE": float(mean_absolute_error(exame[alvo], p2)), "R2": float(r2_score(exame[alvo], p2))}
    out["igual_a_hoje"] = {"MAE": float(mean_absolute_error(exame[alvo], exame["caudal_m3s"])),
                           "R2": float(r2_score(exame[alvo], exame["caudal_m3s"]))}
    out["arvore_por_profundidade"] = {}
    for prof in [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20]:
        a = DecisionTreeRegressor(max_depth=prof, random_state=0).fit(treino[PISTAS_CAUDAL], treino[alvo])
        out["arvore_por_profundidade"][str(prof)] = {
            "R2_treino": float(r2_score(treino[alvo], a.predict(treino[PISTAS_CAUDAL]))),
            "R2_exame": float(r2_score(exame[alvo], a.predict(exame[PISTAS_CAUDAL]))),
            "MAE_exame": float(mean_absolute_error(exame[alvo], a.predict(exame[PISTAS_CAUDAL])))}
    # a cheia de janeiro de 2026: em que dia o modelo passou o limite laranja (376 m³/s) para daqui a 3 dias?
    j = exame[(exame["data"] >= "2025-12-20") & (exame["data"] <= "2026-02-15")].copy()
    j["previsto"] = lin.predict(j[PISTAS_CAUDAL])
    laranja_prev = j[j["previsto"] >= 376]["data"].min()
    laranja_obs = j[j[alvo] >= 376]["data"].min()
    out["cheia_2026"] = {"primeiro_dia_previsao_laranja": str(laranja_prev.date()), "primeiro_dia_alvo_laranja": str(laranja_obs.date()),
                         "pico": float(j["caudal_m3s"].max()), "pico_dia": str(j.loc[j["caudal_m3s"].idxmax(), "data"].date()),
                         "maior_previsao": float(j["previsto"].max())}
    return out


def main():
    r = calcular()
    destino = FAC / "resultados_de_referencia.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k != "anos"}, indent=1, ensure_ascii=False)[:3000])
    for ano, v in r["anos"].items():
        print(ano, {k: (round(x, 1) if isinstance(x, float) else x) for k, x in v.items() if k != "depois_ems_2026"},
              "EMS depois", {k: round(x, 3) for k, x in v["depois_ems_2026"].items()})


if __name__ == "__main__":
    main()
