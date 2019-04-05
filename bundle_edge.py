# bundle edge 

# 1. each bundle visited at least once 
# 2. variable: one for each (node,time), one for each bundle 


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

# u, v, t
vars = m.addVars(n,n, T,vtype=GRB.BINARY, name="e")
vars = m.addVars(B, T,vtype=GRB.BINARY, name="b")

# 1. each edge is visited exactly once 
for u in range(n):
	for v in range(n):
    	m.addConstr(vars.sum(u,v,'*') <= 1)

# 2. each timestep visits only one edge
for t in range(n):
    m.addConstr(vars.sum('*','*', t) == 1)

# 3.1 once leave a bundle, cannot comeback 
for b in range(B-1):
	# init constr
	c = LinExpr()
	for t in range(T-1):
		c.add(1 - vars[b, t])
	# now t is T -1 
	c.add(vars[b,t])
	m.addConstr(c, GRB.GREATER_EQUAL, 2)

# 3.2 if u,v in different bundle 
for u in range(n):
	for v in range(n):
		bu = db[u]
		bv = db[v]
		if bu != bv:
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