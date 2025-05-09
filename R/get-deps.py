"""
Get a topological sorting of all the non-base dependencies for an R package.
My aim is to improve my quality of life when dealing with packaging of R packages for, e.g. writing easyconfig files.

I am pretty sure something better might already exist; I just didn't found it yet.
"""
from collections import defaultdict, deque

import rpy2.robjects as ro
from rpy2.robjects.packages import importr

# Import R's tools package
tools = importr("tools")

def get_package_dependencies(package_name):
    """
    Fetch the dependencies of an R package using tools::package_dependencies.
    """
    # Call tools::package_dependencies in R
    dependencies = ro.r(
        f"tools::package_dependencies('{package_name}', recursive=FALSE)"
    )

    print(f">>> Dependencies for {package_name}", dependencies)

    # Handle NULL return value using is.null
    if ro.r["is.null"](dependencies)[0]:
        return {package_name: []}

    # Convert R list to Python dictionary, handling NULL values
    dep_dict = {
        key: list(dependencies.rx2(key)) if not ro.r["is.null"](dependencies.rx2(key))[0] else []
        for key in dependencies.names
    }
    return dep_dict

def resolve_full_dependency_graph(initial_package):
    """
    Recursively fetch dependencies to build a complete dependency graph.
    """
    full_graph = defaultdict(list)
    queue = deque([initial_package])

    while queue:
        package = queue.popleft()
        if package not in full_graph:  # Avoid re-fetching dependencies
            deps = get_package_dependencies(package)
            full_graph.update(deps)
            for dep in deps.get(package, []):
                if dep not in full_graph:
                    queue.append(dep)

    return full_graph

def topological_sort(dependency_graph):
    """
    Perform topological sorting to determine the correct installation order.
    """
    # Build in-degree map
    in_degree = defaultdict(int)
    for deps in dependency_graph.values():
        for dep in deps:
            in_degree[dep] += 1

    # Initialize queue with nodes having zero in-degree
    queue = deque([node for node in dependency_graph if in_degree[node] == 0])
    sorted_order = []

    while queue:
        node = queue.popleft()
        sorted_order.append(node)

        # Reduce in-degree of neighbors
        for neighbor in dependency_graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check for cycles
    if len(sorted_order) != len(dependency_graph):
        raise ValueError("Dependency graph has a cycle!")

    # Reverse the order for most depended-on first
    return sorted_order[::-1]

def get_package_versions(packages):
    """
    Fetch the versions of the given R packages, excluding base packages.
    """
    versions = {}
    installed = ro.r("installed.packages()")

    # Debugging: Print the column names
    print(">>> COLUMN NAMES:", list(installed.colnames))

    # Access the "Version" column by its index
    try:
        version_column_index = list(installed.colnames).index("Version")
    except ValueError:
        print(">>> ERROR: 'Version' column not found in installed.packages()")
        return {pkg: "Unknown" for pkg in packages}

    # Check if a package is a base package
    is_base_pkg = ro.r("function(pkg) { pkg %in% rownames(installed.packages(priority = 'base')) }")

    # Create a mapping of package names to versions, excluding base packages
    for package in packages:
        try:
            if is_base_pkg(package)[0]:  # Exclude base packages
                print(f">>> SKIPPING BASE PACKAGE: {package}")
                continue

            row_index = list(installed.rownames).index(package)
            version = installed.rx(row_index + 1, version_column_index + 1)[0]
            versions[package] = version
        except ValueError:
            print(f">>> ERROR: Package '{package}' not found in installed.packages()")
            versions[package] = "Unknown"
        except Exception as e:
            print(f">>> ERROR ACCESSING VERSION FOR {package}:", e)
            versions[package] = "Unknown"

    return versions

def main():
    import sys
    package_name = sys.argv[1]
    print(f"Fetching dependencies for R package: {package_name}")

    # Resolve the full dependency graph
    dependency_graph = resolve_full_dependency_graph(package_name)

    # Solve the correct installation order
    try:
        install_order = topological_sort(dependency_graph)

        # Filter out base packages from the install order
        is_base_pkg = ro.r("function(pkg) { pkg %in% rownames(installed.packages(priority = 'base')) }")
        filtered_order = [pkg for pkg in install_order if not is_base_pkg(pkg)[0]]

        # Get versions for non-base packages
        versions = get_package_versions(filtered_order)

        # Prepare the result
        result = [(pkg, versions[pkg]) for pkg in filtered_order]
        print("Correct Installation Order with Versions:")
        for pkg in result:
            print(pkg)
    except ValueError as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
