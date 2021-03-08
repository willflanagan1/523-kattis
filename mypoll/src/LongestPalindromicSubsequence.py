#!/usr/bin/python3 

import numpy as np
import sys

def numberLPS(m):
    number_LPS = 1
    for i1 in range(len(m)):
       for i2 in range(len(m[i1])):
          if ((m[i2, i1] is not None) and 
              (m[1, -1] != m[i2, i1]) and
              (len(m[1,-1]) == len(m[i2, i1]))):
             number_LPS += 1
    return number_LPS
    
def LPS(s):
    
    n = len(s) 
    s = ' '+s
    m = np.empty( (n+1)**2, dtype=object).reshape((n+1,n+1))
    #for i in range(n+1):
    #    m[i,i] = 0
    for i in range(1, n+1):
       m[i,i] = s[i]
    
    for L in range(2, n+1):
        for i in range(1, n-L+2):
            j = i + L -1
            if (s[i] == s[j]) and (i+1 == j):
               m[i,j] = f'{s[i]}{s[j]}'  # The two adjacent, identical elements are palindromic
            elif s[i] == s[j]:
               m[i,j] = f'{s[i]}{m[i+1, j-1]}{s[j]}'  # i,j are bookends to the LPS
            else:
               # s[i] and s[j] are not equal
               if len(m[i+1, j]) > len(m[i, j-1]):
                  m[i,j] = m[i+1, j]
               else:
                  m[i,j] = m[i, j-1]
            # print(f's[{i}]={s[i]} s[{j}]={s[j]} m[{i},{j}]={m[i,j]}')
            
    return m 

if __name__ == "__main__":
   p = np.array([7,2,6,3,4,5])
   m, s, parenthesized_string = MatrixMult(p)
   print(m)
   print(s)
   print(parenthesized_string)

   p = np.array([7,4,4,3,4,5])
   m, s, parenthesized_string = MatrixMult(p)
   print(m)
   print(s)
   print(parenthesized_string)
