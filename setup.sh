#!/bin/bash

## Submodules
git submodule init;
git submodule update;

# ### Java and Maven images
# docker pull openjdk:11;
# docker pull maven:3.9.8-eclipse-temurin-8;

# ### Defects4J image
# cd benchmarks/defects4j;
# cpanm --installdeps .;
# ./init.sh;
# cd ../..;

# ### GitBug-Java
# cd benchmarks/gitbug-java;
# chmod +x gitbug-java;
# poetry install --no-root;
# # Skip setup if in CI
# if [ -z "$CI" ]; then
#  poetry run ./gitbug-java setup;
# fi

### BugsInPy
docker build -t bugsinpy -f Dockerfile.bugsinpy .
# Start the container and keep it running
docker run -d --name bugsinpy-container -it bugsinpy tail -f /dev/null
# Initialize container
docker exec bugsinpy-container bash -c "mkdir -p /bugsinpy/framework/bin/temp && chmod +x /bugsinpy/framework/bin/*"
