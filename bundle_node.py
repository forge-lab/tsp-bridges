# node with bundle
from parse import parse

# Parse argument: need new input format
filename = sys.argv[1]
n, dist, adj = parse(filename)

# create model 
m = Model()
B = 5 # number of bundles 
T = 10 # total time step 
N = 5 # number of nodes 
bd = dict() # bundle dictionary {node: bundle}

# n cities, n timestep 
vars_n = m.addVars(n,n,vtype=GRB.BINARY, name="x")
vars_b = m.addVars(bundles, vtype=GRB.BINARY, name="b")


# 1. each node is visited at most once 
for city in range(n):
    m.addConstr(vars.sum(city,'*') <= 1)

# 2. each timestep visits only one node
for t in range(n):
    m.addConstr(vars.sum('*',t) == 1)

# 3. once leave a bundle, cannot comeback 
for b in range(B-1):
	# init constr
	c = LinExpr()
	for t in range(T-1):
		c.add(1 - vars[b, t])
	# now t is T -1 
	c.add(vars[b,t])
	m.addConstr(c, GRB.GREATER_EQUAL, 2)

for x in range(n):
	neighbors = adj[x]
	for n in range(neighbors):
		if bd[x] == bd[n]:
			for t in range(T-1):
				c = LinExpr()
				c.add(1 - vars[x,t] - vars[n,t+1])
				c.add(1-vars[bd[x], t]) # b = 0 
				c.add(1 - vars[bd[n], t+1]) # b = 0
				m.addConstr(c, GRB.GREATER_EQUAL, 3)
		else:	
			for t in range(T-1):
				c = LinExpr()
				c.add(1 - vars[x,t] - vars[n,t+1])
				c.add(1-vars[bd[x], t]) # b = 0 
				c.add(vars[bd[n], t+1]) # b = 1
				m.addConstr(c, GRB.GREATER_EQUAL, 3)


# opt
goal = QuadExpr()
for t in range(n-1):
    for i in range(n):
        for j in range(n):
            w = dist[i][j]
            goal.add(vars[(i,t)] * vars[(j,t+1)] * w)

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