#!/usr/bin/env python

import argparse
import os
import platform
import subprocess
import sys
import tempfile
from typing import List, Tuple


DEV_TARGET_MOUNT = "/home/lutix/ws/src/target"

OS = platform.uname().system
ARCH = platform.uname().machine


def parseArguments():

    parser = argparse.ArgumentParser(description="Generates a `docker run` with the following properties enabled by default: "
                                                 "interactive tty, remove container after stop, GUI forwarding, GPU support, timezone. "
                                                 "Generates a `docker exec` command to attach to a running container, if `--name` is specified. "
                                                 "Note that the command is printed to `stderr`.")

    parser.add_argument('--dev', action='store_true', help=f'Mount current directory into `{DEV_TARGET_MOUNT}`') # TODO: review thread
    parser.add_argument('--verbose', action='store_true', help='Print generated command')

    parser.add_argument('--no-isolated', action='store_true', help='Disable automatic network isolation') # TODO: review thread
    parser.add_argument('--no-gpu', action='store_true', help='Disable automatic GPU support')
    parser.add_argument('--no-it', action='store_true', help='Disable automatic interactive tty')
    parser.add_argument('--no-x11', action='store_true', help='Disable automatic X11 GUI forwarding')
    parser.add_argument('--no-rm', action='store_true', help='Disable automatic container removal')

    parser.add_argument('--name', default=os.path.basename(os.getcwd()), help='Container name; generates `docker exec` command if already running')
    parser.add_argument('--image', help='Image name') # TODO: review thread: require image name?
    parser.add_argument('--cmd', nargs='*', default=[], help='Command to execute in container')

    args, unknown = parser.parse_known_args()

    return args, unknown


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
        raise RuntimeError(f"System command '{cmd}' failed: {exc}")

    return output.stdout.decode(), output.stderr.decode()


def buildDockerCommand(image: str = "",
                       cmd: str = "",
                       name: str = "",
                       isolated: bool = True,
                       gpus: bool = True,
                       interactive: bool = True,
                       x11: bool = True,
                       remove: bool = True,
                       mount_pwd: bool = False,
                       extra_args: List[str] = []) -> str:
    """Builds an executable `docker run` or `docker exec` command based on the arguments.

    Args:
        image (str, optional): image ("")
        cmd (str, optional): command ("")
        name (str, optional): name ("")
        isolated (bool, optional): enable network isolation (True)
        gpus (bool, optional): enable GPU support (True)
        interactive (bool, optional): enable interactive tty (True)
        x11 (bool, optional): enable X11 GUI forwarding (True)
        remove (bool, optional): enable container removal (True)
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

        print("Starting new container ...")
        docker_cmd = ["docker", "run"]

        # name
        if name is not None and len(name) > 0:
            docker_cmd += nameFlags(name)

        # container removal
        if remove:
            print("\t - container removal")
            docker_cmd += removeFlags()
        
        # network isolation
        if not isolated:
            print("\t - host network")
            docker_cmd += hostNetworkFlags()
        
        # GPU support
        if gpus:
            print("\t - GPU support")
            docker_cmd += gpuSupportFlags()
        
        # GUI forwarding
        if x11:
            print("\t - GUI fowarding")
            docker_cmd += x11GuiForwardingFlags(isolated)
        
        # mount current directory to DEV_TARGET_MOUNT
        if mount_pwd:
            print(f"\t - current directory in `DEV_TARGET_MOUNT`")
            docker_cmd += currentDirMountFlags()

    else: # docker exec

        print(f"Attaching to running container '{name}' ...")
        docker_cmd = ["docker", "exec"]

    # interactive
    if interactive:
        print("\t - interactive")
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


def interactiveFlags() -> List[str]:

    return ["--interactive", "--tty"]


def hostNetworkFlags() -> List[str]:

    return ["--network host"]


def gpuSupportFlags() -> List[str]:

    if ARCH == "x86_64":
        return ["--gpus all"]
    elif ARCH == "aarch64" and OS == "Linux":
        return ["--runtime nvidia"]
    else:
        print(f"GPU not supported by `docker-run` on {OS} with {ARCH} architecture")
        return []


def x11GuiForwardingFlags(isolated: bool = True) -> List[str]:

    display = os.environ.get('DISPLAY')
    if display is None:
        return []

    xsock = "/tmp/.X11-unix"
    xauth = tempfile.NamedTemporaryFile(prefix='.docker.xauth.', delete=False).name
    xauth_output = runCommand("xauth nlist $DISPLAY", env=os.environ)[0]
    xauth_output = "ffff" + xauth_output.stdout.decode()[4:]
    runCommand(f"xauth -f {xauth} nmerge - 2>/dev/null", input=xauth_output.encode())
    os.chmod(xauth, 0o777)

    if isolated:
        display="172.17.0.1:" + display.split(":")[1]
    if OS =='Darwin':
        display="host.docker.internal:" + display.split(":")[1]

    flags = []
    flags.append(f"--env DISPLAY={display}")
    flags.append(f"--env XAUTHORITY={xauth}")
    flags.append(f"--env QT_X11_NO_MITSHM=1")
    flags.append(f"--volume {xauth}={xauth}")
    flags.append(f"--volume {xsock}={xsock}")

    return flags


def currentDirMountFlags() -> List[str]:

    src = os.getcwd()
    target = "DEV_TARGET_MOUNT"

    return [f"--volume {src}:{target}"]


def printDockerCommand(cmd: str):
    """Prints a docker command in human-readable way by line-breaking on each new argument.

    Args:
        cmd (str): docker command
    """

    components = cmd.split()
    print(f"{components[0]} {components[1]}", end="")

    for c in components[2:]:
        if c.startswith("-"):
            print(f" \\\n  {c}", end="")
        else:
            print(f" {c}", end="")
    print("")


def main():

    args, unknown_args = parseArguments()
    cmd = buildDockerCommand(image=args.image,
                             cmd=" ".join(args.cmd),
                             name=args.name,
                             isolated=not args.no_isolated,
                             gpus=not args.no_gpu,
                             interactive=not args.no_it,
                             x11=not args.no_x11,
                             remove=not args.no_rm,
                             mount_pwd=args.dev,
                             extra_args=unknown_args)
    print(cmd, file=sys.stderr) # TODO: review thread: how to handle actual errors, e.g. the system execution exception?
    if args.verbose:
        printDockerCommand(cmd)


if __name__ == "__main__":

    main()
