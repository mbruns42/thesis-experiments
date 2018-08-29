package experiments.dacapo;

import java.io.File;

public class FinkOrIDEALDacapoRunner extends SootSceneSetupDacapo {

    public FinkOrIDEALDacapoRunner(String benchmarkFolder, String benchFolder, String callGraphMode) {
        super(benchmarkFolder, benchFolder, callGraphMode);
    }

    public static void main(String[] args){
        System.setProperty("analysis", args[0]);
        System.setProperty("rule", args[1]);
        new FinkOrIDEALDacapoRunner(args[2], args[3], args[4]).run();
    }

    private void run() {
        String analysis = System.getProperty("analysis");

        String library_jar_files = benchProperties.getProperty("application_includes");
        System.setProperty("application_includes", library_jar_files);
        if (analysis == null)
            throw new RuntimeException("Add -Danalysis to JVM arguments");
        String rule = System.getProperty("rule");
        System.setProperty("ruleIdentifier", rule);
        String outputDirectory = "outputDacapo";
        File outputDir = new File(outputDirectory);
        if (!outputDir.exists())
            outputDir.mkdir();
        String outputFile = outputDirectory + File.separator + getMainClass() + "-" + analysis + "-" + rule + "-"
                + callGraphMode + ".csv";
        System.setProperty("outputCsvFile", outputFile);

        System.out.println("Writing output to file " + outputFile);
        if (analysis.equalsIgnoreCase("ideal")) {
            System.setProperty("rule", selectTypestateMachine(System.getProperty("rule")).getName());
            System.out.println("Running " + System.getProperty("rule"));
            System.setProperty("dacapo", "true");
            new IDEALRunner(benchmarkFolder, project, callGraphMode.toString()).run(outputFile);
        }
    }

    public static Class selectTypestateMachine(String rule) {
        switch (rule) {
            case "IteratorHasNext":
                return typestate.impl.statemachines.HasNextStateMachine.class;
            case "KeyStore":
                return typestate.impl.statemachines.KeyStoreStateMachine.class;
            case "URLConnection":
                return typestate.impl.statemachines.URLConnStateMachine.class;
            case "EmptyVector":
                return typestate.impl.statemachines.VectorStateMachine.class;
            case "InputStreamCloseThenRead":
                return typestate.impl.statemachines.alloc.InputStreamStateMachine.class;
            case "PipedInputStream":
                return typestate.impl.statemachines.PipedInputStreamStateMachine.class;
            case "OutputStreamCloseThenWrite":
                return typestate.impl.statemachines.alloc.OutputStreamStateMachine.class;
            case "PipedOutputStream":
                return typestate.impl.statemachines.PipedOutputStreamStateMachine.class;
            case "PrintStream":
                return typestate.impl.statemachines.alloc.PrintStreamStateMachine.class;
            case "PrintWriter":
                return typestate.impl.statemachines.alloc.PrintWriterStateMachine.class;
            case "Signature":
                return typestate.impl.statemachines.SignatureStateMachine.class;
        }
        throw new RuntimeException("Select an appropriate rule");
    }

}
