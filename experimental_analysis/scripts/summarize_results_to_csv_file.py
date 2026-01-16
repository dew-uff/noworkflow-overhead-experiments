from typing import List


def extract_values(data: str, result: dict):
  data = data.split("\n")
  exp_path, data = extract_exp_path(data)
  if exp_path not in result: result[exp_path] = {}

  command, data = extract_next_command(data)
  if command not in result[exp_path]: result[exp_path][command] = {}

  next_trial = len(result[exp_path][command]) + 1
  result[exp_path][command][f"trial{next_trial}"] = extract_trial_info(data)

  return result


def extract_exp_path(data: List[str]):
  for i in range(len(data)):
    line = data[i].strip()
    if line.startswith("Entering experiment folder: "):
      return line[len("Entering experiment folder: "):].strip(), data[i+1:]


def extract_next_command(data: List[str]):
  for i in range(len(data)):
    line = data[i].strip()
    if line.startswith("Executing command:"):
        return line[len("Executing command: "):].strip(), data[i+1:]


def extract_trial_info(data: List[str]):
  time = ''
  space = ''
  space_human = ''
  for i in range(len(data)):
    line = data[i].strip()

    if line == 'noWorkflow folder not found!':
        time = data[i-1].strip()

    if line == 'Executing command: du .noworflow/':
        time = data[i-1].strip()
        space = data[i+1].split()[0].strip()

    if line == 'Executing command: du -hs .noworflow/':
        space_human = data[i+1].split()[0].strip()

  return {'time': time, 'space': space, 'space_human': space_human}


def write_csv_file(content: dict):
  with open('out.out', 'wt') as out:
    out.write("Experiment Path\t\
              Comando\t\
              trial1 - time\t\
              trial2 - time\t\
              trial3 - time\t\
              trial4 - time\t\
              trial5 - time\t\
              trial6 - time\t\
              trial7 - time\t\
              trial8 - time\t\
              trial9 - time\t\
              trial10 - time\t\
              space\t\
              All space equal?\t\
              space_human\t\
              All space_human equal?\n")

    for exp_path, data in content.items():
      for command, trials in data.items():
        spaces = [trial_data['space'] for trial_data in trials.values()]
        all_spaces_equal = spaces.count(spaces[0]) == len(spaces)

        spaces_human = [trial_data['space_human'] for trial_data in trials.values()]
        all_spaces_human_equal = spaces_human.count(spaces_human[0]) == len(spaces_human)

        out.write(f"{exp_path}\t\
                    {command}\t\
                    {trials['trial1']['time']}\t\
                    {trials['trial2']['time']}\t\
                    {trials['trial3']['time']}\t\
                    {trials['trial4']['time']}\t\
                    {trials['trial5']['time']}\t\
                    {trials['trial6']['time']}\t\
                    {trials['trial7']['time']}\t\
                    {trials['trial8']['time']}\t\
                    {trials['trial9']['time']}\t\
                    {trials['trial10']['time']}\t\
                    {spaces[0]}\t\
                    {all_spaces_equal}\t\
                    {spaces_human[0]}\t\
                    {all_spaces_human_equal}\n")

# data = {
#   'experiment_path': {
#     'command': {
#       'trial1': {
#         'time': 10.1,
#         'space': 1012131,
#         'space_human': '10MB'
#       }
#     }
#   }
# }


EXTRACTED_DATA = {}
INPUT_FILES = ['output_trial1.txt',
               'output_trial2.txt',
               'output_trial3.txt',
               'output_trial4.txt',
               'output_trial5.txt',
               'output_trial6.txt',
               'output_trial7.txt',
               'output_trial8.txt',
               'output_trial9.txt',
               'output_trial10.txt']

for file in INPUT_FILES:
  with open(file, 'rt') as f:
    exp_data = f.read().split('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')[1:]
    for data in exp_data:
        EXTRACTED_DATA = extract_values(data, EXTRACTED_DATA)

write_csv_file(EXTRACTED_DATA)
