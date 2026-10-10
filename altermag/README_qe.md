# Local altermagnet confirmation with Quantum ESPRESSO (Mac)

Runs the 4 headline double-perovskite candidates on this machine. No cluster.

## 1. Install QE
```bash
brew install quantum-espresso     # provides pw.x (and mpirun)
pw.x -h | head                    # sanity check
```

## 2. Get pseudopotentials (SSSP efficiency, PBE)
Download the SSSP efficiency library (https://www.materialscloud.org/discover/sssp/),
then put the needed UPF files in `./pseudos/`, named `<Element>.upf`:

```
pseudos/Fe.upf  pseudos/O.upf  pseudos/Sr.upf  pseudos/W.upf
pseudos/Ba.upf  pseudos/Mo.upf pseudos/Ca.upf  pseudos/Cr.upf  pseudos/La.upf
```
(The exact set you need is in `qe_inputs/pseudos_needed.txt`. SSSP files have long
names — symlink or copy them to the short `<Element>.upf` names the inputs expect.)

## 3. Generate inputs (already done; re-run to change settings)
```bash
MP_API_KEY=... python prep_qe.py --outdir qe_inputs --ecutwfc 50 --kspacing 0.30
```

## 4. Run
```bash
chmod +x run_qe_local.sh
./run_qe_local.sh qe_inputs 8          # 8 = perf cores on M1 Max
```
Each candidate does scf then bands. The script prints the net magnetization after
scf — it should be ~0 (compensated AFM). Expect a few hours to ~1 day per 20-atom
candidate; the 4 together may take 1–3 days.

## 5. Analyze
```bash
python analyze_qe.py qe_inputs --threshold 0.05
```
Verdict per candidate:
- **ALTERMAGNET** — net moment ~0 AND max up/down band splitting >= 50 meV near E_F
- **no-splitting (AFM)** — compensated but no spin splitting (conventional AFM)
- **SPLIT-but-FM?** — splitting but non-zero net moment (re-check the magnetic config)

## Notes / tuning
- For a real publication-quality result, raise `--ecutwfc` (e.g. 60–80 Ry),
  tighten `--kspacing` (e.g. 0.20), and converge both. The defaults are a
  fast first pass.
- If scf struggles to converge (magnetic systems can), lower `mixing_beta`
  in `scf.in` (e.g. 0.2) or raise `electron_maxstep`.
- Start with **mp-19266 (Sr2FeWO6)** as your test case before running all four.
```
