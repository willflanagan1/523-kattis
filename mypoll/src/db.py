"""
database wrapper for my poll code
"""
import importlib
import os.path as osp
import config
from config import course_name

connection_string = ""
admins = config.admins + ['www-data']

exists = course_name != '' and osp.exists(f'./{course_name}/db.py')
assert exists, f'You must define config.py and./{course_name}/db.py createTables'

db_mod = importlib.import_module(f'{course_name}.db')
createTables = db_mod.createTables
with_db = db_mod.with_db
init = db_mod.init
open_db = db_mod.open_db
