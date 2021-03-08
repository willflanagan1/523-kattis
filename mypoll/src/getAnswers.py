#! /usr/bin/python3
"""Generate the answer files from the templates"""

import bottle
from config import assessment_folders
from inputs import inputs
from glob import glob
import Args
import sys
from evalInContext import evalInContext
import os.path as osp
from datetime import datetime
import json

try:
    import db
except ModuleNotFoundError:
    print("no db module")
    sys.exit(0)

args = Args.Parse(force=0, local=0, verbose=0)

bottle.SimpleTemplate.defaults["get_url"] = lambda x: x
bottle.SimpleTemplate.defaults["static"] = lambda x: x


def getAnswers(path):
    """Save the answer from a post"""
    key = path.split("/")[-1].split(".")[0]
    inp = inputs(key)
    pages = None
    section = '003'
    team_number = 0
    member_number = 0
    rid = 1
    # Render assuming no pages, but re-render w/ pages to get all the info
    x =bottle.template(path, key=key, pages=pages, rid=rid, section=section, team_number=team_number, member_number=member_number, get_url=lambda x: x, **inp.env())
    pages = inp.info.get('pages', [])
    inp = inputs(key) # reset
    y= bottle.template(path, key=key, pages=pages, rid=rid, section=section, team_number=team_number, member_number=member_number, get_url=lambda x: x, **inp.env())
    problems, total, count = inp.save()
    return key, problems, inp.info.get("codes", {}), total, count, inp.info


"""
I think problems look like this in the database. The solutions get omitted when they
are injected into the page.

problems = {
    tag: {
        type: str,
        solution: str,
        tests: [
            {
                hash: str,
                context: {
                    var1: value,
                    var2: value,
                },
                arguments: [arg1, arg2],
            }
        ]
    }
}
"""

def json_converter(obj):
    if isinstance(obj, datetime):
       return str(obj)

def updateProblems(db, key, problems, info, mtime):
    """Update the db to contain the problems"""
    print(f"getAnswers: updating problems for {key}")
    answers = {}
    answers["_info"] = info
    for tag, problem in problems.items():
        answer = {}
        answer["correction_rate"] = problem.get("correction_rate", -1)
        answer["kind"] = problem["kind"]
        answer["solution"] = problem["solution"]
        if problem["kind"] == "expression":
            answer["tests"] = []
            for context in problem["contexts"]:
                value = evalInContext(problem["solution"], context)
                if "error" in value:
                    print(f"getAnswers: updateProblems: key: {key} value: {value}")
                    raise Exception(f"Assignment {key}: problem: {problem['solution']} error: {value['error']}")
                print("value", value)
                answer["tests"].append({"context": context, "hash": value["hash"]})
        else:
            value = evalInContext(problem["solution"], False)
            print("value", value)
            answer["tests"] = [value]
        answers[tag] = answer
    text = json.dumps(answers, default=json_converter)
    db.execute(
        """
        insert into problems (key, time, json)
               values (%s, %s, %s)
               on conflict (key) do
               update set json = %s, time = %s""",
        [key, mtime, text, text, mtime],
    )

@db.with_db
def main(db=None):
    """Process questions"""
    # process all the content to get answers and codes
    paths = []
    for folder in assessment_folders:
        paths.extend(glob(f"content/{folder}/*.tmd"))
    allCodes = {}
    for path in paths:
        if args.verbose:
            print(f"Processing {path}")
        key, problems, codes, total, count, info = getAnswers(path)
        mtime = datetime.fromtimestamp(osp.getmtime(path))
        # scream on code conflict
        for code in codes:
            if code in allCodes:
                print(code, path)
                assert code not in allCodes
            allCodes[code] = codes[code]
        if total > 0 and args.verbose:
            print(f"{key}: total {total}/count {count}")
        # see if we need to update the db
        db.execute("""select time from problems where key = %s""", [key])
        row = db.fetchone()
        if row is None or row.time < mtime or args.force:
            updateProblems(db, key, problems, info, mtime)

    # update the codes in the db
    for code in allCodes:
        db.execute(
            """insert into codes (time, code)
                      values (%(expires)s, %(code)s)
                      on conflict (code) do
                      update set time=%(expires)s""",
            {"code": code, "expires": allCodes[code]},
        )


if __name__ == "__main__":
    db.init(host=None if not args.local else None)
    
    main()

    # Ensure bundle.js is a merge of all other js
    files = []
    files.extend( glob("*.js") )
    files.extend( glob("static/js/bundle.js") )
    files.sort(key=osp.getmtime)
    assert files[-1] == "static/js/bundle.js", "Must run npm run watch"
