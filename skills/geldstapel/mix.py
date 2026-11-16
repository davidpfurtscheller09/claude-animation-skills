#!/usr/bin/env python3
"""Puts voice, music and the sound effects onto a rendered /geldstapel video, in sync with its animation.

    python3 mix.py <spec.json> <video.mp4> <out.mp4> [--voice v.mp3] [--music m.mp3] [--plan plan.csv]

The effect times follow template.html: each stage starts at spec.starts[i] (or 0.3 + i * stage_seconds),
and every animation inside a stage has a fixed offset from that start. The voice is always on top:
music and effects duck while someone speaks. Ends at -14 LUFS.
"""
import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SFX = HERE / 'assets' / 'sfx'
SR = 48000
sys.path.insert(0, str(HERE))
from build import DEFAULTS  # noqa: E402


def load(path, sr=SR):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, '<f4').astype(float)


def pitch(x, factor):
    """plays a sound slower (factor < 1 = deeper and longer)"""
    idx = np.arange(0, len(x) - 1, factor)
    return np.interp(idx, np.arange(len(x)), x)


def events(spec):
    """(time, sound, gain, pitch, what) for every visual event"""
    st, n = spec['stages'], len(spec['stages'])
    starts = spec['starts'] or [0.3 + i * spec['stage_seconds'] for i in range(n)]
    ev = []
    for i, t0 in enumerate(starts):
        grow = i / max(1, n - 1)                          # 0 .. 1: later stages sound bigger
        if i > 0:
            ev.append((t0 - .35, 'whoosh_soft', .55, 1.0, f'Kamera fährt zu Stufe {i + 1}'))
        ev.append((t0 + .25, 'pop_soft', .55, 1.0, f'Person {st[i]["person"]} erscheint'))
        ev.append((t0 + .55, 'paper_riffle_long' if i >= 2 else 'paper_riffle', .45 + .35 * grow, 1.0, 'Stapel wächst'))
        ev.append((t0 + .75, 'click_tiny', .5, 1.0, 'Hinweislinie'))
        ev.append((t0 + .55 + (st[i].get('count_seconds') or 1.0) * .45, 'pop_deep', .55 + .4 * grow, 1.0 - .22 * grow, f'Stapel setzt auf ({st[i]["amount"]:,} €)'.replace(',', '.')))
        if st[i]['amount'] >= 30_000_000:                 # from UHNWI on: a deeper low end with every stage
            deep = min(1.0, (st[i]['amount'] / 30_000_000) ** .25 / 2.4)
            ev.append((t0 + 1.0, 'bass_soft', .45 + .4 * deep, 1.0 - .12 * deep, f'tiefer Bass ({st[i]["title"]})'))
        if st[i]['amount'] >= 1_000_000_000:              # the billion: powerful but elegant
            ev.append((t0 + 1.05, 'shimmer', .8, 1.0, 'Milliarde: edler Klang'))
            ev.append((t0 + .55 + (st[i].get('count_seconds') or 1.0), 'pop_deep', .9, .62, 'Milliarde erreicht'))
        ev.append((t0 + 1.35, 'pop_mid', .6, 1.0, f'Skill-Karte „{st[i]["title"]}“'))
        lines = st[i].get('skills') or [st[i].get('subtitle', ''), st[i].get('range', '')]
        for k, line in enumerate(lines):
            ev.append((t0 + 1.6 + .12 * k, 'click_tiny', .45, 1.0 + .06 * k, f'Kartenzeile „{line}“'))
        ev.append((t0 + .6 + (st[i].get('count_seconds') or 1.0), 'tick_soft', .5, 1.0 + .03 * i, 'Zähler am Ziel'))
    if spec.get('intro'):
        ev.append((.05, 'pop_mid', .55, .9, 'Titel erscheint'))
        ev.append((.5, 'click_tiny', .5, 1.0, 'Frage erscheint'))
        ev.append((starts[0] - .5, 'whoosh_soft', .5, 1.1, 'Titel geht, Stufe 1 kommt'))
    if spec.get('outro'):
        ev.append((spec['outro']['at'] + .2, 'pop_mid', .55, .85, 'Schlusssatz: Nettovermögen ≠ Bargeld'))
    return sorted(ev)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec'); ap.add_argument('video'); ap.add_argument('out')
    ap.add_argument('--voice'); ap.add_argument('--music'); ap.add_argument('--plan')
    a = ap.parse_args()
    spec = dict(DEFAULTS); spec.update(json.loads(Path(a.spec).read_text()))
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.video],
                               capture_output=True, text=True, check=True).stdout)
    N = int(dur * SR)
    ev = events(spec)
    fx = np.zeros(N)
    cache = {}
    for t, name, g, p, _ in ev:
        x = cache.setdefault(name, load(SFX / f'{name}.wav'))
        if p != 1.0:
            x = pitch(x, p)
        i = int(t * SR); j = min(N, i + len(x))
        if i < N:
            fx[i:j] += g * x[:j - i]
    voice = np.zeros(N)
    if a.voice:
        v = load(a.voice); voice[:min(N, len(v))] = v[:N]
        voice /= max(1e-9, np.abs(voice).max()) / .9
    music = np.zeros(N)
    if a.music:
        m = load(a.music)[:N]; music[:len(m)] = m
        music /= max(1e-9, np.sqrt(np.mean(music[:int(min(dur, 20) * SR)] ** 2)))
        music *= .05
        fo = int(1.2 * SR); music[-fo:] *= np.linspace(1, 0, fo)
    # duck music and effects under the voice
    lvl = np.convolve(np.abs(voice), np.ones(int(.1 * SR)) / int(.1 * SR), 'same')
    speaking = np.clip(lvl / .05, 0, 1)
    mix = voice + music * (1 - .6 * speaking) + fx * (1 - .45 * speaking) * .6
    tmp = Path(a.out).with_suffix('.mix.wav')
    pcm = (np.clip(mix / max(1e-9, np.abs(mix).max()) * .9, -1, 1) * 32767).astype('<i2')
    with wave.open(str(tmp), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    meas = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(tmp), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float([l for l in meas.splitlines() if l.strip().startswith('I:')][-1].split()[1])
    gain = -14 - I
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.video, '-i', str(tmp), '-map', '0:v', '-map', '1:a',
                    '-af', f'aresample=192000,volume={gain:.2f}dB,alimiter=limit=0.70:attack=1:release=60:level=false,aresample=48000',
                    '-ac', '2', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', a.out], check=True)
    tmp.unlink()
    if a.plan:
        with open(a.plan, 'w') as f:
            f.write('zeit_s;sound;lautstaerke;ereignis\n')
            for t, name, g, p, what in ev:
                f.write(f'{t:.2f};{name};{g:.2f};{what}\n')
    print('done:', a.out)


if __name__ == '__main__':
    main()
