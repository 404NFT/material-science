#!/bin/bash
# Wait for the constrained SCF to stop; run bands if a density was saved
# (formal convergence OR controlled maxstep stop both write the .save).
cd /Users/a404/Documents/materialsScience/altermag/qe_inputs/mp-1277787
QE=/Users/a404/Documents/materialsScience/altermag/qe-native/bin
OMPI=/opt/homebrew/opt/open-mpi/bin
while /usr/bin/pgrep -f 'pw.x -in sc.in' >/dev/null; do sleep 60; done
grep -E "convergence has been achieved|convergence NOT achieved" sc.out | tail -1
if ! ls out_c/amag.save/charge-density* >/dev/null 2>&1; then
  echo "[watch] no density saved -- cannot run bands"; exit 1; fi
echo "[watch] density present: $(grep 'total magnetization' sc.out | tail -1)"
sed -i '' "s|outdir = './out'|outdir = './out_c'|" bands.in
$OMPI/mpirun -np 8 $QE/pw.x -in bands.in > bands.out 2>&1
grep -q "JOB DONE" bands.out && echo "[watch] bands DONE" || echo "[watch] bands issue"
cd /Users/a404/Documents/materialsScience/altermag
.venv/bin/python analyze_qe_xml.py qe_inputs --threshold 0.05 | tee qe_all_results.txt
