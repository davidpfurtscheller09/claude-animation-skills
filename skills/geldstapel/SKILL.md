---
name: geldstapel
description: Makes a clean white-background comparison reel of money stacks next to people. Bundles of 100-euro notes grow from the floor, a counter rolls up to the amount, a skill card slides in, then the camera moves left to the next, bigger stack. Use when the user runs /geldstapel or asks for a money-stack size comparison with people and skill cards.
---

# /geldstapel

Same pipeline as `/minimalistic-graphics`: a spec fills `template.html`, `kit/anim.py` renders it with HyperFrames (1080x1920, 30 fps) and writes an mp4 plus a contact sheet.

## Steps
1. **Spec.** Write `<name>.geldstapel.json` (below). `{}` renders the four default stages.
2. **Build.** `python3 "$SKILL_DIR/build.py" <spec.json>` (about 30 s). `--snap 1.5,4.2` writes PNG frames only.
3. **Check** the sheet: people and stacks fully visible, numbers on one line, cards readable.

## Spec
```json
{"stages": [
  {"amount": 100000, "person": 1, "stack": 1, "icon": "cap", "title": "Einsteiger-Skills", "skills": ["Fachwissen", "Zuverlässigkeit", "Teamarbeit"]},
  {"amount": 1000000, "person": 2, "stack": 2, "icon": "chart", "title": "Profi-Skills", "skills": ["Erfahrung", "Problemlösung", "Projekte"]}
], "scale": 1.35, "stage_seconds": 3.4, "note": "Beispielhafte Einordnung – keine Garantie für Einkommen oder Vermögen."}
```
- `person` / `stack`: number of `assets/person_N.png` / `assets/stack_N.png`. Stacks 1–4 grow in size; people 1–4 are different ages.
- `icon`: `cap`, `chart`, `team` or `rocket`.
- `scale`: one factor for people and stacks alike, so the size comparison stays honest. 1.35 keeps the largest stack inside the safe area.
- `hold`, `out`: as in the other skills.

## Components (template.html)
`Person`, `Stack` (grows from the floor via clip reveal), `Amount` (rolling counter + leader line with a dot onto the stack), `SkillCard` (icon, title, three skills). The camera moves one screen width per stage and drifts slowly while a stage holds.

## Taste
- White background, lots of space, navy type (#1c2b4a), one gold accent from the bands only.
- Never claim that skills guarantee a fortune; keep the note line.
- Assets come from the user's reference image; replace them with higher-resolution PNGs (same names) when available.

## Strict black & white (`"style": "bw"`)
- Pure white ground, black type, outlines and hatching only: no colour, no grey fills, no gradients.
- People: `python3 bw_assets.py` turns `person_N.png` into ink drawings `person_N_bw@3x.png` (thick outline, thin inner lines).
- Money: give each stage `"block": [cols, rows, layers]` and it is drawn as a block of bundles (black band stripe, paper edges, hatched shadow side, the outline draws itself). With one block per fixed amount the volumes are exact, e.g. 1 block = 50.000 € → 2, 20, 100, 600, 2.000, 20.000 blocks.
- Keep a note that says what one block stands for and that the drawing is not to scale.
