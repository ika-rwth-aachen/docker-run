#!/bin/bash
DOCKER_RUN_DIR="$(realpath $(dirname ${0}))"
echo "export PATH=\"${DOCKER_RUN_DIR}/bin:\$PATH\"" >> ~/.bashrc
echo "source ${DOCKER_RUN_DIR}/bash-completion/docker-run" >> ~/.bashrc
source ~/.bashrc