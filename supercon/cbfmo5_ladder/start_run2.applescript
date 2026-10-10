-- Queues run2.sh (waits for run.sh to finish first); log -> run2.log in this folder.
do shell script "export PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin; cd /Users/a404/Documents/materialsScience/supercon/cbfmo5_ladder && nohup /bin/bash run2.sh > run2.log 2>&1 < /dev/null &"
