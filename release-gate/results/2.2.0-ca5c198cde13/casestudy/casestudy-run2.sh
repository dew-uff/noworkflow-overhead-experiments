#!/bin/bash
# Second round of the case study on the prepared machine, inside the unit nowgate-casestudy2 (AllowedCPUs = the run CPU):
# overhead.py and rdtlite_time.py (with trial4-plain), 10 repetitions each. The 3-repetition round stays in overhead/ and rdtlite/.
set -u
V=$HOME/gate/env-2.2.0-ca5c198cde13/venv
A=$HOME/noworkflow-analysis/beyond-python
D=$HOME/creditcard.csv
C=$HOME/gate/casestudy
echo "scripts: $(cd $C && sha1sum overhead.py rdtlite_time.py | tr '\n' ' ')"
echo "start $(date -u +%FT%TZ); $(taskset -pc $$); analysis $(git -C $A log -1 --format=%h); $($V/bin/now --version); R $(Rscript -e 'cat(R.version.string, "rdtLite", as.character(packageVersion("rdtLite")))'); $(cc --version | head -1); $(strace -V | head -1)"
$V/bin/python $C/overhead.py $V $A $D $C/overhead-10 10
echo "overhead.py exit $? at $(date -u +%FT%TZ)"
$V/bin/python $C/rdtlite_time.py $V $A $D $C/rdtlite-10 10
echo "rdtlite_time.py exit $? at $(date -u +%FT%TZ)"
