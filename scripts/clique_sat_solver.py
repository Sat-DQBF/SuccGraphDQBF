# pip install python-sat
from pysat.formula import CNF
from pysat.card import CardEnc
from pysat.solvers import Minisat22
from pysat.solvers import Cadical195

import argparse

def parse_graph_file(filename):
    """
    Parse a graph file in DIMACS-like edge format:
    Lines starting with 'p' define problem: p edge <num_vertices> <num_edges>
    Lines starting with 'e' define edges: e <vertex1> <vertex2>

    Returns:
        n: number of vertices
        edges: set of (i,j) tuples with i<j
    """
    edges = set()
    n = 0
    num_edges = 0
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):  # skip comments or empty lines
                continue
            tokens = line.split()
            if tokens[0] == 'p':  # problem line
                if tokens[1] != 'edge':
                    raise ValueError(f"Unexpected format: {line}")
                n = int(tokens[2])
                num_edges = int(tokens[3])  # optional, we can ignore
            elif tokens[0] == 'e':
                i = int(tokens[1])
                j = int(tokens[2])
                if i > j:
                    i, j = j, i  # ensure i < j
                edges.add((i,j))
            else:
                raise ValueError(f"Unexpected line in graph file: {line}")
    if num_edges != 0 and len(edges) != num_edges:
        raise ValueError(f"Expected {num_edges} edges but found {len(edges)}")
    return n, edges


def encode_k_clique(n, edges, k):
    """
    Build CNF encoding to check if graph with n vertices has a k-clique.
    Vertices are 1..n
    edges is a set of (i,j) pairs with i<j
    """

    # Boolean variables: v_i = vertex i is in the clique
    # We'll use DIMACS convention: variable IDs are 1..n
    v = list(range(1, n+1))

    cnf = CNF()

    # --- (1) Non-edge exclusion ---
    all_pairs = set((min(i,j), max(i,j)) for i in range(1,n) for j in range(i+1,n+1))
    non_edges = all_pairs - edges
    for (i,j) in non_edges:
        cnf.append([-v[i-1], -v[j-1]])

    # --- (2) Cardinality constraint: exactly k chosen ---
    lits = v  # all vertex variables
    # at-least-k
    amk = CardEnc.atleast(lits, bound=k, encoding=1)
    cnf.extend(amk.clauses)

    # at-most-k
    # next_id = amk.nv  # avoid aux var collision
    # amk2 = CardEnc.atmost(lits, bound=k, encoding=1, top_id=next_id)
    # cnf.extend(amk2.clauses)

    return cnf

def solve_k_clique_with_cadical(n, edges, k):
    cnf = encode_k_clique(n, edges, k)

    with Cadical195(bootstrap_with=cnf.clauses) as solver:
        sat = solver.solve()
        print(sat)
        if sat:
            model = solver.get_model()
            clique = [i for i in range(1,n+1) if model[i-1] > 0]  # keep positives
            return clique
        else:
            return None

def solve_k_clique(n, edges, k):
    cnf = encode_k_clique(n, edges, k)

    with Minisat22(bootstrap_with=cnf.clauses) as solver:
        sat = solver.solve()
        print(sat)
        if sat:
            model = solver.get_model()
            clique = [i for i in range(1,n+1) if model[i-1] > 0]  # keep positives
            return clique
        else:
            return None

# --------------------------
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="k-Clique SAT solver")
    parser.add_argument("-k", type=int, default=3, help="Size of clique to find", required=True)
    parser.add_argument("--graph_file", type=str, help="Input graph file", required=True)
    parser.add_argument("--solver", type=str, choices=["minisat", "cadical"], default="cadical", help="SAT solver to use")
    args = parser.parse_args()
    k = args.k
    graph_file = args.graph_file
    solver_choice = args.solver

    n, edges = parse_graph_file(graph_file)
    print(f"Graph has {n} vertices and {len(edges)} edges")

    if solver_choice == "cadical":
        print("Using Cadical solver")
        clique = solve_k_clique_with_cadical(n, edges, k)
    else:
        print("Using Minisat solver")
        clique = solve_k_clique(n, edges, k)

    if clique:
        print(f"Found clique of size {k}: {clique}")
    else:
        print(f"No clique of size {k}")
