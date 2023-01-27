#!/usr/bin/env python

import argparse
import os
import platform
import subprocess
import sys
import tempfile
from typing import Tuple


def parseArguments():

    parser = argparse.ArgumentParser(description="Generates a `docker run` with the following properties enabled by default: "
                                                 "interactive tty, remove container after stop, GUI forwarding, GPU support. "
                                                 "Generates a `docker exec` command to attach to a running container, if `--name` is specified. "
                                                 "Note that the command is printed to `stderr`.")

    parser.add_argument('--dev', action='store_true', help='Mount current directory into `/home/lutix/ws/src/target`') # TODO: review thread
    parser.add_argument('--verbose', action='store_true', help='Print full docker run command')

    parser.add_argument('--no-isolated', action='store_true', help='Disable automatic network isolation') # TODO: review thread
    parser.add_argument('--no-gpu', action='store_true', help='Disable automatic GPUs')
    parser.add_argument('--no-it', action='store_true', help='Disable automatic interactive tty')
    parser.add_argument('--no-x11', action='store_true', help='Disable automatic GUI forwarding')
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

def buildDockerRunCommand(args, unknown_args) -> str:

    OS = platform.uname().system
    ARCH = platform.uname().machine
    EXEC = False

    # check for running container
    runningContainers = runCommand('docker ps --format "{{.Names}}"')[0]
    runningContainers = runningContainers.split('\n')
    if args.name in runningContainers:
        # init docker exec command
        print(f"Attatch to running container <{args.name}> ...")
        docker_command = ['docker', 'exec']
        EXEC = True
    else:
        # init docker run command
        print("Start new Container...")
        docker_command = ['docker', 'run']

    # check for gpu support -> default: use gpu
    if not args.no_gpu and not EXEC:
        if ARCH == "x86_64":
            docker_command += ['--gpus', 'all'] # "normal" Workstation
            print("\t - with GPU-Support")
        elif ARCH == "aarch64":
            docker_command += ['--runtime', 'nvidia'] # Orin
            print("\t - with GPU-Support")
        # else (e.g. Mac) -> no gpu

    # default: run in interactive mode
    if not args.no_it:
        print("\t - interactive")
        docker_command += ['-it']

    # default: remove container after exiting
    if not args.no_rm and not EXEC:
        print("\t - remove after exiting")
        docker_command += ['--rm']

    if args.no_isolated and not EXEC:
        print("\t - not isolated")
        docker_command += ['--network', 'host']

    # default: run with gui forewarding
    if not args.no_x11 and not EXEC:
        print("\t - With GUI-Forewarding")
        XSOCK='/tmp/.X11-unix'  # to support X11 forwarding in isolated containers on local host (not thorugh SSH)
        XAUTH=tempfile.NamedTemporaryFile(prefix='.docker.xauth.', delete=False)
        xauth_output = subprocess.run('xauth nlist $DISPLAY', stdout=subprocess.PIPE, shell=True, env=os.environ)
        xauth_output = "ffff" + xauth_output.stdout.decode()[4:]
        subprocess.run(f'xauth -f {XAUTH.name} nmerge - 2>/dev/null', input=xauth_output.encode(), shell=True)
        os.chmod(XAUTH.name, 0o777)

        DISPLAY=os.environ.get('DISPLAY')
        if not args.no_isolated:
            DISPLAY="172.17.0.1:" + DISPLAY.split(":")[1] # replace with docker host ip if any host is given
        if OS =='Darwin':
            DISPLAY="XY" # TODO

        docker_command += ['-e', f'DISPLAY={DISPLAY}']
        docker_command += ['-e', 'QT_X11_NO_MITSHM=1']
        docker_command += ['-e', f'XAUTHORITY={XAUTH.name}']
        docker_command += ['-v', f'{XAUTH.name}:{XAUTH.name}']
        docker_command += ['-v', f'{XSOCK}:{XSOCK}']

    # get timezone 
    if OS == "Darwin":
        # https://apple.stackexchange.com/questions/424957/non-sudo-alternatives-to-get-the-current-time-zone
        TZ=runCommand("readlink /etc/localtime | sed 's#/var/db/timezone/zoneinfo/##g'")[0]
    else:
        TZ=runCommand("cat /etc/timezone")[0][:-1]
    docker_command += ['-e', f'TZ={TZ}']

    # mount pwd into /home/lutix/ws/src/target
    if args.dev:
        print(f"\t - mounting `{os.getcwd()}` to `/home/lutix/ws/src/target`")
        docker_command += ['-v', f'{os.getcwd()}:/home/lutix/ws/src/target']

    # add --name flag to docker_command
    if args.name and not EXEC:
        docker_command += ['--name', args.name]

    # add all unknown args (docker run args) to docker_command
    docker_command += unknown_args

    # add image/name to docker_command
    if EXEC:
        docker_command += [args.name]
    elif args.image:
        docker_command += [args.image]

    # add cmd to docker_command
    if args.cmd:
        docker_command += args.cmd
    elif EXEC:
        docker_command += ['bash']

    return docker_command


def main():

    args, unknown_args = parseArguments()
    cmd = buildDockerRunCommand(args, unknown_args)
    print(' '.join(cmd), file=sys.stderr)
    if args.verbose:
        print(' '.join(cmd))

if __name__ == "__main__":

    main()
