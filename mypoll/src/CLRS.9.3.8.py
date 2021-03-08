#!/usr/bin/python3

def two_array_median(A, B):
   print(f'Entering two_array with A={A} B={B}')
   n = len(A)
   assert len(A) == len(B)

   if n==1:
      print(f'The median is lower of {A[0]} and {B[0]}... {min(A[0], B[0])}')
      return min(A[0], B[0])

   if n % 2:
      m = n // 2
   else:
      m = n // 2 - 1
   print(f"Len {n} means m={m} A[m]={A[m]} and B[m]={B[m]}")

   i = m+1
   if A[m] < B[m]:
      return two_array_median(A[-i:], B[:i])
   return two_array_median(A[:i], B[-i:])

A = [ 1, 2, 3, 4, 5, 6, 17 , 18, 19 , 20 ]
B = [ 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ]
two_array_median(A, B)
