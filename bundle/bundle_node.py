# Yinglan Chen
# March - April, 2019
from parse import parse_node_dist,parse_bundle,get_bundle_dict
import sys 
from gurobipy import *

def subtourelim(model, where):
    if where == GRB.Callback.MIPSOL:
        # make a list of edges selected in the solution
        vals = model.cbGetSolution(model._vars)
        bvals = model.cbGetSolution(model._bundles)
        selected = tuplelist((i,t) for i,t in model._vars.keys() if vals[(i,t)] > 0.5)
        # print("selected: ", selected)
        # print("bundles: ", bvals)
        # find the shortest cycle in the selected edge list
        tour = subtour(selected) # None indicate success
        if tour != None:
            broken = tour[0]
            broken2 = tour[1]
            timestep = tour[2]
            # print("broken at vertices ", broken, broken2, "at timestep ", timestep)
            
            # node t implies neighbor t+1
            # x_t => (n1_t+1 or n2_t+1)
            # (1-x_t) or n1_t+1 or n2_t+1 .. 
            constr = LinExpr()
            neighbors = adj[broken]
            try:
                constr.add(1 - model._vars[broken, timestep])
                for n in neighbors: 
                    constr.add(model._vars[(n, timestep+1)])
                # print("newly added: ",constr)
                model.cbLazy(constr >= 1)


            # tried to enforce all timestep but impossible
            except GurobiError as e:
                print('Error code ' + str(e.errno) + ": " + str(e))

# Given a tuplelist of city timestep, validate connectivity 
def subtour(steps):
    for t in range(T-1):
        curr = steps.select("*",t)[0][0]
        next = steps.select("*",t+1)[0][0]
        if (curr,next) not in dist:
            return (curr, next, t)
    return None

# each node is visited at most once 
def node_constr(m, vars_n):
    for city in nodes:
        m.addConstr(vars_n.sum(city,'*') <= 1)

def timestep_constr(m, vars_n):
    for t in range(T):
        # print(vars_n.sum('*' ,t))
        m.addConstr(vars_n.sum('*',t) == 1)

def bundle_visit_constr(m, vars_b):
    for b in range(B):
        m.addConstr(vars_b[(b, T-1)] == 1) # no bundle left alone 

def bundle_start_constr(m, vars_b):
    m.addConstr(vars_b.sum('*', 0) == 0)

def bundle_maintain_visited(m, vars_b):
    for b in range(B):
        for t in range(T-1):
            c = LinExpr()
            # b_t => b_t+1
            c.add(1 - vars_b[(b, t)]) 
            c.add(vars_b[(b,t+1)])
            m.addConstr(c, GRB.GREATER_EQUAL, 1)

def solve(T):
    # create model 
    m = Model()
    vars_n = m.addVars(nodes,T,vtype=GRB.BINARY, name="x")
    vars_b = m.addVars(B, T, vtype=GRB.BINARY, name="b")
    m.update()

    # 1. each node is visited at most once 
    node_constr(m, vars_n)
    
    # 2. each timestep visits only one node
    timestep_constr(m, vars_n)
    

    # 3. each bundle is visited at least once 
    bundle_visit_constr(m, vars_b)

    # at timestep 0, cannot have more than one "true"
    bundle_start_constr(m, vars_b)


    # 4. once leave a bundle, cannot comeback 
    # once visited, always set to one 
    bundle_maintain_visited(m, vars_b)

    for x in nodes:
        # neighbors = adj[x]
        # for n in neighbors:
        for n in nodes:
            if n == x: continue
            if bd[x] == bd[n]: # within the same bundle 
                # x_t = 1 and n_t+1 = 1 => (b1_t = 0 & b1_t+1 = 0)
                # !x_t  or !n_t+1  or (!b1_t and !b1_t+1)
                # c1: !x_t  or !n_t+1  or !b1_t 
                # c2: !x_t  or !n_t+1  or !b1_t+1

                for t in range(T-1):
                    c1 = LinExpr()
                    c2 = LinExpr()
                    c1.add(1 - vars_n[(x,t)])
                    c2.add(1 - vars_n[(x,t)])
                    c1.add(1 - vars_n[(n,t+1)])
                    c2.add(1 - vars_n[(n,t+1)])
                    c1.add(1 - vars_b[(bd[x], t)])
                    c2.add(1 - vars_b[(bd[n], t+1)])
                    m.addConstr(c1, GRB.GREATER_EQUAL, 1) # c1 and c2
                    m.addConstr(c2, GRB.GREATER_EQUAL, 1)


                # new !!!
                # iterate all bundles except bd[x]
                for b in range(B):
                    if b == bd[x]: continue
                    for t in range(T-1):
                        c = LinExpr()
                        # bug here should be: 
                        # x_t = 1 and n_t+1 = 1 and b_t = 0 => b_t+1 = 0
                        # !x_t or !n_t+1 or b_t or !b_t+1
                        c.add(1 - vars_n[(x,t)])
                        c.add(1 - vars_n[(n, t+1)])
                        c.add(vars_b[(b,t)])
                        c.add(1 - vars_b[(b, t+1)])
                        # print(c)
                        m.addConstr(c, GRB.GREATER_EQUAL, 1)

            else: 
                # x_t = 1 and n_t+1 = 1 => (b1_t+1 = 1 and b2_t+1 = 0)
                # !x_t or  !n_t+1 or (b1_t+1  and !b2_t+1)
                # c1: !x_t or !n_t+1 or b1_t+1 
                # c2: !x_t or !n_t+1 or !b2_t+1 
                for t in range(T-1):
                    c1 = LinExpr()
                    c2 = LinExpr()
                    c1.add(1 - vars_n[x,t])
                    c1.add(1 - vars_n[n,t+1])
                    c2.add(1 - vars_n[x,t])
                    c2.add(1 - vars_n[n,t+1])
                    c1.add(vars_b[bd[x], t+1])
                    # edge case: x_t = 1 and n_t+1 = 1 => (b1_t+1 = 1 and b2_t+1 = 1 and b2_t = 0)
                    if t == T-2: 
                        c2.add(vars_b[bd[n], t+1])
                        c3 = LinExpr()
                        c3.add(1 - vars_n[x,t])
                        c3.add(1 - vars_n[n,t+1])
                        c3.add(1 - vars_b[bd[n],t])
                        m.addConstr(c3, GRB.GREATER_EQUAL, 1)
                    else: c2.add(1 - vars_b[bd[n], t+1])
                    m.addConstr(c1, GRB.GREATER_EQUAL, 1)
                    m.addConstr(c2, GRB.GREATER_EQUAL, 1)


                for b in range(B):
                    if b == bd[x]: continue
                    if b == bd[n]: continue
                    for t in range(T-1):
                        c = LinExpr()
                        # x_t = 1 and n_t+1 = 1 and b_t = 0 => b_t+1 = 0
                        # !x_t or !n_t+1 or b_t or !b_t+!
                        # bug here, should add x = 1 and x = 1
                        c.add(1 - vars_n[(x,t)])
                        c.add(1 - vars_n[(n, t+1)])
                        c.add(vars_b[(b,t)])
                        c.add(1 - vars_b[(b, t+1)])
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
    m._bundles = vars_b
    m.Params.lazyConstraints = 1
    m.setObjective(goal, GRB.MINIMIZE) 

    m.optimize(subtourelim)

    print('')
    if (m.status == GRB.OPTIMAL):

        print('Optimal cost: %g' % m.objVal)
        print("print out solution in ascending timestep")
        vals = m.getAttr('x', vars_n)
        for timestep in range(T):
            for n in nodes:
                if (vals[(n,timestep)] > 0): 
                    print("timestep ", timestep, ": ", n)
        vals = m.getAttr('x', vars_b)
        print(vals)
        return True
    if (m.status == GRB.INFEASIBLE):
        print("INFEASIBLE")
        return False
    print('')

def main():
    # Parse argument: need new input format
    global nodes, dist, adj, B, bundles, bd, n, T
    node_file = sys.argv[1]
    bundle_file = sys.argv[2]
    nodes, dist, adj = parse_node_dist(node_file)
    bundles = parse_bundle(bundle_file)
    bd = get_bundle_dict(bundles) # bundle dictionary {node: bundle}
    B = len(bundles) # number of bundles 
    n = len(nodes) # number of nodes 
    # print("nodes: ", nodes)
    # print("dist: ", dist)
    # print("adj: ", adj)
    # print("bundles: ", bundles)
    # print("bd: ", bd)    
    # print("B = ", B)
    # print("==============")

    for T in range(B, n):
        print("############################## T = ", T)
        if solve(T): 
            print("SOLVED AT T = ", T)
            return
        
    print("TRIED all T, INFEASIBLE")
    return


if __name__ == '__main__':
    main()
