import os
import sys

import pandas as pd


def readData(dirname):
    raw_df = []
    for file in os.listdir(dirname):
        if file.endswith(".csv"):
            data_from_this_csv = pd.read_csv(os.path.join(dirname, file), sep=';')
            raw_df.append(data_from_this_csv)
    return raw_df





def main(dirname):
    rawData = readData(dirname)
    print(rawData)

if __name__== "__main__":
    main(sys.argv[1])