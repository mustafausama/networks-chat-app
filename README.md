# Installation
## Installing MongoDB
You can install MongoDB using either of the two following methods.
### Option 1: Using the official installer
You can install MongoDB community edition by following the MongoDB documentation in [this link](https://www.mongodb.com/docs/manual/administration/install-community/).

### Option 2: Using docker
If you have docker installed on your system. You can run the following command and you're good to go with MongoDB  
`docker run -itd --name mongodb -p 27017:27017 mongo`

**If you modify any of the default config of mongodb (port, host, username, password, database), make sure to add the new config in the file `chat/server/db.py`**
## Insatlling the Application
### Option 1: Using poetry
1. Install the dependencies, install the project, create the venv  
`poetry install`  

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
## Unit and integration testing
You can test the application by running the command  
`python -m unittest discover -b tests`
You can see a detailed report of the tests by running the command  
`poetry run pytest -v tests/`
## Stress and performance testing
### Stress testing using bash
You can run the stress testing by simply running the command `./stress_performance.bash` after giving the file execution permissions using `chmod +x ./stress_performance.bash`.  
In order to run the stress testing, you need to have a bash terminal with the command bc.
You can install it in ubuntu by running `sudo apt-get install bc`
If you are on windows, you need to use a bash-based terminal such as **git bash**.  
If you encounter the error where pkill is not avaialable on windows, you will need to use `taskkill` instead to kill all the processes of `"chat/peer.py"`.
### Stress testing using python unittest
You can run the stress testing python script by running the file stress.py using python's unittest module.  
To do so, run the following command `python -m unittest tests/stress.py`.  
- If you have poetry, you can run the application without activating poetry shell by using:
   `poetry run python -m unittest tests/stress.py`



# Running the applications
## Activating the virtual environment
Whenever you run any script, you need to activate the virtual environment before running the script.  

- Using venv: `. venv/bin/activate`
- Using poetry: `poetry shell`  

*Note: in poetry, you can always run the application without activating the virtual environment by using `poetry run python <file_path>`*

## Running the registry
You can run the registry using the command `python chat/registry.py`
- If you have poetry, you can run the application without activating poetry shell by using:
   `poetry run python chat/registry.py`
## Running a client app
You can run a client using the command `python chat/peer.py`
- If you have poetry, you can run the application without activating poetry shell by using:
   `poetry run python chat/peer.py`
