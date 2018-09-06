package examples;

import java.util.ArrayList;
import java.util.List;
import java.util.Vector;

public class PrecomputedCallers{

    public void precomputedCaller() {
        Configuration config = new DefaultConfiguration();
        buildConfig(config, null);
    }
    public void buildConfig(Configuration config, Vector<Option> options) {
        if (options == null)
            options = new Vector<>();
        config.load(options);
    }
    interface Configuration {
        void load(Vector<Option> options);
    }
    class DefaultConfiguration implements Configuration {
        public void load(Vector<Option> options) {
            options.addAll(getDefaultOptions());
            if (options.get(0).isActive()){
                Configuration config = new ExtendedConfiguration();
                buildConfig(config, options);
            }
        }
    }
    class ExtendedConfiguration implements Configuration {
        public void load(Vector<Option> options) {
            Option header = options.get(0);
        }
    }
    public static List<Option> getDefaultOptions(){ return new ArrayList<>(); }

    abstract class Option {
        public abstract boolean isActive();
    }

}