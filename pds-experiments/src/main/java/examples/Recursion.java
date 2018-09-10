package examples;

public class Recursion {

    static Value recursion(Value v, Type t){
        if (staticallyUnknown(v)){
            return t.value();
        } else {
            return recursion(v, t);
        }
    }

    static boolean staticallyUnknown(Value v){
        return true;
    }


    class Value{ }
    class Type{
        Value value(){
            return new Value();
        }
    }
}
