# Einstein Intent Python Wrappers and UI

Contained herein are three python files designed to interact with the Einstein Platform Services API, specifically the Intent functionality. 

## einstein_session.py

The einstein_session.py file contains the definition of one class: the EinsteinPlatformSession class. Instances of this class are created to hold an access token, and the credentials necessary to restart an access token when they expire. 

## dataset.py

The dataset file contains definitions of two classes: Dataset and Model. A Dataset object holds information about an active session, and contains methods for uploading a .csv file to EPS, getting upload status, deleting a dataset, and getting associated models. A Model object holds information about an active session, and a connected dataset. It supports methods to train a new model, get model training status, make a prediction with a model, upload feedback data, and get model metrics/training data. 

## main.py
This is a UI app developed with tkinter to facilitate interacting with these classes. 