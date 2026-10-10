#!/usr/bin/env python3
"""Read the final vc-relax geometry and write FiM / FM / NM scf, nscf and dos inputs."""
import re
from pathlib import Path
from common import build

BOHR = 0.529177210903
t = Path('relax.out').read_text()
if 'Begin final coordinates' not in t:
    raise SystemExit('vc-relax did not finish (no final coordinates)')
blk = t.split('Begin final coordinates')[1].split('End final coordinates')[0]
lines = blk.splitlines()
i = next(k for k, l in enumerate(lines) if l.strip().startswith('CELL_PARAMETERS'))
hdr = lines[i]
vec = [list(map(float, lines[i + j].split())) for j in (1, 2, 3)]
m = re.search(r'alat=\s*([\d.]+)', hdr)
if m:
    s = float(m.group(1)) * BOHR
    vec = [[x * s for x in v] for v in vec]
elif 'bohr' in hdr:
    vec = [[x * BOHR for x in v] for v in vec]
cell = "CELL_PARAMETERS angstrom\n" + "".join(f"  {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n" for v in vec)
j = next(k for k, l in enumerate(lines) if l.strip().startswith('ATOMIC_POSITIONS'))
unit = re.search(r'\((\w+)\)', lines[j]).group(1)
pos = f"ATOMIC_POSITIONS {unit}\n" + "\n".join(lines[j + 1:j + 11]) + "\n"
Path('relaxed_cell.txt').write_text(cell + pos)
for mag in ('fim', 'fm', 'nm'):
    d = Path(mag); d.mkdir(exist_ok=True)
    (d / 'scf.in').write_text(build(f'cbfmo5_{mag}', 'scf', cell, pos, mag))
    if mag != 'nm':
        (d / 'nscf.in').write_text(build(f'cbfmo5_{mag}', 'nscf', cell, pos, mag, kp='10 10 10'))
        (d / 'dos.in').write_text(f"&DOS\n  prefix = 'cbfmo5_{mag}'\n  outdir = './out'\n  fildos = 'cbfmo5_{mag}.dos'\n"
                                  "  DeltaE = 0.005\n  Emin = -10.0\n  Emax = 25.0\n/\n")
print('wrote fim/ fm/ nm/ inputs from relaxed geometry')
