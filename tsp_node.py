#!/usr/bin/python
# node and timestep

import sys
import math
import random
import itertools
from gurobipy import *


def parse(filename):
    dist = []
    adj = dict()
    with open(filename) as f:
        l = f.readline()
        n = int(l[:-1])
        for node in range(n):
            l = f.readline()

            entries = l.split(" ")
            print(entries, len(entries))

            points = list(map(int, entries))
            # create adj 
            adj[node] = []
            for neighbor in range(n):
                if (neighbor != node and points[neighbor] != -1): 
                    adj[node].append(neighbor)
            dist.append(points)
    return n, dist, adj

filename = sys.args[0]

# Parse argument
n, dist, adj = parse()

m = Model()

# n cities, n-1 timestep 
vars = m.addVars(n,n,vtype=GRB.BINARY, name="e")

# 0. if fix start and end 
start = 1
end = 3
# m.addConstr(vars[start,0], GRB.EQUAL, 1)
# m.addConstr(vars[end,n-2], GRB.EQUAL, 1)

# 1. each city is visited once 
for city in range(n):
    m.addConstr(vars.sum(city,'*') == 1)

# 2. each timestep visits only one city 
for t in range(n-1):
    m.addConstr(vars.sum('*',t) == 1)

# 3. connectivity
for timestep in range(n-1):
    for node in range(n):
        # node t implies neighbor t+1
        neighbors = adj[node]
        constr = LinExpr()
        constr.add(1-vars[node, timestep])
        for neighbor in neighbors: 
            constr.add(vars[neighbor, timestep+1])
            # print(constr)
            # c = m.addConstr(constr, GRB.GREATER_EQUAL, 1)
            # print(c)

# opt
goal = QuadExpr()
for t in range(n-1):
    for i in range(n):
        for j in range(n):
            w = dist[i][j]
            goal.add(vars[(i,t)] * vars[(j,t+1)] * w)

m.setObjective(goal, GRB.MINIMIZE) 

m.optimize()

print(m.printAttr('x') )
print("===")

print('')

print('Optimal cost: %g' % m.objVal)
print('')