"""Cria o projeto QGIS do ETE já configurado: qgis/ete_marracuene.qgz

Correr com o Python do sistema (o que traz o QGIS), não com o .venv:

    QT_QPA_PLATFORM=offscreen /usr/bin/python3 scripts/build_qgis_project.py

O projeto guarda caminhos relativos, por isso funciona em qualquer computador
que tenha a mesma pasta do projeto. Pode ser gerado de novo a qualquer momento;
o que for editado em labels.gpkg não é tocado.
"""

import sys
from pathlib import Path

from qgis.core import (QgsApplication, QgsCategorizedSymbolRenderer, QgsColorRampShader,
                       QgsContrastEnhancement, QgsCoordinateReferenceSystem, QgsFillSymbol, QgsLineSymbol,
                       QgsMarkerSymbol, QgsMultiBandColorRenderer, QgsProject, QgsRasterLayer,
                       QgsRendererCategory, QgsSingleBandGrayRenderer, QgsSingleBandPseudoColorRenderer,
                       QgsSingleSymbolRenderer, QgsStyle, QgsVectorLayer)

ROOT = Path(__file__).resolve().parents[1]
NAME = "marracuene"
EVENT, WET, DRY = "2026-01", "2023-02", "2022-08"

app = QgsApplication([], False)
app.initQgis()
project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:32736"))
project.setTitle("ETE - Rio Incomáti, Marracuene")
root = project.layerTreeRoot()
missing = []


def raster(path, title):
    layer = QgsRasterLayer(str(ROOT / path), title)
    if not layer.isValid():
        missing.append(path)
        return None
    return layer


def vector(path, title, layer_name=None):
    uri = str(ROOT / path) + (f"|layername={layer_name}" if layer_name else "")
    layer = QgsVectorLayer(uri, title, "ogr")
    if not layer.isValid():
        missing.append(path)
        return None
    return layer


def colours(layer, band, vmin, vmax, ramp, invert=False):
    """Escala de cores contínua entre vmin e vmax."""
    if layer is None:
        return None
    colour_ramp = QgsStyle.defaultStyle().colorRamp(ramp)
    if invert:
        colour_ramp.invert()
    renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), band)
    renderer.setClassificationMin(vmin)
    renderer.setClassificationMax(vmax)
    renderer.createShader(colour_ramp, QgsColorRampShader.Interpolated, QgsColorRampShader.Continuous, 0, False)   # False: valores fora da escala ficam com a cor do extremo
    layer.setRenderer(renderer)
    return layer


def _stretch(layer, band, vmin, vmax):
    enhancement = QgsContrastEnhancement(layer.dataProvider().dataType(band))
    enhancement.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
    enhancement.setMinimumValue(vmin)
    enhancement.setMaximumValue(vmax)
    return enhancement


def grey(layer, band, vmin, vmax):
    if layer is None:
        return None
    renderer = QgsSingleBandGrayRenderer(layer.dataProvider(), band)
    renderer.setContrastEnhancement(_stretch(layer, band, vmin, vmax))
    layer.setRenderer(renderer)
    return layer


def true_colour(layer, red, green, blue, vmax):
    if layer is None:
        return None
    renderer = QgsMultiBandColorRenderer(layer.dataProvider(), red, green, blue)
    renderer.setRedContrastEnhancement(_stretch(layer, red, 0, vmax))
    renderer.setGreenContrastEnhancement(_stretch(layer, green, 0, vmax))
    renderer.setBlueContrastEnhancement(_stretch(layer, blue, 0, vmax))
    layer.setRenderer(renderer)
    return layer


def symbol(layer, sym):
    if layer is not None:
        layer.setRenderer(QgsSingleSymbolRenderer(sym))
    return layer


def add(group, layer, visible=True):
    if layer is None:
        return
    project.addMapLayer(layer, False)
    group.addLayer(layer).setItemVisibilityChecked(visible)


def month_group(title, month, expanded, visible):
    group = root.addGroup(title)
    idx = f"data/interim/features/indices/{month}"
    # bandas: vv, vh, vv_vh_ratio, dvv, dvh, vv_p10, vh_p10, dvv_p10, dvh_p10
    s1 = f"{idx}/sentinel1_features_{NAME}_{month}_10m.tif"
    add(group, colours(raster(s1, f"Radar: queda do VH no momento mais escuro {month} (azul = água nova)"), 9, -15, 15, "RdBu", invert=True), visible)
    add(group, grey(raster(s1, f"Radar VH no momento mais escuro {month} (preto = água)"), 7, -32, -10), False)
    add(group, colours(raster(s1, f"Radar ΔVV da mediana {month} (azul = água nova)"), 4, -6, 6, "RdBu", invert=True), False)
    add(group, grey(raster(s1, f"Radar VV mediana {month} (escuro = água)"), 1, -25, 0), False)
    s2i = f"{idx}/sentinel2_indices_{NAME}_{month}_10m.tif"          # bandas: ndwi, mndwi, ndvi, ndmi, ...
    add(group, colours(raster(s2i, f"MNDWI Sentinel-2 {month} (azul = água)"), 2, -0.6, 0.6, "RdBu"), False)
    add(group, colours(raster(s2i, f"NDVI Sentinel-2 {month} (verde = vegetação)"), 3, 0, 0.9, "RdYlGn"), False)
    s2 = f"data/raw/optical/sentinel2/{month[:4]}/sentinel2_{NAME}_{month}_10m.tif"   # blue, green, red, ...
    add(group, true_colour(raster(s2, f"Sentinel-2 cor verdadeira {month}"), 3, 2, 1, 0.25), visible)
    group.setExpanded(expanded)
    group.setItemVisibilityChecked(visible)
    return group


def ems_group():
    """Mapas diários da cheia de janeiro de 2026 feitos pelo Copernicus EMS (ativação EMSR857)."""
    group = root.addGroup("3. Cheia de jan. 2026 dia a dia (Copernicus EMS)")
    base = "data/raw/labels/ems_unosat/EMSR857_AOI06_Palmeira"
    days = [("EMSR857_AOI06_DEL_MONIT04_v1", "24 jan (ICEYE)", "0,60,200,150"),
            ("EMSR857_AOI06_DEL_MONIT03_v2", "23 jan (Sentinel-1)", "0,120,230,150"),
            ("EMSR857_AOI06_DEL_MONIT01_v1", "18 jan (COSMO-SkyMed)", "70,170,250,150"),
            ("EMSR857_AOI06_DEL_PRODUCT_v1", "17 jan (Sentinel-1)", "150,210,255,150")]
    for i, (folder, label, colour) in enumerate(days):
        layer = vector(f"{base}/{folder}/{folder.replace('_v1', '').replace('_v2', '')}_observedEventA_{folder[-2:]}.shp", f"Alagado a {label}")
        add(group, symbol(layer, QgsFillSymbol.createSimple({"color": colour, "outline_style": "no"})), i == 0)
    area = "EMSR857_AOI06_DEL_MONIT04_v1"
    add(group, symbol(vector(f"{base}/{area}/EMSR857_AOI06_DEL_MONIT04_areaOfInterestA_v1.shp", "Área analisada pelo Copernicus"),
                      QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "255,140,0", "outline_style": "dash", "outline_width": "0.6"})), True)
    group.setExpanded(True)


# ----------------------------------------------------------------------------- grupos (de cima para baixo)
g = root.addGroup("1. Área de estudo")
add(g, symbol(vector("data/raw/aoi/marracuene_district.geojson", "Distrito de Marracuene"),
              QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "0,0,0", "outline_width": "0.7"})))
add(g, symbol(vector("data/raw/static/hydrography/rivers_incomati.geojson", "Linhas de água (HydroSHEDS, aproximadas)"),
              QgsLineSymbol.createSimple({"color": "30,100,220", "width": "0.3"})), False)
add(g, symbol(vector("data/interim/features/river_channel_marracuene.gpkg", "Canal real do Incomáti (JRC + terreno)"),
              QgsFillSymbol.createSimple({"color": "0,90,255,160", "outline_color": "0,60,200", "outline_width": "0.2"})))
add(g, symbol(vector("data/raw/aoi/aoi.geojson", "Retângulo das imagens"),
              QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "220,30,30", "outline_style": "dash", "outline_width": "0.5"})), False)
add(g, symbol(vector("data/raw/aoi/incomati_basin.geojson", "Bacia do Incomáti"),
              QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "30,60,160", "outline_width": "0.6"})), False)

g = root.addGroup("2. Rótulos (para desenhar)")
labels = vector("data/raw/labels/manual/labels.gpkg", "Amostras água / não-água", "amostras")
if labels is not None:
    cats = [QgsRendererCategory("water", QgsFillSymbol.createSimple({"color": "0,120,255,120", "outline_color": "0,60,200", "outline_width": "0.5"}), "água"),
            QgsRendererCategory("non_water", QgsFillSymbol.createSimple({"color": "255,140,0,120", "outline_color": "200,90,0", "outline_width": "0.5"}), "não é água"),
            QgsRendererCategory("", QgsFillSymbol.createSimple({"color": "200,200,200,120", "outline_color": "90,90,90", "outline_width": "0.5"}), "por classificar")]
    labels.setRenderer(QgsCategorizedSymbolRenderer("class", cats))
add(g, labels)
ems = vector("data/raw/labels/ems_unosat/ems_labels.gpkg", "Referência Copernicus EMS, jan 2026 (EMSR857)", "amostras")
if ems is not None:
    ems.setRenderer(QgsCategorizedSymbolRenderer("class", [
        QgsRendererCategory("water", QgsFillSymbol.createSimple({"color": "0,170,255,150", "outline_style": "no"}), "alagado"),
        QgsRendererCategory("non_water", QgsFillSymbol.createSimple({"color": "255,200,120,90", "outline_style": "no"}), "não alagado")]))
add(g, ems, False)

g = root.addGroup("Modelos: risco e cheia (Semana 3)")
add(g, symbol(vector("data/processed/maps/modelo_b/cheia_marracuene_2026-01.gpkg", "Modelo B: cheia de jan. 2026 (polígonos)"),
              QgsFillSymbol.createSimple({"color": "0,90,220,150", "outline_style": "no"})), False)
add(g, colours(raster("data/processed/maps/modelo_b/agua_marracuene_2026-01_10m.tif", "Modelo B: probabilidade de água, jan. 2026"), 1, 0, 1, "Blues"), False)
add(g, colours(raster("data/processed/maps/modelo_a/suscetibilidade_marracuene_30m.tif", "Modelo A: classe de suscetibilidade (1 baixa ... 4 muito alta)"), 2, 1, 4, "YlOrRd"), False)
add(g, colours(raster("data/processed/maps/modelo_a/suscetibilidade_marracuene_30m.tif", "Modelo A: nota de suscetibilidade (0-1)"), 1, 0, 1, "YlOrRd"), False)
zonas = vector("data/processed/maps/zonas_de_aviso/zonas_de_aviso_marracuene.gpkg", "Zonas de aviso (1 = primeiras a alagar, 2 = cheia grande)")
if zonas is not None:
    zonas.setRenderer(QgsCategorizedSymbolRenderer("zona", [
        QgsRendererCategory(1, QgsFillSymbol.createSimple({"color": "192,57,43,170", "outline_style": "no"}), "zona 1: primeiras a alagar"),
        QgsRendererCategory(2, QgsFillSymbol.createSimple({"color": "245,176,65,150", "outline_style": "no"}), "zona 2: cheia grande")]))
add(g, zonas, False)
lugares = vector("data/processed/maps/zonas_de_aviso/lugares_marracuene.gpkg", "Lugares por ordem de alagamento")
if lugares is not None:
    from qgis.core import QgsPalLayerSettings, QgsTextBufferSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling
    from qgis.PyQt.QtGui import QColor, QFont
    place_colours = {"alaga primeiro": "192,57,43", "alaga em cheia grande": "230,126,34", "na margem da cheia": "241,196,15", "fora das zonas de aviso": "127,140,141"}
    lugares.setRenderer(QgsCategorizedSymbolRenderer("categoria", [
        QgsRendererCategory(k, QgsMarkerSymbol.createSimple({"name": "circle", "color": v, "outline_color": "255,255,255", "size": "2.8"}), k) for k, v in place_colours.items()]))
    text = QgsTextFormat(); text.setFont(QFont("Sans", 8)); text.setSize(8); text.setColor(QColor(20, 20, 20))
    halo = QgsTextBufferSettings(); halo.setEnabled(True); halo.setSize(1); halo.setColor(QColor(255, 255, 255)); text.setBuffer(halo)
    label = QgsPalLayerSettings(); label.fieldName = "lugar"; label.setFormat(text)
    lugares.setLabeling(QgsVectorLayerSimpleLabeling(label)); lugares.setLabelsEnabled(True)
add(g, lugares, False)
qa = "data/processed/maps/qualidade_agua/qualidade_agua_marracuene_2026-01_10m.tif"       # bandas: ndti, ndci
add(g, colours(raster(qa, "Qualidade da água: turbidez NDTI, jan. 2026 (castanho = mais turva)"), 1, -0.15, 0.08, "YlOrBr"), False)
qd = "data/processed/maps/qualidade_agua/qualidade_agua_marracuene_2022-08_10m.tif"
add(g, colours(raster(qd, "Qualidade da água: turbidez NDTI, ago. 2022 (mês seco)"), 1, -0.15, 0.08, "YlOrBr"), False)
g.setExpanded(True)

ems_group()

g = root.addGroup("Módulo Q: qualidade da água por troço (fronteira à foz)")
TROCOS = "data/interim/water_quality/trocos_rio.gpkg"
add(g, symbol(vector(TROCOS, "Troços: corredor de procura (2,5 km)", "corredores"), QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "120,120,120", "outline_style": "dash"})), False)
add(g, symbol(vector(TROCOS, "Água permanente (onde se mede; a rever)", "agua_permanente"), QgsFillSymbol.createSimple({"color": "46,134,193,200", "outline_style": "no"})), True)
add(g, symbol(vector(TROCOS, "Água pura para o Sentinel-2 (10 m da margem)", "agua_pura_sentinel2"), QgsFillSymbol.createSimple({"color": "26,82,118,220", "outline_style": "no"})), False)
add(g, symbol(vector(TROCOS, "Água pura para o Landsat (30 m da margem)", "agua_pura_landsat"), QgsFillSymbol.createSimple({"color": "20,40,80,230", "outline_style": "no"})), False)
trocos = vector(TROCOS, "Troços Q1 a Q9 (linha do rio)", "linhas")
if trocos is not None:
    from qgis.core import QgsLineSymbol, QgsPalLayerSettings, QgsTextBufferSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling
    from qgis.PyQt.QtGui import QColor, QFont
    trocos.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "142,68,173", "width": "0.8"})))
    text = QgsTextFormat(); text.setFont(QFont("Sans", 9)); text.setSize(9); text.setColor(QColor(60, 20, 90))
    halo = QgsTextBufferSettings(); halo.setEnabled(True); halo.setSize(1.2); halo.setColor(QColor(255, 255, 255)); text.setBuffer(halo)
    label = QgsPalLayerSettings(); label.fieldName = "nome"; label.setFormat(text)
    trocos.setLabeling(QgsVectorLayerSimpleLabeling(label)); trocos.setLabelsEnabled(True)
add(g, trocos, True)
g.setExpanded(False)

g = root.addGroup("4. Exposição")
add(g, symbol(vector("data/raw/exposure/osm/osm_health_marracuene.gpkg", "Unidades de saúde (OSM)"),
              QgsMarkerSymbol.createSimple({"name": "cross_fill", "color": "220,30,30", "size": "3"})), False)
add(g, symbol(vector("data/raw/exposure/osm/osm_schools_marracuene.gpkg", "Escolas (OSM)"),
              QgsMarkerSymbol.createSimple({"name": "square", "color": "255,200,0", "size": "2.2"})), False)
add(g, symbol(vector("data/raw/exposure/osm/osm_roads_marracuene.gpkg", "Estradas (OSM)"),
              QgsLineSymbol.createSimple({"color": "90,90,90", "width": "0.3"})), False)
add(g, symbol(vector("data/raw/exposure/buildings/open_buildings_marracuene.gpkg", "Edifícios (Google Open Buildings)"),
              QgsFillSymbol.createSimple({"color": "120,60,20", "outline_style": "no"})), False)
g.setExpanded(False)

month_group(f"5. Cheia de janeiro de 2026 ({EVENT})", EVENT, True, True)
month_group(f"6. Cheia de fevereiro de 2023 ({WET})", WET, False, False)
month_group(f"7. Mês seco ({DRY})", DRY, False, False)

g = root.addGroup("8. Terreno e água histórica")
stack = "data/interim/features/static_stack_marracuene_30m.tif"   # elevation, slope, aspect, hand, upstream, dist, log_up, twi, land_cover, occ, season
add(g, colours(raster(stack, "HAND - altura acima do rio (m)"), 4, 0, 15, "Viridis", invert=True), False)
add(g, colours(raster(stack, "Ocorrência histórica de água JRC (%)"), 10, 0, 100, "Blues"), False)
add(g, colours(raster(stack, "Elevação (m)"), 1, 0, 80, "Spectral", invert=True), False)
add(g, colours(raster(stack, "Declive (graus)"), 2, 0, 8, "Magma"), False)
add(g, colours(raster(stack, "Distância ao canal do Incomáti (m)"), 12, 0, 8000, "Cividis"), False)
add(g, colours(raster(stack, "Distância a água permanente (m)"), 13, 0, 5000, "Cividis"), False)
g.setExpanded(False)
g.setItemVisibilityChecked(True)

g = root.addGroup("9. Mapa de base")
osm = QgsRasterLayer("type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0", "OpenStreetMap (precisa de internet)", "wms")
add(g, osm if osm.isValid() else None, False)

# vista inicial: o distrito de Marracuene com uma margem (sem isto o mapa abre vazio)
district_layer = next((l for l in project.mapLayers().values() if l.name() == "Distrito de Marracuene"), None)
if district_layer is not None:
    from qgis.core import QgsCoordinateTransform, QgsReferencedRectangle
    to_project = QgsCoordinateTransform(district_layer.crs(), project.crs(), project)
    view = to_project.transformBoundingBox(district_layer.extent())
    view.scale(1.15)
    project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(view, project.crs()))
    project.viewSettings().setPresetFullExtent(QgsReferencedRectangle(view, project.crs()))

out = ROOT / "qgis" / "ete_marracuene.qgz"
out.parent.mkdir(exist_ok=True)
project.setPresetHomePath("..")      # "Project Home" no painel Browser = pasta do projeto ETE (data/, reports/, ...)
project.writeEntryBool("Paths", "/Absolute", False)
ok = project.write(str(out))
print("escrito" if ok else "FALHOU", out.relative_to(ROOT), "| camadas:", len(project.mapLayers()))
if missing:
    print("ficheiros em falta (camadas não incluídas):", *missing, sep="\n  ")
app.exitQgis()
sys.exit(0 if ok else 1)
