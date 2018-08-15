import re
import sys

import matplotlib.pyplot as plt
import numpy as np


def autolabel(ax, rects, xpos='center'):
    xpos = xpos.lower()  # normalize the case of the parameter
    ha = {'center': 'center', 'right': 'left', 'left': 'right'}
    offset = {'center': 0.5, 'right': 0.57, 'left': 0.43}  # x_txt = x + w*off

    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()*offset[xpos], 1.0*height,
                '{:,}'.format(height), ha=ha[xpos], va='bottom', fontsize=10)

def plot(bench, chaEdges, chaTimes, sparkEdges, sparkTimes):
    ind = np.arange(len(bench))  # the x locations for the groups
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    bar1 = ax.bar(ind - width/2, chaEdges, width, color='SkyBlue', label='CHA')
    bar2 = ax.bar(ind + width/2, sparkEdges, width, color='LightGreen', label='Spark')

    ax.set_ylabel('Number of edges')
    ax.set_xticks(ind)
    ax.set_xticklabels(bench)
    plt.xticks(rotation=30)
    ax.legend()
    autolabel(ax, bar1)
    autolabel(ax, bar2)
    plt.savefig("CallGraphEdges.pdf", dpi = 300)
    plt.close()

def main(filename):
    with open(filename,'rb') as file:
        lines = file.readlines()
    bench = []
    chaTimes = []
    chaEdges = []
    sparkTimes = []
    sparkEdges = []

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
    plot(bench, chaEdges, chaTimes, sparkEdges, sparkTimes)
    for i in range(len(bench)):
        print(bench[i], " & ", "{:,}".format(chaTimes[i]), " & ", "{:,}".format(sparkTimes[i]), " & ",
              "{:,}".format(chaEdges[i]), " & ", "{:,}".format(sparkEdges[i]), "\\\\")


if __name__== "__main__":
    main(sys.argv[1])