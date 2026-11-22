#!/bin/zsh
# D061: JUnit 5 jars for F8-E, copied from the local Maven cache and checked against Maven Central's .sha1 files.
set -eu
ROOT=${0:A:h:h}
DEST="$ROOT/runtimes/java-junit"
M2="$HOME/.m2/repository"
mkdir -p "$DEST"
: > "$DEST/SHA1SUMS"
for a in org/junit/jupiter/junit-jupiter-api/5.12.2 org/junit/jupiter/junit-jupiter-engine/5.12.2 \
         org/junit/platform/junit-platform-launcher/1.12.2 org/junit/platform/junit-platform-engine/1.12.2 \
         org/junit/platform/junit-platform-commons/1.12.2 org/opentest4j/opentest4j/1.3.0 org/apiguardian/apiguardian-api/1.1.2; do
  jar="$M2/$a/${a:h:t}-${a:t}.jar"
  want=$(cut -c1-40 "$jar.sha1")
  got=$(shasum -a 1 "$jar" | cut -c1-40)
  [[ $want == $got ]] || { echo "sha1 mismatch: $jar"; exit 1; }
  cp "$jar" "$DEST/"
  echo "$got  ${jar:t}" >> "$DEST/SHA1SUMS"
done
(cd "$DEST" && shasum -a 1 -c SHA1SUMS)
