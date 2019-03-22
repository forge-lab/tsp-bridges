#!/usr/bin/python
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
            entries = l.split()
            print(entries)
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


def main():

    # Parse argument
    start = 1 # B
    end = 3   # D
    filename = sys.argv[1]
    n, dist, adj = parse(filename)
    # print(n)
    # print(dist)
    # print(adj)
    m = Model()

    # Create variables, time step 0 ~ n-1
    vars = m.addVars(n,n,n-1,vtype=GRB.BINARY, name="e")

    # Add constraints
    # 1.1 add start point constraint: E_BA_0 + E_BC_0 = 1
    start_pt = LinExpr()
    for neighbor in adj[start]:
        start_pt.add(vars[start, neighbor, 0])
    
    c_start = m.addConstr(start_pt , GRB.EQUAL, 1, name="fix_start")

    # 1.2 add end point constraint: 
    end_pt = LinExpr()
    for neighbor in adj[end]:
        end_pt.add(vars[neighbor, end, n-2])
    c_end = m.addConstr(end_pt, GRB.EQUAL, 1)

    # 2. exactly one edge at each time step 
    m.addConstrs(vars.sum('*', '*', t) == 1 for t in range(n-1))

    # 3. each node (not start and end) is visited exactly once 
    for node in range(n):
        if (node != start and node != end):
            constr = LinExpr()
            for neighbor in adj[node]:
                constr.add(vars.sum(node, neighbor, '*'))
                constr.add(vars.sum(neighbor, node, '*'))
            m.addConstr(constr, GRB.EQUAL, 2)

    # 4. connected path 
    for timestep in range(n-1-1):
        for node in range(n):
            neighbors = adj[node]
            for neighbor in neighbors: 
            # for each edge (node, neighbor)
                constr = LinExpr()
                constr.add(1-vars[node, neighbor, timestep])
                
                for nn in adj[neighbor]:
                    # for each possible next move, (neigbor, nn)
                    if nn == node: continue
                    constr.add(vars[neighbor, nn, timestep+1])

                # print("===", node, neighbor, constr)
                m.addConstr(constr, GRB.GREATER_EQUAL, 1)

    # 5. opt
    goal = LinExpr()
    for i in range(n):
        for j in adj[i]:
            for t in range(n-1):
                goal.add(vars[(i,j,t)] * dist[i][j])

    m.setObjective(goal, GRB.MINIMIZE) 
    # optimize: 
    m.optimize()


    # print(m.printAttr('x') )
    vals = m.getAttr('x', vars)
    print("print out solution in ascending timestep")
    for timestep in range(n-1):
        for i in range(n):
            for j in range(n):
                if (vals[(i,j,timestep)] > 0):
                    print("timestep ", timestep, ": ", i, j)

    print('')
    print('Optimal cost: %g' % m.objVal)
    print('')

if __name__ == '__main__':
    main()