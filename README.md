# noWorkflow 2 — Overhead Experiments

This repository holds the scripts, the execution harness, the measurement results and the
analysis code of the **overhead evaluation** of noWorkflow 2, reported in the article *The
Conception and Evolution of noWorkflow* (Information Systems, Elsevier). It is the companion
artifact the article cites as `noworkflow-overhead-experiments`, and the article's numbers are
reproduced from what is committed here.

The evaluation measures how much **execution time** and **storage** noWorkflow 2 adds to 21
Python scripts, comparing plain Python against eight provenance collection configurations.
Since the article's revision R1 it is also the **release gate** of noWorkflow: the candidate
wheel of a release runs the 21 scripts, must compute what plain Python computes, and only then
is tagged and uploaded, so that the numbers of the article are those of the released
[noWorkflow 2.2.0](https://github.com/gems-uff/noworkflow/releases/tag/2.2.0).

- Tool under evaluation: noWorkflow **2.2.0** (the wheel of the release, sha256 `ca5c198c…`)
- Scripts: 21, obtained from public repositories and research data sites (see *Scripts*)
- Repetitions: each script × configuration pair ran **10 times** on a machine prepared for the
  measurement; the article reports the median
- Time limit: **none**; a run that does not fit in 120 GiB of memory ends and is reported as such
- Results: `release-gate/results/2.2.0-ca5c198cde13/` (the correctness pass, the timing pass
  and the case study of the article's section "Beyond Python")
- Environment: `paper-environment/`, every version pinned, the same for every execution of
  noWorkflow the article reports or shows

## Repository structure

| Path | Content |
|---|---|
| `release-gate/` | The harness of the evaluation from 2.2.0 on: the 21 scripts and their arguments (`scripts.py`), the candidate's environment (`setup.py`), the correctness and timing passes (`gate.py`), the preparation of the machine (`prepare.py`), the verdicts (`compare.py`) and the tables of the article (`paper_tables.py`); its README says how to run it |
| `release-gate/results/2.2.0-ca5c198cde13/` | The results the article reports: one JSON per run of the two passes, the machine records, and `casestudy/` (the overhead of the case study of "Beyond Python" and of its rdtLite trial, with the scripts that measured them) |
| `paper-environment/` | The environment of every noWorkflow execution of the article: `measurement.txt` (the venv of the gate, frozen) and `requirements.txt` (the same plus the ML stack of the running example), which the reproducibility package [`dew-uff/noworkflow-analysis`](https://github.com/dew-uff/noworkflow-analysis) installs |
| `03dataoneexps/`, `04benchproglangs/`, `05msrgithubexps/`, `menger-sponge/` | The 21 evaluated scripts, with their data (see *Scripts*) |
| `beyond-python/` | `overhead.py` and `rdtlite_time.py`: the measurement of the case study of "Beyond Python" (the three trials of `noworkflow-analysis/beyond-python/run.sh` without noWorkflow, with `--external-tracer none`, with the default `argv` and with `strace`; and the fourth trial, `model.R` under rdtLite, with and without `now run`, next to the R step alone with and without `prov.run`), fresh directory per repetition, order rotated |

## Scripts

The IDs match Table 1 of the article. All scripts are third-party material, collected from public
repositories and research data sites; each one remains under the license of its original authors.

| ID | Script (article) | Folder | Origin | License |
|---|---|---|---|---|
| s1 | Accessing Hydrologic Data | `03dataoneexps/03dataoneexps_exp01_32_Accessing_Hydrologic_Data` | Kitri Spencer, [HydroShare](https://www.hydroshare.org/resource/fc740040c86848bab2987f09bbbc6b41/) | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) |
| s2 | A Method For Calculating | `03dataoneexps/03dataoneexps_exp03_46_A_Method_For_Calculating` | Greg Goodrum, [HydroShare](https://www.hydroshare.org/resource/1b22e76e11864628ba785c17dda3a6fa/) | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) |
| s3 | Analysis of Flow | `03dataoneexps/03dataoneexps_exp04_49_Analysis_Of_Flow` | Jaxon White, [HydroShare](https://www.hydroshare.org/resource/ed3a40af3a2947a59c441f818adc6ea2/) | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) |
| s4 | Agua Salud Rainfall Data | `03dataoneexps/03dataoneexps_exp02_40_e_44_Agua_Salud_Rainfall_Data` | J. A. Regina, F. L. Ogden, J. S. Hall, R. F. Stallard (Agua Salud Project), [HydroShare](https://www.hydroshare.org/resource/7349e6623812408bbce1b876df0ceba2/) | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) |
| s5 | Agua Salud Discharge Data | `03dataoneexps/03dataoneexps_exp05_37_Agua_Salud_Discharge_Data` | J. A. Regina, F. L. Ogden, J. S. Hall, R. F. Stallard (Agua Salud Project), [HydroShare](https://www.hydroshare.org/resource/282177bd87e7426e92899058f075359a/) | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) |
| s6 | Cvar | `05msrgithubexps/05msrgithubexps_exp02_cvar` | Leo Benac, [Research-Project---Risk-Averse-Non-Stationary-Bandits](https://github.com/LeoBenac/Research-Project---Risk-Averse-Non-Stationary-Bandits) | not declared |
| s7 | Eq Solver | `05msrgithubexps/05msrgithubexps_exp03_eq_solver` | Martin Stålberg, [concsolver](https://github.com/mast4461/concsolver) | not declared |
| s8 | Curves | `05msrgithubexps/05msrgithubexps_exp04_curves` | Nicolas P. Rougier, [spatial-computation](https://github.com/rougier/spatial-computation) | BSD 2-Clause |
| s9 | Chunks | `05msrgithubexps/05msrgithubexps_exp05_chunks` | Mikołaj Morzy, [entropy-complex-networks](https://github.com/megaduks/entropy-complex-networks) | not declared |
| s10 | Median | `05msrgithubexps/05msrgithubexps_exp07_median` | Christopher Wilks, [snaptron-experiments](https://github.com/ChristopherWilks/snaptron-experiments) | MIT |
| s11 | Find GC | `05msrgithubexps/05msrgithubexps_exp06_find_gc` | Ken Youens-Clark, [biofx_python](https://github.com/kyclark/biofx_python) | MIT |
| s12 | Mov Robots | `05msrgithubexps/05msrgithubexps_exp01_mov_robots` | Mihir Mulye, [experiments](https://github.com/mihirm05/experiments) | not declared |
| s13 | Iterative Solver Jacobi | `04benchproglangs/04benchpl_exp09_iterative_solver_jacobi_OK` | Jules Kouatchou, [basic_language_comparison](https://github.com/JulesKouatchou/basic_language_comparison) (NASA Earth Sciences Division language benchmark) | [NASA Open Source Agreement v1.3](https://github.com/JulesKouatchou/basic_language_comparison/blob/master/LICENSE.md) |
| s14 | Menger Sponge | `menger-sponge` | John D. Cook, [blog post](https://www.johndcook.com/blog/2011/08/30/slice-a-menger-sponge/) | not declared |
| s15 | Belief Propagation | `04benchproglangs/04benchpl_exp06_belief_propagation_OK` | Jules Kouatchou, [basic_language_comparison](https://github.com/JulesKouatchou/basic_language_comparison) (NASA Earth Sciences Division language benchmark) | [NASA Open Source Agreement v1.3](https://github.com/JulesKouatchou/basic_language_comparison/blob/master/LICENSE.md) |
| s16 | FFT | `04benchproglangs/04benchpl_exp08_fft_OK` | Jules Kouatchou, [basic_language_comparison](https://github.com/JulesKouatchou/basic_language_comparison) (NASA Earth Sciences Division language benchmark) | [NASA Open Source Agreement v1.3](https://github.com/JulesKouatchou/basic_language_comparison/blob/master/LICENSE.md) |
| s17 | Square Root Matrix | `04benchproglangs/04benchpl_exp10_square_root_matrix_OK` | Jules Kouatchou, [basic_language_comparison](https://github.com/JulesKouatchou/basic_language_comparison) (NASA Earth Sciences Division language benchmark) | [NASA Open Source Agreement v1.3](https://github.com/JulesKouatchou/basic_language_comparison/blob/master/LICENSE.md) |
| s18 | Gauss Legendre Quadrature | `04benchproglangs/04benchpl_exp11_gauss_legendre_quadrature_OK` | Jules Kouatchou, [basic_language_comparison](https://github.com/JulesKouatchou/basic_language_comparison) (NASA Earth Sciences Division language benchmark) | [NASA Open Source Agreement v1.3](https://github.com/JulesKouatchou/basic_language_comparison/blob/master/LICENSE.md) |
| s19 | Function Evaluation | `04benchproglangs/04benchpl_exp12_function_evaluation_OK` | Jules Kouatchou, [basic_language_comparison](https://github.com/JulesKouatchou/basic_language_comparison) (NASA Earth Sciences Division language benchmark) | [NASA Open Source Agreement v1.3](https://github.com/JulesKouatchou/basic_language_comparison/blob/master/LICENSE.md) |
| s20 | Metropolis Hastings | `04benchproglangs/04benchpl_exp07_metropolis_hastings` | Jules Kouatchou, [basic_language_comparison](https://github.com/JulesKouatchou/basic_language_comparison) (NASA Earth Sciences Division language benchmark) | [NASA Open Source Agreement v1.3](https://github.com/JulesKouatchou/basic_language_comparison/blob/master/LICENSE.md) |
| s21 | Pernicious Numbers | `04benchproglangs/04benchpl_exp14_pernicious_numbers_OK` | Jules Kouatchou, [basic_language_comparison](https://github.com/JulesKouatchou/basic_language_comparison) (NASA Earth Sciences Division language benchmark) | [NASA Open Source Agreement v1.3](https://github.com/JulesKouatchou/basic_language_comparison/blob/master/LICENSE.md) |

Scripts whose origin declares no license are marked as *not declared*: they were collected from
public repositories that do not include a license file, and are redistributed here only to make the
measurements reproducible. If you are an author of one of these scripts and want it removed or
relicensed, please open an issue.

## Reproducing the article's evaluation (noWorkflow 2.2.0)

The harness, its requirements and the two passes are described in
[`release-gate/README.md`](release-gate/README.md): Linux with systemd and cgroup v2, Python
3.12, `uv` (or `venv` and pip), Git LFS for the HDF5 file of s5, and the wheel of the release.
In short:

```bash
cd release-gate
python3 setup.py <wheel> ~/gate/env-2.2.0-ca5c198cde13 --python python3.12   # the environment
sudo python3 prepare.py launch correctness results/2.2.0-ca5c198cde13 -- ...  # the correctness pass
sudo python3 prepare.py apply && sudo python3 prepare.py launch timing ...    # the timing pass, machine prepared
uv run --with scipy python3 paper_tables.py results/2.2.0-ca5c198cde13 --out <paper>/tables --min-repetitions 10
```

The nine configurations of a script, in the order of the article:

| Configuration | Command |
|---|---|
| Plain Python (baseline) | `python <script>` |
| Fine-grained | `now run <script>` |
| Fine-grained, depth 2 | `now run -d 2 <script>` |
| Fine-grained, depth 3 | `now run -d 3 <script>` |
| Coarse-grained | `now run -cg <script>` |
| Coarse-grained, depth 2 | `now run -cg -d 2 <script>` |
| Coarse-grained, depth 3 | `now run -cg -d 3 <script>` |
| No values | `now run -e none <script>` |
| Function values | `now run -e relevant <script>` |

Every run starts from a fresh copy of the script's folder, and the size of its `.noworkflow`
directory is measured before it is removed. `paper_tables.py` writes the tables of Section 7.3
of the article and the numbers its prose cites from the results directory; its docstring states
each computation.

## Citation

If you use this material, please cite the article:

> J. F. Pimentel, A. Paiva, J. P. Lopez, E. Jandre, R. Marzo, B. Gonçalves, M. Lobo,
> F. Coutinho, J. Freire, L. Murta, V. Braganholo. The Conception and Evolution of noWorkflow.
> Information Systems, Elsevier, 2026 (to appear; the DOI will be added here once published).

The tag `is-2026-r1` of this repository is the state the article cites.

## License

The harnesses and the analysis scripts written by us (`release-gate/`, `beyond-python/`,
`paper-environment/`) are distributed under the MIT License; see [LICENSE](LICENSE).

**The evaluated scripts and their data are third-party material**, collected from public
repositories and research data sites, and each one remains under the license of its original
authors. They are included here only to make the measurements reproducible. The *Scripts* section
lists the origin and the license of each one.
