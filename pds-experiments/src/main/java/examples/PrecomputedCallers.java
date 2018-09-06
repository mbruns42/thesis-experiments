package examples;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.PrintStream;
import java.util.Set;

public class PrecomputedCallers{

    public void precomputedCaller(File file, Set<Category> set) throws FileNotFoundException {
        FormattedPrinter printer = new CategoryPrinter();
        seedMethod(file, set, printer);
    }
    public void seedMethod(File file, Set<Category> set, FormattedPrinter printer) throws FileNotFoundException {
        PrintStream stream = new PrintStream(file);
        for (Category category : set)
            printer.print(stream, category);
    }
    interface FormattedPrinter{
        void print(PrintStream stream, Category category);
    }
    class CategoryPrinter implements FormattedPrinter{
        public void print(PrintStream stream, Category category) {
            String formattedCategory = format(category);
            stream.print(formattedCategory);
            if (category.hasSubcategory()){
                FormattedPrinter printer = new SubcategoryPrinter();
                printer.print(stream, category.getSubcategory());
            }
        }
        private String format(Category category){ return ""; }
    }
    class SubcategoryPrinter implements FormattedPrinter{
        public void print(PrintStream stream, Category category) {
            String formattedSubcategory = format(category);
            stream.print(formattedSubcategory);
            stream.close();
        }
        private String format(Category category){ return ""; }
    }

    class Category{
        public boolean hasSubcategory(){
            return true;
        }
        public Category getSubcategory(){
            return new Category();
        }
    }
}