#!/usr/bin/python3

import copy
from fractions import Fraction
import numpy as np
import re
import sys

class LP(object):
   ''' Create an LP object'''

   def __init__(self, objective, constraint):
      self._constraint = np.array(constraint, dtype=float)
      self._objective = np.array(objective, dtype=float)
      self._constraint_original = np.copy(self._constraint)
      self._objective_original = np.copy(self._objective)
      self._number_non_basics = sum(self._objective>0)
      assert len(self._constraint[0]) == len(self._objective), f'There are {len(self._constraint[0])} constraint variables and {len(self._objective)} variables'
      # You don't always have one constraint per nonbasic+1
      # assert self._number_non_basics + 1 + len(self._constraint) == len(self._objective)
      for index in range(self._number_non_basics):
          assert self._objective[index] > 0  # non-zero, non-basics come first
      self._labels = np.array([f'x{i}' for i in range(1, len(self._objective)) ] +['rhs'])
      self._basics = np.array([f'x{i}' for i in range(self._number_non_basics+1, len(self._objective)) ])
      self._rhs_index = len(self._labels) -1
      self._iteration = 0
      self._entering = None
      self._leaving = None

   @property
   def variables(self):
      return self._labels[:-1]

   @property
   def basic_variables(self):
      return self._basics

   @property
   def nonbasic_variables(self):
      return [ x for x in self.variables if x not in self.basic_variables]

   @property
   def objective(self):
      x = []
      for index in range(len(self._labels)-1):
         if self._objective[index] != 0:
            coefficient = self._objective[index]
            if coefficient.is_integer():
               coefficient = int(coefficient)
               if coefficient == 1:
                  x.append(f'{self._labels[index]}')
                  continue
            else:
               coefficient = Fraction(f'{coefficient}').limit_denominator(20)
               coefficient = f'{coefficient}'
            x.append(f'{coefficient} * {self._labels[index]}')
      # x = [f'{self._objective[index]} * {self._labels[index]}' for index in range(len(self._labels)-1) if self._objective[index] != 0 ]
      if self._objective[self._rhs_index] != 0:
         coefficient = self._objective[self._rhs_index] * -1
         if coefficient.is_integer():
            coefficient = int(coefficient)
         else:
            coefficient = Fraction(f'{coefficient}').limit_denominator(20)
            coefficient = f'{coefficient}'
         if coefficient != 0:
            x.append( f'{coefficient}' )
      eq = ' + '.join(x)
      return re.sub(r' \+ -', r' - ', eq)

   @property
   def objective_value(self):
      coefficient = self._objective[self._rhs_index] * -1
      if coefficient.is_integer():
         coefficient = int(coefficient)
      else:
         coefficient = Fraction(f'{coefficient}').limit_denominator(20)
         coefficient = f'{coefficient}'
      return f'{coefficient}'

   def constraint_variable(self, index):
      assert index < len(self._basics), f'Index {index} is greater than or equal to the number of basic variables {len(self._basics)}'
      return self._basics[index]

   def constraint_equation(self, index1):
      assert index1 < len(self._basics), f'Index {index1} is greater than or equal to the number of basic variables {len(self._basics)}'
      x = []
      for index2 in range(len(self._labels)-1):
         if (self._constraint[index1, index2] != 0) and (self._basics[index1] != self._labels[index2]):
            coefficient = self._constraint[index1, index2] * -1
            if coefficient.is_integer():
               coefficient = int(coefficient)
               if coefficient == 1:
                  x.append(f'{self._labels[index2]}')
                  continue
               elif coefficient == -1:
                  x.append(f'-{self._labels[index2]}')
                  continue
            else:
               coefficient = Fraction(f'{coefficient}').limit_denominator(20)
               coefficient = f'{coefficient}'
            x.append(f'{coefficient} * {self._labels[index2]}')
      # x = [f'{self._constraint[index1, index2] * -1} * {self._labels[index2]}' 
      #      for index2 in range(len(self._labels)-1) 
      #      if (self._constraint[index1, index2] != 0) and (self._basics[index1] != self._labels[index2]) ]
      coefficient = self._constraint[index1, self._rhs_index]
      if coefficient.is_integer():
         coefficient = int(coefficient)
      else:
         coefficient = Fraction(f'{coefficient}').limit_denominator(20)
         coefficient = f'{coefficient}'
      if coefficient != 0:
         x.append( f'{coefficient}' )
      eq = ' + '.join(x)
      return re.sub(r' \+ -', r' - ', eq)

   def subject_to_lt(self, index1):
      assert index1 < len(self._basics), f'Index {index1} is larger than or equal to the number of basic variables {len(self._basics)}'
      x = []
      for index2 in range(len(self._labels)-1):
         if (self._constraint[index1, index2] != 0) and (self._basics[index1] != self._labels[index2]):
            coefficient = self._constraint[index1, index2]
            if coefficient.is_integer():
               coefficient = int(coefficient)
            else:
               coefficient = Fraction(f'{coefficient}').limit_denominator(20)
               coefficient = f'{coefficient}'
            if coefficient == 1:
               x.append(f'{self._labels[index2]}')
            elif coefficient == -1:
               x.append(f'-{self._labels[index2]}')
            else:
               x.append(f'{coefficient} * {self._labels[index2]}')
      # x = [f'{self._constraint[index1, index2]} * {self._labels[index2]}' 
      #      for index2 in range(len(self._labels)-1) 
      #      if (self._constraint[index1, index2] != 0) and (self._basics[index1] != self._labels[index2]) ]
      x = ' + '.join(x)
      assert self._constraint[index1, self._rhs_index] != 0
      coefficient = self._constraint[index1, self._rhs_index]
      if coefficient.is_integer():
         coefficient = int(coefficient)
      else:
         coefficient = Fraction(f'{coefficient}').limit_denominator(20)
         coefficient = f'{coefficient}'
      x += f' <= {coefficient}'
      return re.sub(r' \+ -', r' - ', x)

   def subject_to_gt(self, index1):
      assert index1 < len(self._basics)
      x = []
      for index2 in range(len(self._labels)-1):
         if (self._constraint[index1, index2] != 0) and (self._basics[index1] != self._labels[index2]):
            coefficient = self._constraint[index1, index2] * -1
            if coefficient.is_integer():
               coefficient = int(coefficient)
            else:
               coefficient = Fraction(f'{coefficient}').limit_denominator(20)
               coefficient = f'{coefficient}'
            if coefficient == 1:
               x.append(f'{self._labels[index2]}')
            elif coefficient == -1:
               x.append(f'-{self._labels[index2]}')
            else:
               x.append(f'{coefficient} * {self._labels[index2]}')
      # x = [f'{self._constraint[index1, index2] * -1} * {self._labels[index2]}' 
      #      for index2 in range(len(self._labels)-1) 
      #      if (self._constraint[index1, index2] != 0) and (self._basics[index1] != self._labels[index2]) ]
      x = ' + '.join(x)
      assert self._constraint[index1, self._rhs_index] != 0
      coefficient = self._constraint[index1, self._rhs_index]*-1
      if coefficient.is_integer():
         coefficient = int(coefficient)
      else:
         coefficient = Fraction(f'{coefficient}').limit_denominator(20)
         coefficient = f'{coefficient}'
      x += f' >= {coefficient}'
      return re.sub(r' \+ -', r' - ', x)

   @property 
   def solved(self):
      ''' If all nonbasic variable coefficients are negative we can't increase profit
          If all constraint RHS are positive we have a feasible solution '''
      can_increase_objective = max(self._objective[:-1]) <= 0
      if can_increase_objective:
         return True
      # assert min(self._constraint[:,-1]) >0, f'This is an infeasible solution!'
      return False

   @property
   def entering(self):
      assert self._entering is not None
      return self._entering

   @property
   def leaving(self):
      assert self._leaving is not None
      return self._leaving

   def iterate(self):
      assert not self.solved

      assert sum(self._objective.max() == self._objective) == 1, f'Two objective coefficients the same {self._objective}\nObjective:\n{self._objective_original}\nConstraints:\n{self._constraint_original}'
      self._entering = self._labels[ self._objective.argmax() ]
      self._entering_index = np.argmax( self._labels == self._entering )

      # Leaving is the min ratio of the basic variables
      # Note, cannot divide by self._constraint[:, self._entering_index] because some elements may be zero
      # min_ratio_basic = self._constraint[:, self._rhs_index] / self._constraint[:, self._entering_index]
      # min_ratio_basic = min_ratio_basic[min_ratio_basic >0].min()
      # self._leaving_index = np.argmax( self._constraint[:, self._rhs_index] / self._constraint[:, self._entering_index] == min_ratio_basic )
      min_ratio_basic = None
      for index in range(len(self._constraint[:, self._entering_index])):
         if self._constraint[index, self._entering_index]>0:
            ratio = self._constraint[index, self._rhs_index] / self._constraint[index, self._entering_index]
            assert ratio != min_ratio_basic, f'Two columns have the same ratio {ratio}, entering {self._entering}/{self._constraint[index, self._rhs_index]}/{self._constraint[index, self._entering_index]}, two possible solutions.\nObjective:\n{self._objective_original}\nConstraints:\n{self._constraint_original}'
            if (ratio>0) and ((min_ratio_basic is None) or (ratio<min_ratio_basic)):
               min_ratio_basic = ratio
               self._leaving_index = index

      assert min_ratio_basic is not None, f'For entering {self._entering} and leaving {self._leaving} there is no min_ratio_basic'
      self._leaving = self._basics[ self._leaving_index ]

      new_constraint = self._constraint[ self._leaving_index, : ] / self._constraint[ self._leaving_index, self._entering_index]
      self._objective = self._objective - self._objective[self._entering_index] * new_constraint
      for index in range(len(self._constraint)):
          if index != self._leaving_index:
             self._constraint[index] = self._constraint[index] - self._constraint[index, self._entering_index] * new_constraint
          else:
             self._constraint[index] = new_constraint
      self._basics[self._leaving_index] = self._entering

      old_constraint = copy.deepcopy( self._constraint )
      old_basics = np.copy( self._basics )
      index = 0
      for key in sorted(self._basics):
         self._basics[index] = key
         old_index = np.argmax( old_basics == key )
         self._constraint[index] = old_constraint[old_index]
         assert abs(self._constraint[index, np.argmax(self._labels == key)]) == 1, f'Constraint row {index} should have {key} coefficent 1, but constraint[{index}] is {self._constraint[index]} with {self._labels} labels'
         index += 1
      self._iteration += 1

# Driver program to test the above function
if __name__ == "__main__":
   labels =     np.array(['x1', 'x2', 'x3', 'x4', 'x5', 'rhs' ])
   constraint = np.array([[  1,   2,     1,    0,    0,    16 ],
                          [  1,   1,     0,    1,    0,     9 ],
                          [  3,   2,     0,    0,    1,    24 ]], dtype=float)
   objective  = np.array([  40,  30,     0,    0,    0,     0 ], dtype=float)
   basic      = np.array([            'x3',  'x4', 'x5' ])
   rhs_index  = len(labels) -1

   iteration = 1
   while max(objective[:-1]) > 0:   # Do not include right hand size
      entering = labels[ objective.argmax() ]
      entering_index = np.argwhere( labels == entering)[0][0]

      # Leaving is the min ratio of the basic variables
      min_ratio_basic = constraint[:, rhs_index].max()
      for index in range(len(constraint)):
         if constraint[index, rhs_index] / constraint[index, entering_index] < min_ratio_basic:
            leaving_index = index
            min_ratio_basic = constraint[index, rhs_index] / constraint[index, entering_index]
      leaving = basic[ leaving_index ]
      print(f"Iteration {iteration} entering variable {entering} leaving variable {leaving}")

      new_constraint = constraint[ leaving_index, : ] / constraint[ leaving_index, entering_index]
      objective = objective - objective[entering_index] * new_constraint
      for index in range(len(constraint)):
          if index != leaving_index:
             constraint[index] = constraint[index] - constraint[index, entering_index] * new_constraint
          else:
             constraint[index] = new_constraint
      basic[leaving_index] = entering

      old_constraint = copy.deepcopy( constraint )
      old_basic = np.copy( basic )
      index = 0
      for key in sorted(basic):
         basic[index] = key
         old_index = np.argmax( old_basic == key )
         constraint[index] = old_constraint[old_index]
         assert constraint[index, np.argmax(labels == key)] == 1, f'Constraint row {index} should have {key} coefficent 1, but constraint[{index}] is {constraint[index]} with {labels} labels'
         index += 1
      iteration += 1

   print(f'Maximum objective function value is {-objective[rhs_index]}')
   for index in range(len(constraint)):
      print(f'   {basic[index]} = {round(constraint[index, rhs_index], 0)}')
