# Starting structure: Sr3Fe2O5 (Immm, a=3.515 b=3.953 c=20.913 A; RSC Adv. 2016 c5ra22015g),
# Sr -> Ca (perovskite-block site) + 2 Ba (rock-salt site), Fe2 -> Fe + Mo on the ladder rung.
# Cell expanded ~2.5% in-plane / 3% along c for the larger Ba; vc-relax does the rest.
from common import build
a, b, c = 3.60, 4.05, 21.55
zF, zO2, zBa = 2.00, 4.00, 4.00   # Angstrom heights above the rung-bridging O1
cell = ("CELL_PARAMETERS angstrom\n"
        f"  {-a/2:.6f} {b/2:.6f} {c/2:.6f}\n  {a/2:.6f} {-b/2:.6f} {c/2:.6f}\n  {a/2:.6f} {b/2:.6f} {-c/2:.6f}\n")
atoms = [('O', 0, 0, 0), ('Ca', a/2, b/2, 0),
         ('Fe', 0, 0, zF), ('Mo', 0, 0, -zF),
         ('O', 0, b/2, zF), ('O', 0, b/2, -zF),
         ('O', 0, 0, zO2), ('O', 0, 0, -zO2),
         ('Ba', a/2, b/2, zBa), ('Ba', a/2, b/2, -zBa)]
pos = "ATOMIC_POSITIONS angstrom\n" + "".join(f"  {s} {x:.6f} {y:.6f} {z:.6f}\n" for s, x, y, z in atoms)
ctrl = "  tprnfor = .true.\n  tstress = .true.\n  forc_conv_thr = 1.0d-3\n  etot_conv_thr = 1.0d-5\n  nstep = 120\n"
blocks = "&IONS\n/\n&CELL\n  cell_dofree = 'all'\n  press_conv_thr = 0.5\n/\n"
open('relax.in', 'w').write(build('cbfmo5', 'vc-relax', cell, pos, 'fim', extra_ctrl=ctrl, extra_blocks=blocks))
