"""
database wrapper for COMP550 mypoll code
"""
import contextlib
import getpass
import os
import sys
import psycopg2
import psycopg2.extras
import config

connection_string = ""
admins = config.admins + ['www-data']

# Note: You must manually `sudo -u postgres createuser <username> for everyone in config.admins

def log(*args):
   """Print for debugging"""
   print(*args, file=sys.stderr)


def init(host=None):
   """initialize my db setup"""
   global connection_string  # pylint: disable=global-statement

   if os.getcwd().startswith("/var/www/mypoll"):
      connection_string = "dbname='mypoll' user='www-data'"
   else:
      username = getpass.getuser()
      connection_string = f"dbname='mypoll' user='{username}'"
      if host:
         connection_string += f" host='{host}'"
   createTables()


def open_db():
   """Open the database, return the connection"""
   assert connection_string != "", 'You must run db.init() before running db.open_db'
   return psycopg2.connect(
      connection_string, cursor_factory=psycopg2.extras.NamedTupleCursor
   )

# a decorator to manage db access
def with_db(func):
   """Add an extra argument with a database connection"""

   def func_wrapper(*args, **kwargs):
      connection = open_db()
      with contextlib.closing(connection):
         cursor = connection.cursor()
         result = func(*args, **dict(kwargs, db=cursor))
         connection.commit()
         return result

   return func_wrapper


@with_db
def createTables(db=None):
   """define tables for mypoll"""
   def createTableAndGrants(db, table, create, grants):
      """ Test if table exists. If not create and do grants"""
      db.execute(f"""
            select exists(
                   select 1 from information_schema.tables
                       where table_catalog = 'mypoll' and
                             table_name='{table}')"""
                )
      row = db.fetchall()
      if not row[0].exists:
         db.execute(create)
         for grant in grants:
            try:
               db.execute(grant)
            except Exception as e:
               log(f'createTables: {grant}: {e}')
               raise

   # record their posts
   grants = ([f"""grant all privileges on table post to "{userid}" """ for userid in admins] +
             [f"""grant all privileges on table post_id_seq to "{userid}" """ for userid in admins])
   createTableAndGrants(db, "post", """
        create table if not exists post
        (id serial primary key,
         time timestamp,
         onyen text,
         key text,
         ip text)""",
                        grants)

   # pages available
   # non-null fields should be "" if not used
   grants = [f"""grant all privileges on table pages to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "pages", """
            create table if not exists pages
            (key text NOT NULL,
             onyen text NOT NULL,
             section text
                constraint valid_section
                check (section in ('000', '001', '002', '003')),
             activePages text[],
             PRIMARY KEY (key, onyen, section))""",
                        grants)

   # record their answers
   grants = ([f"""grant all privileges on table answer to "{userid}" """ for userid in admins] +
             [f"""grant all privileges on table answer_id_seq to "{userid}" """
              for userid in admins])
   createTableAndGrants(db, "answer", """
        create table if not exists answer
        (id serial primary key,
         postid serial references post(id) ON DELETE CASCADE,
         field text,
         value text)""",
                        grants)

   # record them fetching questions
   grants = ([f"""grant all privileges on table fetched to "{userid}" """ for userid in admins] +
             [f"""grant all privileges on table fetched_id_seq to "{userid}" """
              for userid in admins])
   createTableAndGrants(db, "fetched", """
        create table if not exists fetched
        (id serial primary key,
         time timestamp,
         onyen text,
         key text,
         pages text[] default '{}',
         url text,
         ip text)""",
                        grants)

   # record the 404 response codes (not found)
   grants = ([f"""grant all privileges on table notfound to "{userid}" """ for userid in admins] +
             [f"""grant all privileges on table notfound_id_seq to "{userid}" """
              for userid in admins])
   createTableAndGrants(db, "notfound", """
        create table notfound
        (id serial primary key,
         time timestamp,
         onyen text,
         url text,
         ip text)""",
                        grants)

   # record various state
   grants = [f"""grant all privileges on table state to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "state", """
        create table if not exists state
        (id serial primary key,
         key text unique,
         value text)""",
                        grants)

   # record browser events
   grants = ([f"""grant all privileges on table browser to "{userid}" """ for userid in admins] +
             [f"""grant all privileges on table browser_id_seq to "{userid}" """
              for userid in admins])
   createTableAndGrants(db, "browser", """
        create table if not exists browser
        (id serial primary key,
         time timestamp,
         onyen text,
         event text)""",
                        grants)

   # record valid submit codes
   grants = [f"""grant all privileges on table codes to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "codes", """
        create table if not exists codes
        (id serial primary key,
         time timestamp,
         code text unique)""",
                        grants)

   # associate info with posts for reporting scores and such
   grants = ([f"""grant all privileges on table feedback to "{userid}" """
              for userid in admins] +
             [f"""grant all privileges on table feedback_postid_seq to "{userid}" """
              for userid in admins])
   createTableAndGrants(db, "feedback", """
        create table if not exists feedback
        (postid serial primary key references post(id) ON DELETE CASCADE,
         score real,
         points_total real,
         msg text)""",
                        grants)

   # create a table for zoom
   grants = [f"""grant all privileges on table zoom to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "zoom", """
        create table zoom
        (url text,
         type text,
         onyen text,
         section text
            constraint valid_section
            check (section in ('000', '001', '002', '003')),
         UNIQUE (url, type, section, onyen))
         """,
                        grants)

   # create a clasroll table
   grants = [f"""grant all privileges on table roll to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "roll", """
        create table if not exists roll
        (onyen text primary key,
         pid text,
         name text,
         section text
            constraint valid_section
            check (section in ('000', '001', '002', '003')),
         imageURL text,
         zwsp text,
         rid serial unique,
         extended real default 0)""",
                        grants)

   grants = [f"""grant all privileges on table grades to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "grades", """
        create table grades
        (onyen           text primary key,
         letterGrade     text,
         total           float default 0,
         fe              float default 0,
         midterm2extra   float default 0,
         midterm2Boost   float default 0,
         midterm2        float default 0,
         midterm1extra   float default 0,
         midterm1Boost   float default 0,
         midterm1        float default 0,
         homeworks       float default 0,
         quizzes         float default 0,
         worksheets      float default 0,
         worksheet_bonus float default 0)""",
                        grants)

   grants = ([f"""grant all privileges on table worksheet_bonus to "{userid}" """
              for userid in admins] +
             [f"""grant all privileges on table worksheet_bonus_id_seq to "{userid}" """
              for userid in admins])
   createTableAndGrants(db, "worksheet_bonus", """
        create table worksheet_bonus
        (id              serial primary key,
         onyen           text,
         submitter       text,
         share_time      timestamp,
         reason          text,
         ip              text,
         points          float default 5)""",
                        grants)

   # create a table for seat assignments
   grants = [f"""grant all privileges on table seats to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "seats", """
        create table if not exists seats
        (onyen text,
         exam text,
         seat text,
         primary key(onyen, exam))""",
                        grants)

   # create a table for rubrics
   grants = [f"""grant all privileges on table rubrics to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "rubrics", """
        create table if not exists rubrics
        (key text primary key,
         time timestamp,
         questions json not NULL,
         info json not NULL)""",
                        grants)

   # create a table for questions from students
   grants = [f"""grant all privileges on table messages to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "messages", """
        create table if not exists messages
        (id serial primary key,
         time timestamp,
         onyen text,
         msg text)""",
                        grants)

   # create a table for tracking teams
   grants = [f"""grant all privileges on table teams to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "teams", """
        create table if not exists teams
        (onyen text primary key references roll(onyen) ON DELETE CASCADE,
         member_number integer,
         team_number integer)""",
                        grants)

   # create a table for lecture presentations
   grants = [f"""grant all privileges on table lectures to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "lectures", """
        create table if not exists lectures
        (title varchar(255) CONSTRAINT firstkey PRIMARY KEY,
         url text,
         absolute_fn text,
         section text
            constraint valid_section
            check (section in ('000', '001', '002', '003')),
         lecture_date date)""",
                        grants)

   # create a table for agenda checklists
   grants = ([f"""grant all privileges on table checklist to "{userid}" """ for userid in admins] +
             [f"""grant all privileges on table checklist_id_seq to "{userid}" """ for userid in admins])
   createTableAndGrants(db, "checklist", """
        create table if not exists checklist
        (id serial primary key,
         lecture_date date,
         item text,
         time timestamp,
         checked boolean default false,
         agenda_type text,
         onyen text references roll(onyen) ON DELETE CASCADE)""",
                        grants)

   grants = [f"""grant all privileges on table problems to "{userid}" """ for userid in admins]
   createTableAndGrants(db, "problems", """
        create table if not exists problems
        (id serial primary key,
         name text,
         description text,
         solution text)""",
                        grants)