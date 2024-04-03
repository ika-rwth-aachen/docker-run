#!/usr/bin/env python

import argparse
import importlib
import os
import sys
from typing import Any, Dict, List, Tuple

import docker_run
from docker_run.utils import log, runCommand, validDockerContainerName
from docker_run.plugins.plugin import Plugin

# automatically load all available plugins inheriting from `Plugin`
PLUGINS = []
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")
for file_name in os.listdir(PLUGINS_DIR):
    if file_name.endswith(".py") and file_name != "plugin.py":
        module_name = os.path.splitext(file_name)[0]
        module = importlib.import_module(f"docker_run.plugins.{module_name}")
        for name, cls in module.__dict__.items():
            if isinstance(cls, type) and issubclass(cls, Plugin) and cls is not Plugin:
                PLUGINS.append(cls)

DEFAULT_CONTAINER_NAME = validDockerContainerName(os.path.basename(os.getcwd()))

def parseArguments() -> Tuple[argparse.Namespace, List[str], List[str]]:

    class DockerRunArgumentParser(argparse.ArgumentParser):

        def print_help(self, file=None):
            super().print_help(file=sys.stderr if file is None else file)

        def format_help(self):
            parser._actions.sort(key=lambda x: x.dest)
            parser._action_groups[1]._group_actions.sort(key=lambda x: x.dest)
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
    parser.add_argument("--image", help="image name (may also be specified without --image as last argument before command)")
    parser.add_argument("--name", default=DEFAULT_CONTAINER_NAME, help="container name; generates `docker exec` command if already running")
    parser.add_argument("--no-name", action="store_true", help="disable automatic container name (current directory)")
    parser.add_argument("--verbose", action="store_true", help="print generated command")
    parser.add_argument("--version", action="store_true", help="show program's version number and exit")

    # plugin args
    for plugin in PLUGINS:
        plugin.addArguments(parser)

    args, unknown = parser.parse_known_args()

    # separate unknown args before and after --
    try:
        double_dash_index = unknown.index("--")
        unknown_args = unknown[:double_dash_index]
        cmd_args = unknown[double_dash_index+1:]
    except ValueError:
        unknown_args = unknown
        cmd_args = []

    # version
    if args.version:
        log(f"{docker_run.__name__} v{docker_run.__version__}")
        parser.exit()

    return args, unknown_args, cmd_args


def buildDockerCommand(args: Dict[str, Any], unknown_args: List[str] = [], cmd_args: List[str] = []) -> str:
    """Builds an executable `docker run` or `docker exec` command based on the given arguments.

    Args:
        args (Dict[str, Any]): known arguments that are handled explicitly
        unknown_args (List[str], optional): extra arguments to include in `docker` command ([])
        cmd_args (List[str], optional): extra arguments to append at the end of `docker` command ([])

    Returns:
        str: executable `docker run` or `docker exec` command
    """

    # check for running container
    if args["no_name"]:
        args["name"] = None
        new_container = True
    else:
        new_container = False
        running_containers = runCommand('docker ps --format "{{.Names}}"')[0].split('\n')
        new_container = not (args["name"] in running_containers)
        if not new_container and args["image"] is not None and len(args["image"]) > 0:
            args["name"] = None if args["name"] == DEFAULT_CONTAINER_NAME else args["name"]
            new_container = True

    if new_container: # docker run

        log_msg = f"Starting new container "
        if args["name"] is not None:
            log_msg += f"'{args['name']}'"
        log(log_msg + " ...")
        docker_cmd = ["docker", "run"]

        # name
        if args["name"] is not None and len(args["name"]) > 0:
            docker_cmd += [f"--name {args['name']}"]

        # plugin flags
        for plugin in PLUGINS:
            docker_cmd += plugin.getRunFlags(args, unknown_args)

    else: # docker exec

        log(f"Attaching to running container '{args['name']}' ...")
        docker_cmd = ["docker", "exec"]

        # plugin flags
        for plugin in PLUGINS:
            docker_cmd += plugin.getExecFlags(args, unknown_args)

    # append all extra args
    docker_cmd += unknown_args

    if new_container: # docker run

        # image
        if args["image"] is not None and len(args["image"]) > 0:
            docker_cmd += [args["image"]]

        # command
        docker_cmd += cmd_args

    else: # docker exec

        # name
        docker_cmd += [args["name"]]

        # command
        if len(cmd_args) > 0:
            docker_cmd += cmd_args
        else:
            docker_cmd += ["bash"] # default exec command

    # plugin modifications
    for plugin in PLUGINS:
        docker_cmd = plugin.modifyFinalCommand(docker_cmd, args, unknown_args)

    return " ".join(docker_cmd)


def printDockerCommand(cmd: str):
    """Prints a docker command in human-readable way by line-breaking on each new argument.

    Args:
        cmd (str): docker command
    """

    components = cmd.split()
    log(f"{components[0]} {components[1]}", end="")

    for c in components[2:]:
        if c.startswith("-"):
            log(f" \\\n  {c}", end="")
        else:
            log(f" {c}", end="")
    log("")


def generateDockerCommand():

    args, unknown_args, cmd_args = parseArguments()

    cmd = buildDockerCommand(vars(args), unknown_args, cmd_args)
    print(cmd)
    if args.verbose:
        printDockerCommand(cmd)
