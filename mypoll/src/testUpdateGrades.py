#!/usr/bin/python3
"""
  A test driver of updateGrades(db, user)
"""

import db
from app import updateGrades

db.init()
connection = db.open_db()
cursor = connection.cursor()

import pdb; pdb.set_trace()
result = updateGrades(cursor, 'cdrubido')
connection.commit()
