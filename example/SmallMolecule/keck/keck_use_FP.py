import sys
#sys.path.remove('/usr/lib/python2.7/dist-packages')
sys.path.append("../virtual-screening/virtual_screening")
from lightchem.ensemble.virtualScreening_models import *
from lightchem.featurize import fingerprint
from lightchem.eval import defined_eval
from lightchem.utility.util import reverse_generate_fold_index
from function import *
#from data_preparation import *
from evaluation import * # need to comment out rpy2* and croc.
from openpyxl import Workbook
import pandas as pd
import numpy as np
import operator
from rdkit import Chem
from rdkit.Chem import AllChem
import time
import os


# Need to make sure relative directory has required datasets.
# Need to download prive datasets from Tony's lab.
start_date = time.strftime("%Y_%m_%d_%H")
store_prediction = True
feature_used = 'FP'

#if __name__ == "__main__"
for fold_num in [5,3,4]:

#    complete_df = pd.read_csv('./dataset/keck_complete.csv')
    k = fold_num
    #k = 5
    directory = './dataset/fixed_dataset/fold_{}/'.format(k)
    file_list = []
    for i in range(k):
        file_list.append('file_{}.csv'.format(i))
    #greedy_multi_splitting(complete_df, k, directory=directory, file_list=file_list)

    dtype_list = {'Molecule': np.str,
                'SMILES':np.str,
                'Fingerprints': np.str,
                'Keck_Pria_AS_Retest': np.int64,
                'Keck_Pria_FP_data': np.int64,
                'Keck_Pria_Continuous': np.float64,
                'Keck_RMI_cdd': np.float64}
    output_file_list = [directory + f_ for f_ in file_list]
    train_roc = []
    val_roc = []
    test_roc = []
    train_precision = []
    val_precision = []
    test_precision = []
    train_bedroc = []
    val_bedroc = []
    test_bedroc = []
    train_efr1 = []
    val_efr1 = []
    test_efr1 = []

    test_ef01 = []
    test_ef02 = []
    test_ef0015 = []
    test_ef001 = []

    for j in range(k):
        start = time.time()
        index = list(set(range(k)) - set([j]))
        train_file = list(np.array(output_file_list)[index])
        test_file = [output_file_list[j]]
        print train_file
        train_pd = read_merged_data(train_file)
        print test_file
        test_pd = read_merged_data(test_file)
        my_fold_index = reverse_generate_fold_index(train_pd, train_file,
                                                     index, 'Molecule')

        # Using lightchem

        target_name = 'KECK_Pria'
        smile_colname = 'SMILES'
        label_name_list = ['Keck_Pria_AS_Retest','Keck_Pria_Continuous']
        eval_name = 'ROCAUC'
        dir_to_store = './'

        preDefined_eval = defined_eval.definedEvaluation()
        preDefined_eval.validate_eval_name(eval_name)
        df = train_pd
        #---------- Build Model
        print 'Preparing training data fingerprints'
        # morgan(ecfp) fp
        fp = fingerprint.smile_to_fps(df,smile_colname)
        morgan_fp = fp.Morgan()
        # MACCSkeys fp
        fp = fingerprint.smile_to_fps(df,smile_colname)
        maccs_fp = fp.MACCSkeys()
        comb1 = (morgan_fp,label_name_list)
        comb2 = (maccs_fp,label_name_list)
        training_info = [comb1,comb2]

        print 'Preparing testing data fingerprints'
        df_test = test_pd
        # morgan(ecfp) fp
        fp = fingerprint.smile_to_fps(df_test,smile_colname)
        morgan_fp = fp.Morgan()
        # MACCSkeys fp
        fp = fingerprint.smile_to_fps(df_test,smile_colname)
        maccs_fp = fp.MACCSkeys()
        comb1_test = (morgan_fp,None)# test data does not need label name
        comb2_test = (maccs_fp,None)
        testing_info = [comb1_test,comb2_test]

        print 'Building and selecting best model'
        # Current VsEnsembleModel create test data by default
        model = VsEnsembleModel_keck_test(training_info,
                                     eval_name,
                                     fold_info = my_fold_index,
                                     createTestset = False)
        model.train()
        cv_result = model.training_result()
        all_results = model.detail_result()

        #cv_result.to_csv(dir_to_store + target_name + "_result.csv")
        #all_results.to_csv(dir_to_store + target_name + "_result_allModels.csv")

        #----------- Predict testset
        print 'Predict test data'
        y_pred_on_test = model.predict(testing_info)
        y_pred_on_train = model.predict(training_info)
        y_test = np.array(df_test['Keck_Pria_AS_Retest'])
        y_train = np.array(comb1[0]['Keck_Pria_AS_Retest'])
        validation_info = model.get_validation_info()
        #---------- Use same evaluation functions
        if not os.path.exists("./result"):
            os.makedirs("./result")

        for z,val in enumerate(validation_info):
            str1 = './result/result_' + start_date + "_" + str(fold_num)
            str2 = 'fold_test' + str(j) + '_' + str(z) +'.txt'
            f = open(str1 + str2 , 'a')
            print >> f, "########################################"
            print >> f, "Number of Fold: ", k
            print >> f, "Test file: ", j
            print >> f, "Stopping metric: ", eval_name
            print >> f, "Features: ", feature_used
            print >> f, all_results
            print >> f, cv_result
            print >> f, " "
            print >> f,('train precision: {}'.format(precision_auc_single(
                        y_train, y_pred_on_train, mode='auc.sklearn')))
            print >> f,('train roc: {}'.format(roc_auc_single(
                        y_train, y_pred_on_train)))
            print >> f,('train bedroc: {}'.format(bedroc_auc_single(
                        reshape_data_into_2_dim(y_train),
                        reshape_data_into_2_dim(y_pred_on_train))))
            n_actives, ef, ef_max = enrichment_factor_single(y_train, y_pred_on_train, 0.01)
            print >> f,('train EFR1: {}'.format(ef))

            print >> f, " "
            print >> f,('validation precision : {}'.format(
                     precision_auc_single(val.label, val.validation_pred,
                     mode='auc.sklearn')))
            print >> f,('validation roc : {}'.format(
                     roc_auc_single(val.label, val.validation_pred)))
            print >> f,('validation bedroc : {}'.format(
                     bedroc_auc_single(reshape_data_into_2_dim(val.label),
                     reshape_data_into_2_dim(val.validation_pred))))
            n_actives, ef, ef_max = enrichment_factor_single(np.array(val.label),
                                                             np.array(val.validation_pred),
                                                             0.01)
            print >> f,('validation EFR1: {}'.format(ef))

            print >> f, " "
            print >> f,('test precision: {}'.format(precision_auc_single(
                        y_test, y_pred_on_test,mode='auc.sklearn')))
            print >> f,('test roc: {}'.format(roc_auc_single(
                        y_test, y_pred_on_test)))
            print >> f,('test bedroc: {}'.format(bedroc_auc_single(
                        reshape_data_into_2_dim(y_test),
                        reshape_data_into_2_dim(y_pred_on_test))))
            n_actives, ef, ef_max = enrichment_factor_single(y_test, y_pred_on_test, 0.01)
            print >> f,('test EFR1: {}'.format(ef))
            print >> f, " "

            EF_ratio_list = [0.02, 0.01, 0.0015, 0.001]
            for EF_ratio in EF_ratio_list:
                n_actives, ef, ef_max = enrichment_factor_single(y_test, y_pred_on_test, EF_ratio)
                print >> f,('ratio: {}, EF: {}, EF_max: {}\tactive: {}'.format(EF_ratio, ef, ef_max, n_actives))

            end = time.time()
            print >> f, 'time used: ', end - start
            f.close()

        # Accumulate results for each set. ex: 5fold, 4fold, 3fold.
        # ROCAUC
        train_roc.append(roc_auc_single(y_train, y_pred_on_train))
        for i,val in enumerate(validation_info):
            val_roc.append(roc_auc_single(val.label, val.validation_pred))
        test_roc.append(roc_auc_single(y_test, y_pred_on_test))
        # PRAUC
        train_precision.append(precision_auc_single(y_train, y_pred_on_train, mode='auc.sklearn'))
        for i,val in enumerate(validation_info):
            val_precision.append(precision_auc_single(val.label, val.validation_pred,mode='auc.sklearn'))
        test_precision.append(precision_auc_single(y_test, y_pred_on_test, mode='auc.sklearn'))
        # BEDROC
        train_bedroc.append(bedroc_auc_single(reshape_data_into_2_dim(y_train),
                                              reshape_data_into_2_dim(y_pred_on_train)))
        for i,val in enumerate(validation_info):
            val_bedroc.append(bedroc_auc_single(reshape_data_into_2_dim(val.label),
                                                reshape_data_into_2_dim(val.validation_pred)))
        test_bedroc.append(bedroc_auc_single(reshape_data_into_2_dim(y_test),
                                             reshape_data_into_2_dim(y_pred_on_test)))
        # EFR1
        n_actives, ef, ef_max = enrichment_factor_single(y_train, y_pred_on_train, 0.01)
        train_efr1.append(ef)
        for i,val in enumerate(validation_info):
            n_actives, ef, ef_max = enrichment_factor_single(np.array(val.label),
                                                             np.array(val.validation_pred),
                                                             0.01)
            val_efr1.append(ef)
        n_actives, ef, ef_max = enrichment_factor_single(y_test, y_pred_on_test, 0.01)
        test_efr1.append(ef)

        n_actives, ef, ef_max = enrichment_factor_single(y_test, y_pred_on_test, 0.01)
        test_ef01.append(ef)
        n_actives, ef, ef_max = enrichment_factor_single(y_test, y_pred_on_test, 0.02)
        test_ef02.append(ef)
        n_actives, ef, ef_max = enrichment_factor_single(y_test, y_pred_on_test, 0.0015)
        test_ef0015.append(ef)
        n_actives, ef, ef_max = enrichment_factor_single(y_test, y_pred_on_test, 0.001)
        test_ef001.append(ef)

        # Store prediction scores.
        if store_prediction:
            base_dir = "./predictions/pred_" + start_date
            directory = base_dir + "/" + str(fold_num) + 'fold' + "_" +"test" + str(j)
            if not os.path.exists(directory):
                os.makedirs(directory)
            train = pd.DataFrame({'label':y_train,'train_pred':y_pred_on_train})
            train.to_csv(directory + "/train_pred.csv", index = False)
            for i,val in enumerate(validation_info):
                val.to_csv(directory + "/val_pred" + str(i) + ".csv", index = False)
            test = pd.DataFrame({'label':y_test,'train_pred':y_pred_on_test})
            test.to_csv(directory + "/test_pred.csv", index = False)

        # Store ef curve info
        EF_ratio_list = np.linspace(0.0001, 0.15, 200)
        ef_values = []
        ef_max_values = []
        for EF_ratio in EF_ratio_list:
            n_actives, ef, ef_max = enrichment_factor_single(y_test, y_pred_on_test, EF_ratio)
            ef_values.append(ef)
            ef_max_values.append(ef_max)
        ef_curve_df = pd.DataFrame({'ef_values':ef_values,
                                    'ef_max_values':ef_max_values,
                                    'ef_ratio':EF_ratio_list})
        directory = "./result/"
        #directory = base_dir + "/test" + str(j) + "_" + str(fold_num) + 'fold'
        if not os.path.exists(directory):
            os.makedirs(directory)
        str1 = directory + 'EF_curve_' + start_date + '_' + str(fold_num)
        str2 = 'fold_test' + str(j) + '.csv'
        ef_curve_df.to_csv(str1 + str2 , index = False)


    f = open('./result/summary_' + start_date + "_" + str(fold_num) + 'fold.txt', 'a')
    print >> f, "########################################"
    print >> f, "Number of Fold: ", k
    print >> f, "Stopping metric: ", eval_name
    print >> f, "Features: ", feature_used
    print >> f, 'Train ROC AUC mean: ', np.mean(train_roc)
    print >> f, 'Train ROC AUC std', np.std(train_roc)
    print >> f, 'Validatoin ROC AUC mean: ', np.mean(val_roc)
    print >> f, 'Validation ROC AUC std', np.std(val_roc)
    print >> f, 'Test ROC AUC mean: ', np.mean(test_roc)
    print >> f, 'Test ROC AUC std', np.std(test_roc)
    print >> f, 'Train Precision mean: ', np.mean(train_precision)
    print >> f, 'Train Precision std', np.std(train_precision)
    print >> f, 'Validation Precision mean: ', np.mean(val_precision)
    print >> f, 'Validation Precision std', np.std(val_precision)
    print >> f, 'Test Precision mean: ', np.mean(test_precision)
    print >> f, 'Test Precision std', np.std(test_precision)
    print >> f, 'Train BEDROC AUC mean: ', np.mean(train_bedroc)
    print >> f, 'Train BEDROC AUC std', np.std(train_bedroc)
    print >> f, 'Validatoin BEDROC AUC mean: ', np.mean(val_bedroc)
    print >> f, 'Validation BEDROC AUC std', np.std(val_bedroc)
    print >> f, 'Test BEDROC AUC mean: ', np.mean(test_bedroc)
    print >> f, 'Test BEDROC AUC std', np.std(test_bedroc)
    print >> f, 'Train ef@0.01 mean: ', np.mean(train_efr1)
    print >> f, 'Train ef@0.01 std', np.std(train_efr1)
    print >> f, 'Validatoin ef@0.01 mean: ', np.mean(val_efr1)
    print >> f, 'Validation ef@0.01 std', np.std(val_efr1)
    print >> f, 'Test ef@0.01 mean: ', np.mean(test_efr1)
    print >> f, 'Test ef@0.01 std', np.std(test_efr1)
    print >> f, 'Test ef@0.01 mean: ', np.mean(test_ef01)
    print >> f, 'Test ef@0.01 std', np.std(test_ef01)
    print >> f, 'Test ef@0.02 mean: ', np.mean(test_ef02)
    print >> f, 'Test ef@0.02 std', np.std(test_ef02)
    print >> f, 'Test ef@0.0015 mean: ', np.mean(test_ef0015)
    print >> f, 'Test ef@0.0015 std', np.std(test_ef0015)
    print >> f, 'Test ef@0.001 mean: ', np.mean(test_ef001)
    print >> f, 'Test ef@0.001 std', np.std(test_ef001)
    f.close()
