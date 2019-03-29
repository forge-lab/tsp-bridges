# Yinglan Chen 

# documentation
# variables: e_uv_t = 1 if edge uv is visited at timestep t , represented as a triple (u,v,t)
#            range: node u,v in [0,n-1], timestep t in [0, n-2], inclusive

# constraints:
# - optional: if fix start and end point, 
#             sum_nb e_{start,nb}_0 = 1, where nb's are start's neighbors
#             sum_nb e_{end, nb}_t-2 = 1, where nb's are end's neighbors
# - each time step visits exactly one edge: 
#   forall t, sum_uv e_uv_t = 1
# - optional: each edge is visited at most once [covered by the next constraints]
#   forall (u,v), sum_t e_uv_t <= 1, t in range(n-1)
# - each node (not start and end) is visited exactly once : 
#   fix node n, define nn to be n's neighbors
#   sum_{nn,t} e_{n,nn}_t + e_{nn,n}_t = 1
# - connectivity: 
#   for t and edge (n, nb), e_{n,nb}_t => OR e_{nb, nbb}_{t+1}

# objective:
# - sum of all t and uv: e_uv_t * d_uv

import sys
import math
import random
import itertools
from gurobipy import *
from parse import parse

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

    # Create variables, time step 0 ~ n-2
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