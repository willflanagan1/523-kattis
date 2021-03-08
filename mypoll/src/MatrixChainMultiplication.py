#!/usr/bin/python3 

import numpy as np
import sys
from functools import lru_cache

def get_parenthesized_string_from_s(s, i, j, string):
    ''' Given the s matrix, the current i,j, and the string so far,
        return the parenthesized string '''
    if i == j:
        string += "A{}".format(j)
    else:
        string += "("
        string += get_parenthesized_string_from_s(s, i, s[i,j], "")
        string += get_parenthesized_string_from_s(s, s[i,j]+1, j, "")
        string += ")"
    return string

def MatrixMult(p, min_mcm=True):
    
    n = len(p) -1
    m = np.zeros( (n+1)**2, dtype=int).reshape((n+1,n+1))
    s = np.zeros( (n+1)**2, dtype=int).reshape((n+1,n+1))
    #for i in range(n+1):
    #    m[i,i] = 0
    
    for L in range(2, n+1):
        for i in range(1, n-L+2):
            j = i + L -1
            m[i,j] = sys.maxsize if min_mcm else 0
            
            for k in range(i, j):
                q = m[i,k] + m[k+1,j] + p[i-1] * p[k] * p[j]
                
                assert q != m[i,j], f'A tie exists for m[{i},{j}] and m[{i},{s[i,k]}] both have {q}'
                if ((min_mcm and (q < m[i,j])) or
                    (not min_mcm and (q > m[i,j]))):
                    s[i,j] =k
                    m[i,j] = q
            
    parenthesized_string = get_parenthesized_string_from_s(s, 1, len(p)-1, "")
    return m, s, parenthesized_string 

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


@lru_cache(maxsize=1024)
def get_matrix_m_s_parenthesized_string(p, min_mcm=True):
    ''' Given a tuple of matrix p counts, return the m, s, and parenthesized string '''
    return MatrixMult(p, min_mcm)
