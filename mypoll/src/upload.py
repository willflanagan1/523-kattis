"""Upload data to the db"""

import db
from db import with_db
import csv
import Args
import json
import timestring

args = Args.Parse(roll="", seats="", feedback="", ars="ars.csv", local=0)

db.init(host="comp580sp20.cs.unc.edu" if not args.local else None)


@with_db
def upload_roll(rollcsv, arscsv, db=None):
    """Upload the classroll to the db"""
    ars = {}
    with open(arscsv) as fp:
        for row in csv.DictReader(fp):
            ars[row["onyen"]] = float(row["extension"])

    db.execute("""delete from roll""")
    with open(rollcsv) as fp:
        for row in csv.DictReader(fp):
            db.execute(
                """
                insert into roll (onyen, pid, name, extended)
                values (%s, %s, %s, %s)""",
                [
                    row["Student ID"],
                    row["PID"],
                    row["Student Name"],
                    ars.get(row["Student ID"], 0.0),
                ],
            )


@with_db
def upload_seats(seatscsv, db=None):
    """Upload seat assignments to the db"""
    with open(seatscsv) as fp:
        for row in csv.DictReader(fp):
            db.execute(
                """
                insert into seats (onyen, exam, seat)
                values (%(onyen)s, %(exam)s, %(seat)s)
                on conflict (onyen, exam) do update
                    set seat = %(seat)s""",
                {"onyen": row["onyen"], "exam": row["exam"], "seat": row["seat"]},
            )


@with_db
def upload_feedback(fbjson, db=None):
    """Upload feedback to the db"""
    feedback = json.load(open(fbjson, "r"))
    for fb in feedback:
        # check to see if we already have it
        db.execute(
            """
            select id
            from post P
            where P.onyen = %(onyen)s and P.key = %(key)s""",
            fb,
        )
        fb["time"] = timestring.Date(fb["time"]).date
        existing = db.fetchone()
        if not existing:
            db.execute(
                """
                insert into post (time, onyen, key, ip)
                values (%(time)s, %(onyen)s, %(key)s, '')
                returning id""",
                fb,
            )
            fb["postid"] = db.fetchone()[0]
        else:
            fb["postid"] = existing[0]
        db.execute(
            """
            insert into feedback (postid, score, msg)
            values (%(postid)s, %(score)s, %(msg)s)
            on conflict (postid) do update
            set score = %(score)s, msg = %(msg)s""",
            fb,
        )


if args.roll:
    upload_roll(args.roll, args.ars)
if args.seats:
    upload_seats(args.seats)
if args.feedback:
    upload_feedback(args.feedback)
