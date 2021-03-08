#!/usr/bin/python3

from LP import LP  
lp = LP([  40,  30,     0,    0,    0,     0],
       [[  1,   2,     1,    0,    0,    16 ],
        [  1,   1,     0,    1,    0,     9 ],
        [  3,   2,     0,    0,    1,    24 ]])
lp.iterate()
print(lp.objective)


from LP import LP
objective_equation =   [ 4, 5, 6, 0, 0, 0, 0]
constraint_equation = [[ 1, 2, 3, 1, 0, 0, 12],
                       [ 3, 1, 2, 0, 1, 0, 20],
                       [ 4, 1, 1, 0, 0, 1, 16]]
l = LP(objective_equation, constraint_equation)
l.iterate()
l.iterate()
import pdb; pdb.set_trace()
l.iterate()
print(l.entering, l.leaving)


