#!/usr/bin/python3
""" Read a Connect Carolina PDF of student pictures with the corresponding
    Sakai CSV to create a classroll.csv file of students, pids, names and pictures
    that would be read by ReadClassRollIntoSQL.py
"""

# Need to pip3 install pymupdf

import Args
import fitz
import pandas
import re
import dotenv

dotenv.load_dotenv()
dotenv_values = dotenv.dotenv_values()

args = Args.Parse(pdf=str,
                  csv=str,
                  verbose=0,
                 )

# doc = fitz.open("COMP550.001.20200704.pdf")
doc = fitz.open(args.pdf)

roll = pandas.read_csv(args.csv)
roll = roll[['Student ID', 'PID', 'Name', 'Section', 'imageURL']]
roll.columns = ['onyen', 'pid', 'name', 'section', 'imageURL']
roll = roll.fillna('')

# Just read the PDF to get the PID and the image which are
# in a one-to-one match order pids / image
student_pids = []
student_image_fns = []
for i in range(len(doc)):
   text = doc.getPageText(i).split('\n')

   text_counter = 0
   while text_counter < len(text):

      # Ignore ' ' and stop when you get lower case words
      while (text_counter < len(text)) and (text[text_counter] == ' '):
         text_counter += 1
      if re.search(r'[a-z]', text[text_counter]):
         # The text has lower case characters so it is not a student name
         break

      name = ''
      while (text_counter < len(text)) and not text[text_counter].isnumeric():
         name += text[text_counter]
         name = name.strip()
         text_counter += 1

      if text_counter == len(text):
         raise f"got name {name} without pid"

      pid = int(text[text_counter])
      if not (roll['pid'] == pid).any():
         print(f"pid {pid} in {args.pdf} is not in {args.csv}")
      student_pids.append(pid)
      text_counter += 1

   for img in doc.getPageImageList(i):
      xref = img[0]
      pix = fitz.Pixmap(doc, xref)

      pid = student_pids[len(student_image_fns)]
      try:
         onyen = roll.loc[roll.pid == pid].iloc[0, 0]
      except:
         print(f"PID {pid} not found in {args.pdf}")
         raise
      fn = f"../static/images/students/{onyen}.png"
      roll.loc[roll.pid == pid, 'imageURL'] = \
         f'{dotenv_values["HTTPS_FQDN"]}/static/images/students/{onyen}.png'

      # Convert integer section to a string 00x section
      section = f'00{roll.loc[roll.pid==pid].section.iloc[0]}'
      roll.loc[roll.pid == pid, 'section'] = section

      if pix.n < 5:       # this is GRAY or RGB
         pix.writePNG(fn)
      else:               # CMYK: convert to RGB first
         pix1 = fitz.Pixmap(fitz.csRGB, pix)
         pix1.writePNG("p%s-%s.png" % (i, xref))
         pix1 = None
      pix = None
      student_image_fns.append(fn)

   assert len(student_pids) == len(student_image_fns)

# I don't want to actually put the CSV into the database
# Let's get it into a file and let the admin verify it's correct
# They might want to merge it into the existing file, or whatever
roll.columns = ['Student ID', 'PID', 'Name', 'Section', 'imageURL']
roll.to_csv('x.csv', index=False, columns=["Student ID", "PID", "Name", "Section", "imageURL"])
print(f'./ReadClassRollIntoSQL.py csv=x.csv')
