"""
Configuration inputs used to manage multiple MYPOLL deployments

See README.txt for more information
"""
import dotenv
import os

# pylint: disable=eval-used

dotenv.load_dotenv()

course_name = os.getenv('COURSE_NAME')
assert course_name, 'You must set COURSE_NAME variable in .env'

admins = os.getenv('ADMINS')
assert admins, 'You must set ADMINS variable in .env'
admins = eval(admins)
assert isinstance(admins, list), \
   f'ADMINS={admins}, but must be a string that can be eval\'s into a Python list of strings'
assert all(isinstance(admin, str) for admin in admins), \
   f'ADMINS={admins}, but must be a string that can be eval\'s into a Python list of strings'

assessment_folders = os.getenv('ASSESSMENT_FOLDERS')
assert assessment_folders, 'You must set ASSESSMENT_FOLDERS variable in .env'
assessment_folders = eval(assessment_folders)
msg = (f'ASSESSMENT_FOLDERS={assessment_folders}, but must be a string that can be '+
       'eval\'s into a Python list of strings')
assert isinstance(assessment_folders, list), msg
assert all(isinstance(assessment_folder, str) for assessment_folder in assessment_folders), msg

admin_email = os.getenv('ADMIN_EMAIL')
assert admin_email, 'You must set ADMIN_EMAIL variable in .env'
