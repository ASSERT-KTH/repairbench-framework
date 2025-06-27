#!/bin/bash

### Submodules
git submodule init;
git submodule update;

### Java and Maven images
docker pull openjdk:11;
docker pull maven:3.9.8-eclipse-temurin-8;

### Defects4J image
cd benchmarks/defects4j;
cpanm --installdeps .;
./init.sh;
cd ../..;

### GitBug-Java
cd benchmarks/gitbug-java;
chmod +x gitbug-java;
poetry install --no-root;
# Skip setup if in CI
if [ -z "$CI" ]; then
 poetry run ./gitbug-java setup;
fi

### BugsInPy
cd benchmarks/BugsInPy;
git checkout docker;
git pull origin docker;
docker build -t bugsinpy .;
# Start the container and keep it running
docker run -d --name bugsinpy-container -it bugsinpy tail -f /dev/null;
docker exec -it bugsinpy-container ./init.sh;
cd ../..;
