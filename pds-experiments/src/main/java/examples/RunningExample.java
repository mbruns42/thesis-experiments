package examples;

import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;

public class RunningExample {
    abstract class Printer {
        public abstract void printAll(Iterator iterator);
    }
    class NewPrinter extends Printer {
        public void printAll(Iterator i) {
            while (i.hasNext()) {
                Object o = i.next();
                System.out.println(o); }
        }
    }
    class OldPrinter extends Printer {
        public void printAll(Iterator i) {
            while (i != null) {
                Object o = i.next();
                System.out.println(o); }
        }
    }
    public static void printWith(Printer printer, Iterator<Item> iterator) {
        printer.printAll(iterator);
    }
    public void otherContextCaller(Set<Item> set){
        Iterator<Item> iterator = set.iterator();
        if (iterator.hasNext()){
            otherContext(iterator);}
    }
    public void otherContext(Iterator<Item> iterator) {
        Printer printer = new OldPrinter();
        printWith(printer, iterator);
    }
    public void seedMethod() {
        HashSet<Item> emptySet = new HashSet<>();
        Iterator<Item> iterator = emptySet.iterator();
        Printer printer = new NewPrinter();
        printWith(printer, iterator);
    }

    class Item {
    }
}
