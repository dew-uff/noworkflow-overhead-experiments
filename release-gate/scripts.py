"""The scripts of the paper's evaluation and the configurations it runs them under."""

# id (Table 1 of the paper), folder, arguments: those of run.sh, the original inputs
# (no reduced input: the gate runs s14, s20 and s21 as the paper did, without a time limit).
SCRIPTS = [
    ("s1", "03dataoneexps/03dataoneexps_exp01_32_Accessing_Hydrologic_Data", "main.py"),
    ("s2", "03dataoneexps/03dataoneexps_exp03_46_A_Method_For_Calculating", "main.py"),
    ("s3", "03dataoneexps/03dataoneexps_exp04_49_Analysis_Of_Flow", "main.py"),
    ("s4", "03dataoneexps/03dataoneexps_exp02_40_e_44_Agua_Salud_Rainfall_Data", "export_rainfall.py --site MOS -d gage_data --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z"),
    ("s5", "03dataoneexps/03dataoneexps_exp05_37_Agua_Salud_Discharge_Data", "export_discharge.py --site FOR -d discharge_sharp --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z"),
    ("s6", "05msrgithubexps/05msrgithubexps_exp02_cvar", "cvar.py 500"),
    ("s7", "05msrgithubexps/05msrgithubexps_exp03_eq_solver", "eq_solver.py 500"),
    ("s8", "05msrgithubexps/05msrgithubexps_exp04_curves", "curves.py 5000 5000 5000 5000 5000 5000 5000 5000"),
    ("s9", "05msrgithubexps/05msrgithubexps_exp05_chunks", "chunks.py 500"),
    ("s10", "05msrgithubexps/05msrgithubexps_exp07_median", "median.py 500"),
    ("s11", "05msrgithubexps/05msrgithubexps_exp06_find_gc", "gc.py CR954253.fasta"),
    ("s12", "05msrgithubexps/05msrgithubexps_exp01_mov_robots", "mov_robots.py"),
    ("s13", "04benchproglangs/04benchpl_exp09_iterative_solver_jacobi_OK", "test_laplace_jacobi2.py 105"),
    ("s14", "menger-sponge", "menger_sponge2.py"),
    ("s15", "04benchproglangs/04benchpl_exp06_belief_propagation_OK", "test_belief_propagation.py 20000"),
    ("s16", "04benchproglangs/04benchpl_exp08_fft_OK", "test_compute_FFT.py 20000"),
    ("s17", "04benchproglangs/04benchpl_exp10_square_root_matrix_OK", "test_sqrt_matrix.py 6000"),
    ("s18", "04benchproglangs/04benchpl_exp11_gauss_legendre_quadrature_OK", "gauss_legendre_quadrature_py3.py 10000"),
    ("s19", "04benchproglangs/04benchpl_exp12_function_evaluation_OK", "test_evaluate_functions.py 80000"),
    ("s20", "04benchproglangs/04benchpl_exp07_metropolis_hastings", "metropolis_hastings.py 27000000"),
    ("s21", "04benchproglangs/04benchpl_exp14_pernicious_numbers_OK", "test_pernicious_numbers.py 20000000"),
]

# The eight configurations of the paper's §7, after plain Python. python-control is a second
# plain run, in the correctness pass only: what the two plain runs disagree on is noise.
PLAIN = ["python", "python-control"]
CONFIGS = {
    "python": [],
    "python-control": [],
    "now": ["run"],
    "d2": ["run", "-d", "2"],
    "d3": ["run", "-d", "3"],
    "cg": ["run", "-cg"],
    "cg-d2": ["run", "-cg", "-d", "2"],
    "cg-d3": ["run", "-cg", "-d", "3"],
    "e-none": ["run", "-e", "none"],
    "e-relevant": ["run", "-e", "relevant"],
}

# Under noWorkflow these run with nothing else beside them in the correctness pass: s19 held
# 36.5 GiB under 2.1.3, and s14, s20 and s21 never finished under it (they ran out of the
# evaluation's 30 minutes), so how much memory they reach is unknown.
ALONE = {"s14", "s19", "s20", "s21"}

# What a run is expected to hold at its peak, in GiB, for the scheduling of the correctness
# pass under the memory cap: measured under 2.1.3 (gems-uff/noworkflow#467), rounded up.
# The rest are below 5. An estimate that falls short costs a rerun alone, never a result.
PEAK_GIB = {"s2": 24, "s16": 25, "s19": 38}
DEFAULT_PEAK_GIB = 5
