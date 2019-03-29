# Yinglan Chen
# March 2019

# adapted from reference code of tsp on gurobi website
# https://www.gurobi.com/documentation/8.1/examples/tsp_py.html
# http://examples.gurobi.com/traveling-salesman-problem/
# change to be asymmetric and "visit each city once", not a round tour 

# definition(s)
# - subtours:
#   tours that don't visit every city.  The lazy constraint callback
#   adds new constraints to cut them off.

# documentation
# variables: x_ij = 1 if edge {i,j} in tour , represented as a tuple (i,j)
# constraints:
# - each node i has exactly one in-edge and one out-edge
# - for any non-empty subset S, summing all directed edge (i,j) in S, we should have
#   sum_{i,j} x_ij <= |S|-1, otherwise it forms a subtour 

import sys
import math
import random
import itertools
from gurobipy import *
from parse import parse

# Callback - use lazy constraints to eliminate sub-tours
# modified by myself
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
# no modification
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

def main():
    # parse
    global n, dist
    n,d,adj = parse(sys.argv[1])
    # create distance dictionary, with key = (i,j)
    dist = dict()
    for i in range(n):
        for j in range(n):
            if (i==j): continue
            if (d[i][j] != -1): dist[(i,j)] = d[i][j]
    m = Model()

    # add variables (i,j)
    vars = m.addVars(dist.keys(), vtype=GRB.BINARY, name='x')

    # constraint: each node i has exactly one in-edge and one out-edge
    for i in range(n):
        expr1 = LinExpr() # init empty expr
        expr2 = LinExpr()
        for j in range(n): 
            if (i != j): # enumerate all nodes other than i
                if ((i,j) in dist): expr1.add(vars[i,j])
                if ((j,i) in dist): expr2.add(vars[j,i])
        m.addConstr(expr1 == 1) # one out-edge
        m.addConstr(expr2 == 1) # one in-edge

    # setObjective
    goal = LinExpr()
    for i in range(n):
        for j in adj[i]:
            goal.add(vars[(i,j)] * dist[(i,j)])

    m.setObjective(goal, GRB.MINIMIZE) 


    # Optimize model
    m._vars = vars
    m.Params.lazyConstraints = 1

    m.optimize(subtourelim)

    vals = m.getAttr('x', vars)
    selected = tuplelist((i,j) for i,j in vals.keys() if vals[i,j] > 0.5)

    tour = subtour(selected)
    assert len(tour) == n

    print('')
    print('Optimal tour: %s' % str(tour))
    print('Optimal cost: %g' % m.objVal)
    print('')

if __name__ == '__main__':
    main()