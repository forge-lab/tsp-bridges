# Yinglan Chen 

# documentation
# variables: x_t_i = 1 if city i is visited at timestep t , represented as a tuple (i,t)
#            range: node i in [0,n-1], timestep t in [0, n-1]

# constraints:
# - optional: if fix start and end point, x_0_start = 1, x_{n}_end = 1
# - each city is visited once: forall i, sum_t x_t_i = 1
# - each timestep visits only one city: forall t, sum_i x_t_i = 1
# - connectivity: for each t, for each node n, x_n_t => OR x_nn_{t+1} where nn are neighbors 

# objective:
# - sum of t from 0 to n-1: x_i_t * x_j_t+1 * d_ij

import sys
import math
import random
import itertools
from parse import parse
from gurobipy import *


filename = sys.argv[1]

# Parse argument
n, dist, adj = parse(filename)

# create model 
m = Model()

# n cities, n timestep 
vars = m.addVars(n,n,vtype=GRB.BINARY, name="e")

# 0. if fix start and end 
start = 1
end = 3
# m.addConstr(vars[start,0], GRB.EQUAL, 1)
# m.addConstr(vars[end,n], GRB.EQUAL, 1)

# 1. each city is visited once 
for city in range(n):
    m.addConstr(vars.sum(city,'*') == 1)

# 2. each timestep visits only one city
for t in range(n):
    print(vars.sum('*',t))
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
        # bug, wrong indentation before, add constr after loop through neighbors
        # print(constr)
        c = m.addConstr(constr, GRB.GREATER_EQUAL, 1)
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

print('')

print('Optimal cost: %g' % m.objVal)
print("print out solution in ascending timestep")
vals = m.getAttr('x', vars)
for timestep in range(n):
    for i in range(n):
            if (vals[(i,timestep)] > 0):
                print("timestep ", timestep, ": ", i)
print('')