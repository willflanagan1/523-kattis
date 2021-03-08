#!/usr/bin/python3


from LP import LP
objective = [  40,  30,  0,  0, 0, 0]
constraint = [[ 1,   2,  1,  0, 0, 16],
              [ 1,   1,  0,  1, 0,  9],
              [ 3,   2,  0,  0, 1, 24]] 
l = LP(objective, constraint)
print(l.objective)
print
print(f'{l.basic_variables[0]} = {l.constraint_equation(0)}')
print(f'{l.basic_variables[1]} = {l.constraint_equation(1)}')
print(f'{l.basic_variables[2]} = {l.constraint_equation(2)}')

l.iterate()
assert l.solved == False
print("First iteration")
print(l.objective)
print
print(f'Entering {l.entering}, Leaving {l.leaving}')
print(f'{l.basic_variables[0]} = {l.constraint_equation(0)}')
print(f'{l.basic_variables[1]} = {l.constraint_equation(1)}')
print(f'{l.basic_variables[2]} = {l.constraint_equation(2)}')

l.iterate()
assert l.solved == True
print("Second iteration")
print(l.objective)
print
print(f'Entering {l.entering}, Leaving {l.leaving}')
print(f'{l.basic_variables[0]} = {l.constraint_equation(0)}')
print(f'{l.basic_variables[1]} = {l.constraint_equation(1)}')
print(f'{l.basic_variables[2]} = {l.constraint_equation(2)}')
