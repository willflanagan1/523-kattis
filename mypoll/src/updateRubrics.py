#! /usr/bin/python3
"""Get the rubrics from the templates into the db"""

import bottle
from config import course_name, assessment_folders
from inputs import inputs
from appbase import static
from glob import glob
import Args
import sys
from evalInContext import evalMultiple
import os.path as osp
from datetime import datetime
import json
import math

# Add class directory to template directory
bottle.TEMPLATE_PATH.append('./md-includes/')
bottle.TEMPLATE_PATH.insert(0, f'./views/{course_name}/')
bottle.TEMPLATE_PATH = list(dict.fromkeys(bottle.TEMPLATE_PATH))

try:
   import db
except ModuleNotFoundError:
   print("no db module")
   sys.exit(0)

args = Args.Parse(force=0, local=0, verbose=0)

# Dummy functions
bottle.SimpleTemplate.defaults["get_url"] = lambda x, **y: x
bottle.SimpleTemplate.defaults["linkable_header"] = lambda y: y
bottle.SimpleTemplate.defaults["static"] = static


def json_converter(obj):
   """ JSON override for datetime objects"""
   if isinstance(obj, datetime):
      return str(obj)

def getRubrics(path, db):
   """Get the rubric from a template"""
   # pylint: disable=possibly-unused-variable

   # Set up local variables for bottle.template
   key = path.split("/")[-1].split(".")[0]
   inp = inputs(key)
   pages = []
   section = '003'
   team_number = 0
   member_number = 0
   rid = 1
   db.execute("select onyen from roll")
   onyens = [row.onyen for row in db.fetchall()]

   # The path may actually be a itmd file.  Get the path of the tmd file
   index = path.find(key)
   tmd_path = f'{path[:index]}{key}.tmd'

   # Render assuming no pages, but re-render w/ pages to get all the info
   bottle.template(tmd_path, constant_e=math.e, constant_pi=math.pi, log=math.log,
                   get_url=lambda x, **y: x, **inp.env(), **locals())
   pages = inp.info.get('pages', [])
   inp = inputs(key) # reset
   bottle.template(tmd_path, constant_e=math.e, constant_pi=math.pi, log=math.log,
                   get_url=lambda x, **y: x, **inp.env(), **locals())
   rubrics, _, _ = inp.save()
   return key, rubrics, inp.info

def updateRubrics(db, key, rubrics, info, mtime):
   """Update the db to contain the problems"""
   print(f"updateRubrics: updating rubrics for {key}")
   answers = {tag: rubrics[tag]["solution"] for tag in rubrics}
   answers["_info"] = info
   result = evalMultiple(answers, rubrics)
   # There should be some rubrics if there were any points
   assert (result != {}) or ('points_total' not in info and not info.points_limit),\
           f"{key}: No results found"
   for tag in result:
      # There should be no errors
      if 'error' in result[tag]:
         if 'tests' in result[tag]:
           for test in result[tag]['tests']:
              if ('context' in test) and ('_aux' in test['context']):
                 print('_aux:')
                 lines = test['context']['_aux'].split('\n')
                 for index in range(len(lines)):
                    print(f"{index}: {lines[index]}")
         lines = result[tag]['solution'].split('\n')
         for index in range(len(lines)):
            print(f"{index}: {lines[index]}")
      assert 'error' not in result[tag], \
             f"{key}: For question {tag} has error {result[tag]['error']}"
   result_json = json.dumps(result, default=json_converter)
   info_json = json.dumps(info, default=json_converter)
   db.execute("""
        insert into rubrics (key, time, questions, info)
               values (%s, %s, %s, %s)
               on conflict (key) do
               update set questions = %s, info = %s, time = %s""",
              [key, mtime, result_json, info_json, result_json, info_json, mtime],
              )
   db.connection.commit()


@db.with_db
def main(db=None):
   """Process questions"""
   # process all the content to get answers and codes
   paths = []
   for folder in assessment_folders:
      paths.extend(glob(f"content/{course_name}/{folder}/*.tmd"))
      paths.extend(glob(f"content/{course_name}/{folder}/*.itmd"))
   allCodes = {}
   for path in paths:
      # if args.verbose:
      #   print(f"Processing {path}")
      key, rubrics, info = getRubrics(path, db)
      codes = info.get("codes", {})
      mtime = datetime.fromtimestamp(osp.getmtime(path))
      # scream on code conflict
      for code in codes:
         if code in allCodes:
            print(code, path)
            assert code not in allCodes
         allCodes[code] = codes[code]
      # see if we need to update the db
      db.execute("""select time from rubrics where key = %s""", [key])
      row = db.fetchone()
      if row is None or row.time < mtime or args.force:
         updateRubrics(db, key, rubrics, info, mtime)

   # update the codes in the db
   for code in allCodes:
      db.execute("""insert into codes (time, code)
                      values (%(expires)s, %(code)s)
                      on conflict (code) do
                      update set time=%(expires)s""",
                 {"code": code, "expires": allCodes[code]},
                 )


if __name__ == "__main__":
   db.init()
   main()
