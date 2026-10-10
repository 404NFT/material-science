"""Shared input builder for the hypothetical CaBa2FeMoO5 (Sr3Fe2O5-type, Immm) runs."""
PSEUDO = '/Users/a404/Documents/materialsScience/altermag/pseudos'
SPECIES = [('Ca', 40.078), ('Ba', 137.327), ('Fe', 55.845), ('Mo', 95.94), ('O', 15.9994)]
MAG = {'fim': {'Fe': 0.7, 'Mo': -0.5}, 'fm': {'Fe': 0.7, 'Mo': 0.5}}


def build(prefix, calc, cell_card, pos_card, mag, kp='7 7 7', extra_ctrl='', extra_blocks=''):
    nspin = 1 if mag == 'nm' else 2
    sm = ''
    if nspin == 2:
        for i, (s, _) in enumerate(SPECIES, 1):
            sm += f"  starting_magnetization({i}) = {MAG[mag].get(s, 0.0):.2f}\n"
    if calc == 'nscf':
        occ = "  occupations = 'tetrahedra_opt'\n  nbnd = 80\n"
        elec = "  conv_thr = 1.0d-9\n"
    else:
        occ = "  occupations = 'smearing'\n  smearing = 'mv'\n  degauss = 0.015\n"
        elec = ("  conv_thr = 1.0d-7\n  mixing_mode = 'local-TF'\n  mixing_beta = 0.2\n"
                "  mixing_ndim = 12\n  electron_maxstep = 300\n")
    return f"""&CONTROL
  calculation = '{calc}'
  prefix = '{prefix}'
  outdir = './out'
  pseudo_dir = '{PSEUDO}'
{extra_ctrl}/
&SYSTEM
  ibrav = 0
  nat = 10
  ntyp = 5
  ecutwfc = 60.0
  ecutrho = 480.0
{occ}  nspin = {nspin}
{sm}/
&ELECTRONS
{elec}/
{extra_blocks}ATOMIC_SPECIES
""" + "".join(f"  {s}  {m:.4f}  {s}.upf\n" for s, m in SPECIES) + cell_card.rstrip() + "\n" + pos_card.rstrip() + \
        f"\nK_POINTS automatic\n  {kp} 0 0 0\nHUBBARD (ortho-atomic)\nU Fe-3d 4.5\nU Mo-4d 2.5\n"
