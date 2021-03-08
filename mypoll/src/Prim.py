#!/usr/bin/python3 

from collections import defaultdict
import heapq

def create_spanning_tree(graph, starting_vertex):
    mst = defaultdict(set)
    visited = set([starting_vertex])
    edges = [
        (cost, starting_vertex, to)
        for to, cost in graph[starting_vertex].items()
    ]
    heapq.heapify(edges)

    while edges:
        cost, frm, to = heapq.heappop(edges)
        if to not in visited:
            visited.add(to)
            mst[frm].add(to)
            for to_next, cost in graph[to].items():
                if to_next not in visited:
                    heapq.heappush(edges, (cost, to, to_next))

    return mst

example_graph = {
    'A': {'C': 130, 'D': 225, 'F': 265, 'J': 365, 'N': 400, 'R': 255, 'W': 150},
    'C': {'A': 130, 'D': 155, 'F': 140, 'J': 235, 'N': 260, 'R': 160, 'W':  85},
    'D': {'A': 225, 'C': 155, 'F':  75, 'J': 145, 'N': 165, 'R':  25, 'W':  80},
    'F': {'A': 265, 'C': 140, 'D':  75, 'J': 105, 'N': 120, 'R':  65, 'W': 135},
    'J': {'A': 365, 'C': 235, 'D': 145, 'F': 105, 'N':  45, 'R': 125, 'W': 210},
    'N': {'A': 400, 'C': 260, 'D': 165, 'F': 120, 'J':  45, 'R': 170, 'W': 215},
    'R': {'A': 255, 'C': 160, 'D':  25, 'F':  65, 'J': 125, 'N': 170, 'W': 115},
    'W': {'A': 150, 'C':  85, 'D':  80, 'F': 135, 'J': 210, 'N': 215, 'R': 115},
}

import pdb; pdb.set_trace()

mst = dict(create_spanning_tree(example_graph, 'R'))
print(f"spanning tree {mst}")

# {'A': set(['B']),
#  'B': set(['C', 'D']),
#  'D': set(['E']),
#  'E': set(['F']),
#  'F': set(['G'])}
