#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 26 08:16:36 2018

@author: andrewcarroll
"""
import requests
from requests_toolbelt import MultipartEncoder
from einstein_constants import LANG_BASE_URL
import json
from random import randint

class Dataset:
    """The dataset class contains methods for creating and interacting with datasets.

    This simple wrapper contains all information and methods necessary for uploading
    and interacting with datasets in EPS. 
    """
    
    def __init__(self,einstein_session,datasetId=None):
        """Init method associates a session and, if provided a datasetId, queries the status.

        Note:
            If a datasetId is provided, the init method will make a call to the EPS API to query
            the status of the dataset with that ID. Othwerise, the object is returned with no data.

        Args:
            einstein_session (EinsteinPlatformSession): An active EinsteinPlatformSession object
                whose information will be used for each API call.
            datasetId (:obj:`str`, optional): If provided, the a call will be made to query the
                status of the dataset with the given ID in Einstein Intent during the initialization.

        Attributes:
            session (EinsteinPlatformSession): A name for the active session.
            datasetId (str): The EPS ID for the dataset. If not provided, it will be set when
                the dataset is created in EPS.
            dataset_metadata (dict): Initialized as an empty dictionary, once a dataset is created
                on EPS, this will hold the metadata from a successful update status call to the dataset.
            labels (list): List of class labels. Automatically populated when the dataset is created.
        """
        self.session = einstein_session 
        self.datasetId = datasetId
        self.dataset_metadata = None
        self.labels=[]

        if datasetId:
            _,_ = self.update_dataset_status()
    
    def __repr__(self):
        return '<Dataset %s, %s>'%(
                self.datasetId,self.__class__.__name__)
        
    def header_helper(self,multipart_data):
        return {'Authorization': 'Bearer ' + self.session.token,
                'Content-Type': multipart_data.content_type}

    def reset_token(self,session_time=3600):
        """Class method to resest an Authorization Token for access to Einstein Platform Services.

        Args:
            session_time (int, optional): Valid duration of the access token, in seconds.
        """
        self.session.reset_authorization_token(session_time)

    def create_dataset(self,filepath=None,urlpath=None):
        """Class method for creating a dataset in EPS.

        The create_dataset method, when provided with a means of accessing a data file, will
        call the datasets upload endpoint in the EPS API. If successful, the datasetId and
        dataset_metadata attributes will be populated.

        Note: 
            At least one of the two optional arguments must be provided. An assertion failure
            will result if the datasetId has already been provided (in this case, make a new object).

        Args:
            filepath (str, optional): Filepath to a comma-separated-values file to upload as dataset.
            urlpath (str, optional): url pointing to a comma-separated-values file to upload as dataset.
        """
        assert not self.datasetId, """This dataset has already been populated.
To create a new dataset, make a new Dataset object"""
        assert (filepath or urlpath), "User must provide filepath or urlpath"
        if filepath:
            print('Warning: this has issues on Mac OS')
            multipart_data = MultipartEncoder(
                    fields={
                        'data': '@'+filepath,
                        'type': 'text-intent'})
        elif urlpath:
            multipart_data = MultipartEncoder(
                    fields={
                        'path': urlpath,
                        'type': 'text-intent'})


        res = requests.post(LANG_BASE_URL+'/datasets/upload',
                            headers=self.header_helper(multipart_data),
                            data=multipart_data)
        if res.ok:
            self.datasetId = str(json.loads(res.text)['id'])
            self.dataset_metadata = json.loads(res.text)
        
        return json.loads(res.text), res.status_code
            

    def delete_self(self):
        """Class method for deleting the dataset from EPS.

        Note:
            EPS dataset is not immediately deleted. As a result, the object stays alive
            so that the user can query the deletion status.            
        """
        headers = {'Authorization': 'Bearer ' + self.session.token}
        status_update = requests.delete(LANG_BASE_URL+'/datasets/'+self.datasetId,
                                     headers=headers
                                     )
        return json.loads(status_update.text), status_update.status_code

    def update_deletion_status(self):
        headers = {'Authorization': 'Bearer ' + self.session.token}
        status_update = requests.delete(LANG_BASE_URL+'/deletion/'+self.datasetId,
                                     headers=headers
                                     )
        return json.loads(status_update.text), status_update.status_code
        
    def update_dataset_status(self):
        """Class method to query the upload status of the dataset and retrieve metadata.

        """
        assert self.datasetId, "No dataset found."
        multipart_data = MultipartEncoder(
                                fields={'type': 'text-intent'})

        status_update = requests.get(LANG_BASE_URL+'/datasets/'+self.datasetId,
                                     headers=self.header_helper(multipart_data),
                                     data=multipart_data
                                     )

        self.dataset_metadata = json.loads(status_update.text)
        try:
            for l in self.dataset_metadata['labelSummary']['labels']:
                if l['name'] not in self.labels:
                    self.labels.append(l['name'])
        except:
            print("Could not find labels in %s"%self.dataset_metadata)
        if status_update.status_code != 200:
            print("There's a problem. Check the status code, %s"%status_update.status_code)
            
        return json.loads(status_update.text), status_update.status_code

    @property
    def dataset_isReady(self):
        pass
    
    @dataset_isReady.getter
    def dataset_isReady(self):
        try:
            if not self.dataset_metadata['available']:
                _,_ = self.update_dataset_status()
            return self.dataset_metadata['available']
        except:
            print('Make sure there is dataset_metadata')
            return False
    
    def get_associated_models(self):
        
        headers={'Authorization': 'Bearer ' + self.session.token}
        
        assoc_models = requests.get(LANG_BASE_URL+'/datasets/%s/models'%self.datasetId,
                                     headers=headers)
        
        return json.loads(assoc_models.text), assoc_models.status_code
    
    
class Model:

    def __init__(self,dataset=None,session=None,datasetId=None,modelId=None,model_name=None):
        """Model objects are containers for the API calls used with models.

        """
        #model can be initialized with various start data
        #ideally the user would pass a dataset object (this is the object oriented method)
        #a dataset object contains the session information and datasetId
        #with only session and datasetId, we can make a dataset object
        #with a session and modelId, we can get a datasetId and create a dataset
        self.model_metadata = None
        self.modelId=modelId

        if dataset:
            self.dataset = dataset
            self.session = self.dataset.session
        else:
            if not session:
                print("Model class requires a session, which hasn't been provided")
            else:
                if datasetId:
                    self.dataset=Dataset(session,datasetId=datasetId)
                else:
                    print("Model requires either a dataset object or a dataset ID with which to create said object.")
        
        if modelId:
            self.model_metadata, status_code = self.update_model_status()
            if status_code != 200:
                print("Irregular status code %s. There may be no metadata.")
            
    def header_helper(self,multipart_data):
        return {'Authorization': 'Bearer ' + self.session.token,
                'Content-Type': multipart_data.content_type}
        
    def update_model_status(self):
        assert self.modelId, "No model found."
        multipart_data = MultipartEncoder(
                                fields={'type': 'text-intent'})

        status = requests.get(LANG_BASE_URL+'/train/'+self.modelId,
                              headers=self.header_helper(multipart_data),
                              data=multipart_data)
        
        self.model_metadata = json.loads(status.text)
        
        return json.loads(status.text), status.status_code        

    @property
    def modelId(self):
        return self.__modelId
    
    @modelId.setter
    def modelId(self,idn):
        self.__modelId = idn
        
    @modelId.getter
    def modelId(self):
        try:
            return self.model_metadata['modelId']
        except KeyError:
            return self.__modelId
        except AttributeError:
            return self.__modelId
        except TypeError:
            return self.__modelId

    @property
    def model_isReady(self):
        pass
    
    @model_isReady.getter
    def model_isReady(self):
        try:
            if self.model_metadata['status']!='SUCCEEDED':
                _,_ = self.update_model_status()
            return (self.model_metadata['status']=='SUCCEEDED') or (self.model_metadata['status']=='FAILED')
        except KeyError:
            return False
        except AttributeError:
            return False
    
            
        
    def train_model(self,model_name=None):
        if not model_name:
            model_name = 'Model_'+str(randint(10000,99999))
            
        
        multipart_data = MultipartEncoder(
                            fields={'name': model_name,
                                    'datasetId': self.dataset.datasetId})

        post_res = requests.post(LANG_BASE_URL+'/train',
                                     headers=self.header_helper(multipart_data),
                                     data=multipart_data)

        self.model_metadata = json.loads(post_res.text)

        try:
            self.modelId = self.model_metadata['modelId']
        except:
            print('Status code %s when attempting to set modelId from model_metadata' %post_res.status_code)
        return json.loads(post_res.text), post_res.status_code


    def submit_feedback(self,document,expectedLabel,verbose=False):
        assert self.modelId, "No model found."
        multipart_data = MultipartEncoder(
                fields={'modelId': self.modelId,
                        'document': document,
                        'expectedLabel': expectedLabel})

        post_status = requests.post(LANG_BASE_URL+'/feedback',
                                    headers=self.header_helper(multipart_data),
                                    data=multipart_data)
        if verbose:
            if post_status.ok:
                feedback_dict = json.loads(post_status.text)
                print("Feedback item %s added to dataset %s as class %s"
                      %(feedback_dict['id'],feedback_dict['label']['datasetId'],
                        feedback_dict['label']['name']))
            else:
                print("""Error: there was a problem in submit_feedback method with code %s""" %post_status.status_code)
                
        return json.loads(post_status.text), post_status.status_code



    def retrain_model(self,feedback=True):
        assert(self.modelId), "No model available."
        assert(self.model_isReady), "The model is still training. Please wait."
        if feedback:
            feedback='true'
        else:
            feedback='false'
        
        multipart_data = MultipartEncoder(
                    fields={'modelId': self.modelId,
                            'trainParams': '{"withFeedback":%s, "trainSplitRatio": 0.7}'%feedback})

        post_res = requests.post(LANG_BASE_URL+'/retrain',
                                 headers=self.header_helper(multipart_data),
                                 data=multipart_data)
        
        self.model_metadata = json.loads(post_res.text)
        
        return json.loads(post_res.text), post_res.status_code
    

    def predict(self,document):
        assert self.modelId, "No model available."
        assert self.model_isReady, "The model hasn't completed training."

        multipart_data = MultipartEncoder(
                fields={'modelId': self.modelId,
                        'document': document})

        prediction_status = requests.post(LANG_BASE_URL+'/intent',
                                   headers=self.header_helper(multipart_data),
                                   data=multipart_data)
            
        return json.loads(prediction_status.text), prediction_status.status_code

    
    def get_model_metrics(self):
        assert self.model_isReady, "The model hasn't completed training."
        
        headers = {'Authorization': 'Bearer ' + self.session.token}


        metrics_output = requests.get(LANG_BASE_URL+'/models/'+self.modelId,
                                         headers=headers)
            
        return json.loads(metrics_output.text), metrics_output.status_code
    
    def get_learning_curve(self):
        assert self.model_isReady, "The model hasn't completed training."
        
        headers = {'Authorization': 'Bearer ' + self.session.token}


        lc_output = requests.get(LANG_BASE_URL+'/models/%s/lc'%self.modelId,
                                         headers=headers)
            
        return json.loads(lc_output.text), lc_output.status_code

    


