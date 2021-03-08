"""
 COMP xxx Default routes
"""
import site
site.addsitedir('..')

# pylint: disable=wrong-import-position, no-member, unsupported-membership-test
# pylint: disable=import-error, import-self
from appbase import app, auth, user_is_known, get_user, user_is_admin
from app import renderTemplate, renderMarkdown
from app import not_found, not_allowed, user_in_roll
from bottle import view, request
from db import with_db
from editRubrics import editRubrics
import math
from datetime import datetime
import os.path as osp
import sys
import bottle
from config import course_name
from inputs import inputs


def log(*args):
   """Print for debugging"""
   print(*args, file=sys.stderr)


@app.route("/syllabi/<page_name>", name="syllabi")
@with_db
@view("syllabi")
def syllabi(page_name, db):
   """Render a page such as the syllabus, help, etc."""
   path = f"content/{course_name}/syllabi/{page_name}.tmd"
   if not osp.exists(path):
      not_found(db)
   title = ""
   with open(path, "rt") as fp:
      top = fp.readline()
      if top.startswith("# "):
         title = title + top[2:].strip()
   content = renderTemplate(path)
   content = renderMarkdown(content)
   return {"base": content, "title": title}


@app.route("/", name="root")
@auth(user_is_known)
@view("home")
def home():
   """ Display home page """
   return {"user": get_user(), "base": "Welcome to the home page. It is underconstruction",
           "admin": user_is_admin(get_user())}


def get_activePages(db, key, onyen, section, pages):
   """ Given a key/worksheet, return the any active pages
       for the 1) onyen, 2) section, or 3) none
   """
   if not pages:
      return pages
   activepages = []

   db.execute("""
       select onyen, section, activepages
          from pages
          where key = %s
          order by onyen
       """,
              [key],
              )
   for row in db.fetchall():
      if row.onyen == onyen:
         return row.activepages
      if (row.section == section) and (row.onyen == ''):
         activepages = row.activepages
   return activepages


# Process tmd files from assessment_folders
@app.get("/exams/<key>", name="exams")
@app.get("/homeworks/<key>", name="homeworks")
@auth(user_is_known)
@with_db
def get_questions(key, db):  # pylint:  disable=too-many-statements
   """
   Allow rendering a set of questions from a template stored in
   the questions folder.
   """
   user = get_user()
   if 'userid' in request.query:
      raise bottle.HTTPError(401, "Invalid parameter userid")
   if 'onyen' in request.query:
      raise bottle.HTTPError(401, "Invalid parameter onyen")
   if user_is_admin(user) and request.query.user:
      original_user = user
      user = request.query.user
   else:
      original_user = ''
   if not user_in_roll(user, db):
      not_allowed()

   path = f"content/{course_name}/{request.path}.tmd"
   now = datetime.now()
   if not osp.exists(path):
      log(f"mypoll{request.path}: path {path} not found")
      not_found(db)
   ip = request.remote_addr

   inp = inputs(key)

   db.execute("""
      select extended, section, rid, zwsp
      from roll 
      where onyen = %s """,
              [user])
   row = db.fetchone()
   section = row and row.section
   extended = row and row.extended
   zwsp = row and row.zwsp # pylint: disable=possibly-unused-variable
   rid = row and row.rid

   # get the answers as a json formatted string
   db.execute("""
        select info, questions from rubrics
        where key = %s""",
              [key],
              )
   row = db.fetchone()
   if row is None:
      rubrics = {}  
      pages = []
      info = {}
      print("no rubrics")
   else:
      rubrics = editRubrics(row.questions)
      info = row.info
      pages = info.get('pages', [])

   pages = get_activePages(db, key, user, section, pages)
   if (('pages' in info) and
       (pages is not None) and
       (len(pages) == 0)):
      log(f"mypoll/{request.path}: pages=({pages}) so no page shown")
      not_found(db)
   base = renderTemplate(path, user=user, key=key, pages=pages, rid=rid, section=section, constant_e=math.e, constant_pi=math.pi, log=math.log, **inp.env())
   if base.startswith("\n<pre>"):
      # renderTemplate raised an exception
      return base
   base = renderMarkdown(base)

   # Collect up info variables for psform
   # pylint: disable=possibly-unused-variable
   exam = inp.info.get("exam")
   autosave = ((request.path.find("/exams/") == 0) or
               (request.path.find("/quizzes/") == 0) or
               (request.path.find("/worksheets/") == 0))
   includeTimer = extended and exam
   due = inp.info.get("due")
   result = renderTemplate("psform", **locals())
   # hold the lock for as little time as possible
   if original_user == '':
      db.execute("""
         insert into fetched (time, onyen, key, ip, pages, url) values (%s, %s, %s, %s, %s, %s)""",
                 [now, user, key, ip, pages, request.url],
                 )
   return result
