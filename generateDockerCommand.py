#!/usr/bin/env python

import argparse
import os
import platform
import subprocess
import sys
import tempfile
from typing import List, Tuple


DEV_TARGET_MOUNT = "/docker-ros/ws/src/target"

OS = platform.uname().system
ARCH = platform.uname().machine


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
    parser.add_argument('--help', action='help', default=argparse.SUPPRESS, help='show this help message and exit')

    parser.add_argument('--mwd', action='store_true', help=f'mount current directory into `{DEV_TARGET_MOUNT}`')
    parser.add_argument('--verbose', action='store_true', help='print generated command')

    parser.add_argument('--no-gpu', action='store_true', help='disable automatic GPU support')
    parser.add_argument('--no-it', action='store_true', help='disable automatic interactive tty')
    parser.add_argument('--no-x11', action='store_true', help='disable automatic X11 GUI forwarding')
    parser.add_argument('--no-rm', action='store_true', help='disable automatic container removal')
    parser.add_argument('--no-user', action='store_true', help='disable passing local UID/GID into container')
    parser.add_argument('--no-name', action='store_true', help='disable automatic container name (current directory)')

    parser.add_argument('--name', default=os.path.basename(os.getcwd()), help='container name; generates `docker exec` command if already running')
    parser.add_argument('--image', help='image name')
    parser.add_argument('--cmd', nargs='*', default=[], help='command to execute in container')

    args, unknown = parser.parse_known_args()

    return args, unknown


def log(msg: str, *args, **kwargs):
    """Log message to stderr.
    Args:
        msg (str): log message
    """

    print(msg, file=sys.stderr, *args, **kwargs)


def runCommand(cmd: str, *args, **kwargs) -> Tuple[str, str]:
    """Execute system command.

    Args:
        cmd (str): system command

    Returns:
        Tuple[str, str]: stdout, stderr output
    """

    try:
        output = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, *args, **kwargs)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"System command '{cmd}' failed: {exc.stderr.decode()}")

    return output.stdout.decode(), output.stderr.decode()


def buildDockerCommand(image: str = "",
                       cmd: str = "",
                       name: str = "",
                       gpus: bool = True,
                       interactive: bool = True,
                       x11: bool = True,
                       remove: bool = True,
                       user: bool = True,
                       mount_pwd: bool = False,
                       extra_args: List[str] = []) -> str:
    """Builds an executable `docker run` or `docker exec` command based on the arguments.

    Args:
        image (str, optional): image ("")
        cmd (str, optional): command ("")
        name (str, optional): name ("")
        gpus (bool, optional): enable GPU support (True)
        interactive (bool, optional): enable interactive tty (True)
        x11 (bool, optional): enable X11 GUI forwarding (True)
        remove (bool, optional): enable container removal (True)
        user (bool, optional): enable passing local UID/GID into container (True)
        mount_pwd (bool, optional): enable volume mounting of current directory (False)
        extra_args (List[str], optional): extra arguments to include in `docker` command ([])

    Returns:
        str: executable `docker run` or `docker exec` command
    """

    # check for running container
    new_container = False
    running_containers = runCommand('docker ps --format "{{.Names}}"')[0].split('\n')
    new_container = not (name in running_containers)

    if new_container: # docker run

        log("Starting new container ..." )
        docker_cmd = ["docker", "run"]

        # name
        if name is not None and len(name) > 0:
            docker_cmd += nameFlags(name)

        # container removal
        if remove:
            log("\t - container removal")
            docker_cmd += removeFlags()

        # local user ids
        if user:
            docker_cmd += userFlags()

        # GPU support
        if gpus:
            log("\t - GPU support")
            docker_cmd += gpuSupportFlags()

        # GUI forwarding
        if x11:
            log("\t - GUI fowarding")
            gui_forwarding_kwargs = {}
            if "--network" in extra_args:
                network_arg_index = extra_args.index("--network") + 1
                if network_arg_index < len(extra_args):
                    gui_forwarding_kwargs["docker_network"] = extra_args[network_arg_index]
            docker_cmd += x11GuiForwardingFlags(**gui_forwarding_kwargs)

        # mount current directory to DEV_TARGET_MOUNT
        if mount_pwd:
            log(f"\t - current directory in `DEV_TARGET_MOUNT`")
            docker_cmd += currentDirMountFlags()

    else: # docker exec

        log(f"Attaching to running container '{name}' ...")
        docker_cmd = ["docker", "exec"]

        # local user ids
        if user and runCommand("docker exec docker-run bash -c \"echo \$DOCKER_ROS\"")[0] == "true":
            docker_cmd += userExecFlags()

    # interactive
    if interactive:
        log("\t - interactive")
        docker_cmd += interactiveFlags()

    # timezone
    docker_cmd += timezoneFlags()

    # append all extra args
    docker_cmd += extra_args

    if new_container: # docker run

        # image
        if image is not None and len(image) > 0:
            docker_cmd += [image]

        # command
        if cmd is not None and len(cmd) > 0:
            docker_cmd += [cmd]

    else: # docker exec

        # name
        docker_cmd += [name]

        # command
        if cmd is not None and len(cmd) > 0:
            docker_cmd += [cmd]
        else:
            docker_cmd += ['bash']

    return " ".join(docker_cmd)


def nameFlags(name: str) -> List[str]:

    return [f"--name {name}"]


def timezoneFlags() -> List[str]:

    if OS == "Darwin":
        tz = runCommand("readlink /etc/localtime | sed 's#/var/db/timezone/zoneinfo/##g'")[0]
    else:
        tz = runCommand("cat /etc/timezone")[0][:-1]

    return [f"--env TZ={tz}"]


def removeFlags() -> List[str]:

    return ["--rm"]


def userFlags() -> List[str]:

    return [f"--env DOCKER_UID={os.getuid()}", f"--env DOCKER_GID={os.getgid()}"]

def userExecFlags() -> List[str]:

    return [f"--user {os.getuid()}:{os.getgid()}"]

def interactiveFlags() -> List[str]:

    return ["--interactive", "--tty"]


def gpuSupportFlags() -> List[str]:

    if ARCH == "x86_64":
        return ["--gpus all"]
    elif ARCH == "aarch64" and OS == "Linux":
        return ["--runtime nvidia"]
    else:
        log(f"GPU not supported by `docker-run` on {OS} with {ARCH} architecture")
        return []


def x11GuiForwardingFlags(docker_network: str = "bridge") -> List[str]:

    display = os.environ.get('DISPLAY')
    if display is None:
        return []

    xsock = "/tmp/.X11-unix"
    xauth = tempfile.NamedTemporaryFile(prefix='.docker.xauth.', delete=False).name
    xauth_display = display if OS != "Darwin" else runCommand("ifconfig en0 | grep 'inet '")[0].split()[1] + ":0"
    xauth_output = "ffff" + runCommand(f"xauth nlist {xauth_display}")[0][4:]
    runCommand(f"xauth -f {xauth} nmerge - 2>/dev/null", input=xauth_output.encode())
    os.chmod(xauth, 0o777)

    if docker_network != "host" and not display.startswith(":"):
        display="172.17.0.1:" + display.split(":")[1]
    if OS == "Darwin":
        display="host.docker.internal:" + display.split(":")[1]

    flags = []
    flags.append(f"--env DISPLAY={display}")
    flags.append(f"--env XAUTHORITY={xauth}")
    flags.append(f"--env QT_X11_NO_MITSHM=1")
    flags.append(f"--volume {xauth}:{xauth}")
    flags.append(f"--volume {xsock}:{xsock}")

    return flags


def currentDirMountFlags() -> List[str]:

    return [f"--volume {os.getcwd()}:{DEV_TARGET_MOUNT}"]


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


def main():

    args, unknown_args = parseArguments()
    if args.no_name:
        args.name = None
    cmd = buildDockerCommand(image=args.image,
                             cmd=" ".join(args.cmd),
                             name=args.name,
                             gpus=not args.no_gpu,
                             interactive=not args.no_it,
                             x11=not args.no_x11,
                             remove=not args.no_rm,
                             user=not args.no_user,
                             mount_pwd=args.mwd,
                             extra_args=unknown_args)
    print(cmd)
    if args.verbose:
        printDockerCommand(cmd)


if __name__ == "__main__":

    main()
