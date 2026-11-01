#!/bin/bash
# The case study on the prepared machine, inside the unit nowgate-casestudy (AllowedCPUs = the run CPU).
set -u
V=$HOME/gate/env-2.2.0-ca5c198cde13/venv
A=$HOME/noworkflow-analysis/beyond-python
D=$HOME/creditcard.csv
C=$HOME/gate/casestudy
echo "start $(date -u +%FT%TZ); $(taskset -pc $$); analysis $(git -C $A log -1 --format=%h); $($V/bin/now --version); R $(Rscript -e 'cat(R.version.string, "rdtLite", as.character(packageVersion("rdtLite")))'); $(cc --version | head -1); $(strace -V | head -1)"
$V/bin/python $HOME/noworkflow-overhead-experiments/beyond-python/overhead.py $V $A $D $C/overhead 3
echo "overhead.py exit $? at $(date -u +%FT%TZ)"
$V/bin/python $C/rdtlite_time.py $V $A $D $C/rdtlite 3
echo "rdtlite_time.py exit $? at $(date -u +%FT%TZ)"
