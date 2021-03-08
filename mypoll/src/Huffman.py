#!/usr/bin/python3 

# https://www.programiz.com/dsa/huffman-coding
# Huffman Coding in python

string = 'BCAADDDCCACACAC'
string = 'a'*45 + 'b'*13 + 'c'*12 + 'd'*16 + 'e'*9 +'f'*5
string = 'A'*7 + 'B'*16 + 'C'*5 + 'D'*6 + 'E'*8 + 'F'*18

# Creating tree nodes
class NodeTree(object):

    def __init__(self, left=None, right=None, value=0):
        self.left = left
        self.right = right
        self.value = value

    def children(self):
        return (self.left, self.right)

    def nodes(self):
        return (self.left, self.right)

    def __str__(self):
        return '%s_%s' % (self.left, self.right)


# Main function implementing huffman coding
def huffman_code_tree(node, left=True, binString=''):
    if type(node) is str:
        return {node: binString}
    (l, r) = node.children()
    d = dict()
    d.update(huffman_code_tree(l, True, binString + '0'))
    d.update(huffman_code_tree(r, False, binString + '1'))
    return d

class Huffman(object):
   ''' Huffman code object '''

   def _node_value(self, node, string):
       ''' Given a NodeTree node, and a edge traversal string, 
        return the value or None
   
       The string is characters l, r, v'''
       try:
         if (len(string)<1) or (string[0] == 'v'):
            if type(node) is str:
               if node in self.frequency.keys():
                  return f'{node}:{self.frequency[node]}'
               return node
            else:
               return f'{node.value}'
         elif string[0] == 'l':
            return self._node_value(node.left, string[1:])
         elif string[0] == 'r':
            return self._node_value(node.right, string[1:])
         else:
            assert False, f'node_value: string {string} has none l, r, v value'
       except AttributeError:
         return 'None'

   @property
   def frequency(self):
      return self._freq

   @property
   def frequency_labels(self):
      ''' Return character colon frequence '''
      return { k: f'{k}:{v}' for k,v in self.frequency.items() }
 
   @property
   def tree_labels(self):
      ''' Get the midterm2.huffman.png tree labels '''
      tr =   [ self._node_value(self.root, 'v'), 
               self._node_value(self.root, 'lv'),    self._node_value(self.root, 'rv'), 
               self._node_value(self.root, 'llv'),   self._node_value(self.root, 'lrv'), 
               self._node_value(self.root, 'rlv'),   self._node_value(self.root, 'rrv'), 
               self._node_value(self.root, 'lllv'),  self._node_value(self.root, 'llrv'), 
               self._node_value(self.root, 'lrlv'),  self._node_value(self.root, 'lrrv'), 
               self._node_value(self.root, 'rllv'),  self._node_value(self.root, 'rlrv'), 
               self._node_value(self.root, 'rrlv'),  self._node_value(self.root, 'rrrv'), 
               self._node_value(self.root, 'llllv'), self._node_value(self.root, 'lllrv'), 
               self._node_value(self.root, 'llrlv'), self._node_value(self.root, 'llrrv'), 
               self._node_value(self.root, 'lrllv'), self._node_value(self.root, 'lrlrv'), 
               self._node_value(self.root, 'lrrlv'), self._node_value(self.root, 'lrrrv'), 
               self._node_value(self.root, 'rlllv'), self._node_value(self.root, 'rllrv'), 
               self._node_value(self.root, 'rlrlv'), self._node_value(self.root, 'rlrrv'), 
               self._node_value(self.root, 'rrllv'), self._node_value(self.root, 'rrlrv'), 
               self._node_value(self.root, 'rrrlv'), self._node_value(self.root, 'rrrrv'), 
             ]
      numbers = [x for x in tr if x != 'None' ]
      numbers = sorted([ int(x[2:]) if ':' in x else int(x) for x in numbers ])
      for index in range(len(numbers)-1):
         assert numbers[index] != numbers[index+1], f"Duplicate value {numbers[index]} in {tr}"
      return tr

   def __init__(self, string):
      self.string = string

      # Calculating frequency
      self._freq = {}
      for c in string:
          if c in self._freq:
              self._freq[c] += 1
          else:
              self._freq[c] = 1
      # print(f'freq={self._freq}')

      self._nodes = sorted(self._freq.items(), key=lambda x: x[1], reverse=True)
      # print(f"freq = {self._freq[::-1]}")

      while len(self._nodes) > 1:
          (key1, c1) = self._nodes[-1]
          (key2, c2) = self._nodes[-2]
          self._nodes = self._nodes[:-2]
          node = NodeTree(key1, key2, c1+c2)
          self._nodes.append((node, c1 + c2))

          self._nodes = sorted(self._nodes, key=lambda x: x[1], reverse=True)
      # print(f"Nodes {self._nodes}")
      self.root = self._nodes[0][0]

      self.huffmanCode = huffman_code_tree(self.root)

if __name__ == "__main__":
   print(f"String is {string}")
   huffman = Huffman(string)
   print(f"Huffman code tree {huffman.huffmanCode}")

   if False:
      print(' Char | Huffman code ')
      print('----------------------')
      for (char, frequency) in freq:
         print(' %-4r |%12s' % (char, huffmanCode[char]))

   print(' Char | Huffman code ')
   print('----------------------')
   for key in sorted(huffman.freq.keys()):
      print(' %-4r |%12s' % (key, huffman.huffmanCode[key]))
