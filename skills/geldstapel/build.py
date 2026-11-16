#!/usr/bin/env python3
"""/geldstapel: spec.json -> money stacks next to people, the camera moves left from stage to stage (1080x1920, white).

    python3 build.py <spec.json> [--snap 1.5,4.2]
"""
import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'kit'))
import anim  # noqa: E402

STAGES = [
    {'amount': 100_000, 'person': 1, 'stack': 1, 'icon': 'cap', 'title': 'Einsteiger-Skills', 'skills': ['Fachwissen', 'Zuverlässigkeit', 'Teamarbeit']},
    {'amount': 1_000_000, 'person': 2, 'stack': 2, 'icon': 'chart', 'title': 'Profi-Skills', 'skills': ['Erfahrung', 'Problemlösung', 'Projekte']},
    {'amount': 10_000_000, 'person': 3, 'stack': 3, 'icon': 'team', 'title': 'Führungs-Skills', 'skills': ['Führung', 'Strategie', 'Entscheidungen']},
    {'amount': 100_000_000, 'person': 4, 'stack': 4, 'icon': 'rocket', 'title': 'Unternehmer-Skills', 'skills': ['Skalierung', 'Kapitalaufbau', 'Wachstum']},
]
DEFAULTS = {'stages': STAGES, 'scale': 1.35, 'stage_seconds': 3.4,
            'note': 'Beispielhafte Einordnung – keine Garantie für Einkommen oder Vermögen.',
            'starts': None, 'end': None, 'intro': None, 'outro': None, 'finn_space': False}   # optional: stage start times and end, laid onto a voice-over


def duration(spec):
    if spec.get('starts'):
        return float(spec['end'])
    return 0.3 + len(spec['stages']) * spec['stage_seconds'] + 0.6


def check(spec):
    if not 1 <= len(spec['stages']) <= 6:
        sys.exit('spec: "stages" takes 1 to 6 stages')
    for s in spec['stages']:
        for k in ('person', 'stack'):
            if not (HERE / 'assets' / f'{k}_{s[k]}.png').exists():
                sys.exit(f'spec: assets/{k}_{s[k]}.png is missing')
        if len(' · '.join(s.get('skills', []))) > 44:
            print(f'note: the skills of "{s["title"]}" are long and may not fit the card')


def inline_assets(work_dir):
    """the render folder holds only fonts and GSAP, so the PNGs travel inside the page as data URIs (size in the mime params)"""
    from PIL import Image
    assets = {}
    for f in sorted((HERE / 'assets').glob('*.png')):
        w, h = Image.open(f).size
        assets[f.stem] = f'data:image/png;w={w};h={h};base64,' + base64.b64encode(f.read_bytes()).decode()
    page = (HERE / 'template.html').read_text().replace('__ASSETS__', json.dumps(assets))
    work_dir.mkdir(parents=True, exist_ok=True)
    out = work_dir / 'geldstapel.template.html'
    out.write_text(page)
    return out


if __name__ == '__main__':
    spec_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None
    if spec_path is None:
        sys.exit(__doc__)
    template = inline_assets(spec_path.parent / '.work')
    anim.build(template, DEFAULTS, duration=duration, check=check)
