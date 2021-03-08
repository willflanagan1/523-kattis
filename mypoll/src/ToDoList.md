# mypoll

We use this for polling, worksheets, quizzes, and exams. It started as a very
simple hack and grew over time.

This version has several changes.

1. I factored the boiler-plate Bottle code out into appbase.py. I'm hoping to
   reuse that code in other projects.
2. Expression evaluation is only done in Javascript; the hack of depending on
   Python and Javascript to produce the same exact results produced too many
   problems.
3. Solutions are stored in the database.

## To do

1. mypoll.js needs lots of cleanup. I did the minimum to get it working.
2. getAnswers.py still includes its own hash function. We should do all hashing
   in Javascript to assure consistency.
3. runner.js should accept batches of work to do. In fact, evalInContext.py
   should probably go away and all that code simply move into getAnswers.py.
4. The rundb.sh hack depends on being able to login to my machine. Something
   more generic would be good.
5. Lots of routes still to be added to app.py but they should mostly just copy
   over.
6. Deploy scripts.
7. Should make a `requirements.txt` file for Python dependencies.
8. Should minify and compress the css and other files
9. Should cleanup unused js and css functions

## Building

`npm install` to get the dependencies.

To build `bundle.js` run `npm run watch`; it will build automatically when you
change it.

To test, run `make dev`; it will reload itself on changes to the Python and
reload the browser when anything changes. Very convenient.
