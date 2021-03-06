package experiments.dacapo.demand.driven;

import com.google.common.base.Stopwatch;

import java.util.concurrent.TimeUnit;


public abstract class AliasQuerySolver {
    Stopwatch watch = Stopwatch.createUnstarted();
    protected final int timeoutMS;

    public AliasQuerySolver(int timeoutMS) {
        this.timeoutMS = timeoutMS;
    }

    protected AliasQueryExperimentResult computeQuery(AliasQuery q) {
        if (watch.isRunning())
            watch.stop();
        watch.reset();
        watch.start();
        try {
            boolean sol = internalComputeQuery(q);
            watch.stop();
            return new AliasQueryExperimentResult(q, watch.elapsed(TimeUnit.MILLISECONDS) > timeoutMS || sol, watch.elapsed(TimeUnit.MILLISECONDS), watch.elapsed(TimeUnit.MILLISECONDS) > timeoutMS);
        } catch (Exception e) {
            if (!(e instanceof SkipQueryException)) {
                e.printStackTrace();
            }
        }
        return new AliasQueryExperimentResult(q, true, -1, true);
    }

    protected abstract boolean internalComputeQuery(AliasQuery q);
}
