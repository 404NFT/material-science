# Native Quantum ESPRESSO on Apple Silicon — build notes & results

## Why

The earlier `qe-env` (micromamba) is an **Intel binary under Rosetta 2** — no
native arm64 QE package exists. Compiling natively removes emulation AND lets QE
use Apple's Accelerate BLAS, which is very fast on Apple Silicon.

## Result: ~45× speedup

Benchmark, Sr2FeWO6 (+U, 20-atom cell, 8 MPI ranks) on an M1 Max:

| Build | per SCF iteration |
|---|---|
| Intel + Rosetta (`qe-env`) | ~330 s |
| **Native arm64 (`qe-native`)** | **~7 s** |

This turns a multi-hour SCF into minutes and makes the Mac genuinely viable for
these ~20-atom candidates. (The 42/84-atom cells still belong on a cluster.)

## Build

```
./build_qe_native.sh          # -> qe-native/bin/pw.x (arm64)
```

Six issues had to be solved (all baked into the script) — this combination is
specific to bleeding-edge gfortran 16 / macOS 26:

1. Default Homebrew `gcc` is **gfortran 16**, too new for QE 7.3.1's MBD library
   -> use **gcc@13** as the Fortran backend via `OMPI_FC`.
2. MPI interface argument mismatches -> `-fallow-argument-mismatch`.
3. Manual `FFT_LIBS` override suppresses FFTW3 auto-detect -> inject `-D__FFTW3`
   into the **Fortran DFLAGS** (not just CFLAGS).
4. Apple clang `cpp` mishandles QE header generation -> use GNU `cpp-13`.
5. `fft_scalar.FFTW3.o` must be built (with `-D__FFTW3` active) **before**
   `fft_scalar.o`, else its module is empty -> compile it explicitly first.
6. Use Accelerate for BLAS/LAPACK, Homebrew FFTW for FFTs.

## Run

```
QE=$PWD/qe-native/bin
OMPI=/opt/homebrew/opt/open-mpi/bin
cd qe_inputs/mp-19266
$OMPI/mpirun -np 8 $QE/pw.x -in scf.in  > scf.out
$OMPI/mpirun -np 8 $QE/pw.x -in bands.in > bands.out
```

## Convergence note (per-material, not a build issue)

Sr2FeWO6's SCF is a stubborn correlated-oxide case: with DFT+U it is stable
(magnetization pinned at ~0, compensated AFM confirmed) but the charge density
sloshes and the last ~decade of convergence is slow. `mixing_mode='local-TF'`
with `mixing_beta=0.1` gives clean monotonic descent to ~1e-4 Ry; pushing to
1e-7 needs more mixing history / patience. For a first-pass band structure a
looser `conv_thr` (e.g. 1e-4–2e-4 Ry) is adequate since the target spin
splitting (~50 meV = 3.7e-3 Ry) is far larger. NOTE: QE only writes the charge
density when the SCF *completes*, so set `conv_thr` to a value it actually
reaches — do not kill the run mid-way, or `bands` will find no density.
