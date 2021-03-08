Configuring MYPOLL

- You will need to set the following variables in the mypoll/src/.env file:
  - CONFIG
     - Set to the name of the directory where course specific files are located.
       For example, set CONFIG=COMP550 so that course specific python files are
       searched in mypoll/src/COMP550 and that course specific assessments are 
       searched in mypoll/src/content/COMP550.
  - ADMINS
     - Set to a string that can be eval'd into a Python list.  The list should be the
       onyens of the Postgress database administrators
  - ASSESSMENT_FOLDERS
     - Set to a string that can be eval'd into a Python list.  The list should be the directory
       names of the different types of assessments offerred for the course.  For example
       ASSESSMENT_FOLDER = '["exams", "homeworks", "quizzes", "worksheets"]'
  - A copy of COMP550's .env file is in env.sample

If you open your browser to the {{hostname}} and get a Bad Gateway or other error, you should
examine the last few lines at the bottom of the nginx and uwsgi log files:
  - sudo vim var/log/uwsgi/app/mypoll.log
  - sudo vim var/log/nginx/error.log

After an syntax error, you more than likely will have to restart nginx and uwsgi:
  - sudo systemctl restart nginx
  - sudo systemctl restart uwsgi

Creating assessments.
  - Go to your class's content directory, for example, mypoll/src/content/COMPxxx/
  - There are lots of examples, the simpliest is in mypoll/src/content/COMPxxx/exams/fe-example.tmd
  - You can copy a more complicated example from mypoll/src/content/COMP550/exams/fe-bit.*
     - Note that the assessment must be in a directory from ASSESSMENT_FOLDERS
     - You can have include files using the itmd prefix, but the make process assumes that all
        <prefix>.itmd files apply to the associated tmd file.   Of course, you can `touch` the
        <prefix>.tmd file and then run make to force an assessment update
  - The different kinds of questions are in the mypoll/src/inputs.py file
     {{!text()}} questions take text answers, there are decimal, hexidecimal, and binary questions
     {{!checkbox}} and {{!select}} are analogous to HTML checkbox and selects.
     {{!calculator}} is a useful field to allow students to enter/try out calculations
     {{!expression}} takes a python/javascript evaluated expression with symbols defined in the contexts list.
     {{!table}} is useful for a collection of select pulldowns in the form of a table

Testing/developing assessments
  - Run `make dev` to bring up a local copy of mypoll. Note the "Serving on" message.
     For example, "Servicing on http://0.0.0.0:8081" means you have a private mypoll
     listening on port 8081
  - On your notebook/workstations start a tunnel to the browser port, for example
     `ssh -NL 8081:localhost:8081 comp550sp21.cs.unc.edu`.  Note the port addresses must match
  - Open the browser on your workstation to `localhost:8081`
  - Navigate to the assessment or see all assessments at `localhost:8081/assessments`

- Granting access to an assessments
  - Assessments are broken up into pags.  See fe-example.tmd's pages in the setInfo()
    All assessments must have at least one page!
  - Then go to /assessments and click on the pages for the assessment created
  - You need to authorize a a section or a particular onyen to an assessment.  Generally, I've put the instructor and LA/TAs in section 003 to facilitate this.
  - Feel confident that you and your LAs can have access to an assessment without students looking at it

  - Each update to <prefix>.tmd will update the browser.   But note, that if you create a new question or update the answer, you will have to run `make` to update the rubrics and see green highlights for correct answers.
