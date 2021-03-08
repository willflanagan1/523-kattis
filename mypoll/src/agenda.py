"""Simple hacks for an agenda"""

from bottle import SimpleTemplate
from datetime import date, timedelta
import re

link = SimpleTemplate('<a href="{{url}}" target="_blank">{{text}}</a>')


# Wellness Days Tue 2/16 and Thur 3/11
def parse(afile, static=None, get_url=None, **kwargs):
    """Parse my class agenda"""
    fdoc = date(2021, 1, 19)
    ldoc = date(2021, 5, 5)
    today = date.today()
    with open(afile, "rt") as fp:
        agenda = fp.read().split("\n| ")
    day = fdoc
    result = []
    for chunk in agenda:
        lines = chunk.split("\n")
        title = lines[0]
        olines = []
        for line in lines[1:]:
            if line.startswith("S "):
                url = static("slides/" + line[2:].strip())
                line = link.render(text="Slides", url=url)
            elif line.startswith("Z"):
                video = line[1:].strip().replace("https://unc.zoom.us", "")
                if not video:
                    url = get_url("zoom", video="j/99515951731")
                    line = link.render(text="Join on Zoom", url=url)
                else:
                    url = get_url("zoom", video=video)
                    line = link.render(text="Recording", url=url)
            olines.append(line)
        if day < today:
            when = "past"
        elif day == today:
            when = "present"
        else:
            when = "future"

        result.append(
            {"date": day, "title": title, "body": "\n".join(olines), "when": when}
        )
        day += timedelta(2 if day.weekday() == 1 else 5)
    return result


def due(m, d):
    return f"{m}/{d}"

