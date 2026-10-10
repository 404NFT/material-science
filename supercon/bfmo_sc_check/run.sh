#!/bin/bash
# Ba2FeMoO6 / Ba1.5Ca0.5FeMoO6 magnetic ground state + spin-resolved DOS at E_F.
# Question answered: is there any state of this compound with BOTH spins at E_F
# and a magnetic splitting small enough for singlet superconductivity?
# Unconstrained runs (no magnetization penalty), so energies are comparable.
# ~7 s/SCF iteration on the M1 Max native build -> expect roughly 1-3 h total.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
QE=/Users/a404/Documents/materialsScience/altermag/qe-native/bin
OMPI=/opt/homebrew/opt/open-mpi/bin; NP=8
for c in bfmo_fim bfmo_afm bfmo_nm bcfmo_fim bcfmo_afm; do
  cd "$HERE/$c"
  if grep -q "JOB DONE" scf.out 2>/dev/null && grep -q "convergence has been achieved" scf.out; then
    echo "[$(date +%H:%M:%S)] $c scf already converged"
  else
    echo "[$(date +%H:%M:%S)] $c scf start"
    $OMPI/mpirun -np $NP $QE/pw.x -in scf.in > scf.out 2>&1
    grep -E "convergence has been achieved|convergence NOT achieved" scf.out | tail -1
  fi
  if [ -f nscf.in ] && grep -q "convergence has been achieved" scf.out; then
    echo "[$(date +%H:%M:%S)] $c nscf + dos"
    $OMPI/mpirun -np $NP $QE/pw.x -in nscf.in > nscf.out 2>&1
    $OMPI/mpirun -np 1 $QE/dos.x -in dos.in > dos.out 2>&1
  fi
done
cd "$HERE"
PY=/Users/a404/Documents/materialsScience/altermag/.venv/bin/python
[ -x "$PY" ] || PY=python3
$PY analyze.py | tee results.txt
