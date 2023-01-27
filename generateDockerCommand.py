#!/usr/bin/env python

import argparse
import os
import platform
import subprocess
import sys
import tempfile
from typing import List, Tuple


def parseArguments():

    parser = argparse.ArgumentParser(description="Generates a `docker run` with the following properties enabled by default: "
                                                 "interactive tty, remove container after stop, GUI forwarding, GPU support. "
                                                 "Generates a `docker exec` command to attach to a running container, if `--name` is specified. "
                                                 "Note that the command is printed to `stderr`.")

    parser.add_argument('--dev', action='store_true', help='Mount current directory into `/home/lutix/ws/src/target`') # TODO: review thread
    parser.add_argument('--verbose', action='store_true', help='Print generated command')

    parser.add_argument('--no-isolated', action='store_true', help='Disable automatic network isolation') # TODO: review thread
    parser.add_argument('--no-gpu', action='store_true', help='Disable automatic GPUs')
    parser.add_argument('--no-it', action='store_true', help='Disable automatic interactive tty')
    parser.add_argument('--no-x11', action='store_true', help='Disable automatic X11 GUI forwarding')
    parser.add_argument('--no-rm', action='store_true', help='Disable automatic container removal')

    parser.add_argument('--name', default=os.path.basename(os.getcwd()), help='Container name; generates `docker exec` command if already running')
    parser.add_argument('--image', help='Image name')
    parser.add_argument('--cmd', nargs='*', help='Command to execute in container')

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
        output = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
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

    OS = platform.uname().system
    ARCH = platform.uname().machine
    EXEC = False

    # check for running container
    runningContainers = runCommand('docker ps --format "{{.Names}}"')[0]
    runningContainers = runningContainers.split('\n')
    if name in runningContainers:
        # init docker exec command
        print(f"Attatch to running container <{name}> ...")
        docker_cmd = ['docker', 'exec']
        EXEC = True
    else:
        # init docker run command
        print("Start new Container...")
        docker_cmd = ['docker', 'run']

    # check for gpu support -> default: use gpu
    if gpus and not EXEC:
        if ARCH == "x86_64":
            docker_cmd += ['--gpus', 'all'] # "normal" Workstation
            print("\t - with GPU-Support")
        elif ARCH == "aarch64":
            docker_cmd += ['--runtime', 'nvidia'] # Orin
            print("\t - with GPU-Support")
        # else (e.g. Mac) -> no gpu

    # default: run in interactive mode
    if interactive:
        print("\t - interactive")
        docker_cmd += ['-it']

    # default: remove container after exiting
    if remove and not EXEC:
        print("\t - remove after exiting")
        docker_cmd += ['--rm']

    if not isolated and not EXEC:
        print("\t - not isolated")
        docker_cmd += ['--network', 'host']

    # default: run with gui forewarding
    if x11 and not EXEC:
        print("\t - With GUI-Forewarding")
        XSOCK='/tmp/.X11-unix'  # to support X11 forwarding in isolated containers on local host (not thorugh SSH)
        XAUTH=tempfile.NamedTemporaryFile(prefix='.docker.xauth.', delete=False)
        xauth_output = subprocess.run('xauth nlist $DISPLAY', stdout=subprocess.PIPE, shell=True, env=os.environ)
        xauth_output = "ffff" + xauth_output.stdout.decode()[4:]
        subprocess.run(f'xauth -f {XAUTH.name} nmerge - 2>/dev/null', input=xauth_output.encode(), shell=True)
        os.chmod(XAUTH.name, 0o777)

        DISPLAY=os.environ.get('DISPLAY')
        if DISPLAY is not None:
            if isolated:
                DISPLAY="172.17.0.1:" + DISPLAY.split(":")[1] # replace with docker host ip if any host is given
            if OS =='Darwin':
                DISPLAY="XY" # TODO
            docker_cmd += ['-e', f'DISPLAY={DISPLAY}']
            docker_cmd += ['-e', 'QT_X11_NO_MITSHM=1']
            docker_cmd += ['-e', f'XAUTHORITY={XAUTH.name}']
            docker_cmd += ['-v', f'{XAUTH.name}:{XAUTH.name}']
            docker_cmd += ['-v', f'{XSOCK}:{XSOCK}']

    # get timezone 
    if OS == "Darwin":
        # https://apple.stackexchange.com/questions/424957/non-sudo-alternatives-to-get-the-current-time-zone
        TZ=runCommand("readlink /etc/localtime | sed 's#/var/db/timezone/zoneinfo/##g'")[0]
    else:
        TZ=runCommand("cat /etc/timezone")[0][:-1]
    docker_cmd += ['-e', f'TZ={TZ}']

    # mount pwd into /home/lutix/ws/src/target
    if mount_pwd:
        print(f"\t - mounting `{os.getcwd()}` to `/home/lutix/ws/src/target`")
        docker_cmd += ['-v', f'{os.getcwd()}:/home/lutix/ws/src/target']

    # add --name flag to docker_cmd
    if name and not EXEC:
        docker_cmd += ['--name', name]

    # add all extra args (docker run args) to docker_cmd
    docker_cmd += extra_args

    # add image/name to docker_cmd
    if EXEC:
        docker_cmd += [name]
    elif image:
        docker_cmd += [image]

    # add cmd to docker_cmd
    if cmd:
        docker_cmd += cmd
    elif EXEC:
        docker_cmd += ['bash']

    return " ".join(docker_cmd)


def main():

    args, unknown_args = parseArguments()
    cmd = buildDockerCommand(image=args.image,
                             cmd=args.cmd,
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
        print(cmd)

if __name__ == "__main__":

    main()
