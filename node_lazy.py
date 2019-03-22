#!/usr/bin/python
# node and timestep

import sys
import math
import random
import itertools
from gurobipy import *

# lazy
# check the shortest subtour, and add one more constraint

def parse(filename):
    dist = []
    adj = dict()
    with open(filename) as f:
        l = f.readline()
        n = int(l[:-1])
        for node in range(n):
            l = f.readline()
            entries = l.split()
            points = []
            for neighbor in range(n):
                points.append(int(entries[neighbor]))
            assert(len(points) == n)
            # create adj 
            adj[node] = []
            for neighbor in range(n):
                if (neighbor != node and points[neighbor] != -1): 
                    adj[node].append(neighbor)
            dist.append(points)
    return n, dist, adj

# Callback - use lazy constraints to eliminate sub-tours

def subtourelim(model, where):
    
    if where == GRB.Callback.MIPSOL:
        # make a list of edges selected in the solution
        vals = model.cbGetSolution(model._vars)
        selected = tuplelist((i,t) for i,t in model._vars.keys() if vals[i,t] > 0.5)

        # find the shortest cycle in the selected edge list
        tour = subtour(selected) # None indicate success
        if tour != None:
            broken = tour[0]
            timestep = tour[1]
            print("broken at ", broken, t)
            constr = LinExpr()
            
            # node t implies neighbor t+1
            neighbors = adj[broken]

            constr.add(-vars[broken, timestep])
            for neighbor in neighbors: 
                constr.add(vars[neighbor, timestep+1])
            print(constr, "===")
            model.cbLazy(constr , GRB.GREATER_EQUAL, 0)


# Given a tuplelist of city timestep, find the shortest subtour

def subtour(steps):
    for t in range(n-1):
        curr = steps.select("*",t)[0][0]
        next = steps.select("*",t+1)[0][0]
        if dist[curr][next] == -1:
            return (curr, t)
    return None


filename = sys.argv[1]

# Parse argument
n, dist, adj = parse(filename)

m = Model()

# n cities, n timestep 
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
for t in range(n):
    m.addConstr(vars.sum('*',t) == 1)

# 3. save connectivity for lazy constraints

# opt
goal = QuadExpr()
for t in range(n-1):
    for i in range(n):
        for j in range(n):
            w = dist[i][j]
            goal.add(vars[(i,t)] * vars[(j,t+1)] * w)

m._vars = vars
m.setObjective(goal, GRB.MINIMIZE) 

m.optimize(subtourelim)

print('')

print('Optimal cost: %g' % m.objVal)
print("print out solution in ascending timestep")
vals = m.getAttr('x', vars)
for timestep in range(n):
    for i in range(n):
            if (vals[(i,timestep)] > 0):
                print("timestep ", timestep, ": ", i)
print('')