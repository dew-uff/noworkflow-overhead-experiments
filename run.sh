#!/bin/bash

if command -v conda >/dev/null 2>&1; then
    CONDA_BASE=$(conda info --base)
    # If conda is installed and initialized, use the base environment
    source "$CONDA_BASE/etc/profile.d/conda.sh"
else
    echo "Error: Conda not found or not initialized."
    exit 1
fi

create_env() {
  local exp_path="$1"

  echo ''
  echo "Entering experiment folder: $exp_path"
  cd $exp_path
}

destroy_env() {
  echo ''
  echo "Erasing noWorkflow: rm -rf .noworkflow/"
  rm -rf .noworkflow/
}

run_exp() {
  local exp_path="$1"
  local exp_cmd="$2"

  echo '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
  
  create_env $exp_path
  
  echo ''
  echo ''

  echo "Executing command: $exp_cmd"
  eval "timeout 30m $exp_cmd"

  if [ -d ".noworkflow/" ]; then
    echo "Executing command: du .noworflow/"
    du -s .noworkflow/

    echo "Executing command: du -hs .noworflow/"
    du -hs .noworkflow/

    echo ''

    destroy_env
  else
    echo "noWorkflow folder not found!"
  fi
}

run_exp_pure_python() {
  local exp_path="$1"
  local script_input_and_options="${2}"

  run_exp "$exp_path" "python ${script_input_and_options}"
}

run_exp_noworkflow_fine_grain() {
  local exp_path="$1"
  local script_input_and_options="${2}"

  run_exp "$exp_path" "now run ${script_input_and_options}"
}

run_exp_noworkflow_depth_2() {
  local exp_path="$1"
  local script_input_and_options="${2}"

  run_exp "$exp_path" "now run -d 2 ${script_input_and_options}"
}

run_exp_noworkflow_depth_3() {
  local exp_path="$1"
  local script_input_and_options="${2}"

  run_exp "$exp_path" "now run -d 3 ${script_input_and_options}"
}

run_exp_noworkflow_coarse_grain() {
  local exp_path="$1"
  local script_input_and_options="${2}"

  run_exp "$exp_path" "now run -cg ${script_input_and_options}"
}

run_exp_noworkflow_no_evaluation() {
  local exp_path="$1"
  local script_input_and_options="${2}"

  run_exp "$exp_path" "now run -e none ${script_input_and_options}"
}

run_exp_noworkflow_relevant_evaluation() {
  local exp_path="$1"
  local script_input_and_options="${2}"

  run_exp "$exp_path" "now run -e relevant ${script_input_and_options}"
}


conda activate $NOWORKFLOW_CONDA_ENV

base_dir=$PATH_TO_GIT_REPOSITORY
base_dataone_dir="${base_dir}/03dataoneexps"
base_bench_dir="${base_dir}/04benchproglangs"
base_msr_dir="${base_dir}/05msrgithubexps"
base_menger_dir="${base_dir}/menger-sponge"

exp_paths=("${base_dataone_dir}/03dataoneexps_exp01_32_Accessing_Hydrologic_Data"
           "${base_dataone_dir}/03dataoneexps_exp02_40_e_44_Agua_Salud_Rainfall_Data"
           "${base_dataone_dir}/03dataoneexps_exp03_46_A_Method_For_Calculating"
           "${base_dataone_dir}/03dataoneexps_exp04_49_Analysis_Of_Flow"
           "${base_dataone_dir}/03dataoneexps_exp05_37_Agua_Salud_Discharge_Data"

           "${base_bench_dir}/04benchpl_exp06_belief_propagation_OK"
           "${base_bench_dir}/04benchpl_exp07_metropolis_hastings"
           "${base_bench_dir}/04benchpl_exp08_fft_OK"
           "${base_bench_dir}/04benchpl_exp09_iterative_solver_jacobi_OK"
           "${base_bench_dir}/04benchpl_exp10_square_root_matrix_OK"
           "${base_bench_dir}/04benchpl_exp11_gauss_legendre_quadrature_OK"
           "${base_bench_dir}/04benchpl_exp12_function_evaluation_OK"
           "${base_bench_dir}/04benchpl_exp14_pernicious_numbers_OK"

           "${base_msr_dir}/05msrgithubexps_exp01_mov_robots"
           "${base_msr_dir}/05msrgithubexps_exp02_cvar"
           "${base_msr_dir}/05msrgithubexps_exp03_eq_solver"
           "${base_msr_dir}/05msrgithubexps_exp04_curves"
           "${base_msr_dir}/05msrgithubexps_exp05_chunks"
           "${base_msr_dir}/05msrgithubexps_exp06_find_gc"
           "${base_msr_dir}/05msrgithubexps_exp07_median"

           "${base_menger_dir}")

exp_script_input_and_options=('main.py'
                              'export_rainfall.py --site MOS -d gage_data --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z'
                              'main.py'
                              'main.py'
                              'export_discharge.py --site FOR -d discharge_sharp --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z'

                              'test_belief_propagation.py 20000'
                              'metropolis_hastings.py 27000000'
                              'test_compute_FFT.py 20000'
                              'test_laplace_jacobi2.py 105'
                              'test_sqrt_matrix.py 6000'
                              'gauss_legendre_quadrature_py3.py 10000'
                              'test_evaluate_functions.py 80000'
                              'test_pernicious_numbers.py 20000000'

                              'mov_robots.py'
                              'cvar.py 500'
                              'eq_solver.py 500'
                              'curves.py 5000 5000 5000 5000 5000 5000 5000 5000'
                              'chunks.py 500'
                              'gc.py CR954253.fasta'
                              'median.py 500'

                              'menger_sponge2.py')

for i in "${!exp_paths[@]}"; do
    a_path="${exp_paths[$i]}"
    a_script_input_and_option="${exp_script_input_and_options[$i]}"
    run_exp_pure_python "$a_path" "$a_script_input_and_option"
done

for i in "${!exp_paths[@]}"; do
    a_path="${exp_paths[$i]}"
    a_script_input_and_option="${exp_script_input_and_options[$i]}"
    run_exp_noworkflow_fine_grain "$a_path" "$a_script_input_and_option"
done

for i in "${!exp_paths[@]}"; do
    a_path="${exp_paths[$i]}"
    a_script_input_and_option="${exp_script_input_and_options[$i]}"
    run_exp_noworkflow_depth_2 "$a_path" "$a_script_input_and_option"
done

for i in "${!exp_paths[@]}"; do
    a_path="${exp_paths[$i]}"
    a_script_input_and_option="${exp_script_input_and_options[$i]}"
    run_exp_noworkflow_depth_3 "$a_path" "$a_script_input_and_option"
done

for i in "${!exp_paths[@]}"; do
    a_path="${exp_paths[$i]}"
    a_script_input_and_option="${exp_script_input_and_options[$i]}"
    run_exp_noworkflow_coarse_grain "$a_path" "$a_script_input_and_option"
done

for i in "${!exp_paths[@]}"; do
    a_path="${exp_paths[$i]}"
    a_script_input_and_option="${exp_script_input_and_options[$i]}"
    run_exp_noworkflow_no_evaluation "$a_path" "$a_script_input_and_option"
done

for i in "${!exp_paths[@]}"; do
    a_path="${exp_paths[$i]}"
    a_script_input_and_option="${exp_script_input_and_options[$i]}"
    run_exp_noworkflow_relevant_evaluation "$a_path" "$a_script_input_and_option"
done
