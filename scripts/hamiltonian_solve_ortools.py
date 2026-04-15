"""Simple Travelling Salesperson Problem (TSP) between cities."""

from ortools.sat.python import cp_model
import argparse

def create_data_model(filename="graph.txt"):
    """Reads the graph from a file."""
    """Adjacency list of unweighted undirected graph (0: no edge, 1: edge)"""
    """Written in graph format"""
    """Example format:
        p edge 64 125
        e 1 2
        ...
        assume from 1 to 64
    """
    with open(filename, "r") as file:
        lines = file.readlines()
        adjacency_list = []
        for line in lines:
            if line.startswith("p edge"):
                parts = line.strip().split()
                size = int(parts[2])
                adjacency_list = [[] for _ in range(size)]
            elif line.startswith("e"):
                parts = line.strip().split()
                u, v = int(parts[1]) - 1, int(parts[2]) - 1
                adjacency_list[u].append(v)
                adjacency_list[v].append(u)
    return adjacency_list, size


def print_solution(solver, arc_vars, num_nodes, adjacency_list):
    """Prints solution on console."""
    current_node = 0
    route = [current_node]

    while True:
        # Find the next node in the cycle
        for j in adjacency_list[current_node]:
            # If the boolean variable for this directed arc is true
            if solver.Value(arc_vars[(current_node, j)]):
                next_node = j
                break

        route.append(next_node)
        current_node = next_node

        # Stop once we have returned to the starting node
        if current_node == 0:
            break

    plan_output = "Route for vehicle 0:\n "
    plan_output += " -> ".join(map(str, route))
    print(plan_output)


def main(input_file):
    """Entry point of the program."""
    # Instantiate the data problem.
    instance = input_file  # Change this to your graph file
    data, size = create_data_model(instance)

    model = cp_model.CpModel()
    arc_vars = {}
    arcs = []

    for i in range(size):
        for j in data[i]:
            # Create a boolean variable that is True if the arc (i -> j) is used in the cycle
            lit = model.NewBoolVar(f'arc_{i}_{j}')
            arcs.append([i, j, lit])
            arc_vars[(i, j)] = lit

    # The AddCircuit constraint forces the selected arcs to form a single cycle covering all nodes in the graph exactly once.
    if arcs:
        model.AddCircuit(arcs)
    else:
        print("The graph has no edges. Not Hamiltonian.")
        return

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Print solution on console.
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print_solution(solver, arc_vars, size, data)
        print("The graph is Hamiltonian.")
    else:
        print("The graph is NOT Hamiltonian.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve Hamiltonian Path Problem using OR-Tools.")
    parser.add_argument("-i", "--input_file", type=str, required=True, help="Path to the input graph file.")
    args = parser.parse_args()
    input_file = args.input_file

    main(input_file)
