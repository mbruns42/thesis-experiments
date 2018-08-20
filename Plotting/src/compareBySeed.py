import os
import sys

import pandas as pd


def read_data(dirname):
    raw_df = pd.DataFrame()
    for file in os.listdir(dirname):
        if file.endswith(".csv"):
            data_from_this_csv = pd.read_csv(os.path.join(dirname, file), sep=';', encoding='UTF-8')
            raw_df = raw_df.append(data_from_this_csv)
    return raw_df

def main(dirname):
    raw_data = read_data(dirname)
    data = raw_data.drop(columns=['Analysis', 'Unnamed: 26'])

    timedout = data.loc[data['Timedout']]
    if (timedout.empty):
        print("Data contains no timeouts.")
    else:
        print("Runs that timed out:", timedout)
    data = data.drop(data['Timedout'])

    print(data.dtypes)
    print(list(data))
    cha_data = data[data['CallGraphMode'] == 'CHA'].drop(columns=['CallGraphMode'])
    cha_dd_data = data[data['CallGraphMode'] == 'CHA_DD'].drop(columns=['CallGraphMode'])
    spark_data = data[data['CallGraphMode'] == 'SPARK'].drop(columns=['CallGraphMode'])
    spark_dd_data = data[data['CallGraphMode'] == 'SPARK_DD'].drop(columns=['CallGraphMode'])
    cha_dd_vs_spark = cha_dd_data.merge(spark_data, on=['Rule', 'Seed', 'SeedStatement', 'SeedMethod', 'SeedClass'],
                                        how='outer', suffixes=('_cha_dd', '_spark'), validate='one_to_one')
    print(list(cha_dd_vs_spark))
    print(cha_dd_vs_spark[['SeedStatement','AnalysisTimes_spark', 'AnalysisTimes_cha_dd']])




if __name__== "__main__":
    main(sys.argv[1])