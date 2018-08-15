package experiments.main;

import experiments.dacapo.CallGraphMode;
import experiments.dacapo.CallGraphRunner;

import java.io.File;
import java.io.IOException;

public class CallGraphTimer {

        static String[] dacapo = new String[]{"antlr", "chart", "eclipse", "hsqldb", "jython", "luindex", "lusearch",
                "pmd", "fop", "xalan", "bloat"};

        public static void main(String... args) {
            for (CallGraphMode callGraphMode : CallGraphMode.values()){
                for (String bench : dacapo) {
                        if (ignore(bench)) {
                            continue;
                        }
                        String javaHome = System.getProperty("java.home");
                        String javaBin = javaHome +
                                File.separator + "bin" +
                                File.separator + "java";

                        ProcessBuilder builder = new ProcessBuilder(new String[]{javaBin, "-Xmx12g", "-Xss164m", "-cp", System.getProperty("java.class.path"), CallGraphRunner.class.getName(),  args[0], bench, callGraphMode.name()});
                        builder.inheritIO();
                        Process process;
                        try {
                            process = builder.start();
                            process.waitFor();
                        } catch (IOException | InterruptedException e) {
                            e.printStackTrace();
                        }
                }
            }
        }

        private static boolean ignore(String rule) {
            return rule.startsWith("#");
        }

}
