#!/usr/bin/env python3
"""Turns the photo people in assets/ into pure black-and-white ink drawings (assets/person_N_bw@3x.png).

    python3 bw_assets.py

Only black lines and white fill, no grey: a difference-of-Gaussians picks the drawn lines, the figure gets a
heavier outline, and the soft floor shadow of the cut-out is left out. Saved at 3x for crisp lines; build.py
reads the @3x suffix and keeps the on-screen size of the original.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

A = Path(__file__).resolve().parent / 'assets'
UP = 3


def ink_drawing(src):
    im = Image.open(src).convert('RGBA'); im = im.resize((im.width * UP, im.height * UP), Image.LANCZOS)
    al = np.array(im)[:, :, 3] / 255.
    body = al > .45
    feet = int(al.shape[0] * .9)
    body[feet:] = al[feet:] > .85                              # strict only near the floor: drops the soft shadow, keeps the hair
    g = np.array(im.convert('L')).astype(float); g = g * al + 255 * (1 - al)
    gi = Image.fromarray(g.astype(np.uint8))
    dog = np.array(gi.filter(ImageFilter.GaussianBlur(2.2))).astype(float) - np.array(gi.filter(ImageFilter.GaussianBlur(1.0))).astype(float)
    ink = (dog > 6) & body                                      # thin inner lines
    m = Image.fromarray((body * 255).astype(np.uint8))
    outline = np.array(m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))) > 0   # heavier outline
    ink |= outline
    out = np.zeros((*ink.shape, 4), np.uint8)
    out[body] = [255, 255, 255, 255]
    out[ink] = [0, 0, 0, 255]
    ys, xs = np.where(out[:, :, 3] > 0)
    return Image.fromarray(out[ys.min():ys.max() + 1, xs.min():xs.max() + 1])


if __name__ == '__main__':
    for f in sorted(A.glob('person_[0-9].png')):
        out = A / f'{f.stem}_bw@{UP}x.png'
        ink_drawing(f).save(out); print('wrote', out.name)
