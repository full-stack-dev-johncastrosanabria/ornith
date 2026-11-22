#!/bin/sh
# Compiles the sources and the acceptance tests with Java 21, then runs JUnit 5 (no Maven, no network).
set -eu
JDK=/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home/bin
CP='/Users/johnbenjamincastrosanabria/Developer/ornith/runtimes/java-junit/*'
rm -rf build
mkdir -p build/main build/test
"$JDK/javac" -J-XX:-UsePerfData -d build/main $(find src/main/java -name '*.java')
"$JDK/javac" -J-XX:-UsePerfData -d build/test -cp "build/main:$CP" $(find tests -name '*.java')
exec "$JDK/java" -XX:-UsePerfData -cp "build/main:build/test:$CP" LabTestMain
