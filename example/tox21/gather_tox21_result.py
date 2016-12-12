import sys
import pandas as pd
import glob
import re

dataset_name = 'tox21'
dir_to_store_result = sys.argv[1]
all_files = glob.glob( dir_to_store_result + 'each_target_cv_result/' + dataset_name + "*_cv_result.csv")
base = pd.read_csv(all_files[0])
cv_result = pd.DataFrame(base.iloc[:,1])
cv_result.index = base.iloc[:,0]

for i,file in enumerate(all_files[1:len(all_files)]):
    temp = pd.read_csv(file)
    temp2 = pd.DataFrame(temp.iloc[:,1])
    temp2.index = temp.iloc[:,0]
    cv_result = pd.concat([cv_result,temp2],axis = 1)

cv_result.to_csv(dir_to_store_result + dataset_name + "_cv_result.csv")

# test result
all_files = glob.glob( dir_to_store_result + 'each_target_test_result/' + dataset_name + "*_test_result.csv")
base = pd.read_csv(all_files[0])
target_name = re.sub(dir_to_store_result + 'each_target_test_result/' + dataset_name + '_','',all_files[0])
target_name = re.sub('_test_result.csv','',target_name)
# reconstruct dataframe for easy to view
test_result = pd.DataFrame({target_name : list(base.iloc[0:6,2])+list(base.iloc[6:12,1])})
test_result.index = base.iloc[:,0]
test_result = test_result.iloc[[0,3,1,2,6,9,7,8]]

for i,file in enumerate(all_files[1:len(all_files)]):
    temp = pd.read_csv(file)
    target_name = re.findall('aid\d{1,10}',file)[0]
    temp2 = pd.DataFrame({target_name : list(temp.iloc[0:6,2])+list(temp.iloc[6:12,1])})
    temp2.index = temp.iloc[:,0]
    temp2 = temp2.iloc[[0,3,1,2,6,9,7,8]]
    test_result = pd.concat([test_result,temp2],axis = 1)

test_result.to_csv(dir_to_store_result + dataset_name + "_test_result.csv")
