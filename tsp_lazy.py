#!/usr/bin/python

# Copyright 2018, Gurobi Optimization, LLC

# Solve a traveling salesman problem on a randomly generated set of
# points using lazy constraints.   The base MIP model only includes
# 'degree-2' constraints, requiring each node to have exactly
# two incident edges.  Solutions to this model may contain subtours -
# tours that don't visit every city.  The lazy constraint callback
# adds new constraints to cut them off.

import sys
import math
import random
import itertools
from gurobipy import *

# Callback - use lazy constraints to eliminate sub-tours

def subtourelim(model, where):
    
    if where == GRB.Callback.MIPSOL:
        # make a list of edges selected in the solution
        vals = model.cbGetSolution(model._vars)
        selected = tuplelist((i,j) for i,j in model._vars.keys() if vals[i,j] > 0.5)

        # find the shortest cycle in the selected edge list
        tour = subtour(selected)
        if len(tour) < n:
            constr = LinExpr()
            for i,j in itertools.combinations(tour, 2): 
                constr.add(model._vars[i,j])
                constr.add(model._vars[j,i])
            
            # add subtour elimination constraint for every pair of cities in tour
            model.cbLazy(constr<= len(tour)-1)


# Given a tuplelist of edges, find the shortest subtour

def subtour(edges):

    unvisited = list(range(n))
    cycle = range(n+1) # initial length has 1 more city
    while unvisited: # true if list is non-empty
        thiscycle = []
        neighbors = unvisited

        while neighbors:
            current = neighbors[0]
            thiscycle.append(current)
            unvisited.remove(current)
            neighbors = [j for i,j in edges.select(current,'*') if j in unvisited]
        if len(thiscycle) < len(cycle):
            cycle = thiscycle
    return cycle


# Parse argument


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


n,d,adj = parse(sys.argv[1])

dist = dict()
for i in range(n):
    for j in range(n):
        if (i != j): dist[(i,j)] = d[i][j]
m = Model()

# Create variables
foo_dict = {(i,j):0 for i in range(n) for j in range(n)}

vars = m.addVars(dist.keys(), obj=dist, vtype=GRB.BINARY, name='e')
# for i,j in vars.keys():
#     vars[j,i] = vars[i,j] # edge in opposite direction

# You could use Python looping constructs and m.addVar() to create
# these decision variables instead.  The following would be equivalent
# to the preceding m.addVars() call...
#
# vars = tupledict()
# for i,j in dist.keys():
#   dist[i][j], ith point, and jth point 
#   vars[i,j] = m.addVar(obj=dist[i,j], vtype=GRB.BINARY,
#                        name='e[%d,%d]'%(i,j))


# Add degree-2 constraint

# m.addConstrs(vars.sum(i,'*') == 2 for i in range(n))
# Using Python looping constructs, the preceding would be...
#

for i in range(n):
    expr1 = LinExpr()
    expr2 = LinExpr()
    for j in range(n):
        if (i != j): 
            expr1.add(vars[i,j])
            expr2.add(vars[j,i])
    m.addConstr(expr1 == 1)
    m.addConstr(expr2 == 1)


# Optimize model
m._vars = vars
m.Params.lazyConstraints = 1
m.optimize(subtourelim)

vals = m.getAttr('x', vars)
selected = tuplelist((i,j) for i,j in vals.keys() if vals[i,j] > 0.5)

tour = subtour(selected)
# assert len(tour) == n

print('')
print('Optimal tour: %s' % str(tour))
print('Optimal cost: %g' % m.objVal)
print('')