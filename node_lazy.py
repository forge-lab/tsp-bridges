"""
Yinglan Chen
March 2019

======================================
           DOCUMENTATION
======================================

VARIABLES:
x_t_i = 1 if city i is visited at timestep t , represented as a tuple (i,t)
           range: node i in [0,n-1], timestep t in [0, n-1], inclusive

CONSTRAINTS:
- optional: if fix start and end point, x_0_start = 1, x_{n}_end = 1
- each city is visited once: forall i, sum_t x_t_i = 1
- each timestep visits only one city: forall t, sum_i x_t_i = 1
- connectivity (lazy): for each t, for each node n, x_n_t => OR x_nn_{t+1} where nn are neighbors 


OBJECTIVE: 
- sum of t from 0 to n-1: x_i_t * x_j_t+1 * d_ij

Lazyness:
if disconnect at timestep t, force connectivity at this timestep and city 

"""

import sys
import math
import random
import itertools
from gurobipy import *
from parse import parse

# lazy
# check the shortest subtour, and add one more constraint

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


# Given a tuplelist of city timestep, validate connectivity 
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