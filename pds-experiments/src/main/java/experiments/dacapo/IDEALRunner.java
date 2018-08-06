package experiments.dacapo;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.Collection;
import java.util.Collections;
import java.util.Map;
import java.util.Map.Entry;
import java.util.concurrent.TimeUnit;

import com.google.common.collect.Table;

import boomerang.BoomerangOptions;
import boomerang.DefaultBoomerangOptions;
import boomerang.WeightedForwardQuery;
import boomerang.debugger.Debugger;
import boomerang.jimple.Statement;
import boomerang.jimple.Val;
import boomerang.results.ForwardBoomerangResults;
import ideal.IDEALAnalysis;
import ideal.IDEALAnalysisDefinition;
import ideal.IDEALResultHandler;
import ideal.IDEALSeedSolver;
import soot.G;
import soot.PackManager;
import soot.Scene;
import soot.SceneTransformer;
import soot.SootClass;
import soot.SootMethod;
import soot.Transform;
import soot.Unit;
import soot.jimple.Stmt;
import soot.jimple.toolkits.ide.icfg.BiDiInterproceduralCFG;
import soot.jimple.toolkits.ide.icfg.JimpleBasedInterproceduralCFG;
import sync.pds.solver.WeightFunctions;
import typestate.TransitionFunction;
import typestate.finiteautomata.ITransition;
import typestate.finiteautomata.TypeStateMachineWeightFunctions;

public class IDEALRunner extends SootSceneSetupDacapo  {

  public IDEALRunner(String benchmarkFolder, String benchFolder) {
		super(benchmarkFolder, benchFolder);
	}

protected IDEALAnalysis<TransitionFunction> createAnalysis() {
    String className = System.getProperty("rule");
    try {
    	final JimpleBasedInterproceduralCFG icfg = new JimpleBasedInterproceduralCFG(false);
    	System.out.println("Reachable Methods" +  Scene.v().getReachableMethods().size());
		final TypeStateMachineWeightFunctions genericsType = (TypeStateMachineWeightFunctions) Class.forName(className).getConstructor()
          .newInstance();
		
		return new IDEALAnalysis<TransitionFunction>(new IDEALAnalysisDefinition<TransitionFunction>() {
			

			@Override
			public Collection<WeightedForwardQuery<TransitionFunction>> generate(SootMethod method, Unit stmt, Collection<SootMethod> calledMethod) {
				if(!method.getDeclaringClass().isApplicationClass())
					return Collections.emptyList();
				return genericsType.generateSeed(method, stmt, calledMethod);
			}

			@Override
			public WeightFunctions<Statement, Val, Statement, TransitionFunction> weightFunctions() {
				return genericsType;
			}

			@Override
			public BiDiInterproceduralCFG<Unit, SootMethod> icfg() {
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
				return new Debugger<>();
//				File file = new File("idealDebugger/" + solver.getSeed());
//				file.getParentFile().mkdirs();
//				return new IDEVizDebugger<>(new File("idealDebugger/" + solver.getSeed()), icfg);
			}
			
			@Override
			public IDEALResultHandler<TransitionFunction> getResultHandler() {
				return new IDEALResultHandler<TransitionFunction>() {
					@Override
					public void report(WeightedForwardQuery<TransitionFunction> seed,
							ForwardBoomerangResults<TransitionFunction> res) {
						 File file = new File(outputFile);
				          boolean fileExisted = file.exists();
				          FileWriter writer;
				          try {
				              writer = new FileWriter(file, true);
				              if(!fileExisted)
				                  writer.write(
				                          "Analysis;Rule;Seed;SeedStatement;SeedMethod;SeedClass;Is_In_Error;Timedout;AnalysisTimes;PropagationCount;VisitedMethod;ReachableMethods;CallRecursion;FieldLoop;MaxAccessPath;MaxMemory\n");
			                  writer.write(asCSVLine(seed, res));
				              writer.close();
				          } catch (IOException e1) {
				              // TODO Auto-generated catch block
				              e1.printStackTrace();
				          }
				//
						super.report(seed, res);
					}
				};
			}
		}){};
    	
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

  private IDEALAnalysis<TransitionFunction> analysis;
  protected long analysisTime;
private String outputFile;

  public void run(final String outputFile) {
    G.v().reset();
    this.outputFile = outputFile;
    setupSoot();
    Transform transform = new Transform("wjtp.ifds", new SceneTransformer() {
      protected void internalTransform(String phaseName,
          @SuppressWarnings("rawtypes") Map options) {
        if (Scene.v().getMainMethod() == null)
          throw new RuntimeException("No main class existing.");
        for(SootClass c : Scene.v().getClasses()){
        	for(String app : IDEALRunner.this.getApplicationClasses()){
        		if(c.isApplicationClass())
        			continue;
        		if(c.toString().startsWith(app.replace("<",""))){
        			c.setApplicationClass();
        		}
        	}
        }
        System.out.println("Application Classes: " + Scene.v().getApplicationClasses().size());
        IDEALRunner.this.getAnalysis().run();

      }
    });

//    PackManager.v().getPack("wjtp").add(new Transform("wjtp.prep", new PreparationTransformer()));
    PackManager.v().getPack("wjtp").add(transform);
    PackManager.v().getPack("cg").apply();
    PackManager.v().getPack("wjtp").apply();
  }

    private String asCSVLine(WeightedForwardQuery<TransitionFunction> key, ForwardBoomerangResults<TransitionFunction> forwardBoomerangResults) {
    		//("Analysis;Rule;Seed;SeedStatement;SeedMethod;SeedClass;Is_In_Error;Timedout;AnalysisTimes;PropagationCount;VisitedMethod;ReachableMethods;CallRecursion;FieldLoop;MaxAccessPath\n");
    		String analysis = "ideal";
    		String rule = System.getProperty("ruleIdentifier");
    		Stmt seedStmt = key.stmt().getUnit().get();
    		SootMethod seedMethod = key.stmt().getMethod();
    		SootClass seedClass = seedMethod.getDeclaringClass();
    		boolean isInErrorState = isInErrorState(key,forwardBoomerangResults);
    		boolean isTimedout = getAnalysis().isTimedout(key);
    		long analysisTime = getAnalysis().getAnalysisTime(key).elapsed(TimeUnit.MILLISECONDS);
    		int propagationCount = forwardBoomerangResults.getStats().getForwardReachesNodes().size();
    		int visitedMethods = forwardBoomerangResults.getStats().getCallVisitedMethods().size();
    		int reachableMethods = Scene.v().getReachableMethods().size();
    		boolean containsCallLoop = forwardBoomerangResults.containsCallRecursion();
    		boolean containsFieldLoop = forwardBoomerangResults.containsFieldLoop();
    		long usedMemory = forwardBoomerangResults.getMaxMemory();
        return String.format("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;\n",analysis,rule,key,seedStmt,seedMethod,seedClass,isInErrorState,isTimedout,analysisTime,propagationCount,visitedMethods,reachableMethods,containsCallLoop,containsFieldLoop, 0, usedMemory);
    }

    private boolean isInErrorState(WeightedForwardQuery<TransitionFunction> key, ForwardBoomerangResults<TransitionFunction> forwardBoomerangResults) {
        Table<Statement, Val, TransitionFunction> objectDestructingStatements = forwardBoomerangResults.getObjectDestructingStatements();
        for(Table.Cell<Statement,Val,TransitionFunction> c : objectDestructingStatements.cellSet()){
            for(ITransition t : c.getValue().values()){
                if(t.to() != null){
                    if(t.to().isErrorState()){
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
  
  protected long getBudget(){
	  return TimeUnit.MINUTES.toMillis(10);
  }
}
