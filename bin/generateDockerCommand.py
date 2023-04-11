#!/usr/bin/env python

import argparse
import os
import sys
from typing import Any, Dict, List

from utils import log, printDockerCommand, runCommand
from plugins.core import CorePlugin
from plugins.docker_ros import DockerRosPlugin


def parseArguments():

    class DockerRunArgumentParser(argparse.ArgumentParser):

        def print_help(self, file=None):
            super().print_help(file=sys.stderr if file is None else file)

        def format_help(self):
            docker_run_help = runCommand("docker run --help")[0]
            separator = f"\n{'-' * 80}\n\n"
            return docker_run_help + separator + super().format_help()

    parser = DockerRunArgumentParser(prog="docker-run",
                                     description="Executes `docker run` with the following features enabled by default, each of which can be disabled individually: "
                                                 "container removal after exit, interactive tty, current directory name as container name, GPU support, X11 GUI forwarding. "
                                                 "Passes any additional arguments to `docker run`. "
                                                 "Executes `docker exec` instead if a container with the specified name (`--name`) is already running.",
                                     add_help=False)

    parser.add_argument("--help", action="help", default=argparse.SUPPRESS, help="show this help message and exit")
    parser.add_argument("--name", default=os.path.basename(os.getcwd()), help="container name; generates `docker exec` command if already running")
    parser.add_argument("--no-name", action="store_true", help="disable automatic container name (current directory)")
    parser.add_argument("--verbose", action="store_true", help="print generated command")
    parser.add_argument("--image", help="image name")
    parser.add_argument("--cmd", nargs="*", default=[], help="command to execute in container")

    # plugin args
    CorePlugin.addArguments(parser)
    DockerRosPlugin.addArguments(parser)

    args, unknown = parser.parse_known_args()

    return args, unknown


def buildDockerCommand(args: Dict[str, Any], unknown_args: List[str]) -> str:
    """Builds an executable `docker run` or `docker exec` command based on the arguments.

    Args:
        TODO

    Returns:
        str: executable `docker run` or `docker exec` command
    """

    # check for running container
    if args["no_name"]:
        args["name"] = None
    new_container = False
    running_containers = runCommand('docker ps --format "{{.Names}}"')[0].split('\n')
    new_container = not (args["name"] in running_containers)

    if new_container: # docker run

        log("Starting new container ..." )
        docker_cmd = ["docker", "run"]

        # name
        if args["name"] is not None and len(args["name"]) > 0:
            docker_cmd += [f"--name {args['name']}"]

        # plugin flags
        docker_cmd += CorePlugin.getRunFlags(args, unknown_args)
        docker_cmd += DockerRosPlugin.getRunFlags(args, unknown_args)

    else: # docker exec

        log(f"Attaching to running container '{args['name']}' ...")
        docker_cmd = ["docker", "exec"]

        docker_cmd += CorePlugin.getExecFlags(args, unknown_args)
        docker_cmd += DockerRosPlugin.getExecFlags(args, unknown_args)

    # append all extra args
    docker_cmd += unknown_args

    if new_container: # docker run

        # image
        if args["image"] is not None and len(args["image"]) > 0:
            docker_cmd += [args["image"]]

        # command
        if args["cmd"] is not None and len(args["cmd"]) > 0:
            docker_cmd += [args["cmd"]]

    else: # docker exec

        # name
        docker_cmd += [args["name"]]

        # command
        if args["cmd"] is not None and len(args["cmd"]) > 0:
            docker_cmd += [args["cmd"]]
        else:
            docker_cmd += ["bash"]

    return " ".join(docker_cmd)


def main():

    args, unknown_args = parseArguments()
    
    cmd = buildDockerCommand(vars(args), unknown_args)
    print(cmd)
    if args.verbose:
        printDockerCommand(cmd)


if __name__ == "__main__":

    main()
