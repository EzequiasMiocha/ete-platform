"""Logótipos da plataforma nas cores da paleta (o roxo do Copernicus; plataforma/static/).

    python scripts/build_platform_logos.py

Lê os originais em logos/ e escreve versões pequenas, para a página carregar depressa:
  ete.png, ete_icone.png    o logótipo do ETE recortado em círculo e passado a tons de roxo
  dara_claro.png, oad_claro.png      apoios num só tom claro (para o rodapé escuro)
  dara_escuro.png, oad_escuro.png    apoios num só tom escuro (para fundos claros)
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC, OUT = ROOT / "logos", ROOT / "plataforma" / "static"
TINTA, CREME = (33, 37, 41), (241, 240, 250)
# tritone for the ETE badge in the platform's colours: deep purple -> Copernicus purple -> lilac -> almost white
STOPS = [(0.0, (44, 41, 80)), (0.42, (97, 92, 159)), (0.72, (142, 138, 196)), (1.0, (246, 246, 249))]


def ramp(lum: np.ndarray) -> np.ndarray:
    out = np.zeros(lum.shape + (3,))
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        m = (lum >= a) & (lum <= b)
        f = ((lum - a) / (b - a))[m][:, None]
        out[m] = np.array(ca) * (1 - f) + np.array(cb) * f
    return out.astype(np.uint8)


def ete() -> None:
    im = Image.open(SRC / "ETE_Log.jpeg").convert("RGB")
    a = np.asarray(im).astype(float) / 255
    # the badge is the large light disc inside the black frame: find it from the non-white, non-black rows
    w, h = im.size
    cx, cy, r = w / 2, h / 2, min(w, h) / 2 - 34
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    lum = np.clip((lum - 0.04) / 0.9, 0, 1) ** 0.95
    rgb = Image.fromarray(ramp(lum))
    mask = Image.new("L", (w * 4, h * 4), 0)
    ImageDraw.Draw(mask).ellipse([(cx - r) * 4, (cy - r) * 4, (cx + r) * 4, (cy + r) * 4], fill=255)
    mask = mask.resize((w, h), Image.LANCZOS)
    badge = rgb.convert("RGBA")
    badge.putalpha(mask)
    badge = badge.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))
    badge.resize((192, 192), Image.LANCZOS).quantize(96, method=Image.Quantize.FASTOCTREE).save(OUT / "ete.png", optimize=True)
    badge.resize((64, 64), Image.LANCZOS).save(OUT / "ete_icone.png", optimize=True)


def mono(name: str, out: str, height: int = 120) -> None:
    im = Image.open(SRC / name).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
    im = im.resize((round(im.width * height / im.height), height), Image.LANCZOS)
    alpha = im.getchannel("A")
    for suffix, colour in (("claro", CREME), ("escuro", TINTA)):
        flat = Image.new("RGBA", im.size, colour + (255,))
        flat.putalpha(alpha)
        flat.save(OUT / f"{out}_{suffix}.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    ete()
    mono("DARA_logo.avif", "dara")
    mono("01_IAU-OAD_transparent.png", "oad", 150)
    for f in sorted(OUT.glob("*.png")):
        print(f"{f.name:20s} {f.stat().st_size / 1024:5.1f} KB  {Image.open(f).size}")
