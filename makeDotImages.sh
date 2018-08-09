#!/bin/bash

for file in $1*.dot
    do
        echo $file
        filename="${file%.*}"
        dot -Tpng $file > $filename.png
    done