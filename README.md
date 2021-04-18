# 523-kattis

### Restrictions
Kattis Problem Practice Tool repository runs strictly within UNC Computer Science's ada.cs.unc.edu server. Compiling and running this file system will not work elsewhere. 

### Overview
This tool is developed with python. Python serves the html and thtml files to be displayed and connects to Docker through the [Docker SDK for Python](https://docker-py.readthedocs.io/en/stable/). The [Bottle](https://bottlepy.org/docs/dev/) framework is used to listen for and handle http requests. 

### Setup
### inside 523/COMP523
  #### initialize git repo
  1. delete everything
  2. run ```git init```
  3. ```git remote add origin https://github.com/willflanagan1/523-kattis.git```
  4. ```git fetch origin```
  5. ```git checkout origin/master```

  #### create your branch
  1. ```git checkout -b "yourname"-branch```
  2. ```git branch --set-upstream origin "yourname"-branch```

  #### get changes from master
  1. ```git checkout yourbranch```
  2. ```git fetch origin```
  3. ```git pull origin master```
  4. ```git push origin yourbranch (push the changes to your remote branch)```


### Run
  ### navigate to the src folder
  1. ```make dev```
