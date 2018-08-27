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


def autolabel(ax, rects, xpos='center'):
    """ Writes the value the bar represents on top of the bar. Can be configured to arrange it to the left or right
        by passing the strings 'left' or 'right' as the xpos parameter. Labeling in the center of the bar is default.
    """
    xpos = xpos.lower()  # normalize the case of the parameter
    ha = {'center': 'center', 'right': 'left', 'left': 'right'}
    offset = {'center': 0.5, 'right': 0.57, 'left': 0.43}  # x_txt = x + w*off

    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()*offset[xpos], 1.0*height,
                '{:,}'.format(height), ha=ha[xpos], va='bottom', fontsize=10)

def plot(bench, chaEdges, chaTimes, sparkEdges, sparkTimes):
    """ Makes the bar chart and stores it to a high-res pdf
    """
    ind = np.arange(len(bench))  # the x locations for the groups
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    bar1 = ax.bar(ind - width/2, chaTimes, width, color='SkyBlue', label='CHA')
    bar2 = ax.bar(ind + width/2, sparkTimes, width, color='LightGreen', label='Spark')

    ax.set_ylabel('Runtime in milliseconds')
    ax.set_xticks(ind)
    ax.set_xticklabels(bench)
    plt.xticks(rotation=30)
    ax.legend()
    autolabel(ax, bar1)
    autolabel(ax, bar2)
    plt.savefig("CallGraphRuntimes.pdf", dpi = 300)
    plt.close()

def parseResults(lines, bench, chaTimes, chaEdges, sparkTimes, sparkEdges):
    for line in lines:
        line =  line.decode(encoding="utf-8", errors="strict")
        match = re.match("! (\w+),(\w+),(\d+),(\d+)", line)
        # Skip lines not detailing desired metrics
        if match is None:
            continue
        if match.group(1) == 'CHA':
            bench.append(match.group(2))
            chaTimes.append(int(match.group(3)))
            chaEdges.append(int(match.group(4)))
        if match.group(1) == 'SPARK':
            sparkTimes.append(int(match.group(3)))
            sparkEdges.append(int(match.group(4)))


def compute_average_factors(chaEdges, chaTimes, sparkEdges, sparkTimes):
    avgCHA = sum(chaEdges) / float(len(chaEdges))
    print("Average number of CHA edges: ", avgCHA)
    avgSpark = sum(sparkEdges) / float(len(sparkEdges))
    print("Average number of Spark edges: ", avgSpark)
    print("Factor of CHA edges to spark edges: ", (avgCHA/avgSpark))
    print()
    avgCHA = sum(chaTimes) / float(len(chaTimes))
    print("Average runtime for CHA: ", avgCHA)
    avgSpark = sum(sparkTimes) / float(len(sparkTimes))
    print("Average runtime for Spark: ", avgSpark)
    print("Factor of CHA runtime to spark runtime: ", (avgCHA/avgSpark))
    print()


def main(filename):
    with open(filename,'rb') as file:
        lines = file.readlines()
    bench = []
    chaTimes = []
    chaEdges = []
    sparkTimes = []
    sparkEdges = []

    parseResults(lines, bench, chaTimes, chaEdges, sparkTimes, sparkEdges)
    plot(bench, chaEdges, chaTimes, sparkEdges, sparkTimes)
    compute_average_factors(chaEdges, chaTimes, sparkEdges, sparkTimes)
    # This prints out a latex table with results
    for i in range(len(bench)):
        print(bench[i], " & ", "{:,}".format(chaTimes[i]), " & ", "{:,}".format(sparkTimes[i]), " & ",
              "{:,}".format(chaEdges[i]), " & ", "{:,}".format(sparkEdges[i]), "\\\\")


if __name__== "__main__":
    main(sys.argv[1])