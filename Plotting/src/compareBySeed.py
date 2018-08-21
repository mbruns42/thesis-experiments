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
    over_ten_minutes = data.loc[data['AnalysisTimes']>600]
    print("Over 10 minutes: ", over_ten_minutes.shape[0])

    timedout = data.loc[data['Timedout']]
    print("Average time for timeout:", str(int((timedout[['AnalysisTimes']].mean()))))
    if (timedout.empty):
        print("Data contains no timeouts.")
        return
    print("Number of runs that timed out:", timedout.shape[0])
    timeouts_per_cgmode = timedout[['CallGraphMode', 'Timedout']].groupby('CallGraphMode').aggregate('sum')
    makeBarPlot(timeouts_per_cgmode, 'Timed out analysis runs', 'TimeoutsPerCGMode.pdf')

    timeouts_per_rule = timedout[['Rule', 'Timedout']].groupby('Rule').aggregate('sum')
    makeBarPlot(timeouts_per_rule, 'Timed out analysis runs', 'TimeoutsPerRule.pdf')

    timeouts_per_rule_per_cg = timedout[['CallGraphMode','Rule', 'Timedout']].groupby(['CallGraphMode',
                                                                                       'Rule']).aggregate('sum')
    makeBarPlot(timeouts_per_rule_per_cg, 'Timed out analysis runs', 'TimeoutsPerRulePerCGMode.pdf', rotation=90,
                label_offset=0.1)


def plot_averages_runtimes(data):
    averages = data[['AnalysisTimes_cha', 'AnalysisTimes_cha_dd',
                                  'AnalysisTimes_spark', 'AnalysisTimes_spark_dd']].mean(axis=0)
    #Convert runtime to seconds
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
    print("Total seeds in CHA: ", cha_dd_seeds.shape[0])
    print("Total seeds in Spark: ", spark_seeds.shape[0])
    merged = cha_dd_seeds.merge(spark_seeds, indicator=True, how='outer')
    print("Seeds in Spark but not in CHA: ", merged[merged['_merge'] == 'right_only'].shape[0])
    merged = spark_seeds.merge(cha_dd_seeds, indicator=True, how='outer')
    print("Seeds in CHA but not in Spark: ", merged[merged['_merge'] == 'right_only'].shape[0])
    #Uncomment next line to see what spark had that CHA didn't
    #print(merged[merged['_merge'] == 'right_only'][['Rule','SeedStatement', 'SeedMethod', 'SeedClass']])


def plot_runtime_curve(data):
    cha_times = data[data['CallGraphMode']=='CHA']['AnalysisTimes'].sample(500).sort_values().reset_index(drop=True)
    cha_dd_times = data[data['CallGraphMode']=='CHA_DD']['AnalysisTimes'].sample(500).sort_values().reset_index(drop=True)
    spark_times = data[data['CallGraphMode']=='SPARK']['AnalysisTimes'].sample(500).sort_values().reset_index(drop=True)
    spark_dd_times = data[data['CallGraphMode']=='SPARK_DD']['AnalysisTimes'].sample(500).sort_values().reset_index(drop=True)

    plt.plot(cha_times, label='CHA')
    plt.plot(cha_dd_times, label='CHA DD')
    plt.plot(spark_times, label='SPARK')
    plt.plot(spark_dd_times, label='SPARK DD')

    plt.xlabel("Analysis runs ordered by runtimes")
    plt.ylabel("Runtime in seconds")

    plt.legend()
    plt.tight_layout()
    plt.savefig("RuntimeDistributionPerCGMode.pdf", dpi = 300)


def analyze_difference_in_results(data):
    all_errors = data.loc[data['Is_In_Error']]
    cha_errors = all_errors.query('CallGraphMode == "CHA"')
    cha_dd_errors = all_errors.query('CallGraphMode == "CHA_DD"')
    spark_errors = all_errors.query('CallGraphMode == "SPARK"')
    spark_dd_errors = all_errors.query('CallGraphMode == "SPARK_DD"')

    print("Total errors: ", all_errors.shape[0])
    print("Errors according to CHA: ", cha_errors.shape[0])
    print("Errors according to CHA DD: ", cha_dd_errors.shape[0])
    print("Errors according to Spark: ", spark_errors.shape[0])
    print("Errors according to Spark DD: ", spark_dd_errors.shape[0])

    errors_per_cgmode = all_errors[['CallGraphMode', 'Is_In_Error']].groupby('CallGraphMode').aggregate('sum')
    makeBarPlot(errors_per_cgmode, 'Detected errors', 'ErrorsPerCGMode.pdf')

    runs_no_timeout = data.query('Timedout == False')[['CallGraphMode', 'Timedout']].groupby('CallGraphMode')\
                                                                                                .aggregate('count')
    errors_per_cgmode_normalized =  errors_per_cgmode['Is_In_Error']/runs_no_timeout['Timedout']
    ax = errors_per_cgmode_normalized.plot(kind='bar', rot=10, legend=False)
    for p in ax.patches:
        ax.annotate('{:.{prec}}'.format(p.get_height(), prec=2), (p.get_x() * 1 + 0.15, p.get_height() * 1.005))
    ax.set_ylabel('Error detection rate for non-timedout runs')
    plt.tight_layout()
    plt.savefig('ErrorsPerCGModeNormalized.pdf', dpi = 300)
    plt.close()

    errors_per_rule = all_errors[['Rule', 'Is_In_Error']].groupby('Rule').aggregate('sum')
    makeBarPlot(errors_per_rule, 'Detected errors', 'ErrorsPerRule.pdf')

    errors_per_rule_per_cg = all_errors[['CallGraphMode','Rule','Is_In_Error']].groupby(['CallGraphMode',
                                                                                 'Rule']).aggregate('sum')
    makeBarPlot(errors_per_rule_per_cg, 'Detected errors', 'ErrorsPerRulePerCGMode.pdf',90, 0.05)


def makeBarPlot(data, ylabel, figurename, rotation=10, label_offset = 0.15):
    ax = data.plot(kind='bar', rot=rotation, legend=False)
    for p in ax.patches:
        ax.annotate(str(int(p.get_height())), (p.get_x() * 1 + label_offset, p.get_height() * 1.005))
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(figurename, dpi = 300)
    plt.close()

def main(dirname):
    #Option to see the printed output more easily
    pd.set_option('display.width', 250)
    pd.set_option('display.max_columns', 5)

    raw_data = read_data(dirname)

    #Drop columns without useful information. Analysis always says "ideal" and there is an emtpy column
    data = raw_data.drop(columns=['Analysis', 'Unnamed: 26'])

    #Drop rows of which duplicates of seeds and call graph mode exist (those are not analysis of actual benchmarks)
    data = data.drop_duplicates(subset= ['Rule', 'Seed', 'SeedStatement', 'SeedMethod', 'SeedClass',
                                                    'CallGraphMode'], keep=False)
    plot_timeouts(data)
    analyze_difference_in_seeds(data)
    analyze_difference_in_results(data)

    #Convert times to seconds and limit maximum analysis time to 10 minutes as this was our timeout
    data['AnalysisTimes'] = data['AnalysisTimes']/1000
    data['AnalysisTimes'] = data['AnalysisTimes'].clip(upper=600)

    plot_runtime_curve(data)
    #data = data.query('Timedout == False')

    merged_data = split_and_merge_data(data)

    plot_averages_runtimes(merged_data)


if __name__== "__main__":
    main(sys.argv[1])