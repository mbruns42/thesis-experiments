import os
import sys

import pandas as pd


def readData(dirname):
    raw_df = pd.DataFrame()
    for file in os.listdir(dirname):
        if file.endswith(".csv"):
            data_from_this_csv = pd.read_csv(os.path.join(dirname, file), sep=';')
            raw_df = raw_df.append(data_from_this_csv)
    return raw_df

def main(dirname):
    rawData = readData(dirname)
    data = rawData.drop(columns=['Analysis', 'Unnamed: 26'])
    #print(data.dtypes)
    timedout = data.loc[data['Timedout']]
    if (timedout.empty):
        print("Data contains no timeouts.")
    else:
        print("Runs that timed out:", timedout)


if __name__== "__main__":
    main(sys.argv[1])