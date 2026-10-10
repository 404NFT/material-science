# Altermagnet-confirmation DFT runs

Per candidate: `static/` then `bands/`.

1. Add real POTCARs (see POTCAR.spec; `pmg config -p <vasp_psp>`).
2. Run `static/` (spin-polarized SCF). Confirm net |moment| ~ 0.
3. Copy `static/CHGCAR` into `bands/`, run `bands/` (ICHARG=11, line mode).
4. Plot spin-up vs spin-down bands. Altermagnet = k-dependent spin
   splitting (>~50 meV near E_F) with zero net moment.

Candidates:
- mp-1048863 CaLaCrMoO6 (Pc, 20 sites)
- mp-19266 Sr2FeWO6 (P2_1/c, 20 sites)
- mp-2240166 MgCu2(O2F)2 (Imm2, 9 sites)
- mp-1272506 Ba2FeWO6 (C2/c, 20 sites)
- mp-684727 CsTaCo(OF2)2 (C2, 18 sites)
- mp-1274449 SrLaCoO4 (Aea2, 14 sites)
- mp-976868 NiH2SeO5 (C2/c, 18 sites)
- mp-759163 VOF2 (C2/c, 8 sites)
- mp-1277241 MnOF (Pnma, 12 sites)
- mp-756665 ZrCoO3 (Pnma, 20 sites)
- mp-1580697 Ca3Co2O7 (Cc, 24 sites)
- mp-2674749 Y2Mo2O7 (C2/c, 22 sites)
- mp-1277787 Ba2FeMoO6 (P4_2/mnm, 20 sites)
- mp-703684 MnH12N2(Cl2O)2 (I-42m, 42 sites)
- mp-728934 CoH9C4NO6 (Pnma, 84 sites)
