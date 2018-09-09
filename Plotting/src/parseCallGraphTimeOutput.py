import re
import sys

import matplotlib.pyplot as plt
import numpy as np


# This script parses the output from the CallGraphTimer.
# All relevant lines are assumed to follow the scheme "! CALLGRAPHMODE,BENCHMARK,RUNTIME_IN_MS,EDGES_IN_GRAPH",
# e.g., "! CHA,antlr,18890,179968". Other lines will be ignored.
# Slashes at the beginning of the file may cause problems, so be sure not to include a first line, like "/bin/java .."
#
# Run with file containing output as only parameter, see example file callGraphTimes.txt, like
# python src/parseCallGraphTimeOutput.py callGraphTimes.txt

def plot(bench, cha_edges, cha_times, spark_edges, spark_times):
    """ Makes the bar chart and stores it to a high-res pdf
    """
    ind = np.arange(len(bench))  # the x locations for the groups
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    ax.bar(ind - width / 2, cha_times, width, color='C0', label='CHA')
    ax.bar(ind + width / 2, spark_times, width, color='C2', label='Spark')
    ax.set_ylabel('Runtime in milliseconds')
    ax.set_xticks(ind)
    ax.set_xticklabels(bench)
    plt.xticks(rotation=30)
    ax.legend()
    plt.savefig("Results/CallGraphRuntimes.pdf", dpi=300)
    plt.close()
    fig, ax = plt.subplots()

    ax.bar(ind - width / 2, cha_edges, width, color='C0', label='CHA')
    ax.bar(ind + width / 2, spark_edges, width, color='C2', label='Spark')
    ax.set_ylabel('Number of Edges')
    ax.set_xticks(ind)
    ax.set_xticklabels(bench)
    plt.xticks(rotation=30)
    ax.legend()
    plt.savefig("Results/CallGraphEdges.pdf", dpi=300)
    plt.close()


def parse_results(lines, bench, cha_times, cha_edges, spark_times, spark_edges):
    for line in lines:
        line = line.decode(encoding="utf-8", errors="strict")
        match = re.match("! (\w+),(\w+),(\d+),(\d+)", line)
        # Skip lines not detailing desired metrics
        if match is None:
            continue
        if match.group(1) == 'CHA':
            bench.append(match.group(2))
            cha_times.append(int(match.group(3)))
            cha_edges.append(int(match.group(4)))
        if match.group(1) == 'SPARK':
            spark_times.append(int(match.group(3)))
            spark_edges.append(int(match.group(4)))


def compute_average_factors(cha_edges, cha_times, spark_edges, spark_times):
    avg_cha = sum(cha_edges) / float(len(cha_edges))
    print("Average number of CHA edges: ", avg_cha)
    avg_spark = sum(spark_edges) / float(len(spark_edges))
    print("Average number of Spark edges: ", avg_spark)
    print("Factor of CHA edges to spark edges: ", (avg_cha / avg_spark))
    print()
    avg_cha = sum(cha_times) / float(len(cha_times))
    print("Average runtime for CHA: ", avg_cha)
    avg_spark = sum(spark_times) / float(len(spark_times))
    print("Average runtime for Spark: ", avg_spark)
    print("Factor of CHA runtime to spark runtime: ", (avg_cha / avg_spark))
    print()


def main(filename):
    with open(filename, 'rb') as file:
        lines = file.readlines()
    bench = []
    cha_times = []
    cha_edges = []
    spark_times = []
    spark_edges = []

    parse_results(lines, bench, cha_times, cha_edges, spark_times, spark_edges)
    plot(bench, cha_edges, cha_times, spark_edges, spark_times)
    compute_average_factors(cha_edges, cha_times, spark_edges, spark_times)
    # This prints out a latex table with results
    for i in range(len(bench)):
        print(bench[i], " & ", "{:,}".format(cha_times[i]), " & ", "{:,}".format(spark_times[i]), " & ",
              "{:,}".format(cha_edges[i]), " & ", "{:,}".format(spark_edges[i]), "\\\\")


if __name__ == "__main__":
    main(sys.argv[1])
