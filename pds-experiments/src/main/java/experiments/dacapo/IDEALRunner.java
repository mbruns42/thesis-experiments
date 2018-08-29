package experiments.dacapo;

import boomerang.BoomerangOptions;
import boomerang.DefaultBoomerangOptions;
import boomerang.WeightedForwardQuery;
import boomerang.callgraph.ObservableICFG;
import boomerang.callgraph.ObservableStaticICFG;
import boomerang.debugger.CallGraphDebugger;
import boomerang.debugger.Debugger;
import boomerang.jimple.Statement;
import boomerang.jimple.Val;
import boomerang.results.ForwardBoomerangResults;
import com.google.common.collect.Table;
import ideal.IDEALAnalysis;
import ideal.IDEALAnalysisDefinition;
import ideal.IDEALResultHandler;
import ideal.IDEALSeedSolver;
import soot.*;
import soot.jimple.Stmt;
import soot.jimple.toolkits.ide.icfg.JimpleBasedInterproceduralCFG;
import sync.pds.solver.WeightFunctions;
import typestate.TransitionFunction;
import typestate.finiteautomata.ITransition;
import typestate.finiteautomata.TypeStateMachineWeightFunctions;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.Collection;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public class IDEALRunner extends SootSceneSetupDacapo {

    private IDEALAnalysis<TransitionFunction> analysis;
    private String outputFile;
    private static int seedNumber=0;

    public IDEALRunner(String benchmarkFolder, String benchFolder, String callGraphMode) {
        super(benchmarkFolder, benchFolder, callGraphMode);
    }

    protected IDEALAnalysis<TransitionFunction> createAnalysis() {
        String className = System.getProperty("rule");

        JimpleBasedInterproceduralCFG staticIcfg = new JimpleBasedInterproceduralCFG(false);

        try {

            System.out.println("Reachable Methods: " + Scene.v().getReachableMethods().size());
            final TypeStateMachineWeightFunctions genericsType = (TypeStateMachineWeightFunctions) Class.forName(className).getConstructor()
                    .newInstance();

            return new IDEALAnalysis<TransitionFunction>(new IDEALAnalysisDefinition<TransitionFunction>() {
                private CallGraphDebugger callGraphDebugger;
                private boolean staticIcfgWasInitialized = false;

                @Override
                public Collection<WeightedForwardQuery<TransitionFunction>> generate(SootMethod method, Unit stmt, Collection<SootMethod> calledMethod) {
                    if (!method.getDeclaringClass().isApplicationClass())
                        return Collections.emptyList();
                    return genericsType.generateSeed(method, stmt, calledMethod);
                }

                @Override
                public WeightFunctions<Statement, Val, Statement, TransitionFunction> weightFunctions() {
                    return genericsType;
                }

                @Override
                public ObservableICFG<Unit, SootMethod> icfg() {
                    if ((getCallGraphMode() == CallGraphMode.CHA || getCallGraphMode() == CallGraphMode.SPARK)
                            && !staticIcfgWasInitialized){
                        System.out.println("Initializing ObservableStaticICFG");
                        icfg = new ObservableStaticICFG(staticIcfg);
                        staticIcfgWasInitialized = true;
                    }
                    return icfg;
                }

                @Override
                public BoomerangOptions boomerangOptions() {
                    return new DefaultBoomerangOptions() {
                        @Override
                        public int analysisTimeoutMS() {
                            return (int) IDEALRunner.this.getBudget();
                        }

                        @Override
                        public boolean arrayFlows() {
                            return false;
                        }

                    };
                }

                @Override
                public Debugger<TransitionFunction> debugger(IDEALSeedSolver<TransitionFunction> solver) {
                    String dotFileName = outputFile.replace(".csv", ".dot");
                    File dotFile = new File(dotFileName);
                    callGraphDebugger =  new CallGraphDebugger(dotFile, icfg().getCallGraphCopy(), icfg);
                    return callGraphDebugger;
                }

                @Override
                public IDEALResultHandler<TransitionFunction> getResultHandler() {
                    return new IDEALResultHandler<TransitionFunction>() {
                        @Override
                        public void report(WeightedForwardQuery<TransitionFunction> seed,
                                           ForwardBoomerangResults<TransitionFunction> res) {
                            seedNumber++;
                            File file = new File(outputFile);
                            boolean fileExisted = file.exists();
                            FileWriter writer;
                            try {
                                writer = new FileWriter(file, true);
                                if (!fileExisted)
                                    writer.write(
                                            "Analysis;Rule;Seed;SeedStatement;SeedMethod;SeedClass;SeedNumber;" +
                                                    "CallGraphMode;Is_In_Error;Timedout;AnalysisTimes;" +
                                                    "PropagationCount;VisitedMethod;ReachableMethods;CallRecursion;" +
                                                    "FieldLoop;MaxMemory;"+
                                                    callGraphDebugger.getCsvHeader() + "\n");
                                writer.write(asCSVLine(seed, res, callGraphDebugger.getCallGraphStatisticsAsCsv()));
                                writer.close();
                            } catch (IOException e1) {
                                e1.printStackTrace();
                            }
                            //
                            super.report(seed, res);
                        }
                    };
                }
            }) {
            };

        } catch (InstantiationException e) {
            e.printStackTrace();
        } catch (IllegalAccessException e) {
            e.printStackTrace();
        } catch (IllegalArgumentException e) {
            e.printStackTrace();
        } catch (InvocationTargetException e) {
            e.printStackTrace();
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
        } catch (SecurityException e) {
            e.printStackTrace();
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
        return null;
    }

    public void run(final String outputFile) {

        G.v().reset();
        this.outputFile = outputFile;

        setupSoot();
        Transform transform = new Transform("wjtp.ifds", new SceneTransformer() {
            protected void internalTransform(String phaseName,
                                             @SuppressWarnings("rawtypes") Map options) {
                if (Scene.v().getMainMethod() == null)
                    throw new RuntimeException("No main class existing.");
                for (SootClass c : Scene.v().getClasses()) {
                    for (String app : IDEALRunner.this.getApplicationClasses()) {
                        if (c.isApplicationClass())
                            continue;
                        if (c.toString().startsWith(app.replace("<", ""))) {
                            c.setApplicationClass();
                        }
                    }
                }
                System.out.println("Application Classes: " + Scene.v().getApplicationClasses().size());
                IDEALRunner.this.getAnalysis().run();

            }
        });

        PackManager.v().getPack("wjtp").add(transform);
        PackManager.v().getPack("cg").apply();
        PackManager.v().getPack("wjtp").apply();
    }

    private String asCSVLine(WeightedForwardQuery<TransitionFunction> key,
                             ForwardBoomerangResults<TransitionFunction> forwardBoomerangResults,
                             String callGraphDebuggerCSV) {
        String analysis = "ideal";
        String rule = System.getProperty("ruleIdentifier");
        String seedString = key.toString();
        Stmt seedStmt = key.stmt().getUnit().get();
        SootMethod seedMethod = key.stmt().getMethod();
        SootClass seedClass = seedMethod.getDeclaringClass();
        boolean isInErrorState = isInErrorState(forwardBoomerangResults);
        boolean isTimedout = getAnalysis().isTimedout(key);
        long analysisTime = getAnalysis().getAnalysisTime(key).elapsed(TimeUnit.MILLISECONDS);
        int propagationCount = forwardBoomerangResults.getStats().getForwardReachesNodes().size();
        int visitedMethods = forwardBoomerangResults.getStats().getCallVisitedMethods().size();
        int reachableMethods = Scene.v().getReachableMethods().size();
        boolean containsCallLoop = forwardBoomerangResults.containsCallRecursion();
        boolean containsFieldLoop = forwardBoomerangResults.containsFieldLoop();
        long usedMemory = forwardBoomerangResults.getMaxMemory();
        return String.format("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n", analysis, rule, seedString,
                seedStmt, seedMethod, seedClass, seedNumber, callGraphMode, isInErrorState, isTimedout, analysisTime,
                propagationCount, visitedMethods, reachableMethods, containsCallLoop, containsFieldLoop,
                usedMemory, callGraphDebuggerCSV);
    }

    private boolean isInErrorState(ForwardBoomerangResults<TransitionFunction> forwardBoomerangResults) {
        Table<Statement, Val, TransitionFunction> objectDestructingStatements = forwardBoomerangResults.asStatementValWeightTable();
        for (Table.Cell<Statement, Val, TransitionFunction> c : objectDestructingStatements.cellSet()) {
            for (ITransition t : c.getValue().values()) {
                if (t.to() != null) {
                    if (t.to().isErrorState()) {
                        return true;
                    }
                }
            }

        }
        return false;
    }


    protected IDEALAnalysis<TransitionFunction> getAnalysis() {
        if (analysis == null)
            analysis = createAnalysis();
        return analysis;
    }

    protected long getBudget() {
        return TimeUnit.MINUTES.toMillis(10);
    }
}
