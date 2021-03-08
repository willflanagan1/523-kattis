"""Simple hacks for an agenda"""

from bottle import SimpleTemplate
from datetime import date, timedelta
import itertools
import re

import db
from appbase import get_url, static, user_is_admin
from app import renderMarkdown, renderTemplate, log

link = SimpleTemplate('<a href="{{url}}" target="_blank">{{text}}</a>')
db.init()

def comment_line(line, user):
   """ When parse reads a line starting with a #, create a comment line for admin users """
   if not user_is_admin(user):
      return ""

   line = renderMarkdown(line[1:])
   return f"<font color='grey'>{line}</font>"

def slide_line(line):
   """ Given an agenda line, create a slide html link for it """
   words = line[2:].strip().split(' ', 1)
   assert len(words) == 2, f"COMP550Agenda split_line should be a filename in static/slides and then a description"
   url = static("slides/" + words[0])
   line = link.render(text=f'Slides: {words[1]}', url=url)
   return line

def zoom_line(line, day, section, lecture_urls, recitation_url):
   """ Given a zoom line, create a zoom html link for it
       Note that the day (T/W/TH) and section number effect the zoom link"""
   video = line[1:].strip().replace("https://unc.zoom.us", "")
   if not video:
      if day.weekday() in [1, 3]:
         if len(lecture_urls) == 1:
            line = link.render(text=f"Join section {section} lecture on Zoom",
                               url=lecture_urls[0]) + '<br />'
         else:
            line = ''
            for index in range(len(lecture_urls)):
               line += link.render(text=f"Join section 00{index+1} lecture on Zoom",
                                   url=lecture_urls[index]) + '<br />'
      else:
         url = recitation_url
         if url:
            line = link.render(text="Join recitation on Zoom", url=url) + '\n'
   else:
      url = get_url("zoom", video=video)
      line = link.render(text="Recording", url=url)
   return line

def set_when(day, today):
   """ Given a day and today, determine when the day is.  past, present, future"""
   if day < today:
      return "past"
   if day == today:
      return "present"
   return "future"

def increment_day(day, last_day_of_classes, result, agenda_type):
   """ Given a day (T/W/TH), increment it to the next class (W/TH/T) """
   if agenda_type == 'la':
      day += timedelta(days=7)
      return day

   if day.weekday() in [1, 2]:
      # Tuesday or Wednesday
      day += timedelta(days=1)  # Tuesday or Wednesday
   else:
      day += timedelta(days=5)  # Thursday
   if day > last_day_of_classes:
      for r in result:
         log(r)
      assert day <= last_day_of_classes, f'Day {day} falls after the "\
                                         flast day of classes {last_day_of_classes}'
   return day

def checklist_line(line, day, checklist):
   """ Given a line of checklist items separated by |, the day, and the user...
       return a html checklist
       Note: If the user previously checked the item, then the checklist dictionary
       will have a key with that date and an array element with the item name
    """

   output_lines = f'<b>Checklist items due before class on {day}</b>'
   output_lines += f'<ul class="checklist" id="check-list-{day}">'
   for item in line[2:].split(' | '):
      item = item.strip()
      item_without_markdown_link = re.sub(r"\[(.+)\]\(.+\)", r"\1", item)
      if day in checklist and item_without_markdown_link in checklist[day]:
         output_lines += f'<li class="unchecked checked">{item}</li>'
      else:
         output_lines += f'<li class="unchecked">{item}</li>'
      if item_without_markdown_link == 'Practice (no points) worksheet demo.':
         print(output_lines)
   output_lines += '</ul>'
   return output_lines

def get_checklist_info(db, user, agenda_type):
   """ Get the checklist information for the user.
       Return a dictionary with the lecture date (not str) as the key with
       a value of an array of each item checked"""
   db.execute('''
      select * from checklist as T1
         where onyen=%(onyen)s
           and agenda_type = %(agenda_type)s
           and NOT EXISTS(select * from checklist as T2
                          where onyen=%(onyen)s 
                            and T1.item = T2.item
                            and T1.time < T2.time)
      ''', dict(onyen=user, agenda_type=agenda_type))
   checks = {}
   grouping = lambda x: x.lecture_date
   for lecture_date, group in itertools.groupby(db.fetchall(), grouping):
      checks[lecture_date] = [g.item for g in group if g.checked]
   return checks


# Wellness Days Tue 2/16 and Thur 3/11
@db.with_db
def parse(file_name, user, agenda_type, db):
   """Main routine called by home.tmd to parse agenda.tmd"""
   db.execute('''select section from roll where onyen=%(onyen)s''', dict(onyen=user))
   row = db.fetchone()
   section = None if row is None else row.section

   # Get Recitation zoom
   db.execute("""select url from zoom where type='recitation'""")
   row = db.fetchone()
   recitation_zoom_url = row.url if row else None

   # Get lecture zoom
   lecture_zoom_urls = []
   if section in ['001', '003']:
      db.execute("""select url from zoom where type='lecture' and section='001'""")
      lecture_zoom_urls.append(db.fetchone().url)
   if section in ['002', '003']:
      db.execute("""select url from zoom where type='lecture' and section='002'""")
      lecture_zoom_urls.append(db.fetchone().url)

   # Get checklist information
   checklist_info = get_checklist_info(db, user, agenda_type)

   if agenda_type == 'la':
      first_day_of_class = date(2021, 1, 12)
   else:
      first_day_of_class = date(2021, 1, 19)
   last_day_of_classes = date(2021, 5, 5)
   today = date.today()
   with open(file_name, "rt") as fp:
      agenda = fp.read().split("\n| ")
   day = first_day_of_class
   result = []
   for one_days_details in agenda:
      lines = one_days_details.split("\n")
      title = lines[0]
      output_lines = []
      for line in lines[1:]:
         if line.startswith("S "):
            line = slide_line(line)
         elif line.startswith("#"):
            line = comment_line(line, user)
         elif line.startswith("Z"):
            line = zoom_line(line, day, section, lecture_zoom_urls, recitation_zoom_url)
         elif line.startswith("CL"):
            line = checklist_line(line, day, checklist_info)
         output_lines.append(line)
      when = set_when(day, today)

      result.append(
         {"date": day, "title": title, "when": when,
          "body": renderMarkdown(renderTemplate("\n".join(output_lines)))})
      day = increment_day(day, last_day_of_classes, result, agenda_type)
   return result


def due(m, d):
   """ Can this be deleted? """
   return f"{m}/{d}"
