#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 26 08:16:36 2018

@author: andrewcarroll
"""


import requests
import jwt
import time
import einstein_constants
import json
import os


class EinsteinPlatformSession:

    def __init__(self,email=None,private_key=None,cert_path=None,token=None,session_duration=3600):
        """
        Session object containing calls to the Einstein Platform Session API related to activity.

        Note:
            Among the optional args [private_key, cert_path, token], not all can be None.
            Given private_key or cert_path, a new session is initialized.
            Given a token, session uses the access token for a currently-active Einstein Platform Session.
        Args: 
            email (str): Email address of user
            private_key (str, optional): User's private key
            cert_path (str, optional): Absolute path to einstein_platform.pem certificate
            token (str, optional): Access token of currently-active session
            session_duration (int, default = 3600): Amount of time (in minutes) to keep access token active
        Attributes:
            API_PATH (str): base path for the API calls
            AUTH_PATH (str): path for authorization
            email (str): Email address of user (used to start a session with a certificate)
            private_key (str): Private key, derived from einstein_platform.pem certificate
            cert_path (str): File path for einstein_platform.pem certificate.
            expiration_time (int): Requested duration 
            session_metadata (dict): JSON data returned from the call to "start session"
        """
        self.API_PATH = einstein_constants.EINSTEIN_BASE_URL
        self.AUTH_PATH = einstein_constants.EINSTEIN_API_OAUTH
        self.email = email
        self.private_key = private_key
        self.cert_path = cert_path
        self.session_duration = session_duration
        self.expiration_time = None
        self.session_metadata = None
        timestamp=time.ctime().split(' ')
        data_folder_name='Session_%s%s_%s'%(timestamp[1],
                                            timestamp[2],
                                            '-'.join(timestamp[3].split(':')))
        os.mkdir(data_folder_name)
        self.data_dir = os.path.join(os.getcwd(),data_folder_name)
        
        if cert_path:
            self.provide_certificate()
            
        if token:
            self.token = token
        else:
            assert(self.private_key), "PrivateKey Error: There was an error in retrieving the key"
            self.reset_authorization_token()
        
    def write_record(self,name,data):
        with open(os.path.join(self.data_dir,name+'_'+str(int(time.time()))),'w') as f:
            json.dump(data,f)

    def monitor_usage(self):

        headers = {'Authorization': 'Bearer ' + self.token}
        
        response = requests.get(url=self.API_PATH+'/apiusage',
                                 headers=headers)
                                 
        self.write_record('usage',json.loads(response.text))
        
        return json.loads(response.text), response.status_code
                
    def time_remaining(self):
        return (self.expiration_time-time.time())/60
        
    def provide_certificate(self):
        with open(self.cert_path,'r') as f:
            self.private_key = f.read()
            
    def get_datasets(self):
        response = requests.get(einstein_constants.LANG_BASE_URL+'/datasets',
                     headers={'Authorization': 'Bearer ' + self.token})
        return json.loads(response.text), response.status_code
    
    def reset_authorization_token(self,session_duration=None):
        if not session_duration:
            session_duration=self.session_duration
        payload = {
                'aud': self.AUTH_PATH,
                'exp': time.time()+session_duration,
                'sub': self.email}
        if not self.private_key:
            self.provide_certificate()                
        header = {'Content-type': 'application/x-www-form-urlencoded'}
        assertion = jwt.encode(payload, self.private_key, algorithm='RS256')
        assertion = assertion.decode('utf-8')
        response = requests.post(url=self.AUTH_PATH,
                                 headers=header,
                                 data='grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion='+assertion)

        if response.status_code==200:
            self.expiration_time = payload['exp']
            self.token = response.json()['access_token']
            self.session_metadata = json.loads(response.text)
        else:
            print('Error: status code %s' %response.status_code)
        return json.loads(response.text), response.status_code