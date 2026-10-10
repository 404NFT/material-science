#!/bin/bash
cd /Users/a404/Documents/materialsScience/altermag/qe_inputs/mp-19266
QE=/Users/a404/Documents/materialsScience/altermag/qe-native/bin
OMPI=/opt/homebrew/opt/open-mpi/bin
while /usr/bin/pgrep -f 'pw.x' >/dev/null; do sleep 120; done
echo "[$(date +%H:%M:%S)] Sr2FeWO6 refined SCF start"
rm -rf out_r; mkdir -p out_r
$OMPI/mpirun -np 8 $QE/pw.x -in sc_ref.in > sc_ref.out 2>&1
grep -E "convergence" sc_ref.out | tail -1
ls out_r/*.save/charge-density* >/dev/null 2>&1 || { echo "no density"; exit 1; }
echo "[$(date +%H:%M:%S)] bands start"
$OMPI/mpirun -np 8 $QE/pw.x -in bands_ref.in > bands_r.out 2>&1
grep -q "JOB DONE" bands_r.out && echo "[$(date +%H:%M:%S)] bands DONE"
cd /Users/a404/Documents/materialsScience/altermag
.venv/bin/python analyze_qe_xml.py qe_inputs --threshold 0.05 | tee qe_refined_results.txt
echo "[$(date +%H:%M:%S)] ALL REFINEMENT COMPLETE"
