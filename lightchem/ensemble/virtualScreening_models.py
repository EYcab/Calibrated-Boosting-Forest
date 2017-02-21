"""
A collection of pre-defined ensemble models for virtual screening.
"""

import numpy as np
import pandas as pd
from lightchem.load import load
from lightchem.fold import fold
from lightchem.data import xgb_data
from lightchem.eval import xgb_eval
from lightchem.eval import eval_testset
from lightchem.model import first_layer_model
from lightchem.model import second_layer_model
from lightchem.eval import defined_eval

# For this specific model object, REQUIRED first label name always represent
# Binary label column, where value are 1 or 0.
class VsEnsembleModel(object):
    """
    Wrapper class to build default ensemble models structure
    """
    def __init__(self,training_info,eval_name,seed = 2016,verbose = False):
        """
        Parameters:
        ----------
        training_info: list
         List of tuple, where each tuple contains 2 items, first item is dataframe
         containing training data(required to have fingerprint column named 'fingerprint',
         and concatanate fingerprint in a string),
         second item is a list containing the one or more label name.
         The first label name of first tuple is the default label that will be
         used for both layer models.
         If multiple label names present, VsEnsembleModel will automatically build
         model based on each label and ensemble them together.
         EX: [(my_dataframe,['binary_label','continuous_label'])]
         For this specific model object, REQUIRED first label name always be
         Binary label name.
        eval_name: str
         Name of evaluation metric used to monitor and stop training process.
         Must in pre-difined evaluation list.
          Currently supports:
          `ROCAUC`: Area under curve of ROC
          `PRAUC`: Area under curve of Precision-recall
          `EFR1`: Enrichment factor at 0.01
          `EFR015`: Enrichment factor at 0.0015
        """
        self.__training_info = training_info
        self.__check_labelType()
        self.__eval_name = eval_name
        self.__setting_list = []
        self.seed  = seed
        self.__prepare_xgbdata()
        self.__layer1_model_list = []
        self.__layer2_model_list = []
        self.__best_model_result = None
        self.__verbose = verbose
    def __prepare_xgbdata(self):
        """
        Internal method to build required data(xgbData) objects
        """
        print 'Preparing data'
        #Based on how many unique number, automatically detect if label column
        # is binary or continuous.
        has_fold = False
        num_xgbData = 0
        num_folds = 3
        my_fold = None
        for item in self.__training_info:
            temp_df = item[0]
            for column_name in item[1]:
                # if it is binary label, use models for binary label.
                if len(np.unique(temp_df[column_name])) == 2:
                    model_name_to_use = ['GbtreeLogistic','GblinearLogistic']
                    temp_labelType = 'binary'
                else:
                    model_name_to_use = ['GbtreeRegression','GblinearRegression']
                    temp_labelType = 'continuous'

                temp_data = load.readData(temp_df,column_name)
                temp_data.read()
                X_data = temp_data.features()
                y_data = temp_data.label()
                # Need to generate fold once, based on binary label
                if not has_fold:
                    my_fold = fold.fold(X_data,y_data,num_folds,self.seed)
                    my_fold = my_fold.generate_skfolds()
                    has_fold = True
                data = xgb_data.xgbData(my_fold,X_data,y_data)
                data.build()
                num_xgbData += 1
                temp_dataName = 'Number:' + str(num_xgbData) + " xgbData, " + 'labelType: ' + temp_labelType
                self.__setting_list.append({'data_name':temp_dataName,
                                            'model_type':model_name_to_use,
                                            'data':data})

    def __check_labelType(self):
        """
        Internal method to check whether label columns are numeric
        """
        for item in self.__training_info:
            temp_df = item[0]
            for name in item[1]:
                assert np.issubdtype(temp_df[name].dtype,np.number)

    def train(self):
        evaluation_metric_name = self.__eval_name
        #---------------------------------first layer models ----------
        for data_dict in self.__setting_list:
            for model_type in data_dict['model_type']:
                unique_name = 'layer1_' + data_dict['data_name'] + '_' + model_type + '_' + evaluation_metric_name
                model = first_layer_model.firstLayerModel(data_dict['data'],
                        evaluation_metric_name,model_type,unique_name)
                # Retrieve default parameter and change default seed.
                default_param,default_MAXIMIZE,default_STOPPING_ROUND = model.get_param()
                default_param['seed'] = self.seed
                if self.__verbose == True:
                    default_param['silent'] = 1
                elif:
                    self.__verbose == False:
                    default_param['silent'] = 0
                model.update_param(default_param,default_MAXIMIZE,default_STOPPING_ROUND)
                model.xgb_cv()
                model.generate_holdout_pred()
                self.__layer1_model_list.append(model)

        #------------------------------------second layer models
        layer2_label_data = self.__setting_list[0]['data'] # layer1 data object containing the label for layer2 model
        layer2_modeltype = ['GbtreeLogistic','GblinearLogistic']
        layer2_evaluation_metric_name = [self.__eval_name]
        for evaluation_metric_name in layer2_evaluation_metric_name:
            for model_type in layer2_modeltype:
                unique_name = 'layer2' + '_' + model_type + '_' + evaluation_metric_name
                l2model = second_layer_model.secondLayerModel(layer2_label_data,self.__layer1_model_list,
                            evaluation_metric_name,model_type,unique_name)
                l2model.second_layer_data()
                # Retrieve default parameter and change default seed.
                default_param,default_MAXIMIZE,default_STOPPING_ROUND = l2model.get_param()
                default_param['seed'] = self.seed
                if self.__verbose == True:
                    default_param['silent'] = 1
                elif:
                    self.__verbose == False:
                    default_param['silent'] = 0
                l2model.update_param(default_param,default_MAXIMIZE,default_STOPPING_ROUND)
                l2model.xgb_cv()
                self.__layer2_model_list.append(l2model)


        #------------------------------------ evaluate model performance on test data
        # prepare test data, retrive from layer1 data
        list_TestData = []
        for data_dict in self.__setting_list:
            for model_type in data_dict['model_type']:
                list_TestData.append(data_dict['data'].get_dtest())
        test_label = layer2_label_data.get_testLabel()
        test_result_list = []
        i = 0
        for evaluation_metric_name in layer2_evaluation_metric_name:
            for model_type in layer2_modeltype:
                test_result = eval_testset.eval_testset(self.__layer2_model_list[i],
                                                        list_TestData,test_label,
                                                        evaluation_metric_name)
                test_result_list.append(test_result)
                i += 1

        # merge cv and test result together. Calcuate the weighted average of
        # cv and test result for each model(layer1, layer2 model). Then use the best
        # model to predict. Need to find the optimal model from model list.
        # collect cv result and convert to a list
        all_model = self.__layer1_model_list + self.__layer2_model_list
        result = []
        for model in all_model:
            result = result + [item for item in np.array(model.cv_score_df())[0]]
        # Retrieve corresponding name of cv result
        result_index = []
        for model in all_model:
            result_index.append(model.name)
        # create a dataframe
        cv_result = pd.DataFrame({'cv_result' : result},index = result_index)

        test_result = pd.concat(test_result_list,axis = 0,ignore_index=False)
        test_result = test_result.rename(columns = {self.__eval_name:'test_result'})
        #Automatically selet distinct row.
        test_result['temp_name'] = test_result.index
        test_result = test_result.drop_duplicates(['temp_name'])
        test_result = test_result.drop('temp_name',1)
        cv_test = pd.merge(cv_result,test_result,how='left',left_index=True,right_index=True)
        num_folds = np.float64(num_folds)
        cv_test['weighted_score'] = cv_test.cv_result * (num_folds-1)/num_folds + cv_test.test_result * (1/num_folds)
        weighted_score = cv_test.cv_result * (num_folds-1)/num_folds + cv_test.test_result * (1/num_folds)

        # Determine does current evaluation metric need to maximize or minimize
        eval_info = defined_eval.definedEvaluation()
        is_max = eval_info.is_maximize(self.__eval_name)
        if is_max:
            position = np.where(cv_test.weighted_score == cv_test.weighted_score.max())
            best_model_name = cv_test.weighted_score.iloc[position].index[0]
        else:
            position = np.where(cv_test.weighted_score == cv_test.weighted_score.min())
            best_model_name = cv_test.weighted_score.iloc[position].index[0]
        # find best model
        all_model_name = [model.name for model in all_model]
        model_position = all_model_name.index(best_model_name)
        best_model = all_model[model_position]
        self.__best_model_result = pd.DataFrame(cv_test.loc[best_model.name])


    def training_result(self):
        if not isinstance(self.__best_model_result,pd.DataFrame):
            raise ValueError('You must call `train` before `training_result`')
        return self.__best_model_result
