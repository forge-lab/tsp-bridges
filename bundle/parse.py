import sys

def parse_node_dist(filename):
    nodes = []
    dist = dict() # dist[(i,j)] 
    adj = dict()  # adj[i]
    with open(filename) as f:
        # read first line 
        l = f.readline()
        n = int(l[:-1])
        # read the second line for node ids 
        l = f.readline()
        entries = l.split()
        for i in range(1, n+1): # ignore the first dummy 
            nodes.append(int(entries[i]))
        # now we have all node ids in set node 
        for row in range(n):
            l = f.readline()
            entries = l.split()
            u = int(entries[0])
            # adj[u]
            u_neighbors = []
            d = list(map(int, entries[1:]))
            for vi in range(n):
                v = nodes[vi]
                if (d[vi] != -1 and v != u):
                    dist[(u,v)] = d[vi]
                    u_neighbors.append(v)
            adj[u] = u_neighbors
    return nodes, dist, adj

def parse_bundle(filename):
    bundles = []
    with open(filename) as f:
        l = f.readline()
        while (l != ""):
            entries = l.split(",")
            bundles.append(list(map(int, entries)))
            l = f.readline()
    return bundles

def get_bundle_dict(bundles):
    d = dict()
    for b_i in range(len(bundles)):
        b = bundles[b_i]
        for member in b:
            d[member] = b_i
    return d


def main():
    node_dist_file = sys.argv[1]
    bundle_corres_file = sys.argv[2]
    parse_node_dist(node_dist_file)
    parse_bundle(bundle_corres_file)

# if __name__ == '__main__':
#     main()