# node with bundle
from parse import parse_node_dist,parse_bundle,get_bundle_dict
import sys 
from gurobipy import *

def subtourelim(model, where):
    if where == GRB.Callback.MIPSOL:
        # make a list of edges selected in the solution
        vals = model.cbGetSolution(model._vars)
        selected = tuplelist((i,t) for i,t in model._vars.keys() if vals[(i,t)] > 0.5)
        print("selected: ", selected)
        # find the shortest cycle in the selected edge list
        tour = subtour(selected) # None indicate success
        print("tour: ", tour)
        if tour != None:
            broken = tour[0]
            broken2 = tour[1]
            timestep = tour[2]
            print("broken at vertices ", broken, broken2, "at timestep ", timestep)
            
            # node t implies neighbor t+1
            # x_t => (n1_t+1 or n2_t+1)
            # (1-x_t) or n1_t+1 or n2_t+1 .. 
            constr = LinExpr()
            neighbors = adj[broken]
            try:
                constr.add(1 - model._vars[broken, timestep])
                for n in neighbors: 
                    constr.add(model._vars[(n, timestep+1)])
                print("newly added: ",constr)
                model.cbLazy(constr >= 1)


            # tried to enforce all timestep but impossible
            except GurobiError as e:
                print('Error code ' + str(e.errno) + ": " + str(e))


# Given a tuplelist of city timestep, validate connectivity 
def subtour(steps):
    for t in range(n-1):
        curr = steps.select("*",t)[0][0]
        next = steps.select("*",t+1)[0][0]
        if (curr,next) not in dist:
            return (curr, next, t)
    return None



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
T = 5 # total time step, minimum value is B
n = len(nodes) # number of nodes 
print("B = ", B)
print("==============")
# n cities, n timestep 
# instead of having 1 ~ n, want to have node_id 

vars_n = m.addVars(nodes,T,vtype=GRB.BINARY, name="x")
vars_b = m.addVars(B, T, vtype=GRB.BINARY, name="b")
m.update()


# 1. each node is visited at most once 
for city in nodes:
    # print(vars_n.sum(city,'*'))
    m.addConstr(vars_n.sum(city,'*') <= 1)

# 2. each timestep visits only one node
for t in range(T):
    # print(vars_n.sum('*',t))
    m.addConstr(vars_n.sum('*',t) == 1)

# 3. each bundle is visited at least once 
for b in range(B):
    m.addConstr(vars_b.sum(b, '*') >= 1)

for t in range(T):
    m.addConstr(vars_b.sum('*', t) >= 1)

# 4. once leave a bundle, cannot comeback 
# once visited, always set to one 
for b in range(B):
    for t in range(T-1):
        c = LinExpr()
        # b_t => b_t+1
        c.add(1 - vars_b[(b, t)]) 
        c.add(vars_b[(b,t+1)])
        m.addConstr(c, GRB.GREATER_EQUAL, 1)

for x in nodes: # 7
    neighbors = adj[x]
    for n in neighbors: # 1
        if bd[x] == bd[n]: # within the same bundle 
            # x_t = 1 and n_t+1 = 1 => (b1_t = 0)
            # x_t = 0 or n_t+1 = 0 or (1 - b1_t == 1)
            for t in range(T-1):
                c = LinExpr()
                c.add(1 - vars_n[(x,t)])
                c.add(1 - vars_n[(n,t+1)])
                c.add(1 - vars_b[(bd[x], t)] - vars_b[(bd[n], t+1)]) # b = 0
                m.addConstr(c, GRB.GREATER_EQUAL, 1)
        else: 
            # x_t = 1 and n_t+1 = 1 => (b1_t = 1 and b2_t+1 = 0)
            # [not (x_t = 1 and n_t+1 = 1)] or ()
            # [x_t = 0 or n_t+1 = 0] or (b1_t = 0 and b2_t+1 = 1)
            # (1 - x_t) +(1 - n_t+1) + ( b1_t - b2_t+1 == 1) >= 1 
            for t in range(T-1): # 0
                c = LinExpr()
                c.add(1 - vars_n[x,t])
                c.add(1 - vars_n[n,t+1])
                c.add(vars_b[bd[x], t] -  vars_b[bd[n], t+1]) # b = 0 
                m.addConstr(c, GRB.GREATER_EQUAL, 1)



# opt
goal = QuadExpr()
for t in range(T-1):
    for i in nodes:
        for j in adj[i]:
            if (i,j) in dist:
                w = dist[(i,j)]
                goal.add(vars_n[(i,t)] * vars_n[(j,t+1)] * w)

m._vars = vars_n
m.Params.lazyConstraints = 1
m.setObjective(goal, GRB.MINIMIZE) 

m.optimize(subtourelim)
# m.optimize()

print('')

print('Optimal cost: %g' % m.objVal)
print("print out solution in ascending timestep")
vals = m.getAttr('x', vars_n)
print(vals)
for timestep in range(T):
    for n in nodes:
        if (vals[(n,timestep)] > 0): 
            print("timestep ", timestep, ": ", n)
vals = m.getAttr('x', vars_b)
print(vals)
print('')