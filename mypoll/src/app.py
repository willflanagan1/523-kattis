#!/usr/bin/python3
"""
A simple system for polls, problem sets, and quizes.
"""

from datetime import datetime, timedelta
import timestring
import db
import glob
from email.mime.text import MIMEText
import smtplib
import os
import os.path as osp

import bottle
from bottle import request, template, view, redirect, static_file
from appbase import app, serve, secrets, get_url
from appbase import application  # pylint: disable=unused-import
from appbase import auth, get_user, user_is_known, user_is_admin
from appbase import allow_json

from config import course_name, assessment_folders, admins, admin_email

# Add class directory to template directory
bottle.TEMPLATE_PATH.append('./md-includes/')
bottle.TEMPLATE_PATH.insert(0, f'./views/{course_name}/')
bottle.TEMPLATE_PATH = list(dict.fromkeys(bottle.TEMPLATE_PATH))
from db import with_db
from inputs import inputs
import re
import random
import markdown
from notify import notify_me
import html
import traceback
import hashlib
import json
import itertools
import importlib
import sys
import csv
import codecs
import dotenv


dotenv.load_dotenv()
dotenv_values = dotenv.dotenv_values()

def log(*args):
   """Print for debugging"""
   print(*args, file=sys.stderr)


db.init()

# md = markdown.Markdown(tab_length=8, extensions=['markdown.extensions.tables', ])
md = markdown.Markdown(tab_length=8, extensions=['extra'])
# md = markdown.Markdown(tab_length=8, extensions=['fenced_code'])
# markdown.markdown('table', extensions=['markdown.extensions.tables'])


def user_in_roll(user, db):
   ''' Return boolean if user is in the class roll '''
   db.execute('''
       select exists (select onyen 
                      from roll 
                      where onyen = %s and section in ('001', '002', '003'))''',
              [user],
              )
   return db.fetchone().exists

def renderMarkdown(base):
   """ Handle Markdown processing by changing dollar sign to spans, etc """
   md.reset()
   # Allow dollar sign and \( for mathjax markdown
   base = re.sub(r"\\\((.*?)\\\)", r'<span class="math">\1</span>', base)
   base = re.sub(r"\$(.*?)\$", r'<span class="math">\1</span>', base)
   base = md.convert(base)
   return base


def renderTemplate(name, **kwargs):
   """Render a template being careful to handle errors"""
   try:
      result = template(name, dotenv_values, **kwargs)
      return result
   except:
      user = get_user()
      if user_is_admin(user):
         result = html.escape(traceback.format_exc())
         result = f"\n<pre>{result}</pre>"
         return result
      raise


def makeToken(user):
   """Get an api token for a user"""
   return hashlib.sha224((user + secrets["api"] + user).encode("utf-8")).hexdigest()


def get_text(fname):
   """Return the first line for identification"""
   line = 'No title'
   with open(fname, "r") as f:
      for line in f:
         if re.match(r'^# .*$', line):
            break
         line = re.sub("^# ", "", line)
   return line


@app.get("/notes", name="notes")
@auth(user_is_admin)
@view("notes")
@allow_json
def notes():
   """Generate a notes data entry screen"""
   return


@app.get("/upload", name="upload")
@auth(user_is_admin)
@view("upload")
def upload():
   """Display form for uploading data"""
   return {}


@app.post("/upload-feedback")
@auth(user_is_admin)
@with_db
@view("upload")
def upload_feedback(db):
   """Upload feedback"""
   upload = request.files.get("feedback")
   reader = csv.DictReader(codecs.iterdecode(upload.file, "utf-8"))
   for fb in reader:
      # check to see if we already have it
      db.execute("""
            select id
            from post P
            where P.onyen = %(onyen)s and P.key = %(key)s""",
                 fb,
                 )
      fb["time"] = timestring.Date(fb["time"]).date
      existing = db.fetchone()
      if not existing:
         db.execute("""
                insert into post (time, onyen, key, ip)
                values (%(time)s, %(onyen)s, %(key)s, '')
                returning id""",
                    fb)
         fb["postid"] = db.fetchone()[0]
      else:
         fb["postid"] = existing[0]
      db.execute("""
            insert into feedback (postid, score, msg)
            values (%(postid)s, %(score)s, %(msg)s)
            on conflict (postid) do update
            set score = %(score)s, msg = %(msg)s""",
                 fb)
   return {}


@app.post("/upload-teams")
@auth(user_is_admin)
@with_db
@view("upload")
def upload_teams(db):
   """Upload teams"""
   upload = request.files.get("teams")
   reader = csv.DictReader(codecs.iterdecode(upload.file, "utf-8"))
   db.execute("""delete from teams""")
   for row in reader:
      db.execute("""
            insert into teams (onyen, number)
            values (%s, %s)""",
                 [row["Onyen"], row["Team #"]],
                 )

   return {}

@app.post("/upload-solution")
@auth(user_is_admin)
@with_db
@view("upload")
def upload_solution(db):
   """Upload solution"""
   upload = request.files.get("solution")
   name, ext = os.path.splitext(upload.filename)
   if ext not in ('.py', '.java'):
        return "File extension not allowed."

   save_path = "kattis-solutions"
   file_path = "{path}/{file}".format(path=save_path, file=upload.filename)
   upload.save(file_path)
   os.system("kattis kattis-solutions/" + upload.filename)
   if os.path.exists(file_path):
      os.remove(file_path)
   return {}


@app.get("/api/token", name="token")
@auth(user_is_admin)
@view("token")
def get_token():
   """Give the token to an admin"""
   user = get_user()
   return {"user": user, "token": makeToken(user)}


@with_db
def get_team(db):
     ''' Get the user's team number '''
     user = get_user()
     db.execute("""
          select R.onyen, R.name
          from roll R, teams T
          where T.onyen = R.onyen and
                T.number = (select number from teams where onyen = %s)
          order by R.name
          """,
                [user],
                )
     result = db.fetchall()
     return result

bottle.SimpleTemplate.defaults["get_team"] = get_team


def check_bad_parm():
     """ Check for things that bite me all the time"""
     if 'userid' in request.query:
        raise bottle.HTTPError(401, "Invalid parameter userid... user")
     if 'onyen' in request.query:
        raise bottle.HTTPError(401, "Invalid parameter onyen... user")


def linkable_header(title):
   ''' given a title, create a linkable header '''
   name = title.lower().replace(' ', '-')
   return f'<a href="#{name}" name="{name}"><u>{title}</u></a>'

bottle.SimpleTemplate.defaults["linkable_header"] = linkable_header


def not_found(db):
   """Return a custom 404 message"""
   user = get_user()
   now = datetime.now()
   ip = request.remote_addr
   url = request.url
   db.execute("""insert into notfound (time, onyen, ip, url) values (%s, %s, %s, %s)""",
              [now, user, ip, url])
   db.connection.commit()  # Need to commit as 404 is a bad return code
   msg = f"""Sorry {user}: File not found. Every access is recorded."""
   raise bottle.HTTPError(404, msg)


def not_allowed():
   """Return a custom 405 message"""
   user = get_user()
   msg = f"""Sorry {user}: It appears you are not registered for this class."""
   raise bottle.HTTPError(405, msg)




exists = course_name != '' and osp.exists(f'./{course_name}/app.py')
if exists:
   app_mod = importlib.import_module(f'{course_name}.app')
   names = [x for x in app_mod.__dict__ if not x.startswith("_")]
   globals().update({k: getattr(app_mod, k) for k in names})


if __name__ == "__main__":
   Testing = True
   serve()
