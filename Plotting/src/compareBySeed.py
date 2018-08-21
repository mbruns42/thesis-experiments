import os
import sys

import matplotlib.pyplot as plt
import pandas as pd


def read_data(dirname):
    raw_df = pd.DataFrame()
    for file in os.listdir(dirname):
        if file.endswith(".csv"):
            data_from_this_csv = pd.read_csv(os.path.join(dirname, file), sep=';', encoding='UTF-8')
            raw_df = raw_df.append(data_from_this_csv)
    return raw_df

def split_and_merge_data(data):
    cha_data = data[data['CallGraphMode'] == 'CHA'].drop(columns=['CallGraphMode'])
    print("CHA Data ", cha_data.shape)
    cha_dd_data = data[data['CallGraphMode'] == 'CHA_DD'].drop(columns=['CallGraphMode'])
    print("CHA  DD Data ", cha_dd_data.shape)
    spark_data = data[data['CallGraphMode'] == 'SPARK'].drop(columns=['CallGraphMode'])
    print("SPARK Data ", spark_data.shape)
    spark_dd_data = data[data['CallGraphMode'] == 'SPARK_DD'].drop(columns=['CallGraphMode'])
    print("SPARK DD Data ", spark_dd_data.shape)
    cha_vs_cha_dd = cha_data.merge(cha_dd_data, on=['Rule', 'Seed', 'SeedStatement', 'SeedMethod', 'SeedClass'],
                                   how='outer', suffixes=('_cha', '_cha_dd'))
    cha_vs_cha_dd_vs_spark = cha_vs_cha_dd.merge(spark_data, on=['Rule', 'Seed', 'SeedStatement', 'SeedMethod',
                                                                 'SeedClass'], how='outer')
    all_data_per_seed = cha_vs_cha_dd_vs_spark.merge(spark_dd_data, on=['Rule', 'Seed', 'SeedStatement', 'SeedMethod',
                                                            'SeedClass'],how='outer',suffixes=('_spark','_spark_dd'))
    return all_data_per_seed

def main(dirname):
    raw_data = read_data(dirname)
    data = raw_data.drop(columns=['Analysis', 'Unnamed: 26'])

    timedout = data.loc[data['Timedout']]
    if (timedout.empty):
        print("Data contains no timeouts.")
    else:
        print("Runs that timed out:", timedout[['Rule','Seed','CallGraphMode']])
    data = data.drop(data['Timedout'])

    all_data_per_seed = split_and_merge_data(data)
    print("Columns of final data: ", list(all_data_per_seed))
    print("Size of final data:", all_data_per_seed.shape)

    averages = all_data_per_seed[['AnalysisTimes_cha', 'AnalysisTimes_cha_dd',
                                  'AnalysisTimes_spark', 'AnalysisTimes_spark_dd']].mean(axis=0)
    print(averages.shape)
    ax = averages.plot(kind='bar')
    ax.set_ylabel('Average runtime in milliseconds')
    for p in ax.patches:
        ax.annotate('{:,}'.format(p.get_height()), (p.get_x() * 1.005, p.get_height() * 1.005))
    plt.show()


if __name__== "__main__":
    main(sys.argv[1])