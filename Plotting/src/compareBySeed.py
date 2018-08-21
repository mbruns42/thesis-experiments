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


def plot_timeouts(data):
    over_ten_minutes = data.loc[data['AnalysisTimes']>600_000]
    print("Over 10 minutes: ", over_ten_minutes.shape[0])

    timedout = data.loc[data['Timedout']]
    print("Average time for timeout:", str(int((timedout[['AnalysisTimes']].mean()))))
    if (timedout.empty):
        print("Data contains no timeouts.")
    else:
        print("Number of runs that timed out:", timedout.shape[0])
        timeouts_per_cgmode = timedout[['CallGraphMode', 'Timedout']].groupby('CallGraphMode').aggregate('sum')
        ax = timeouts_per_cgmode.plot(kind='bar', rot=10, legend=False)
        for p in ax.patches:
            ax.annotate(str(int(p.get_height())), (p.get_x() * 1 + 0.15, p.get_height() * 1.005))
        ax.set_ylabel('Timed out analysis runs')
        plt.savefig("TimeoutsPerCGMode.pdf", dpi = 300)
        plt.close()

def plot_averages_runtimes(data):
    averages = data[['AnalysisTimes_cha', 'AnalysisTimes_cha_dd',
                                  'AnalysisTimes_spark', 'AnalysisTimes_spark_dd']].mean(axis=0)
    #Convert runtime to seconds
    averages = averages/1000
    ax = averages.plot(kind='bar', rot=10)
    ax.set_ylabel('Average runtime in seconds')
    for p in ax.patches:
        ax.annotate('{:.{prec}f}'.format(p.get_height(), prec=1), (p.get_x() * 1 + 0.15, p.get_height() * 1.005))
    plt.savefig("RuntimePerCGMode.pdf", dpi = 300)


def analyze_difference_in_seeds(raw_data):
    cha_dd_seeds = raw_data[raw_data['CallGraphMode'] == 'CHA_DD'][['Rule', 'Seed', 'SeedStatement',
                                                                    'SeedMethod', 'SeedClass']]
    spark_seeds = raw_data[raw_data['CallGraphMode'] == 'SPARK'][['Rule', 'Seed', 'SeedStatement',
                                                                  'SeedMethod', 'SeedClass']]



def main(dirname):
    raw_data = read_data(dirname)

    # Drop columns without useful information. Analysis always says "ideal" and there is an emtpy column
    raw_data = raw_data.drop(columns=['Analysis', 'Unnamed: 26'])

    #Drop rows of which duplicates of seeds and call graph mode exist (those are not analysis of actual benchmarks)
    raw_data = raw_data.drop_duplicates(subset= ['Rule', 'Seed', 'SeedStatement', 'SeedMethod', 'SeedClass',
                                                     'CallGraphMode'], keep=False)
    plot_timeouts(raw_data)

    analyze_difference_in_seeds(raw_data)

    # Limit maximum analysis time to 600_000 as this was our timeout
    raw_data['AnalysisTimes'] = raw_data['AnalysisTimes'].clip(upper=600_000)

    data = split_and_merge_data(raw_data)

    plot_averages_runtimes(data)


if __name__== "__main__":
    main(sys.argv[1])