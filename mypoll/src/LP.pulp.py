#!/usr/bin/python3
# import sys !{sys.executable} -m pip install pulp 
# import the library pulp as p 
import pulp as p 

# Create a LP Minimization problem 
Lp_prob = p.LpProblem('Problem', p.LpMaximize) 

# Create problem Variables 
x1 = p.LpVariable("x1", lowBound = 0) # Create a variable x1 >= 0 
x2 = p.LpVariable("x2", lowBound = 0) # Create a variable x2 >= 0 

# Objective Function 
Lp_prob += 40 * x1 + 30 * x2

# Constraints: 
x3 = p.LpVariable("x3", lowBound=0)
Lp_prob += 16 - x1 - 2 * x2 == x3
x4 = p.LpVariable("x4", lowBound=0)
Lp_prob += 9 - x1 - x2 == x4
x5 = p.LpVariable("x5", lowBound=0)
Lp_prob += 24 - 3 * x1 - 2 * x2 == x5

# Display the problem 
print(Lp_prob) 

status = Lp_prob.solve() # Solver 
print(p.LpStatus[status]) # The solution status 

# Printing the final solution 
print(p.value(x1), p.value(x2), p.value(Lp_prob.objective)) 

import pdb; pdb.set_trace()
print(p.value(x1), p.value(x2), p.value(Lp_prob.objective)) 
