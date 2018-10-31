#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 26 08:16:36 2018

@author: andrewcarroll
"""

import tkinter as tk

import matplotlib.pyplot as plt

# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib.figure import Figure

import threading
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory
from time import ctime,sleep,time
import json
import os
import einstein_session
import dataset

import seaborn as sns

LABEL_WIDTH = 15

class EPAWindow(tk.Tk):
    
    def __init__(self,parent):
        tk.Tk.__init__(self,parent)
        self.parent = parent
        self.session = None
        self.dataset = None
        self.available_datasets = ['Not Available', '']
        self.available_models = ['Not Available', '']
        self.call_history = ''
        self.initialize()


    def initialize(self):
        
        self.nb = ttk.Notebook(self)
        
        """This block constructs the Session tab"""
        session_page = ttk.Frame(self.nb)

        (self.email_field,
            self.cert_button,
            self.cert_var,
            self.time_field,
            self.start_session_with_certificate_button,
            self.record_button,
            self.record_var) = make_session_frame(session_page)

        self.cert_button.configure(
                command=self.get_cert_name
        )

        self.start_session_with_certificate_button.configure(
                command=lambda: self.start_session(email=self.email_field.get(),
                                                cert_path=self.cert_var.get(),
                                                session_duration=self.time_field.get()))

        self.record_button.configure(
            command=self.get_record_directory
        )

        self.time_remaining_label = tk.Label(session_page,
                                   text='Time remaining will update when session begins')

        self.time_remaining_label.pack(side='top',fill='x',padx=5,pady=5)
        self.session_feedback = tk.Text(session_page,height=10,width=30)
        self.session_feedback.pack(side='top',fill='x',padx=10,pady=10)
        
        self.usage_status_button, _ = makebuttonlabelrow(session_page,
                                                         'Check Usage Data')
        self.usage_status_button.configure(command=self.get_usage_status)
    
        self.usage_feedback = tk.Text(session_page,height=10,width=30)
        self.usage_feedback.pack(side='top',fill='x',padx=10,pady=10)
        
        self.get_all_datasets_button, self.get_all_datasets_label = \
                makebuttonlabelrow(session_page,
                                'Get All Datasets')
        
        self.get_all_datasets_button.configure(
                command=self.get_all_datasets)
        
        self.associated_datasets_feedback = tk.Text(session_page,
                                                    height=10,width=30)
        self.associated_datasets_feedback.pack(side='top', fill='x',
                                                padx=10, pady=10)
        
        self.nb.add(session_page,text='Session')
        
        
        """This block constructs the Dataset tab""" 
        
        dataset_page = ttk.Frame(self.nb)
        
        dataset_id_row = tk.Frame(dataset_page)
        self.dataset_lab = tk.Label(dataset_id_row, width=LABEL_WIDTH, text='Dataset ID', anchor='w')
        self.dataset_var = tk.StringVar(dataset_id_row)
        self.dataset_var.set(self.available_datasets[0])
        self.dataset_menu = tk.OptionMenu(dataset_id_row,
                                            self.dataset_var,
                                            *self.available_datasets)
        self.dataset_from_id_button = tk.Button(dataset_id_row, text='Link Dataset', anchor='w')

        self.dataset_lab.pack(side='left')
        self.dataset_menu.pack(side='left',fill='x',expand='yes')
        self.dataset_from_id_button.pack(side='right')
        dataset_id_row.pack(side='top',fill='x',expand='yes')

        self.dataset_from_id_button.configure(
                command=lambda: self.link_dataset(self.dataset_var.get())
                )
        
        self.dataset_url_field, self.upload_dataset_from_url_button = \
            makebuttonrow(dataset_page,
                        'Dataset URL',
                        'Upload dataset from URL')

        self.upload_dataset_from_url_button.configure(
                command=lambda: self.dataset_from_url(
                    self.dataset_url_field.get())
                    )

        
        self.dataset_file_field, self.upload_dataset_from_file_button = \
                makebuttonrow(dataset_page,
                            'Dataset Filepath',
                            'Upload dataset from file')

        self.upload_dataset_from_file_button.configure(
                command=self.dataset_from_file
                )

        self.dataset_status_button, self.dataset_status_label = \
                makebuttonlabelrow(dataset_page, 'Check Dataset Status')
        
        self.dataset_status_button.configure(
                command=self.update_dataset)
        
        self.dataset_delete_button, self.dataset_delete_label = \
                makebuttonlabelrow(dataset_page, 'Delete Dataset')
        
        self.dataset_delete_button.configure(
                command=self.delete_dataset
                )
        
        self.dataset_delete_status_button, self.dataset_delete_status_label = \
                makebuttonlabelrow(dataset_page, 'Dataset Deletion Status')

        self.dataset_delete_status_button.configure(
                command=self.delete_dataset_status)
         
        self.dataset_feedback = tk.Text(dataset_page, height=10, width=30)
        self.dataset_feedback.pack(side='top', fill='x', padx=10, pady=10)
        
        self.get_dataset_models_button, self.get_all_models_label = \
                makebuttonlabelrow(dataset_page, 'Get All Associated Models')
        self.get_dataset_models_button.configure(
                command=self.get_associated_models)
        
        self.associated_models_feedback = tk.Text(dataset_page, height=10, width=30)
        self.associated_models_feedback.pack(side='top', fill='x', padx=10, pady=10)

        self.nb.add(dataset_page,text='Dataset')
        
        
        """This creates the model tab""" 
        
        self.model_page = ttk.Frame(self.nb)

        model_id_row = tk.Frame(self.model_page)
        self.model_lab = tk.Label(model_id_row, width=LABEL_WIDTH, text='Model ID', anchor='w')
        self.model_var = tk.StringVar(model_id_row)
        self.model_var.set(self.available_models[0])
        self.model_menu = tk.OptionMenu(model_id_row,
                                            self.model_var,
                                            *self.available_models)
        self.model_from_id_button = tk.Button(model_id_row, text='Link Model', anchor='w')

        self.model_lab.pack(side='left')
        self.model_menu.pack(side='left',fill='x',expand='yes')
        self.model_from_id_button.pack(side='right')
        model_id_row.pack(side='top',fill='x',expand='yes')
    
        self.model_from_id_button.configure(
                command=lambda: self.link_model(self.model_var.get()))
        
        self.train_new_model_button = tk.Button(self.model_page,
                                                height=3,
                                                text='Train New Model',
                                                command=self.train_new_model)
        self.train_new_model_button.pack(side='top',
                                         fill='x',
                                         expand='yes',
                                         padx=20,
                                         pady=20)
        
        self.model_status_button, self.model_status_label = \
                makebuttonlabelrow(self.model_page,
                                'Check Model Status')
        
        self.model_status_button.configure(
                command=self.check_model_status)
        
        
        
        self.query_field, self.query_button = makebuttonrow(self.model_page,
                                                            'Prediction Query',
                                                            'Predict Class')
        
        self.query_button.configure(
                command=lambda: self.predict(self.query_field.get())
                )
        

        self.feedback_row = tk.Frame(self.model_page)
        
        self.feedback_fields = tk.Frame(self.feedback_row)
        
        self.doc_row = tk.Frame(self.feedback_fields)
        self.feedback_lab = tk.Label(self.doc_row,
                                     width=LABEL_WIDTH,
                                     text='Feedback Example',
                                     anchor='w')

        self.feedback_doc = tk.StringVar()
        self.feedback_ent = tk.Entry(self.doc_row,
                                     textvariable=self.feedback_doc)
        self.feedback_lab.pack(side='left')
        self.feedback_ent.pack(side='right')
        self.doc_row.pack(side='top')
        
        self.class_row = tk.Frame(self.feedback_fields)
        self.feedback_class = tk.StringVar()
        self.feedback_class_lab = tk.Label(self.class_row,
                                           width=LABEL_WIDTH,
                                           text='Feedback Class',anchor='w')
        self.feedback_class_ent = tk.Entry(self.class_row,
                                           textvariable=self.feedback_class)
        self.feedback_class_lab.pack(side='left')
        self.feedback_class_ent.pack(side='right')
        self.class_row.pack(side='top')
     
        self.feedback_fields.pack(side='left')
        
        self.feedback_button = tk.Button(self.feedback_row,
                text='Submit Feedback',
                command=lambda: self.submit_feedback(self.feedback_doc.get(),
                                                    self.feedback_class.get()))
        
        self.feedback_button.pack(side='right')
        self.feedback_row.pack(side='top',
                                fill='x',
                                expand='yes',
                                padx=10,
                                pady=10)
        
        self.feedback_file_field, self.feedback_file_button = \
                makebuttonrow(self.model_page,
                            'Feedback File',
                            'Submit feedback from file')

        self.feedback_file_button.configure(
                command = lambda: self.upload_thread
                )

        self.retrain_model_button = tk.Button(self.model_page,
                                              text='Retrain Model',
                                              command=self.retrain_model,
                                              height=3)
        self.retrain_model_button.pack(side='top',
                                       fill='x',
                                       expand='yes',
                                       padx=20,
                                       pady=20)
        
        self.model_feedback_frame = tk.Frame(self.model_page)
        self.model_feedback_field = tk.Label(self.model_feedback_frame,
                                             anchor='w',
                                             text='Updated at: ')
        self.model_feedback_field.pack(side='top',
                                       fill='x',
                                       expand='yes',
                                       padx=10,
                                       pady=10)
        self.model_feedback = tk.Text(self.model_feedback_frame,
                                      height=10,
                                      width=30)
        self.model_feedback.pack(side='top',fill='x',padx=10,pady=10)
        self.model_feedback_frame.pack(side='top',fill='x',padx=10,pady=10)
        
        self.nb.add(self.model_page,text='Model')
        self.nb.pack(expand=1, fill="both")
        
        """This creates the metrics tab""" 
        
        self.metrics_page = ttk.Frame(self.nb)
        
        
        self.get_model_metrics_button, self.get_model_metrics_label = \
                makebuttonlabelrow(self.metrics_page,
                                    'Get Model Metrics')

        self.get_model_metrics_button.configure(
                command=self.get_model_metrics
                )
        
        
        self.get_model_lc_button, self.get_model_lc_label =\
                makebuttonlabelrow(self.metrics_page,
                                    'Get Learning Curve')

        self.get_model_lc_button.configure(
                command=self.get_model_lc)

        self.nb.add(self.metrics_page,text='Metrics')
        self.nb.pack(expand=1, fill="both")
    
        self.nb.pack(expand=1, fill="both")
        

    def get_cert_name(self):
        cert_file = askopenfilename(title="Choose platform certificate")
        self.cert_var.set(cert_file)

    def get_record_directory(self):
        self.record_dir = askdirectory(title="Choose a directory for record storage")
        self.record_var.set(self.record_dir)

    def get_usage_status(self):
        msg, status = self.session.monitor_usage()
        self.write_record('Usage', 'session', msg)
        add_feedback(self.usage_feedback, msg, 'Usage\n')

    def get_associated_models(self):
        msg, status = self.dataset.get_associated_models()
        self.write_record('Assoc_models', 'dataset', msg)

        try:
            self.available_models = msg['data']
            self.model_var.set('Choose an available model')
            self.model_menu['menu'].delete(0, 'end')
            for model in self.available_models:
                self.model_menu['menu'].add_command(label='%s: %s'%(model['name'][:20],model['modelId']),
                                                    command=tk._setit(self.model_var, model['modelId']))
        except:
            pass
        try:
            add_feedback(self.associated_models_feedback,msg,'Models\n')
        except:
            messagebox.showinfo(title="Associated Models", message=status)
    
    def delete_dataset(self):
        if messagebox.askyesno("Dataset Delete Warning",
                           "This will PERMANENTLY delete model %s from SF Einstein. This cannot be undone. Are you sure?"%self.dataset.datasetId):
            print('Deleting dataset...')
            msg, _ = self.dataset.delete_self()
            messagebox.showinfo(title='Deletion Status', message=msg)
            
    def delete_dataset_status(self):
        msg, _ = self.dataset.update_deletion_status()
        messagebox.showinfo(title='Deletion Status', message=msg)
            
    def update_dataset(self):
        msg,_ = self.dataset.update_dataset_status()
        self.check_dataset_status()
        messagebox.showinfo(title="Dataset Update", message=msg)
        
    def update_model(self):
        msg,_ = self.model.update_model_status()
        self.check_model_status()
        messagebox.showinfo(title="Update Model Information", message=msg)
    
    def get_model_metrics(self):
        msg, status = self.model.get_model_metrics()
        self.write_record('Metrics', 'model', msg)
        pr_data = msg['metricsData']['precisionRecallCurve']
        plt.scatter(pr_data['precision'],pr_data['recall'])
        plt.xlim((-0.05,1.05))
        plt.ylim((-0.05,1.05))
        plt.xlabel('Precision')
        plt.ylabel('Recall')
        plt.title('Precision-recall for %s'%self.model.modelId)
        timestamp = str(time()).split('.')[0]
        plt.savefig(os.path.join(self.record_dir,'PR_%s_%s'%(self.model.modelId,timestamp[-4:])))
        self.get_model_metrics_label.configure(text='Updated at %s'%ctime())

        
    def get_model_lc(self):
        msg, status = self.model.get_learning_curve()
        self.write_record('LC', 'model', msg)
        self.get_model_lc_label.configure(text='Updated at %s'%ctime())
  
    def check_model_status(self):
        try:
            if self.model.model_isReady:
                self.model_status_label.configure(text='The model is ready.',
                                                  background='green2')
            else:
                self.model_status_label.configure(text='The model is not ready.',
                                                  background='coral')
        except:
            self.model_status_label.configure(text='The model could not be found', 
                                              background='blue')
            messagebox.showinfo(title="Model Information", 
                                message="Is there a model yet?")
        try:
            add_feedback(self.model_feedback,
                         self.model.model_metadata,
                         'Model Feedback')
            self.model_feedback_field.configure(
                    text='Responses to calls, updated at: %s'%ctime(time()))
            self.write_record('status', 'model', self.model.model_metadata)
        except:
            pass
        
    def check_dataset_status(self):
        try:
            if self.dataset.dataset_isReady:
                self.dataset_status_label.configure(text='The dataset is ready',
                                                    background='green2')
            else:
                self.dataset_status_label.configure(text='The dataset is not ready.', 
                                                   background='coral')
        except:
            pass
        messagebox.showinfo(title="Dataset Update",
                            message=str(self.dataset.dataset_metadata)+str(self.dataset.labels))
        try:
            add_feedback(self.dataset_feedback,
                         self.dataset.dataset_metadata,
                         'Dataset Feedback')
            
            self.write_record('status', 'dataset', self.dataset.dataset_metadata)
        except:
            print('Could not write dataset record')

    def link_dataset(self,idn):
        self.dataset = dataset.Dataset(self.session,datasetId=idn)
        self.check_dataset_status()
        self.get_associated_models()

    def link_model(self,modelId):
        self.model = dataset.Model(dataset=self.dataset,modelId=modelId)
        self.check_model_status()
        
    def train_new_model(self):
        if messagebox.askyesno("New Model Verification",
                               "This will detatch any other models from this instance."
                               + "Do you wish to train a new model?"):
            self.model = dataset.Model(self.dataset)
            msg, _ = self.model.train_model()
            self.write_record('train', 'model', msg)
            messagebox.showinfo(title="Model Information", message=str(msg))
            self.model_id_field.set(self.model.modelId)
            self.check_model_status()
        
    def retrain_model(self):
        if messagebox.askyesno("Retrain Verification",
                               "This will retrain the existing model. Would you like to continue?"):
            msg, _ = self.model.retrain_model()
            self.write_record('retrain', 'model', msg)
            messagebox.showinfo(title="Initiating Retrain",message=str(msg))
        self.check_model_status()
       
    def predict(self,query):
        msg, status = self.model.predict(query)
        self.write_record('prediction', 'model', msg)
        try: 
            probs_string = ''
            probs = msg['probabilities']
            for prob in probs:
                probs_string+='\nLabel: %s with probability %0.2f'%(prob['label'],100*prob['probability'])
            messagebox.showinfo(title="Predicted class of '%s'"%query, message=probs_string)
        except:
            messagebox.showinfo(title="Error", message="Error! %s\n%s"%(status,msg))
    
    def get_all_datasets(self):
        msg, _ = self.session.get_datasets()
        try:
            self.available_datasets = msg['data']
            self.dataset_var.set('Choose an available dataset')
            self.dataset_menu['menu'].delete(0, 'end')
            for dataset in self.available_datasets:
                self.dataset_menu['menu'].add_command(label='%s: %s'%(dataset['name'][:20],dataset['id']),
                                                        command=tk._setit(self.dataset_var, dataset['id']))
        except:
            pass
        self.write_record('list_all', 'session', msg)
        add_feedback(self.associated_datasets_feedback,
                     msg,
                     title='List of datasets') 
        
    def dataset_from_url(self,url):
        self.dataset = dataset.Dataset(self.session)
        msg, _ = self.dataset.create_dataset(urlpath=url)
        self.write_record('upload_url', 'dataset', msg)
        self.check_dataset_status()
        self.dataset_id_field.set(self.dataset.datasetId)
    
    def dataset_from_file(self):
        dataset_filepath = askopenfilename(title="Choose dataset file")
        if dataset_filepath:
            self.dataset = dataset.Dataset(self.session)
            self.dataset_file_field.set(dataset_filepath)
            msg, _ = self.dataset.create_dataset(filepath=dataset_filepath)
            self.write_record('upload_file', 'dataset', msg)
            self.check_dataset_status()
            self.dataset_var.set(self.dataset.datasetId)
           
    def submit_feedback(self,document,expectedLabel):
        assert(self.dataset.dataset_isReady), "It appears the dataset is not yet ready."
        assert(self.model.model_isReady), "It appears the model is not yet ready."
        msg, _ = self.model.submit_feedback(document,expectedLabel)
        self.write_record('feedback_submission', 'model', msg)
        messagebox.showinfo(title="Feedback Status",
                            message="The line '%s' was submitted with intended label '%s\n"%(document,expectedLabel)+str(msg))

    def upload_feedback(self,limit=1000):
        assert(self.model.model_isReady), "It appears the model is not yet ready."
        errors=0
        feedback_filepath=askopenfilename(title="Choose comma-separated-values feedback file")
        self.feedback_file_field.set(feedback_filepath)
        with open(filepath,'r') as f:
            t = time()
            records = f.read()
            records = records.split('\n')
            N=len(records)
            for i, record in enumerate(records):
                splitted = record.split(',')
                label = splitted[-1]
                document = ' '.join(splitted[:-1])
                if i%5==0:
                    print('%s records of %s uploaded with average load time %0.3f'%(i,N,((time()-t)/5)))
                    t=time()
                if i>limit:
                    break
                if label in self.dataset.labels:
                    try:
                        tries = 2
                        while (tries < 10) and (errors<20):
                            msg,status = self.model.submit_feedback(document,label)
                            if status==200:
                                tries = 10
                            else:
                                tries+=1
                                print('Tried %s times with this document.'%tries)
                                sleep(tries)
                                errors+=1
                        sleep(2)
                    except ConnectionError:
                        print("Connection error, will attempt to reconnect" +\
                                "in 2 minutes. Will attempt a total of %s more times"""%(5-errors))
                        sleep(120)
                        errors+=1
                        if errors>5:
                            break

                else:
                    print('Expected Label of %s inconsistent with model labels %s'%(label,self.dataset.labels))
        messagebox.showinfo(title="Upload Status", message='Upload Complete')
        msg, status = self.dataset.update_dataset_status()
        self.write_record('feedback_update', 'dataset', msg)

    def start_session(self,email=None,private_key=None,cert_path=None,token=None,session_duration=None):
        if session_duration:
            session_duration = int(session_duration)*3600
        else:
            session_duration=3600
        if self.session:
            self.session.reset_authorization_token(session_duration)
        else:
            self.session = (einstein_session
                            .EinsteinPlatformSession(email=email,
                                                    cert_path=cert_path,
                                                    token=token,
                                                    session_duration=session_duration))
        try:
            add_feedback(self.session_feedback,
                        self.session.session_metadata,
                        'Session Feedback')
            self.get_all_datasets()
        except: pass
        self.time_remaining_label.configure(
            text='You have until %s with this token' %ctime(self.session.expiration_time)
            )

    def write_record(self, call_type, object_type, message):
        if self.record_dir:
            if object_type == 'session':
                object_id = self.session.token[-10:]
            elif object_type == 'dataset':
                object_id = self.dataset.datasetId
            elif object_type == 'model':
                object_id = self.model.modelId
            else:
                object_id = ''
            timestamp = str(time()).split('.')
            with open(os.path.join(self.record_dir,'%s_%s_%s_%s'%(object_type.upper(), call_type,object_id,timestamp[0][-4:]+timestamp[1][0])),'w+') as f:
                json.dump(message,f)
        
    def upload_thread(self):
        self.thread = threading.Thread(target = self.upload_feedback)
        self.thread.start()
        
def makebuttonrow(root,field_prompt,button_text):
    row= tk.Frame(root)
    lab = tk.Label(row, width=LABEL_WIDTH, text=field_prompt, anchor='w')
    entry_var = tk.StringVar()
    ent = tk.Entry(row,textvariable=entry_var)

    row.pack(side='top', fill='x',padx=10,pady=10)
    lab.pack(side='left')
    ent.pack(side='left',expand='yes', fill='x')
    but=None
    if button_text:
        but = tk.Button(row,text=button_text)
        but.pack(side='right')
    return entry_var, but

def make_session_frame(root):
    frame = tk.Frame(root)

    record_row = tk.Frame(frame)
    record_row_lab = tk.Label(record_row, width=LABEL_WIDTH, text='Record Folder', anchor='w')
    record_var = tk.StringVar()
    record_ent = tk.Entry(record_row, textvariable=record_var)
    record_but = tk.Button(record_row, text='Select Directory', anchor='w')

    record_row_lab.pack(side='left')
    record_ent.pack(side='left', expand='yes', fill='x')
    record_but.pack(side='left')
    record_row.pack(side='top', fill='x', expand='yes')

    cert_row = tk.Frame(frame)
    cert_row_lab = tk.Label(cert_row, width=LABEL_WIDTH, text='Certificate Path', anchor='w')
    cert_var = tk.StringVar()
    cert_ent = tk.Entry(cert_row, textvariable=cert_var)
    cert_but = tk.Button(cert_row, text='File Explorer', anchor='w')

    cert_row_lab.pack(side='left')
    cert_ent.pack(side='left', expand='yes', fill='x')
    cert_but.pack(side='left')
    cert_row.pack(side='top', fill='x', expand='yes')

    email_row = tk.Frame(frame)
    email_lab = tk.Label(email_row, width=LABEL_WIDTH, text='Email Address', anchor='w')
    email_var = tk.StringVar()
    email_ent = tk.Entry(email_row, textvariable=email_var)

    email_lab.pack(side='left')
    email_ent.pack(side='left', expand='yes', fill='x')
    email_row.pack(side='top', fill='x', expand='yes')

    time_row = tk.Frame(frame)
    time_lab = tk.Label(time_row, width=LABEL_WIDTH, text='Time (in hours)', anchor='w')
    time_var = tk.StringVar()
    time_var.set('1')
    time_ent = tk.Entry(time_row,textvariable=time_var)
    session_but = tk.Button(time_row, text='Start session')
    time_row.pack(side='left', fill='x', expand='yes')

    time_lab.pack(side='left')
    time_ent.pack(side='left',fill='x')
    session_but.pack(side='right')
    

    frame.pack(side='top', fill='x', padx=10, pady=10)

    return (email_var, cert_but, cert_var,
            time_var, session_but, record_but,
            record_var)

def makebuttonlabelrow(root,button_text):
    row = tk.Frame(root)
    lab = tk.Label(row, text='', width=LABEL_WIDTH, anchor='w')
    but = tk.Button(row,text=button_text, anchor='w')

    row.pack(side='top', fill='x',padx=10,pady=10)    
    lab.pack(side='left', fill='x',expand='yes')
    but.pack(side='right')  

    return but, lab

def add_feedback(field,json_dict,title=''):
    output_string='%s\n--------\n%s\n'%(title,str(json_dict))
    field.insert(1.0,output_string)


if __name__ == "__main__":
    app = EPAWindow(None)
    app.title('Einstein Intent')
    app.mainloop()
   


