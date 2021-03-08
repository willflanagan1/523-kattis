#!/usr/bin/python3 

# https://www.geeksforgeeks.org/longest-common-subsequence-dp-4/
# This code is contributed by Nikhil Kumar Singh(nickzuck_007) 
# Dynamic Programming implementation of LCS problem 

class LCS(object):
    ''' Create a LCS object '''

    def __init__(self, X , Y): 
       self._X = X
       self._Y = Y
       # find the length of the strings 
       self._m = len(X) 
       self._n = len(Y) 

       # declaring the array for storing the dp values 
       self._L = [[None]*(self._n+1) for i in range(self._m+1)] 
       self._B = [[0]*(self._n+1) for i in range(self._m+1)] 

       """Following steps build L[m+1][n+1] in bottom up fashion 
       Note: L[i][j] contains length of LCS of X[0..i-1] 
       and Y[0..j-1]"""
       for i in range(self._m+1): 
           for j in range(self._n+1): 
               if i == 0 or j == 0 : 
                   self._L[i][j] = 0
                   self._B[i][j] = 0
               elif X[i-1] == Y[j-1]: 
                   self._L[i][j] = self._L[i-1][j-1]+1
                   self._B[i][j] = 'DIAG'
               else: 
                   if self._L[i-1][j] >= self._L[i][j-1]:
                      self._B[i][j] = 'UP'
                   else:
                      self._B[i][j] = 'LEFT'
                   self._L[i][j] = max(self._L[i-1][j] , self._L[i][j-1]) 
       self._sq = [[ f'{self._L[i][j]}{self._B[i][j]}' for i in range(0, self._m+1) ] for j in range(0, self._n+1) ]

       # Following code is used to get the actual LCS 
       index = self._L[self._m][self._n] 
  
       # Create a character array to store the lcs string 
       self._lcs = [""] * (index+1) 
  
       # Start from the right-most-bottom-most corner and 
       # one by one store characters in self._lcs[] 
       i = self._m 
       j = self._n 
       while i >= 0 and j >= 0: 
           # If current direction is DIAG, then 
           # current character is part of LCS 
           if 'DIAG' == self._B[i][j]: 
               self._lcs[index-1] = X[i-1] 
               i-=1
               j-=1
               index-=1
  
           # If UP, go up, else go left
           elif 'UP' == self._B[i][j]: 
               i-=1
           else: 
               j-=1

    def square(self, i, j):
       assert (0 <= i <= self._m) and (0 <= j <= self._n), f"square({i},{j}) must be less than {self._m},{self._n}"
       return f'{self._L[i][j]}{self._B[i][j]}'

    @property
    def sq(self):
       return self._sq

    @property
    def lcs(self):
       return self._lcs

    @property
    def LCS(self):
       # L[m][n] contains the length of LCS of X[0..n-1] & Y[0..m-1] 
       return self._L[self._m][self._n] 


# Driver program to test the above function 
if __name__ == "__main__":
   X = "AGGTAB"
   Y = "GXTXAYB"
   lcs = LCS(X,Y)
   print(f"X={X}\nY={Y}\nLength of LCS is {lcs.LCS}") 
