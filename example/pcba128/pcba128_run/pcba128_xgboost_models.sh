#!/bin/bash
# input argument1: dir/to/lightchem/example/pcba128/
# e.g. ~/lightchem/example/pcba128/
# argument2: dir/to/store/result/
# e.g. ~/analyzed_result/
# argument3: aid_list.csv
# (A csv file containing target names, e.g. 'aid411')
# Used to loop over each target.

mkdir -p ../pcba128_results

while IFS='' read -r line;do

echo Running $line
python $1/'pcba128_xgboost_models.py' $line $2

done <"$3"

python $1/'gather_pcba128_result.py' $2
