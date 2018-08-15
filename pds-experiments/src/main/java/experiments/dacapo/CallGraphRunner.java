package experiments.dacapo;

import boomerang.WeightedForwardQuery;
import boomerang.callgraph.ObservableICFG;
import boomerang.callgraph.ObservableStaticICFG;
import boomerang.debugger.Debugger;
import boomerang.jimple.Statement;
import boomerang.jimple.Val;
import ideal.IDEALAnalysis;
import ideal.IDEALAnalysisDefinition;
import ideal.IDEALSeedSolver;
import soot.*;
import soot.jimple.toolkits.ide.icfg.JimpleBasedInterproceduralCFG;
import sync.pds.solver.WeightFunctions;
import typestate.TransitionFunction;

import java.util.Collection;
import java.util.Map;

public class CallGraphRunner extends SootSceneSetupDacapo {

    public static void main(String[] args){
        new CallGraphRunner(args[0], args[1], args[2]).run();
    }

    public CallGraphRunner(String benchmarkFolder, String benchFolder, String callGraphMode) {
        super(benchmarkFolder, benchFolder, callGraphMode);
    }

    protected IDEALAnalysis<TransitionFunction> createAnalysis() {

        JimpleBasedInterproceduralCFG staticIcfg = new JimpleBasedInterproceduralCFG(false);

        System.out.println("Reachable Methods: " + Scene.v().getReachableMethods().size());

        return new IDEALAnalysis<TransitionFunction>(new IDEALAnalysisDefinition<TransitionFunction>() {
            private boolean staticIcfgWasInitialized = false;


            @Override
            public Collection<WeightedForwardQuery<TransitionFunction>> generate(SootMethod method, Unit stmt, Collection<SootMethod> calledMethod) {
                return null;
            }

            @Override
            public WeightFunctions<Statement, Val, Statement, TransitionFunction> weightFunctions() {
                return null;
            }

            @Override
            public ObservableICFG<Unit, SootMethod> icfg() {
                if ((getCallGraphMode() != CallGraphMode.DD) && !staticIcfgWasInitialized) {
                    icfg = new ObservableStaticICFG(staticIcfg);
                    staticIcfgWasInitialized = true;
                }
                return icfg;
            }

            @Override
            public Debugger<TransitionFunction> debugger(IDEALSeedSolver<TransitionFunction> idealSeedSolver) {
                return null;
            }

            }
        );
    }


    public void run() {

        G.v().reset();

        setupSoot();
        Transform transform = new Transform("wjtp.ifds", new SceneTransformer() {
            protected void internalTransform(String phaseName,
                                             @SuppressWarnings("rawtypes") Map options) {
                if (Scene.v().getMainMethod() == null)
                    throw new RuntimeException("No main class existing.");
                for (SootClass c : Scene.v().getClasses()) {
                    for (String app : CallGraphRunner.this.getApplicationClasses()) {
                        if (c.isApplicationClass())
                            continue;
                        if (c.toString().startsWith(app.replace("<", ""))) {
                            c.setApplicationClass();
                        }
                    }
                }
                System.out.println("Application Classes: " + Scene.v().getApplicationClasses().size());
                createAnalysis();

            }
        });

        long startTime = System.currentTimeMillis();
        PackManager.v().getPack("wjtp").add(transform);
        PackManager.v().getPack("cg").apply();
        long endTime = System.currentTimeMillis();
        PackManager.v().getPack("wjtp").apply();
        long duration = (endTime - startTime);
        System.out.println("! "+ callGraphMode +","+ getBenchName() + "," + duration);
    }

}
