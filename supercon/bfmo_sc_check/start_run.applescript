-- Starts run.sh in the background; output goes to run.log in this folder.
do shell script "export PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin; cd /Users/a404/Documents/materialsScience/supercon/bfmo_sc_check && nohup /bin/bash run.sh > run.log 2>&1 < /dev/null &"
