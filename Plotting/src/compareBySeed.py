import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib_venn import venn2


def read_data(dirname):
    raw_df = pd.DataFrame()
    for file in os.listdir(dirname):
        if file.endswith(".csv"):
            data_from_this_csv = pd.read_csv(os.path.join(dirname, file), sep=';', encoding='UTF-8')
            raw_df = raw_df.append(data_from_this_csv)
    return raw_df


def plot_timeouts(data):
    over_ten_minutes = data.loc[data['AnalysisTimes'] > 600]
    print("Runs that took over 10 minutes: ", over_ten_minutes.shape[0])

    timedout = data.loc[data['Timedout']]
    if timedout.empty:
        print("Data contains no timeouts.")
        return
    print("Average time for runs with timeout in seconds:", str(int(((timedout[['AnalysisTimes']]/1000).mean()))))
    print("Number of runs that timed out:", timedout.shape[0])
    timeouts_per_cgmode = timedout[['CallGraphMode', 'Timedout']].groupby('CallGraphMode').aggregate('count')
    makeBarPlot(timeouts_per_cgmode, 'Timed out analysis runs', 'Plotting/Results/TimeoutsPerCGMode.pdf', 10, 0.35, 1)

    timeouts_per_rule = timedout[['Rule', 'Timedout']].groupby('Rule').aggregate('count')
    makeBarPlot(timeouts_per_rule, 'Timed out analysis runs', 'Plotting/Results/TimeoutsPerRule.pdf', 10, 0.35, 1)

    timeouts_per_rule_per_cg = timedout[['CallGraphMode', 'Rule', 'Timedout']].groupby(['CallGraphMode',
                                                                                       'Rule']).aggregate('count')
    makeBarPlot(timeouts_per_rule_per_cg, 'Timed out analysis runs', 'Plotting/Results/TimeoutsPerRulePerCGMode.pdf',
                90, 0.1)
    print()


def plot_averages_runtime(data):
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
    data = cha_vs_cha_dd_vs_spark.merge(spark_dd_data, on=['Rule', 'Seed', 'SeedStatement', 'SeedMethod',
                                                           'SeedClass'], how='outer', suffixes=('_spark', '_spark_dd'))
    # Compute averages
    averages = data[['AnalysisTimes_cha', 'AnalysisTimes_cha_dd',
                    'AnalysisTimes_spark', 'AnalysisTimes_spark_dd']].mean(axis=0)
    makeBarPlot(averages, 'Average runtime in seconds', 'Plotting/Results/RuntimePerCGMode.pdf', 10, 0.4, 1)
    print()


def analyze_difference_in_seeds(raw_data):
    cha_dd_seeds = raw_data[raw_data['CallGraphMode'] == 'CHA_DD'][['Rule', 'Seed', 'SeedStatement',
                                                                    'SeedMethod', 'SeedClass']]
    spark_seeds = raw_data[raw_data['CallGraphMode'] == 'SPARK'][['Rule', 'Seed', 'SeedStatement',
                                                                  'SeedMethod', 'SeedClass']]
    print("Total seeds in CHA: ", cha_dd_seeds.shape[0])
    print("Total seeds in Spark: ", spark_seeds.shape[0])

    merged = cha_dd_seeds.merge(spark_seeds, indicator=True, how='outer')
    chaOnly = merged[merged['_merge'] == 'left_only'].shape[0]
    sparkOnly = merged[merged['_merge'] == 'right_only'].shape[0]
    print("Seeds in CHA but not in Spark: ", chaOnly)
    print("Seeds in Spark but not in CHA: ", sparkOnly)
    # Uncomment next line to see what spark had that CHA didn't
    # print(merged[merged['_merge'] == 'right_only'][['Rule','SeedStatement', 'SeedMethod', 'SeedClass']])
    seedsBoth = merged[merged['_merge'] == 'both'].shape[0]
    print("Seeds in both CHA and in Spark: ", seedsBoth)

    venn2(subsets = (cha_dd_seeds.shape[0], spark_seeds.shape[0], seedsBoth),
          set_labels = ('Seeds found by CHA', 'Seeds found by Spark'))
    plt.savefig("Plotting/Results/SeedsVennDiagram.pdf", dpi=300)
    plt.close()
    p1 = plt.bar([1,2], [seedsBoth, seedsBoth], tick_label=['CHA', 'SPARK'])
    p2 = plt.bar([1,2], [chaOnly,sparkOnly], bottom=[seedsBoth, seedsBoth])
    plt.legend((p1[0], p2[0]), ('Found by both', 'Found only by one'))
    plt.ylabel('Number of seeds found')
    plt.tight_layout()
    plt.savefig("Plotting/Results/SeedsByCallGraphMode.pdf", dpi=300)
    plt.close()
    print()


def plot_runtime_curve(data):
    cha_times = data[data['CallGraphMode'] == 'CHA']['AnalysisTimes'].sample(500).sort_values().reset_index(drop=True)
    cha_dd_times = data[data['CallGraphMode'] == 'CHA_DD']['AnalysisTimes'].sample(500).sort_values().\
        reset_index(drop=True)
    spark_times = data[data['CallGraphMode'] == 'SPARK']['AnalysisTimes'].sample(500).sort_values()\
        .reset_index(drop=True)
    spark_dd_times = data[data['CallGraphMode'] == 'SPARK_DD']['AnalysisTimes'].sample(500).sort_values().\
        reset_index(drop=True)

    plt.plot(cha_times, label='CHA')
    plt.plot(cha_dd_times, label='CHA DD')
    plt.plot(spark_times, label='SPARK')
    plt.plot(spark_dd_times, label='SPARK DD')

    plt.xlabel("Analysis runs ordered by runtimes")
    plt.ylabel("Runtime in seconds")

    plt.legend()
    plt.tight_layout()
    plt.savefig("Plotting/Results/RuntimeDistributionPerCGMode.pdf", dpi=300)
    plt.close()


def analyze_difference_in_results(data):
    all_errors = data.loc[data['Is_In_Error']]
    cha_errors = all_errors.query('CallGraphMode == "CHA"')
    cha_dd_errors = all_errors.query('CallGraphMode == "CHA_DD"')
    spark_errors = all_errors.query('CallGraphMode == "SPARK"')
    spark_dd_errors = all_errors.query('CallGraphMode == "SPARK_DD"')

    # Compute absolute number of error per algorithm
    print("Total errors: ", all_errors.shape[0])
    print("Errors according to CHA: ", cha_errors.shape[0])
    print("Errors according to CHA DD: ", cha_dd_errors.shape[0])
    print("Errors according to Spark: ", spark_errors.shape[0])
    print("Errors according to Spark DD: ", spark_dd_errors.shape[0])

    errors_per_cgmode = all_errors[['CallGraphMode', 'Is_In_Error']].groupby('CallGraphMode').aggregate('count')
    makeBarPlot(errors_per_cgmode, 'Detected errors', 'Plotting/Results/ErrorsPerCGMode.pdf', 10,  0.5, 1)

    # Set number of errors in relation to runs, second column does not matter
    runs = data[['CallGraphMode', 'Seed']].groupby('CallGraphMode').aggregate('count')
    errors_per_cgmode_normalized = errors_per_cgmode['Is_In_Error']/runs['Seed']
    ax = errors_per_cgmode_normalized.plot(kind='bar', rot=10, legend=False)
    for p in ax.patches:
        ax.annotate('{:.{prec}}'.format(p.get_height(), prec=2), (p.get_x() * 1 + 0.15, p.get_height() + 0.001))
    ax.set_ylabel('Error detection rate in relation to runs')
    plt.tight_layout()
    plt.savefig('Plotting/Results/ErrorsPerCGModeNormalized.pdf', dpi = 300)
    plt.close()

    errors_per_rule = all_errors[['Rule', 'Is_In_Error']].groupby('Rule').aggregate('count')
    makeBarPlot(errors_per_rule, 'Detected errors', 'Plotting/Results/ErrorsPerRule.pdf', 10, 0.4, 2)

    errors_per_rule_per_cg = all_errors[['CallGraphMode','Rule','Is_In_Error']].groupby(['CallGraphMode',
                                                                                 'Rule']).aggregate('count')
    makeBarPlot(errors_per_rule_per_cg, 'Detected errors', 'Plotting/Results/ErrorsPerRulePerCGMode.pdf',90, 0.1)
    print()


def makeBarPlot(data, ylabel, figurename, rotation=10, label_x_offset = 0.15, label_y_offset=0.001):
    ax = data.plot(kind='bar', rot=rotation, legend=False)
    for p in ax.patches:
        ax.annotate(str(int(p.get_height())), (p.get_x() + (1/len(str(int(p.get_height()))))* label_x_offset,
                                               p.get_height() + label_y_offset))
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(figurename, dpi = 300)
    plt.close()


def compare_result_details(data):
    seed_columns = ['Rule', 'Seed', 'SeedStatement', 'SeedMethod', 'SeedClass']

    #Ignore timeout runs and compare seeds for which all runs finished
    data_no_timeout = data.query('Timedout == False')
    data_no_timeout = data_no_timeout.drop('Timedout', axis=1)
    cha_data = data_no_timeout[data_no_timeout['CallGraphMode'] == 'CHA'].drop(columns=['CallGraphMode'])
    cha_dd_data = data_no_timeout[data_no_timeout['CallGraphMode'] == 'CHA_DD'].drop(columns=['CallGraphMode'])
    spark_data = data_no_timeout[data_no_timeout['CallGraphMode'] == 'SPARK'].drop(columns=['CallGraphMode'])
    spark_dd_data = data_no_timeout[data_no_timeout['CallGraphMode'] == 'SPARK_DD'].drop(columns=['CallGraphMode'])
    cha_vs_cha_dd = cha_data.merge(cha_dd_data, on=seed_columns, how='inner', suffixes=('_cha', '_cha_dd'))
    cha_vs_cha_dd_vs_spark = cha_vs_cha_dd.merge(spark_data, on=seed_columns, how='inner')
    all_data_per_seed = cha_vs_cha_dd_vs_spark.merge(spark_dd_data, on=seed_columns,how='inner',
                                                     suffixes=('_spark','_spark_dd'))
    all_data_per_seed.to_csv("Plotting/Results/SharedSeedsNoTimeout.csv", sep=';')
    print("Seeds for which all runs finished: ", all_data_per_seed.shape[0])

    # Include timeouts and compare shared seeds
    cha_data = data[data['CallGraphMode'] == 'CHA'].drop(columns=['CallGraphMode'])
    cha_dd_data = data[data['CallGraphMode'] == 'CHA_DD'].drop(columns=['CallGraphMode'])
    spark_data = data[data['CallGraphMode'] == 'SPARK'].drop(columns=['CallGraphMode'])
    spark_dd_data = data[data['CallGraphMode'] == 'SPARK_DD'].drop(columns=['CallGraphMode'])
    cha_vs_cha_dd = cha_data.merge(cha_dd_data, on=seed_columns, how='inner', suffixes=('_cha', '_cha_dd'))
    cha_vs_cha_dd_vs_spark = cha_vs_cha_dd.merge(spark_data, on=seed_columns, how='inner')
    all_data_per_seed = cha_vs_cha_dd_vs_spark.merge(spark_dd_data, on=seed_columns,how='inner',
                                                     suffixes=('_spark','_spark_dd'))
    all_data_per_seed.to_csv("Plotting/Results/SharedSeedsTimeoutsIncluded.csv", sep=';')
    print("Seeds for which all algorithms started: ", all_data_per_seed.shape[0])

    #Report only values for which any of the algorithm actually found errors
    all_data_per_seed = all_data_per_seed.loc[( (all_data_per_seed['Is_In_Error_cha'] == True) |
                                                (all_data_per_seed['Is_In_Error_cha_dd'] == True) |
                                                (all_data_per_seed['Is_In_Error_spark'] == True) |
                                                (all_data_per_seed['Is_In_Error_spark_dd'] == True))]
    all_data_per_seed.to_csv("Plotting/Results/SharedSeedsTimeoutsIncludedWithErrors.csv", sep=';')
    print("Seeds for which all algorithms started and some contain errors: ", all_data_per_seed.shape[0])

    #Store values from above again with subset of columns for easier readability
    all_data_per_seed = all_data_per_seed[['Rule', 'Seed', 'SeedStatement', 'SeedMethod', 'SeedClass',
                                'Timedout_cha', 'Timedout_cha_dd', 'Timedout_spark', 'Timedout_spark_dd',
                                'Is_In_Error_cha', 'Is_In_Error_cha_dd', 'Is_In_Error_spark', 'Is_In_Error_spark_dd']]
    all_data_per_seed.to_csv("Plotting/Results/SharedSeedsTimeoutsIncludedWithErrorsSimple.csv", sep=';')

    #Check if there is any error reported by demand-driven analysis and not by whole program analysis
    all_data_per_seed = all_data_per_seed.loc[((all_data_per_seed['Is_In_Error_cha'] == False) &
                                               (all_data_per_seed['Timedout_cha'] == False) &
                                               (all_data_per_seed['Is_In_Error_cha_dd'] == True ) |
                                                (all_data_per_seed['Is_In_Error_spark'] == False) &
                                                (all_data_per_seed['Timedout_spark'] == False) &
                                                (all_data_per_seed['Is_In_Error_spark_dd'] == True ))]
    print("Seeds for which the whole program did not report errors and the demand-driven version did:",
          all_data_per_seed.shape[0])
    if(not all_data_per_seed.empty):
        all_data_per_seed.to_csv("Plotting/Results//SeedsDemandDrivenMoreErrors.csv", sep=';')
    print()


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

    plot_averages_runtime(data)

    compare_result_details(data)


if __name__== "__main__":
    main(sys.argv[1])