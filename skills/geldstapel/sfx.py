#!/usr/bin/env python3
"""Makes the subtle sound effects for /geldstapel as 48 kHz WAV files in assets/sfx/ (numpy only, deterministic).

    python3 sfx.py
"""
import wave
from pathlib import Path

import numpy as np

SR = 48000
OUT = Path(__file__).resolve().parent / 'assets' / 'sfx'
rng = np.random.default_rng(11)


def t(d):
    return np.arange(int(d * SR)) / SR


def env(d, a, r):
    x = t(d)
    return np.minimum(1, x / max(a, 1e-4)) * np.exp(-x / r)


def sweep(f0, f1, d, curve=3.0):
    x = t(d); f = f1 + (f0 - f1) * np.exp(-x * curve / d * 3)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def room(x, size=.18, mix=.16):
    """short, soft room tail so the pops sit in a space instead of sounding synthetic"""
    n = int(size * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 5))
    ir = np.convolve(ir, np.ones(24) / 24, 'same')        # darker tail
    ir /= np.abs(ir).sum()
    wet = np.convolve(x, ir)
    dry = np.pad(x, (0, len(wet) - len(x)))
    return dry * (1 - mix) + wet * mix * 6


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')


def norm(x, peak):
    return x / max(1e-9, np.abs(x).max()) * peak


SOUNDS = {
    # weich und rund: Person erscheint
    'pop_soft': lambda: norm(room(sweep(520, 240, .12) * env(.12, .002, .035)), .45),
    # Pop mit kurzem Glanz: Skill-Karte
    'pop_mid': lambda: norm(room(sweep(760, 330, .14) * env(.14, .0015, .04) + .18 * sweep(2600, 2200, .14) * env(.14, .001, .015)), .5),
    # tiefer Pop: Stapel setzt auf (Grundversion, wird je Stufe tiefer gepitcht)
    'pop_deep': lambda: norm(room(sweep(260, 95, .22) * env(.22, .002, .07) + .25 * lowpass(rng.standard_normal(int(.22 * SR)), 30) * env(.22, .001, .02), .25, .2), .6),
    # sehr leiser Klick: Hinweislinie, einzelne Skills
    'click_tiny': lambda: norm(lowpass(np.diff(rng.standard_normal(int(.03 * SR)), prepend=0), 3) * env(.03, .0004, .005) + .4 * sweep(1900, 1700, .03) * env(.03, .0004, .006), .22),
    # kurzer heller Ton: Zähler am Ziel
    'tick_soft': lambda: norm(room(np.sin(2 * np.pi * 1320 * t(.35)) * env(.35, .003, .09) + .3 * np.sin(2 * np.pi * 2640 * t(.35)) * env(.35, .003, .05)), .25),
    # Papier-Rascheln: Stapel wächst (viele kleine, gefilterte Impulse, die dichter werden)
    'paper_riffle': lambda: _riffle(.9),
    'paper_riffle_long': lambda: _riffle(1.0, dense=1.6),
    # leiser Luftzug: Kamerafahrt
    'whoosh_soft': lambda: _whoosh(1.1),
    # tiefer weicher Bass: 100 Mio.
    'bass_soft': lambda: norm(sweep(70, 42, .9, 1.2) * env(.9, .01, .35), .55),
}


def _riffle(d, dense=1.0):
    x = np.zeros(int(d * SR))
    n = int(70 * d * dense)
    for i in range(n):
        p = (i / n) ** .7
        k = int(p * (len(x) - 900))
        b = lowpass(rng.standard_normal(700), 2) * np.exp(-np.arange(700) / 90) * (.4 + .6 * rng.random())
        x[k:k + 700] += b
    x = lowpass(x, 4) * np.sin(np.linspace(0, np.pi, len(x))) ** .6
    return norm(room(x, .12, .1), .32)


def _whoosh(d):
    x = rng.standard_normal(int(d * SR)); y = np.zeros_like(x); s = 0.0
    c = .02 + .14 * np.sin(np.linspace(0, np.pi, len(x)))     # filter opens and closes
    for i in range(len(x)):
        s += c[i] * (x[i] - s); y[i] = s
    return norm(y * np.sin(np.linspace(0, np.pi, len(x))) ** 2, .35)


def write(name, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(str(OUT / f'{name}.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for name, make in SOUNDS.items():
        write(name, make()); print('wrote', OUT / f'{name}.wav')
