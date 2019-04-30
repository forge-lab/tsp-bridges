# generate benchmakr from all_distance_matrix
# bridge_node_correspondence

# first output a file of bundles 
import json, random
import sys

print(sys.argv[1], sys.argv[2])
k = int(sys.argv[1])
test_id = int(sys.argv[2])

filename = "bridge_node_correspondence.csv"
all_dist = "all_distance_matrix.csv"

def parse_node_dist(filename):
    nodes = []
    dist = dict() # dist[(i,j)] 
    with open(filename) as f:
        # read the second line for node ids 
        l = f.readline()[:-1] # ignore "/n"
        entries = l.split(",")
        n = len(entries) - 1
        for i in range(1, len(entries)): # ignore the first dummy 
            nodes.append(int(entries[i][1:-1]))
        # now we have all node ids in set node 
        haha = True
        for row in range(n):
            l = f.readline()[:-1]
            entries = l.split(",")
            # First extract node u 
            u = int(entries[0][1:-1])
            d = []
            for vi in range(len(entries[1:])):
                d_str =  entries[1:][vi]
                v = nodes[vi]
                if d_str == "": 
                    dist[(u,v)] = 0
                else:

                    dist[(u,v)] = int(float(d_str))
    return nodes, dist


def find_bundles(filename):

    f = open(filename, "r")
    l = f.readlines()[1:] # ignore first line

    # use set to remove duplicates
    bundles = dict()
    for line in l:
        nid = int(line.split(",")[0])
        bid = int(line.split(",")[1])
        if (bid in bundles):
            bundles[bid].add(nid)
        else:
            bundles[bid] = set()
            bundles[bid].add(nid)

    # change to list for easy formatting 
    for bid in bundles:
        s = bundles[bid]
        bundles[bid] = list(s)

    with open('bundles.json', 'w') as outfile:  
        json.dump(bundles, outfile)

    return bundles

bundles = find_bundles(filename)
B = len(bundles)

def random_choose_bundles(bundles, k):
    sample = random.sample(bundles.keys(), k)
    result = []
    for bid in sample:
        result.append(bundles[bid])

    with open('test'+str(k)+'/bundle' + str(test_id), 'w') as outfile:
        for nodes in result:
            outfile.write(str(nodes)[1:-1] + "\n")
    return result

sample = random_choose_bundles(bundles, k)
print("sample:", sample)

def create_dist_matrix(sample):
    nodes = [node for bundle in sample for node in bundle]
    n = len(nodes)

    header = "0 "
    for node in nodes:
        header += str(node) + " "
    
    body = ""
    for node in nodes:
        body += str(node) + " "
        for v in nodes:
           
            body += str(all_dist[(node,v)]) + " "
        body = body[:-1] + "\n"


    print(str(n) + "\n" + header + "\n" +  body)
    with open('test'+str(k)+'/node' + str(test_id), 'w') as outfile:
        
        outfile.write(header + "\n" +  body)



all_nodes, all_dist = parse_node_dist("all_distance_matrix.csv")
create_dist_matrix(sample)
