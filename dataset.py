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
    def __init__(self,einstein_session,datasetId=None):
        self.session = einstein_session #a session object is passed to the dataset class
        self.datasetId = datasetId
        self.dataset_metadata = None
        self.labels=[]

        if datasetId:
            _,_ = self.update_dataset_status()
    
    def __repr__(self):
        return '<Dataset %s, %s, %s>'%(
                self.datasetId,self.__class__.__name__,self.__sizeof__())
        
    def header_helper(self,multipart_data):
        return {'Authorization': 'Bearer ' + self.session.token,
                'Content-Type': multipart_data.content_type}

    def reset_token(self,session_time=3600):
        self.session.reset_authorization_token(session_time)

    def create_dataset(self,filepath=None,urlpath=None):
        assert not self.datasetId, """This dataset has already been populated.
To create a new dataset, make a new Dataset object"""
        assert (filepath or urlpath), "User must provide filepath or urlpath"
        if filepath:#this doesn't work yet
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

    


