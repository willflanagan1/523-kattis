#!/usr/bin/python3
"""
A simple program to find answers student put for Q47 adjacency
"""

from datetime import datetime, timedelta
import db
from db import with_db
import os.path as osp
import glob
from inputs import inputs
import re
import random
import markdown
from notify import notify_me
import pandas as pd
import pam
import html
import traceback
import hashlib
import json
import itertools
import sys
import csv
import codecs
import timestring
import contextlib


db.init()

connection = db.open_db()
with contextlib.closing(connection):
    cursor = connection.cursor()

    graded = pd.read_sql(
        """
        select P.id, P.onyen, max(F.score) as score
            from post P, roll R, feedback F
            where P.onyen = R.onyen and
                  P.id = F.postid and
                  P.key = 'm2-simon'
            group by P.onyen, P.id order by P.onyen""",
        connection,
    )
    postids = graded['id'].tolist()
    Q47 = pd.read_sql(
        """
        SELECT P.id, A.value
            FROM post P, answer A 
            WHERE A.field = 'Q47' AND
                  A.postid = P.id AND
                  A.postid in ({})
        """.format(','.join(str(x) for x in postids)),
        connection,
        index_col="id",
    )
    import pdb; pdb.set_trace()

    q47_dict = {}
    for value in Q47.values:
        value = value[0]
        q47_dict[value] = q47_dict.get(value,0) + 1
    print(q47_dict)
