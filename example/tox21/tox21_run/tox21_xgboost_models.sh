#!/bin/bash

while IFS='' read -r line;do

python $1/'tox21_xgboost_models.py' $line $2

done <"$3"

python $1/'gather_tox21_result.py' $2
