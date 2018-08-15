package experiments.dacapo;

import boomerang.callgraph.ObservableDynamicICFG;
import boomerang.callgraph.ObservableICFG;
import boomerang.callgraph.ObservableStaticICFG;
import soot.*;
import soot.jimple.toolkits.ide.icfg.JimpleBasedInterproceduralCFG;
import wpds.impl.Weight;

import java.util.Map;

public class CallGraphRunner extends SootSceneSetupDacapo {
    ObservableICFG<Unit, SootMethod> icfg;

    public static void main(String[] args){
        new CallGraphRunner(args[0], args[1], args[2]).run();
    }

    public CallGraphRunner(String benchmarkFolder, String benchFolder, String callGraphMode) {
        super(benchmarkFolder, benchFolder, callGraphMode);
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
                JimpleBasedInterproceduralCFG staticIcfg = new JimpleBasedInterproceduralCFG(false);
                if ((getCallGraphMode() == CallGraphMode.DD)) {
                    icfg = new ObservableDynamicICFG<Weight.NoWeight>(null);
                } else {
                    icfg = new ObservableStaticICFG(staticIcfg);
                }
                System.out.println("Application Classes: " + Scene.v().getApplicationClasses().size());
                System.out.println("Reachable Methods: " + Scene.v().getReachableMethods().size());

            }
        });

        long startTime = System.currentTimeMillis();
        PackManager.v().getPack("wjtp").add(transform);
        PackManager.v().getPack("cg").apply();
        PackManager.v().getPack("wjtp").apply();
        long endTime = System.currentTimeMillis();
        long duration = (endTime - startTime);
        System.out.println("! "+ callGraphMode +","+ getBenchName() + "," + duration + "," + icfg.getCallGraphCopy().size());
    }

}
