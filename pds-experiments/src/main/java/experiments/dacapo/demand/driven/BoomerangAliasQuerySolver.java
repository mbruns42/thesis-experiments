package experiments.dacapo.demand.driven;

import boomerang.BackwardQuery;
import boomerang.Boomerang;
import boomerang.DefaultBoomerangOptions;
import boomerang.ForwardQuery;
import boomerang.callgraph.ObservableICFG;
import boomerang.debugger.Debugger;
import boomerang.debugger.IDEVizDebugger;
import boomerang.results.BackwardBoomerangResults;
import boomerang.seedfactory.SimpleSeedFactory;
import com.beust.jcommander.internal.Sets;
import soot.SootMethod;
import soot.Unit;
import wpds.impl.Weight.NoWeight;

import java.io.File;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.nio.file.Files;
import java.util.Set;

public class BoomerangAliasQuerySolver extends AliasQuerySolver {

    public static boolean VISUALIZATION = false;
    protected final ObservableICFG<Unit, SootMethod> icfg;
    protected final SimpleSeedFactory seedFactory;
    private Boomerang solver;
    private Set<BackwardQuery> crashed = Sets.newHashSet();

    public BoomerangAliasQuerySolver(int timeoutMS, ObservableICFG<Unit, SootMethod> icfg, SimpleSeedFactory seedFactory) {
        super(timeoutMS);
        this.icfg = icfg;
        this.seedFactory = seedFactory;
    }

    @Override
    protected boolean internalComputeQuery(AliasQuery q) {
        if (q.getLocalA().equals(q.getLocalB()))
            return true;
        Set<ForwardQuery> allocsA = getPointsTo(q.queryA, q);
        if (allocsA.isEmpty())
            return false;
        Set<ForwardQuery> allocsB = getPointsTo(q.queryB, q);
        for (ForwardQuery a : allocsA) {
            if (allocsB.contains(a))
                return true;
        }
        return false;
    }


    private Set<ForwardQuery> getPointsTo(BackwardQuery q, AliasQuery aliasQuery) {
        if (crashed.contains(q)) {
            throw new SkipQueryException();
        }
        recreateSolver(q, aliasQuery);
        BackwardBoomerangResults<NoWeight> res = solver.solve(q);
        solver.debugOutput();
        if (res.isTimedout()) {
            crashed.add(q);
        }
        return res.getAllocationSites().keySet();
    }

    private void recreateSolver(BackwardQuery q, AliasQuery aliasQuery) {
        DefaultBoomerangOptions options = new DefaultBoomerangOptions() {
            @Override
            public boolean arrayFlows() {
                return true;
            }

            @Override
            public boolean staticFlows() {
                return true;
            }

            @Override
            public int analysisTimeoutMS() {
                return BoomerangAliasQuerySolver.this.timeoutMS;
            }
        };
        solver = new Boomerang(options) {
            @Override
            public ObservableICFG<Unit, SootMethod> icfg() {
                return icfg;
            }

            @Override
            public Debugger createDebugger() {
                if (!VISUALIZATION) {
                    return new Debugger<>();
                }
                File ideVizFile;
                try {
                    ideVizFile = new File(
                            "target/IDEViz/" + URLEncoder.encode(aliasQuery.toString(), "UTF-8") + "/" + URLEncoder.encode(q.toString(), "UTF-8") + ".json");
                } catch (UnsupportedEncodingException e1) {
                    throw new RuntimeException("Wrong encoding error for creating IDEViz output!");
                }
                if (!ideVizFile.getParentFile().exists()) {
                    try {
                        Files.createDirectories(ideVizFile.getParentFile().toPath());
                    } catch (IOException e) {
                        throw new RuntimeException("Was not able to create directories for IDEViz output!" + ideVizFile.getParentFile().toPath());
                    }
                }
                return new IDEVizDebugger(ideVizFile, icfg);
            }

            @Override
            public SimpleSeedFactory getSeedFactory() {
                return seedFactory;
            }
        };
    }

}
