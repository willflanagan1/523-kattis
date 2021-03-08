#!/usr/bin/python3 

from functools import lru_cache

# https://www.geeksforgeeks.org/cutting-a-rod-dp-13/
# A Dynamic Programming solution for Rod cutting problem 
INT_MIN = -32767

# Returns the best obtainable price for a rod of length n and 
# price[] as prices of different pieces 
def cutRod(price, cost=0): 
    '''
     Given a rod of length n inches and an array of prices that contains
     prices of all pieces of size smaller than n. Determine the maximum 
     value obtainable by cutting up the rod and selling the pieces. 

     For example, if length of the rod is 8 and the values of different 
     pieces are given as following, then the maximum obtainable value is
     22 (by cutting in two pieces of lengths 2 and 6)

     length   | 1   2   3   4   5   6   7   8  
     --------------------------------------------
     price    | 1   5   8   9  10  17  17  20

     And if the prices are as following, then the maximum obtainable value
     is 24 (by cutting in eight pieces of length 1)

     length   | 1   2   3   4   5   6   7   8  
     --------------------------------------------
     price    | 3   5   8   9  10  17  17  20

     If parameter cost is non-zero, this is the cost to make the actual cut.
    '''
    n = len(price)
    val = [0 for x in range(n+1)] 
    val[0] = 0
    text = [''] * len(val)

    # Build the table val[] in bottom up manner and return 
    # the last entry from the table 
    for i in range(1, n+1): 
        max_val = INT_MIN 
        max_text = ''
        for j in range(i): 
            if i - j == 1:
               this_price = price[j] + val[i-j-1]
            else:
               this_price = price[j] + val[i-j-1] - cost
            if this_price > max_val:
                #if max_val != INT_MIN:
                #   print(f"i={i} j={j} max_val={max_val}, max_text={max_text}")
                #   import pdb; pdb.set_trace()
                max_val = this_price
                max_text = f'1 cut of {j+1}, {text[i-j-1]}'
        val[i] = max_val 
        text[i] = max_text
        # print(f"The best way to cut {i} is max_text={max_text}")

    # print(f"val={val}")
    # print(f"text={text[n]}")
    # print(f"The best way to cut a pipe of length {n} is {text[n]} for a cost of {val[n]}")
    # text[n] = text[n].rstrip(' ').rstrip(',')
    return val, text 

# Driver program to test above functions 

if __name__ == "__main__":
   arr = [1, 5, 8, 9, 10, 17, 17, 20] 
   value, text = cutRod(arr)
   assert value == 22
   print(f"The maximum obtainable value for {arr} is {value} using {text}")
   
   arr = [2, 3, 4, 9, 12, 17, 18, 22, 25, 30]
   for index in range(len(arr)):
      arr2 = arr[:index+1]
      value, text = cutRod(arr2)
      print(f"The maximum obtainable value for {arr2} is {value} using {text}")
   

@lru_cache(maxsize=1024)
def get_pipe_values(prices, costs):
    ''' Given a tuple of prices and costs, return a list of the rod cutiting values '''
    return [ cutRod(prices[i], costs[i])[0][1:] for i in range(len(prices)) ]
