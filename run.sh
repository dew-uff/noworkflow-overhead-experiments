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
  eval "$exp_cmd"

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


conda activate $NOWORKFLOW_CONDA_ENV

base_dir=$PATH_TO_GIT_REPOSITORY
base_dataone_dir="${base_dir}/03dataoneexps"

exp_paths=("${base_dataone_dir}/03dataoneexps_exp01_32_Accessing_Hydrologic_Data"
           "${base_dataone_dir}/03dataoneexps_exp02_40_e_44_Agua_Salud_Rainfall_Data"
           "${base_dataone_dir}/03dataoneexps_exp03_46_A_Method_For_Calculating"
           "${base_dataone_dir}/03dataoneexps_exp04_49_Analysis_Of_Flow"
           "${base_dataone_dir}/03dataoneexps_exp05_37_Agua_Salud_Discharge_Data")

exp_script_input_and_options=('main.py'
                              'export_rainfall.py --site MOS -d gage_data --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z'
                              'main.py'
                              'main.py'
                              'export_discharge.py --site FOR -d discharge_sharp --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z')

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
