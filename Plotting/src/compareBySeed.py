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
    print("Number of CHA data rows:", cha_data.shape[0])
    cha_dd_data = data[data['CallGraphMode'] == 'CHA_DD'].drop(columns=['CallGraphMode'])
    print("Number of CHA DD data rows:", cha_dd_data.shape[0])
    spark_data = data[data['CallGraphMode'] == 'SPARK'].drop(columns=['CallGraphMode'])
    print("Number of SPARK data rows:", spark_data.shape[0])
    spark_dd_data = data[data['CallGraphMode'] == 'SPARK_DD'].drop(columns=['CallGraphMode'])
    print("Number of SPARK DD data rows:", spark_dd_data.shape[0])
    cha_vs_cha_dd = cha_data.merge(cha_dd_data, on=['Rule', 'Seed', 'SeedStatement', 'SeedMethod', 'SeedClass'],
                                   how='outer', suffixes=('_cha', '_cha_dd'))
    cha_vs_cha_dd_vs_spark = cha_vs_cha_dd.merge(spark_data, on=['Rule', 'Seed', 'SeedStatement', 'SeedMethod',
                                                                 'SeedClass'], how='outer')
    all_data_per_seed = cha_vs_cha_dd_vs_spark.merge(spark_dd_data, on=['Rule', 'Seed', 'SeedStatement', 'SeedMethod',
                                                            'SeedClass'],how='outer',suffixes=('_spark','_spark_dd'))
    print("Columns of final data: ", list(all_data_per_seed))
    print("Number of data rows in data merged by seed:", all_data_per_seed.shape[0])
    return all_data_per_seed


def handle_timeouts(data):
    timedout = data.loc[data['Timedout']]
    if (timedout.empty):
        print("Data contains no timeouts.")
    else:
        print("Number of runs that timed out:", timedout.shape[0])
        print("Call Graph Algorithms leading to timeout:", timedout[['CallGraphMode', 'Seed']].groupby('CallGraphMode').count())
        timeouts_per_cgmode = timedout[['CallGraphMode', 'Timedout']].groupby('CallGraphMode').aggregate('sum')
        ax = timeouts_per_cgmode.plot(kind='bar', rot=10, legend=False)
        for p in ax.patches:
            ax.annotate(str(int(p.get_height())), (p.get_x() * 1.005, p.get_height() * 1.005))
        ax.set_ylabel('Timed out analysis runs')
        plt.show()
        print ("Dropping timed out analysis runs from here on.")
        data = data.drop(data['Timedout'])
        data = data.drop(labels=['Timedout'], axis=1)
    return data


def main(dirname):
    raw_data = read_data(dirname)
    data = raw_data.drop(columns=['Analysis', 'Unnamed: 26'])

    data = handle_timeouts(data)
    all_data_per_seed = split_and_merge_data(data)

    averages = all_data_per_seed[['AnalysisTimes_cha', 'AnalysisTimes_cha_dd',
                                  'AnalysisTimes_spark', 'AnalysisTimes_spark_dd']].mean(axis=0)
    #Convert runtime to seconds
    averages = averages/1000
    ax = averages.plot(kind='bar', rot=10)
    ax.set_ylabel('Average runtime in seconds')
    for p in ax.patches:
        ax.annotate('{:.{prec}f}'.format(p.get_height(), prec=1), (p.get_x() * 1.005, p.get_height() * 1.005))
    plt.show()


if __name__== "__main__":
    main(sys.argv[1])