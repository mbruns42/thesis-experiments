package experiments.dacapo.demand.driven;

import boomerang.BackwardQuery;
import boomerang.Query;
import boomerang.callgraph.ObservableICFG;
import boomerang.callgraph.ObservableStaticICFG;
import boomerang.jimple.Statement;
import boomerang.jimple.Val;
import boomerang.preanalysis.PreTransformBodies;
import boomerang.seedfactory.SeedFactory;
import com.google.common.base.Joiner;
import com.google.common.collect.HashMultimap;
import com.google.common.collect.Lists;
import com.google.common.collect.Multimap;
import com.google.common.collect.Sets;
import experiments.dacapo.SootSceneSetupDacapo;
import heros.solver.Pair;
import soot.*;
import soot.jimple.AssignStmt;
import soot.jimple.FieldRef;
import soot.jimple.InstanceFieldRef;
import soot.jimple.Stmt;
import soot.jimple.toolkits.ide.icfg.JimpleBasedInterproceduralCFG;
import wpds.impl.Weight.NoWeight;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.util.*;

public class DataraceClientExperiment extends SootSceneSetupDacapo {

    public static void main(String[] args) {
        DataraceClientExperiment expr = new DataraceClientExperiment(args[0], args[1]);
        expr.run();
    }


    protected Set<Pair<Local, Stmt>> queries = Sets.newHashSet();
    private ObservableICFG<Unit, SootMethod> icfg;
    private static final int TIMEOUT_IN_MS = 1000;
    protected Multimap<SootField, BackwardQuery> fieldToQuery = HashMultimap.create();

    public DataraceClientExperiment(String benchmarkFolder, String benchFolder) {
        super(benchmarkFolder, benchFolder);
    }

    public void run() {
        setupSoot();
        PackManager.v().getPack("wjtp").add(new Transform("wjtp.prepare", new PreTransformBodies()));
        Transform transform = new Transform("wjtp.ifds", new SceneTransformer() {

            protected void internalTransform(String phaseName, @SuppressWarnings("rawtypes") Map options) {

                icfg = new ObservableStaticICFG(new JimpleBasedInterproceduralCFG(false));
                System.out.println("Application Classes: " + Scene.v().getApplicationClasses().size());
                final SeedFactory<NoWeight> seedFactory = new SeedFactory<NoWeight>() {
                    @Override
                    public ObservableICFG<Unit, SootMethod> icfg() {
                        return icfg;
                    }

                    @Override
                    protected Collection<? extends Query> generate(SootMethod method, Stmt u,
                                                                   Collection calledMethods) {
                        if (!method.hasActiveBody())
                            return Collections.emptySet();
                        if (!isApplicationMethod(method.getSignature())) {
                            return Collections.emptySet();
                        }
                        if (u.containsFieldRef() && !method.isJavaLibraryMethod()) {
                            FieldRef fieldRef = u.getFieldRef();
                            if (u instanceof AssignStmt && fieldRef instanceof InstanceFieldRef) {
                                InstanceFieldRef ifr = (InstanceFieldRef) fieldRef;
                                BackwardQuery q = new BackwardQuery(new Statement(u, method),
                                        new Val(ifr.getBase(), method));
                                fieldToQuery.put(ifr.getField(), q);
                                return Collections.singleton(q);
                            }
                        }
                        return Collections.emptySet();
                    }

                    private boolean isApplicationMethod(String name) {
                        for (String s : getApplicationClasses()) {
                            if (name.startsWith(s))
                                return true;
                        }
                        return false;
                    }

                };
                Collection<Query> seeds = seedFactory.computeSeeds();
                System.out.println("Points-To Queries: " + seeds.size());
                Set<AliasQuery> dataraceQueries = Sets.newHashSet();
                Set<BackwardQuery> excludeDoubles = Sets.newHashSet();
                int skipped = 0;
                for (SootField field : fieldToQuery.keySet()) {
                    Collection<BackwardQuery> backwardQueries = fieldToQuery.get(field);
                    for (BackwardQuery q1 : backwardQueries) {
                        excludeDoubles.add(q1);
                        for (BackwardQuery q2 : backwardQueries) {
                            if (excludeDoubles.contains(q2))
                                continue;
                            if (isDataracePair(q1.stmt(), q2.stmt())) {
                                AliasQuery q = new AliasQuery(q1, q2);
                                if (!sparkReportsDataRace(new AliasQuery(q1, q2))) {
                                    skipped++;
                                    continue;
                                }
                                dataraceQueries.add(q);
                            }
                        }
                    }
                }
                BoomerangAliasQuerySolver bSolver = new BoomerangAliasQuerySolver(TIMEOUT_IN_MS, icfg, seedFactory);
                System.out.println("Solving queries " + dataraceQueries.size() + " skipped, cause spark reports false:" + skipped);

                int solved = 0;
                for (AliasQuery q : dataraceQueries) {
                    if (solved % 200 == 0) {
                        System.out.println(String.format("Status, #Solved queries: %s ", solved));
                    }
                    AliasQueryExperimentResult bRes = bSolver.computeQuery(q);
                    solved++;
                    File f = new File("outputDataraceDacapo" + File.separator + DataraceClientExperiment.this.getBenchName() + "-datarace.csv");
                    if (!f.getParentFile().exists()) {
                        try {
                            Files.createDirectories(f.getParentFile().toPath());
                        } catch (IOException e) {
                            throw new RuntimeException("Was not able to create directories for IDEViz output!");
                        }
                    }
                    FileWriter writer;
                    try {
                        if (!f.exists()) {
                            writer = new FileWriter(f);
                            LinkedList<String> header = Lists.newLinkedList();
                            header.add("QueryA");
                            header.add("QueryB");
                            header.add("Boomerang_res");
                            header.add("Boomerang_time(ms)");
                            header.add("Boomerang_timeout");
                            writer.write(Joiner.on(";").join(header));
                            writer.write("\n");
                        } else {
                            writer = new FileWriter(f, true);
                        }
                        LinkedList<Object> row = Lists.newLinkedList();

                        row.add(q.queryA);
                        row.add(q.queryB);
                        row.add(bRes.queryResult);
                        row.add(bRes.analysisTimeMs);
                        row.add(bRes.timeout);
                        writer.write(Joiner.on(";").join(row));
                        writer.write("\n");
                        writer.flush();
                        writer.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }

        });

        PackManager.v().getPack("wjtp").add(transform);
        PackManager.v().runPacks();
    }

    protected boolean sparkReportsDataRace(AliasQuery q) {
        Local a = q.getLocalA();
        Local b = q.getLocalB();
        if (a.equals(b)) {
            return false;
        }
        return Scene.v().getPointsToAnalysis().reachingObjects(a)
                .hasNonEmptyIntersection(Scene.v().getPointsToAnalysis().reachingObjects(b));
    }

    protected boolean isDataracePair(Statement s1, Statement s2) {
        boolean a = isFieldLoad(s1.getUnit().get());
        boolean b = isFieldLoad(s2.getUnit().get());
        return !(a && b);
    }

    private boolean isFieldLoad(Stmt s) {
        if (s instanceof AssignStmt) {
            AssignStmt as = (AssignStmt) s;
            return as.getRightOp() instanceof InstanceFieldRef;
        }
        return false;
    }

}
