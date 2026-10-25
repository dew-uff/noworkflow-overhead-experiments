# noWorkflow 2 — Overhead Experiments

This repository contains the scripts, execution harness, and results of the **overhead evaluation**
of noWorkflow 2, reported in the article *The Conception and Evolution of noWorkflow* (submitted to
*Information Systems*, Elsevier). It is the companion artifact cited in the paper as
`noworkflow-overhead-experiments`.

The evaluation measures how much **execution time** and **storage** noWorkflow 2 adds to 21 Python
scripts, comparing pure Python execution against several provenance collection configurations.

- Tool under evaluation: [noWorkflow](https://github.com/gems-uff/noworkflow) **2.1.3**
- Scripts: 21, obtained from public repositories and research data sites (see *Scripts*)
- Repetitions: each script × configuration pair was executed **10 times**; the paper reports the median
- Time limit: executions were interrupted after **30 minutes** (`timeout 30m` in `run.sh`)

## Repository structure

| Path | Content |
|---|---|
| `03dataoneexps/` | Scripts from hydrology/environmental data experiments (5 scripts) |
| `04benchproglangs/` | Numerical and algorithmic benchmark scripts (8 scripts) |
| `05msrgithubexps/` | Small scripts collected from GitHub (7 scripts) |
| `menger-sponge/` | Menger Sponge script (1 script) |
| `run.sh` | Execution harness: runs every script under every configuration |
| `experimental_analysis/results/` | Raw output of the 10 executions (`output_trial1.txt` … `output_trial10.txt`) |
| `experimental_analysis/scripts/` | `summarize_results_to_csv_file.py`, which parses the raw output into CSV |
| `noWorkflow 2 experiments.xlsx` | Spreadsheet with the consolidated measurements |
| `release-gate/` | From noWorkflow 2.2.0 on: the evaluation run on each release candidate, which must compute what plain Python computes before the release is tagged (its README), and the measurement of 2.1.3 that led to it |

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

## Requirements

- **Conda**, which `run.sh` requires to activate the environment of each experiment
- **Python 3** with the dependencies of each script (some folders have their own `README.md` listing them)
- **noWorkflow 2.1.3**: `pip install noworkflow[all]==2.1.3`
- **Git LFS**, needed for `03dataoneexps/03dataoneexps_exp05_37_Agua_Salud_Discharge_Data/AguaSaludDischarge.h5`,
  which is stored with LFS. Without `git lfs install` followed by `git lfs pull`, that file is only a
  pointer and script s5 does not run.

## Running the experiments

```bash
./run.sh
```

`run.sh` iterates over every experiment and executes it under the baseline and the eight noWorkflow configurations reported in the article, in this order:

| Configuration | Command |
|---|---|
| Pure Python (baseline) | `python <script>` |
| Fine-grained | `now run <script>` |
| Fine-grained, depth 2 | `now run -d 2 <script>` |
| Fine-grained, depth 3 | `now run -d 3 <script>` |
| Coarse-grained | `now run -cg <script>` |
| Coarse-grained, depth 2 | `now run -cg -d 2 <script>` |
| Coarse-grained, depth 3 | `now run -cg -d 3 <script>` |
| No values | `now run -e none <script>` |
| Function values | `now run -e relevant <script>` |

After each execution, the harness measures the size of the `.noworkflow` directory with `du` and then
removes it, so that every execution starts from a clean state. Each run of `run.sh` produces one
`output_trialN.txt` file; the ten files in `experimental_analysis/results/` correspond to the ten
repetitions reported in the paper.

## Analysing the results

```bash
python experimental_analysis/scripts/summarize_results_to_csv_file.py
```

The script parses the `output_trialN.txt` files and produces a CSV with one row per
experiment/configuration/repetition. The consolidated numbers, together with the tables of the
article, are in `noWorkflow 2 experiments.xlsx`.

## Citation

If you use this material, please cite the article:

> J. F. Pimentel, A. Paiva, J. P. Lopez, E. Jandre, R. Marzo, B. Gonçalves, M. Lobo, F. Coutinho,
> J. Freire, L. Murta, V. Braganholo. The Conception and Evolution of noWorkflow. ⚠️ TO FILL
> (venue and year once published).

## License

The execution harness and the analysis scripts written by us (`run.sh`,
`experimental_analysis/`) are distributed under the MIT License; see [LICENSE](LICENSE).

**The evaluated scripts and their data are third-party material**, collected from public
repositories and research data sites, and each one remains under the license of its original
authors. They are included here only to make the measurements reproducible. The *Scripts* section
lists the origin and the license of each one.
