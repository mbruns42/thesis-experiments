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
        ax.text(rect.get_x() + rect.get_width()*offset[xpos], 1.01*height,
                '{:,}'.format(height), ha=ha[xpos], va='bottom')

def plot(bench, chaEdges, chaTimes, sparkEdges, sparkTimes):
    ind = np.arange(len(bench))  # the x locations for the groups
    width = 0.3  # the width of the bars

    fig, ax = plt.subplots()
    bar1 = ax.bar(ind - width/2, chaTimes, width, color='SkyBlue', label='CHA')
    bar2 = ax.bar(ind + width/2, sparkTimes, width, color='LightGreen', label='Spark')
    #bar3 = ax.bar(ind + width/2, chaEdges, width, color='Blue', label='CHA Edges')
    #bar4 = ax.bar(ind + width*1.5, sparkEdges, width, color='Black', label='Spark Edges')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Time in ms')
    ax.set_title('Runtime for call graph construction')
    ax.set_xticks(ind)
    ax.set_xticklabels(bench)
    ax.legend()
    autolabel(ax, bar1)
    autolabel(ax, bar2)
    #autolabel(ax, bar3)
    #autolabel(ax, bar4)
    #plt.yscale('symlog')
    plt.show()

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