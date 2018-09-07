## Thesis experiments

These experiments can be run using openjdk version 1.8.0_181. 

### Whole program call graph construction (precomputation)

The runtime and amount of edges for the whole program call graphs can be obtained 
by running the `CallGraphTimer` and parsing the command line output using 
`parseCallGraphTimeOutput.py`. Store the output to a text file and pass that as 
a single argument to the script, for example like this:

`python parseCallGraphTimeOutput.py callGraphTimes.txt`

### Typestate analysis

The other experiments compare the IDEal typestate analysis on the dacapo 
benchmark suite using either the demand-driven call graph generation or 
a whole-program call graph. The used call graph algorithms are CHA and Spark.
Each analysis is available with or without demand-driven call graph generation.

The typestate analysis can be run like this: 

```java -jar pds-experiments/build/typestate-experiments-jar-with-dependencies.jar dacapo/ CHA```

The first argument is the path to a folder containing the jar files for the
dacapo benchmark. The second parameter is the call graph mode.
The options are CHA, SPARK, CHA_DD and SPARK_DD. The first two use the 
whole-program call graph without further computation, while the last two
use demand-driven (DD) call graph generation in addition.

To obtain the full results the experiment should be run for every call graph
option. The program will output .csv and .dot files to the folder 
`outputDacapo`. The csv files contain the results and work as input 
to `compareBySeed.py`. The path to the folder containing the csv files is 
passed to the script parsing the results, like this: 

`python compareBySeed.py outputDacapo`

The script will output metrics about the results and generate plots in 
`Plotting/Results`. It will also output csv files containing comparable 
data in the results to the same folder.

The dot files the experiment generates contain the call graph per seed or (if not
working demand-driven) per program. They can be linked to the csv files using the
seednumber. So if a finding may warrant investigation, the call graph can be plotted
using dot, e.g.,

`dot -Tng org.hsqldb.hsqldbDoopDriver-ideal-PrintWriter-CHA_DD1.dot > callgraph.png`