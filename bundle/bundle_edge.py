# bundle edge 

# 1. each bundle visited at least once 
# 2. variable: one for each (node,time), one for each bundle 


from parse import parse_node_dist,parse_bundle,get_bundle_dict
import sys 
from gurobipy import *

# Parse argument: need new input format
node_file = sys.argv[1]
bundle_file = sys.argv[2]
nodes, dist, adj = parse_node_dist(node_file)
bundles = parse_bundle(bundle_file)
bd = get_bundle_dict(bundles) # bundle dictionary {node: bundle}
print("nodes: ", nodes)
print("dist: ", dist)
print("adj: ", adj)
print("bundles: ", bundles)
print("bd: ", bd)

# create model 
m = Model()
B = len(bundles) # number of bundles 
T = 4 # total time step, minimum value is B
n = len(nodes) # number of nodes 
print("B = ", B)
print("==============")

# u, v, t
vars = m.addVars(nodes,nodes, T,vtype=GRB.BINARY, name="e")
vars = m.addVars(B, T,vtype=GRB.BINARY, name="b")
m.update()

# 1. each edge is visited exactly once 
for u in nodes:
    for v in adj[u]:
        m.addConstr(vars.sum(u,v,'*') <= 1)

# 2. each timestep visits only one edge
for t in range(T):
    m.addConstr(vars.sum('*','*', t) == 1)

# 3.1 once leave a bundle, cannot comeback 

for b in range(B):
    for t in range(T-1):
        c = LinExpr()
        # b_t => b_t+1
        c.add(1 - vars_b[(b, t)]) 
        c.add(vars_b[(b,t+1)])
        m.addConstr(c, GRB.GREATER_EQUAL, 1)

# 3.2 if u,v in different bundle 
for u in nodes:
    for v in adj[u]:
        bu = db[u]
        bv = db[v]
        if bu != bv:
            # e_uv_t = 1 => b_u_t = 1 & b_v_t+1 = 0
            # e_uv_t = 0 OR (b_u_t - b_v_t+!)
            for t in range(T-1):
                c = LinExpr()
                c.add(1-vars[u,v,t]) # if e(u,v,t) = 1 
                c.add(1 - vars[bu,t]) # want b(bu,t) = 0
                c.add(vars[bv,t+1]) 
                m.addConstr(c, GRB.GREATER_EQUAL, 2)
        else:
            # same bundle 
            for t in range(T-1):
                c = LinExpr()
                c.add(1-vars[u,v,t]) # if e(u,v,t) = 1 
                c.add(1 - vars[bu,t]) # want b(bu,t) = 0
                c.add(1-vars[bv,t+1])  
                m.addConstr(c, GRB.GREATER_EQUAL, 2)



# opt
goal = QuadExpr()
for t in range(T):
    for u in range(n):
        for v in range(n):
            w = dist[i][j]
            goal.add(vars[(u,v,t)] * w)

m._vars = vars
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