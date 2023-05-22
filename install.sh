#!/bin/bash
DOCKER_RUN_DIR="$(realpath $(dirname ${BASH_SOURCE[0]}))"
grep -qxF "export PATH=\"${DOCKER_RUN_DIR}/bin:\$PATH\"" ~/.bashrc || echo "export PATH=\"${DOCKER_RUN_DIR}/bin:\$PATH\"" >> ~/.bashrc
grep -qxF "source ${DOCKER_RUN_DIR}/bash-completion/docker-run" ~/.bashrc || echo "source ${DOCKER_RUN_DIR}/bash-completion/docker-run" >> ~/.bashrc
source ~/.bashrc
