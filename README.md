# Installation
## Installing MongoDB
You can install MongoDB using either of the two following methods.
### Option 1: Using the official installer
You can install MongoDB community edition by following the MongoDB documentation in [this link](https://www.mongodb.com/docs/manual/administration/install-community/).

### Option 2: Using docker
If you have docker installed on your system. You can run the following command and you're good to go with MongoDB  
`docker run -itd --name mongodb -p 27017:27017 mongo`
### Option 1: Using poetry
1. Install the dependencies, install the project, create the venv  
`potry install`  

2. Activate the venv in the current terminal 
`poetry shell`

### Option 2: Using venv
1. Create and activate the venv  
`python3 -m venv venv && . venv/bin/activate` or  
   `python -m venv venv && . venv/bin/activate`  

2. Install the dependencies  
`pip install --no-cache-dir -r requirements.txt`  

3. Install the project  
`pip install .`

# Testing the application
You can test the application by running the command  
`python -m unittest discover tests`

# Running the applications
Open two terminals where the current virtual environment is activated.
## Activating the venv
- Using poetry: `poetry shell`
- Using venv: `. venv/bin/activate`

## Running the registry
You can run the registry using the command `python chat/registry.py`
## Running a client app
You can run a client using the command `python chat/peer.py`
