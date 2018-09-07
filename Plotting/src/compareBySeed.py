import os
import sys

import matplotlib.pyplot as plt
import pandas as pd

seed_columns = ['Rule', 'Seed', 'SeedStatement', 'SeedMethod', 'SeedClass']


def read_data(dirname):
    raw_df = pd.DataFrame()
    for file in os.listdir(dirname):
        if file.endswith(".csv"):
            data_from_this_csv = pd.read_csv(os.path.join(dirname, file), sep=';', encoding='UTF-8')
            assert not data_from_this_csv.empty
            raw_df = raw_df.append(data_from_this_csv)
    return raw_df


def autolabel(ax, rect, precision, xpos='center'):
    """ Writes the value the bar represents on top of the bar. Can be configured to arrange it to the left or right
        by passing the strings 'left' or 'right' as the xpos parameter. Labeling in the center of the bar is default.
    """
    xpos = xpos.lower()  # normalize the case of the parameter
    ha = {'center': 'center', 'right': 'left', 'left': 'right'}
    offset = {'center': 0.5, 'right': 0.57, 'left': 0.43}  # x_txt = x + w*off
    height = rect.get_height()
    ax.text(rect.get_x() + rect.get_width() * offset[xpos], 1.0 * height,
            '{:.{prec}f}'.format(height, prec=precision), ha=ha[xpos], va='bottom', fontsize=10)


def make_bar_plot(data, ylabel, figurename, rotation=10, precision=0, log_y=False):
    ax = data.plot(kind='bar', rot=rotation, legend=False, logy=log_y)
    for p in ax.patches:
        autolabel(ax, p, precision)
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(figurename, dpi=300)
    plt.close()


def plot_timeouts(data):
    timedout = data.loc[data['Timedout']]
    if timedout.empty:
        print("Data contains no timeouts.")
        print()
        return
    timeouts_per_cgmode = timedout[['CallGraphMode', 'Timedout']].groupby('CallGraphMode').aggregate('count')
    make_bar_plot(timeouts_per_cgmode, 'Timed out analysis runs', 'Plotting/Results/TimeoutsPerCGMode.pdf', 0)

    timeouts_per_rule_per_cg = timedout[['CallGraphMode', 'Rule', 'Timedout']].groupby(['CallGraphMode',
                                                                                        'Rule']).aggregate('count')
    make_bar_plot(timeouts_per_rule_per_cg.unstack(0), 'Timed out analysis runs', 'Plotting/Results/'
                                                                                  'TimeoutsPerRulePerCGMode.pdf', 20)


def plot_averages_runtime(data):
    averages = data[['AnalysisTimes', 'CallGraphMode']].groupby('CallGraphMode').agg('mean')
    make_bar_plot(averages, 'Average runtime in seconds', 'Plotting/Results/RuntimePerCGMode.pdf', 0, 1)


def analyze_seeds(data):
    cha_seeds = data[data['CallGraphMode'] == 'CHA'][['Rule', 'Seed', 'SeedStatement',
                                                      'SeedMethod', 'SeedClass']]
    spark_seeds = data[data['CallGraphMode'] == 'SPARK'][['Rule', 'Seed', 'SeedStatement',
                                                          'SeedMethod', 'SeedClass']]
    cha_dd_seeds = data[data['CallGraphMode'] == 'CHA_DD'][['Rule', 'Seed', 'SeedStatement',
                                                            'SeedMethod', 'SeedClass']]
    spark_dd_seeds = data[data['CallGraphMode'] == 'SPARK_DD'][['Rule', 'Seed', 'SeedStatement',
                                                                'SeedMethod', 'SeedClass']]
    print("Total seeds in CHA: ", cha_seeds.shape[0])
    print("Total seeds in Spark: ", spark_seeds.shape[0])
    print("Total seeds in CHA DD: ", cha_dd_seeds.shape[0])
    print("Total seeds in Spark DD: ", spark_dd_seeds.shape[0])

    merged = cha_dd_seeds.merge(spark_dd_seeds, indicator=True, how='outer')
    cha_only = merged[merged['_merge'] == 'left_only'].shape[0]
    spark_only = merged[merged['_merge'] == 'right_only'].shape[0]
    print("Seeds in CHA but not in Spark: ", cha_only)
    print("Seeds in Spark but not in CHA: ", spark_only)
    # Uncomment next line to see what spark had that CHA didn't
    # print(merged[merged['_merge'] == 'right_only'][['Rule','SeedStatement', 'SeedMethod', 'SeedClass']])
    seeds_both = merged[merged['_merge'] == 'both'].shape[0]
    print("Seeds in both CHA and in Spark: ", seeds_both)

    p1 = plt.bar([1, 2], [seeds_both, seeds_both], tick_label=['CHA', 'SPARK'])
    p2 = plt.bar([1, 2], [cha_only, spark_only], bottom=[seeds_both, seeds_both])
    plt.legend((p1[0], p2[0]), ('Found by both', 'Found only by one'))
    plt.ylabel('Number of seeds found')
    plt.tight_layout()
    plt.savefig("Plotting/Results/SeedsByCallGraphMode.pdf", dpi=300)
    plt.close()
    print()


def plot_runtime_curve(data):
    cha_times = data[data['CallGraphMode'] == 'CHA']['AnalysisTimes'].sample(400).sort_values().reset_index(drop=True)
    cha_dd_times = data[data['CallGraphMode'] == 'CHA_DD']['AnalysisTimes'].sample(400).sort_values(). \
        reset_index(drop=True)
    spark_times = data[data['CallGraphMode'] == 'SPARK']['AnalysisTimes'].sample(400).sort_values() \
        .reset_index(drop=True)
    spark_dd_times = data[data['CallGraphMode'] == 'SPARK_DD']['AnalysisTimes'].sample(400).sort_values(). \
        reset_index(drop=True)

    plt.plot(cha_times, label='CHA')
    plt.plot(cha_dd_times, label='CHA DD', linestyle=':')
    plt.plot(spark_times, label='SPARK', linestyle='-.')
    plt.plot(spark_dd_times, label='SPARK DD', linestyle='--')

    plt.xlabel("Analysis runs ordered by runtimes")
    plt.ylabel("Runtime in seconds")

    plt.legend()
    plt.tight_layout()
    plt.savefig("Plotting/Results/RuntimeDistributionPerCGMode.pdf", dpi=300)
    plt.close()


def analyze_errors(data):
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
    make_bar_plot(errors_per_cgmode, 'Detected errors', 'Plotting/Results/ErrorsPerCGMode.pdf', 10)

    # Set number of errors in relation to runs, second column does not matter
    runs = data[['CallGraphMode', 'Seed']].groupby('CallGraphMode').aggregate('count')
    errors_per_cgmode_normalized = errors_per_cgmode['Is_In_Error'] / runs['Seed']
    ax = errors_per_cgmode_normalized.plot(kind='bar', rot=0, legend=False)
    for p in ax.patches:
        autolabel(ax, p, 2)
    ax.set_ylabel('Error detection rate in relation to runs')
    plt.tight_layout()
    plt.savefig('Plotting/Results/ErrorsPerCGModeNormalized.pdf', dpi=300)
    plt.close()

    errors_per_rule = all_errors[['Rule', 'Is_In_Error']].groupby('Rule').aggregate('count')
    make_bar_plot(errors_per_rule, 'Detected errors', 'Plotting/Results/ErrorsPerRule.pdf', 10)

    errors_per_rule_per_cg = all_errors[['CallGraphMode', 'Rule', 'Is_In_Error']].groupby(['CallGraphMode',
                                                                                           'Rule']).aggregate('count')
    make_bar_plot(errors_per_rule_per_cg.unstack(0), 'Detected errors', 'Plotting/Results/ErrorsPerRulePerCGMode.pdf',
                  90)
    print()


def export_result_details_to_csv(data):
    # Ignore timeout runs and compare seeds for which all runs finished
    data_no_timeout = data.query('Timedout == False')
    data_no_timeout = data_no_timeout.drop('Timedout', axis=1)
    cha_data = data_no_timeout[data_no_timeout['CallGraphMode'] == 'CHA'].drop(columns=['CallGraphMode'])
    cha_dd_data = data_no_timeout[data_no_timeout['CallGraphMode'] == 'CHA_DD'].drop(columns=['CallGraphMode'])
    spark_data = data_no_timeout[data_no_timeout['CallGraphMode'] == 'SPARK'].drop(columns=['CallGraphMode'])
    spark_dd_data = data_no_timeout[data_no_timeout['CallGraphMode'] == 'SPARK_DD'].drop(columns=['CallGraphMode'])
    cha_vs_cha_dd = cha_data.merge(cha_dd_data, on=seed_columns, how='inner', suffixes=('_cha', '_cha_dd'))
    cha_vs_cha_dd_vs_spark = cha_vs_cha_dd.merge(spark_data, on=seed_columns, how='inner')
    all_data_per_seed = cha_vs_cha_dd_vs_spark.merge(spark_dd_data, on=seed_columns, how='inner',
                                                     suffixes=('_spark', '_spark_dd'))
    all_data_per_seed.to_csv("Plotting/Results/SharedSeedsNoTimeout.csv", sep=';')
    print("Seeds for which all runs finished: ", all_data_per_seed.shape[0])

    # Include timeouts and compare shared seeds
    cha_data = data[data['CallGraphMode'] == 'CHA'].drop(columns=['CallGraphMode'])
    cha_dd_data = data[data['CallGraphMode'] == 'CHA_DD'].drop(columns=['CallGraphMode'])
    spark_data = data[data['CallGraphMode'] == 'SPARK'].drop(columns=['CallGraphMode'])
    spark_dd_data = data[data['CallGraphMode'] == 'SPARK_DD'].drop(columns=['CallGraphMode'])
    cha_vs_cha_dd = cha_data.merge(cha_dd_data, on=seed_columns, how='inner', suffixes=('_cha', '_cha_dd'))
    cha_vs_cha_dd_vs_spark = cha_vs_cha_dd.merge(spark_data, on=seed_columns, how='inner')
    all_data_per_seed = cha_vs_cha_dd_vs_spark.merge(spark_dd_data, on=seed_columns, how='inner',
                                                     suffixes=('_spark', '_spark_dd'))
    all_data_per_seed.to_csv("Plotting/Results/SharedSeedsTimeoutsIncluded.csv", sep=';')
    print("Seeds for which all algorithms started: ", all_data_per_seed.shape[0])

    # Report only values for which any of the algorithm actually found errors, but not all
    all_data_per_seed = all_data_per_seed.loc[((all_data_per_seed['Is_In_Error_cha'] == True) |
                                               (all_data_per_seed['Is_In_Error_cha_dd'] == True) |
                                               (all_data_per_seed['Is_In_Error_spark'] == True) |
                                               (all_data_per_seed['Is_In_Error_spark_dd'] == True))]
    all_data_per_seed = all_data_per_seed.loc[~((all_data_per_seed['Is_In_Error_cha'] == True) &
                                                (all_data_per_seed['Is_In_Error_cha_dd'] == True) &
                                                (all_data_per_seed['Is_In_Error_spark'] == True) &
                                                (all_data_per_seed['Is_In_Error_spark_dd'] == True))]
    print("Seeds for which all algorithms started and some contain errors: ", all_data_per_seed.shape[0])

    # Store values from above with subset of columns for easier readability
    all_data_per_seed = all_data_per_seed[['Rule', 'Bench_cha', 'SeedStatement', 'SeedMethod', 'SeedClass',
                                           'Timedout_cha', 'Timedout_cha_dd', 'Timedout_spark', 'Timedout_spark_dd',
                                           'Is_In_Error_cha', 'Is_In_Error_cha_dd', 'Is_In_Error_spark',
                                           'Is_In_Error_spark_dd']]
    all_data_per_seed.to_csv("Plotting/Results/SharedSeedsWithDifferentResults.csv", sep=';')

    # Check if there is any error reported by demand-driven analysis and not by whole program analysis
    all_data_per_seed = all_data_per_seed.loc[((all_data_per_seed['Is_In_Error_cha'] == False) &
                                               (all_data_per_seed['Timedout_cha'] == False) &
                                               (all_data_per_seed['Is_In_Error_cha_dd'] == True) |
                                               (all_data_per_seed['Is_In_Error_spark'] == False) &
                                               (all_data_per_seed['Timedout_spark'] == False) &
                                               (all_data_per_seed['Is_In_Error_spark_dd'] == True))]
    print("Seeds for which the whole program did not report errors and the demand-driven version did:",
          all_data_per_seed.shape[0])
    if not all_data_per_seed.empty:
        all_data_per_seed.to_csv("Plotting/Results/SeedsDemandDrivenMoreErrors.csv", sep=';')

    # Store differences in Spark and Spark DD
    spark_vs_spark_dd = spark_data.merge(spark_dd_data, on=seed_columns, how='inner', suffixes=('_spark', '_spark_dd'))
    spark_vs_spark_dd = spark_vs_spark_dd.loc[((spark_vs_spark_dd['Is_In_Error_spark'] == True) |
                                               (spark_vs_spark_dd['Is_In_Error_spark_dd'] == True))]
    spark_vs_spark_dd = spark_vs_spark_dd.loc[~((spark_vs_spark_dd['Is_In_Error_spark'] == True) &
                                                (spark_vs_spark_dd['Is_In_Error_spark_dd'] == True))]

    spark_vs_spark_dd = spark_vs_spark_dd[['Rule', 'Bench_spark', 'SeedStatement', 'SeedMethod', 'SeedClass',
                                           'Timedout_spark', 'Timedout_spark_dd', 'Is_In_Error_spark',
                                           'Is_In_Error_spark_dd']]
    spark_vs_spark_dd.to_csv("Plotting/Results/SharedSeedsWithDifferentResultsJustSpark.csv", sep=';')
    print()


def plot_graph_sizes(data):
    # Exclude timedout runs. Might give unfair advantage to demand driven since size might be smaller
    # However might be more advantageous for CHA since that might have timed out less for smaller graphs
    not_timedout = data.loc[~data['Timedout']]
    avg_edges = not_timedout[['CallGraphMode', 'numOfEdgesInCallGraph']].groupby('CallGraphMode').agg('mean')

    make_bar_plot(avg_edges, 'Average number of edges', 'Plotting/Results/AvgEdgesPerCGMode.pdf', log_y=True)

    edges_spark = not_timedout[not_timedout['CallGraphMode'] == 'SPARK'].drop_duplicates(['Bench'])[
        ['Bench', 'numOfEdgesInCallGraph']].set_index('Bench')
    edges_cha = not_timedout[not_timedout['CallGraphMode'] == 'CHA'].drop_duplicates(['Bench'])[
        ['Bench', 'numOfEdgesInCallGraph']].set_index('Bench')
    edges_cha_dd = not_timedout[not_timedout['CallGraphMode'] == 'CHA_DD'][
        ['Bench', 'numOfEdgesInCallGraph']].groupby('Bench').agg('sum')
    edges_spark_dd = not_timedout[not_timedout['CallGraphMode'] == 'SPARK_DD'][
        ['Bench', 'numOfEdgesInCallGraph']].groupby('Bench').agg('sum')

    bench_to_edges = pd.DataFrame(columns=['CHA', 'CHA_DD', 'SPARK', 'SPARK_DD'], index=edges_spark.index)
    bench_to_edges['SPARK'] = edges_spark
    bench_to_edges['CHA'] = edges_cha
    bench_to_edges['CHA_DD'] = edges_cha_dd
    bench_to_edges['SPARK_DD'] = edges_spark_dd
    ax = bench_to_edges.plot(kind='bar', rot=10, logy=True)
    ax.set_ylabel('Total number of edges')
    plt.tight_layout()
    plt.savefig('Plotting/Results/TotalEdgesPerCGMode.pdf', dpi=300)
    plt.close()


def print_performance_correlations(data):
    edges_spark = data[data['CallGraphMode'] == 'SPARK'].drop_duplicates(['Bench'])[
        ['Bench', 'numOfEdgesInCallGraph', 'avgNumOfPredecessors']].set_index('Bench')
    edges_cha = data[data['CallGraphMode'] == 'CHA'].drop_duplicates(['Bench'])[
        ['Bench', 'numOfEdgesInCallGraph', 'avgNumOfPredecessors']].set_index('Bench')
    bench_to_edges = pd.DataFrame(columns=['CHA_Edges', 'SPARK_Edges', 'CHA_Pred', 'SPARK_Pred'],
                                  index=edges_spark.index)
    bench_to_edges['SPARK_Edges'] = edges_spark['numOfEdgesInCallGraph']
    bench_to_edges['CHA_Edges'] = edges_cha['numOfEdgesInCallGraph']
    bench_to_edges['SPARK_Pred'] = edges_spark['avgNumOfPredecessors']
    bench_to_edges['CHA_Pred'] = edges_cha['avgNumOfPredecessors']

    # Find out how many edges were in the precomputed graph
    with_precomputed = data.copy()
    with_precomputed['EdgesInPrecomputed'] = float('nan')
    with_precomputed.loc[with_precomputed['CallGraphMode'] == 'SPARK', ['EdgesInPrecomputed']] = \
        with_precomputed[with_precomputed['CallGraphMode'] == 'SPARK']['numOfEdgesInCallGraph']
    with_precomputed.loc[with_precomputed['CallGraphMode'] == 'CHA', ['EdgesInPrecomputed']] = \
        with_precomputed[with_precomputed['CallGraphMode'] == 'CHA']['numOfEdgesInCallGraph']
    with_precomputed['PredInPrecomputed'] = float('nan')
    with_precomputed.loc[with_precomputed['CallGraphMode'] == 'SPARK', ['PredInPrecomputed']] = \
        with_precomputed[with_precomputed['CallGraphMode'] == 'SPARK']['avgNumOfPredecessors']
    with_precomputed.loc[with_precomputed['CallGraphMode'] == 'CHA', ['PredInPrecomputed']] = \
        with_precomputed[with_precomputed['CallGraphMode'] == 'CHA']['avgNumOfPredecessors']

    # Join with bench table, new column will have suffix, extract value from new column
    with_precomputed = with_precomputed.merge(bench_to_edges, left_on='Bench', right_index=True, suffixes=['', '_pre'])
    with_precomputed.loc[with_precomputed['CallGraphMode'] == 'SPARK_DD', ['EdgesInPrecomputed']] = \
        with_precomputed[with_precomputed['CallGraphMode'] == 'SPARK_DD']['SPARK_Edges']
    with_precomputed.loc[with_precomputed['CallGraphMode'] == 'CHA_DD', ['EdgesInPrecomputed']] = \
        with_precomputed[with_precomputed['CallGraphMode'] == 'CHA_DD']['CHA_Edges']
    with_precomputed.loc[with_precomputed['CallGraphMode'] == 'SPARK_DD', ['PredInPrecomputed']] = \
        with_precomputed[with_precomputed['CallGraphMode'] == 'SPARK_DD']['SPARK_Pred']
    with_precomputed.loc[with_precomputed['CallGraphMode'] == 'CHA_DD', ['PredInPrecomputed']] = \
        with_precomputed[with_precomputed['CallGraphMode'] == 'CHA_DD']['CHA_Pred']

    columns = ['AnalysisTimes', ' edgesFromPrecomputed', 'avgNumOfPredecessors', 'numOfEdgesInCallGraph',
               'EdgesInPrecomputed', 'PredInPrecomputed']
    print("CHA corr", with_precomputed[with_precomputed['CallGraphMode'] == 'CHA'][columns].corr(), "\n")
    print("CHA DD corr", with_precomputed[with_precomputed['CallGraphMode'] == 'CHA_DD'][columns].corr(), "\n")
    print("Spark corr", with_precomputed[with_precomputed['CallGraphMode'] == 'SPARK'][columns].corr(), "\n")
    print("Spark DD corr", with_precomputed[with_precomputed['CallGraphMode'] == 'SPARK_DD'][columns].corr(), "\n")


def plot_performance_correlations(data):
    corr = data[['AnalysisTimes', ' edgesFromPrecomputed', 'CallGraphMode']]
    ax1 = corr[corr['CallGraphMode'] == 'CHA'].plot(kind='scatter', x=' edgesFromPrecomputed', y='AnalysisTimes',
                                                    color='C0', logx=True, logy=True)
    ax2 = corr[corr['CallGraphMode'] == 'CHA_DD'].plot(kind='scatter', x=' edgesFromPrecomputed', y='AnalysisTimes',
                                                       color='C1', ax=ax1, logx=True, logy=True)
    ax3 = corr[corr['CallGraphMode'] == 'SPARK'].plot(kind='scatter', x=' edgesFromPrecomputed', y='AnalysisTimes',
                                                      color='C2', ax=ax2, logx=True, logy=True)
    corr[corr['CallGraphMode'] == 'SPARK_DD'].plot(kind='scatter', x=' edgesFromPrecomputed', y='AnalysisTimes',
                                                   color='C3', ax=ax3, logx=True, logy=True)
    plt.xlabel("Edges from precomputed call graph")
    plt.ylabel("Analysis Time in seconds")
    plt.savefig("Plotting/Results/CorrelationEdgesFromPrecomputedToRuntime.pdf", dpi=300)

    corr = data[['AnalysisTimes', 'numOfEdgesInCallGraph', 'CallGraphMode']]
    ax1 = corr[corr['CallGraphMode'] == 'CHA'].plot(kind='scatter', x='numOfEdgesInCallGraph', y='AnalysisTimes',
                                                    color='C0', logx=True, logy=True)
    ax2 = corr[corr['CallGraphMode'] == 'CHA_DD'].plot(kind='scatter', x='numOfEdgesInCallGraph', y='AnalysisTimes',
                                                       color='C1', ax=ax1, logx=True, logy=True)
    ax3 = corr[corr['CallGraphMode'] == 'SPARK'].plot(kind='scatter', x='numOfEdgesInCallGraph', y='AnalysisTimes',
                                                      color='C2', ax=ax2, logx=True, logy=True)
    corr[corr['CallGraphMode'] == 'SPARK_DD'].plot(kind='scatter', x='numOfEdgesInCallGraph', y='AnalysisTimes',
                                                   color='C3', ax=ax3, logx=True, logy=True)
    plt.xlabel("Edges in call graph")
    plt.ylabel("Analysis Time in seconds")
    plt.savefig("Plotting/Results/CorrelationNumberEdgesToRuntime.pdf", dpi=300)


def main(dirname):
    # Option to see the printed output more easily
    pd.set_option('display.width', 250)
    pd.set_option('display.max_columns', 6)

    raw_data = read_data(dirname)

    # Drop columns without useful information. Analysis always says "ideal" and there is an emtpy column
    data = raw_data.drop(columns=['Analysis', 'Unnamed: 27'])
    print(list(data))

    # Drop duplicates of seeds and call graph mode
    data = data.drop_duplicates(subset=['Rule', 'Seed', 'SeedStatement', 'SeedMethod', 'SeedClass', 'CallGraphMode'])

    # Convert times to seconds and limit maximum analysis time to 10 minutes as this was our timeout
    data['AnalysisTimes'] = data['AnalysisTimes'] / 1000
    over_five_minutes = data.loc[data['AnalysisTimes'] > 300]
    print("Runs that took over 5 minutes: ", over_five_minutes.shape[0])
    print("Average time for runs with timeout in seconds:", str(int(((over_five_minutes[['AnalysisTimes']]).mean()))))
    data['AnalysisTimes'] = data['AnalysisTimes'].clip(upper=300)
    print()

    # Seeds
    analyze_seeds(data)

    # Runtime and timeouts
    plot_timeouts(data)
    plot_runtime_curve(data)
    plot_averages_runtime(data)

    # Precision
    analyze_errors(data)
    export_result_details_to_csv(data)

    # Demand-driven call graph performance
    plot_graph_sizes(data)
    print_performance_correlations(data)
    plot_performance_correlations(data)


if __name__ == "__main__":
    main(sys.argv[1])
