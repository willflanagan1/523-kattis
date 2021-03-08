"""Inputs for mypoll"""
import json
import sys
from datetime import datetime
from bottle import template

# Todos:
#  - Document general concept within class inputs
#  - Why does expression test for >?
#  - In input handlers, document what is checked/required
#  - select should use options not choices

def log(*args):
    """Print for debugging"""
    print(*args, file=sys.stderr)

class inputs:
    """Handle inputs"""

    def __init__(self, key):
        self.key = key
        self.rubrics = {}
        self.info = {}
        self.number = 0
        self.seq_no = 0
        self.interval = 0
        self.focus = 0

    def next(self):
        """Advance to next question number and return it.  Use in place of a name"""
        self.number += 1
        return str(self.number)

    def _name(self, n):
        """Return the tag for this question"""
        return (n or "Q{}").format(self.number)

    def _addRubric(self, name, solution, kind, points, correction_rate, **attrs):
        """Add an answer making sure there are no duplicates"""
        if (points == 0) and (name[0] != '_'):
            if not ('required' in attrs) or (attrs['required'] != 'required'):
               print(f'{self.key}: Warning: Question {name} has no points')
            return
        if name in self.rubrics:
            log(f"Question {name} already exists: {self.rubrics[name]}")
        assert name not in self.rubrics, \
            f"Question {name} already exists: {self.rubrics[name]}"
        self.seq_no += 1
        self.rubrics[name] = dict(solution=solution,
                                  seq_no=self.seq_no,
                                  kind=kind,
                                  points=points,
                                  correction_rate=-1,  # Override correction rate for Spring 2020
                                  **attrs)

    def save(self):
        """Save the answers for grading"""
        total = sum([a['points'] for a in self.rubrics.values()])
        count = len(self.rubrics)
        if 'points_total' in self.info:
            if total != self.info['points_total']:
                print(f"Warning: For {self.key}, total points {total}",
                      f"but info shows total points {self.info['points_total']}")
        else:
            self.info['points_total'] = total
        return self.rubrics, total, count

    def report(self):
        """Report the points and questions"""
        _, total, count = self.save()
        return template("report", total=total, count=count)

    def T(self, answer="", name="", points=0, correction_rate=5, symbols="", **attrs):
        """input any text"""
        name = self._name(name)
        symbols = json.dumps(symbols)
        self._addRubric(name, answer, "text", points, correction_rate, **attrs)
        return template("input", type="text", **locals(), **attrs)

    def N(self, value, name="", points=0, correction_rate=5, **attrs):
        """Input a decimal number"""
        name = self._name(name)
        self._addRubric(
            name, str(value), "decimal", points, correction_rate, **attrs,
        )
        return template(
            "input",
            type="text",
            placeholder="Enter a base-10 value",
            **locals(),
            **attrs,
        )

    def H(self, value, name="", points=0, correction_rate=5, **attrs):
        """Input a hex number"""
        name = self._name(name)
        self._addRubric(
            name, value, "hex", points, correction_rate, **attrs,
        )
        return template(
            "input", type="text", placeholder="Enter hex value", **locals(), **attrs
        )

    def B(self, value, name="", points=0, correction_rate=5, **attrs):
        """Input a binary number"""
        name = self._name(name)
        self._addRubric(
            name, value, "binary", points, correction_rate, **attrs,
        )
        return template(
            "input", type="text", placeholder="Enter binary value", **locals(), **attrs
        )

    def checkbox(self, answer=False, points=0, correction_rate=-1, name="", **attrs):
        """Display a checkbox"""
        name = self._name(name)
        correction_rate = -1
        answer = "on" if answer else "off"
        self._addRubric(name, answer, "checkbox", points, correction_rate, **attrs)
        return template("checkbox", **locals(), **attrs)

    def select(self, answer, choices, points=0, correction_rate=-1, name="", **attrs):
        """Allow selection from choices"""
        assert answer in choices, f"input.py table: {self.key} {name} " \
                                  f"Answer '{answer}' does not appear in the choices {choices}."
        name = self._name(name)
        choices = list(set(choices))
        correction_rate = -1
        self._addRubric(name, answer, "select", points, correction_rate, choices=choices, **attrs)
        return template("select", **locals())

    def expression(self, answer, *contexts, correction_rate=5, points=0, name="", **attrs):
        """Evaluate an expression in a given context"""
        assert isinstance(answer, str)
        answer = answer.replace('&#62;', '>')
        name = self._name(name)
        tests = [{"context": context} for context in contexts]
        self._addRubric(name, answer, "expression", points, correction_rate, tests=tests, **attrs)
        return template("expression", name=name, points=points, attrs=attrs,)

    def javascriptProgram(self, answer, *contexts, num_rows=10, correction_rate=10,
                          points=0, name="", **attrs):
        """Execute a JavaScript program using an array of checks
           Each check is a string of setup JS statements.
        """
        name = self._name(name)
        tests = [{"context": context} for context in contexts]
        self._addRubric(name, answer, "function", points, correction_rate, tests=tests, **attrs)
        return template("javascriptProgram", name=name, num_rows=num_rows,
                        points=points, attrs=attrs)


    def calculator(self, name="_calculator"):
        """Display a calculator box"""
        assert name[:11] == '_calculator', f' inputs.py calculator: {self.key} {name}'\
                                'Calculator names must start with an underscore calculator'
        points = 0
        tests = "[{}]"
        correction_rate = -1
        self._addRubric(name, '0', 'expression', points, tests=tests, correction_rate=correction_rate)
        return template("expression", name=name, tests=tests, points=points, correction_rate=correction_rate)

    def expressionHelp(self):
        """Emit a help block for the expressions"""
        return template("expressionhelp")

    def table(self, inputs=0, headings="", table="", symbols="",
              points=0, correction_rate=5, name=""):
        """Display a table"""
        name = self._name(name)
        assert headings != "", "Heading not entered"
        assert table != "", "table not entered"
        assert isinstance(symbols, list)
        symbols = list(set(symbols))  # Remove duplicates
        if points == 0:
            print(f"Input: table {name} has no points", file=sys.stderr)
        table = [[x.replace('&#44;', ',')
                  for x in row.strip().split(",")]
                 for row in table.strip().split("\n")]
        for row in table:
            assert len(row) > inputs, f"input.py table: {self.key} {name} " \
                                      f"Row {row} needs more columns than {inputs}"
        solution = "-".join(["-".join(row[inputs:]) for row in table])
        for s in solution.split('-'):
            if isinstance(symbols, range):
                assert int(s) in symbols, f'input.py table: {self.key} {name} ' \
                                          f'uses symbol "{s}" of type {type(s)}, not in {symbols}'
            else:
                assert s in symbols, f'input.py table: {self.key} {name}' \
                                     f'uses symbol "{s}" of type {type(s)} but not in {symbols}'

        headings = headings.strip()
        self._addRubric(name, solution, "table", points, correction_rate=correction_rate,
                        headings=headings, symbols=symbols)
        return template("table", **locals())

    def textarea(self, name="", **kwargs):
        """A free input text box"""
        name = self._name(name)
        return template("textarea", name=name, attrs=kwargs)

    def autoSubmit(self, interval=5):
        """Enable automatic submission every interval minutes"""
        self.interval = interval

    def trackFocus(self, status=1):
        """Enable focus reporting"""
        self.focus = status

    def submitCode(self):
        """Require a code for submission"""
        return template("submitCode")

    def elapsed(self):
        """Display elapsed time"""
        return template("elapsed")

    def getInfo(self):
        """ Return the info object """
        return self.info

    def setInfo(self, **values):
        """Insert key/value pairs into the info"""
        self.info.update(values)

    def date(self, month, day, hour=23, minutes=59):
        """Simple access to datetime inside templates"""
        n = datetime.now()
        return datetime(n.year, month, day, hour, minutes)

    def env(self):
        """Return the public methods as a dictionary of bound functions
           for use in a template"""
        r = {}
        for s in dir(self):
            if not s.startswith("_") and s != "env":
                f = getattr(self, s)
                if hasattr(f, "__self__"):
                    r[s] = f
        return r
