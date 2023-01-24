#!/usr/bin/env python

import argparse
import subprocess
import tempfile
import os
import sys


def parseArguments():

    parser = argparse.ArgumentParser()

    parser.add_argument('--no-isolated', action='store_true', default=True, help='Do not run isolated')
    parser.add_argument('--no-gpu', action='store_true', help='Do not use GPUs')
    parser.add_argument('--no-it', action='store_true', help='Do not use interactive mode')
    parser.add_argument('--no-x11', action='store_true', help='Do not use GUI forwarding')
    parser.add_argument('--no-rm', action='store_true', help='Do not remove Container after exiting')
    parser.add_argument('--name', default=os.getcwd(), help='Name of the Container, which is started')
    parser.add_argument('--image', help='Name of Image, which is used to start the container')
    parser.add_argument('--cmd', nargs='*', help='Command, which is executed in the container')

    args, unknown = parser.parse_known_args()

    return args, unknown

def checkCommand(str, *args, **kwargs) -> bool:

    try:
        output = subprocess.run(str, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError as e:
        return False

    return True

def runCommand(str, *args, **kwargs) -> str:
    # wrapper around subprocess.xyz(*args, **kwargs)

    try:
        output = subprocess.run(str, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError as e:
        print("An error has occurred while running the command: ", e)
        exit(1)

    return output.stdout.decode(), output.stderr.decode()

def buildDockerRunCommand(args, unknown_args) -> str:

    OS = subprocess.run(['uname', '-s'], capture_output=True).stdout.decode()
    ARCH = subprocess.run(['uname', '-m'], capture_output=True).stdout.decode()

    # check for running container -> docker exec
    runningContainers = runCommand('docker ps --format "{{.Names}}"')[0]
    runningContainers = runningContainers.split('\n')
    if args.name in runningContainers:
        print(f"Attatch to running container <{args.name}> ...")
        cmd = ' '.join(args.cmd) if args.cmd else 'bash'
        docker_command = ['docker', 'exec', '-it', args.name, cmd]
        return docker_command

    # init docker run command
    print("Start new Container...")
    docker_command = ['docker', 'run']
    
    # check for gpu support -> default: use gpu
    if not args.no_gpu:
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
    if not args.no_rm:
        print("\t - remove after exiting")
        docker_command += ['--rm']

    # default: run with gui forewarding
    if not args.no_x11:
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

    # add --name flag to docker_command
    if args.name:
        docker_command += ['--name', args.name]

    # add all unknown args (docker run args) to docker_command
    docker_command += unknown_args

    # add image and cmd to docker_command
    if args.image:
        docker_command += [args.image]
    if args.cmd:
        docker_command += args.cmd
    elif not args.no_it and unknown_args:
        if not checkCommand(unknown_args[-1]):
            print("\t - Using a bash")
            docker_command += ['bash']

    return docker_command


def main():

    args, unknown_args = parseArguments()
    cmd = buildDockerRunCommand(args, unknown_args)
    print(' '.join(cmd), file=sys.stderr)

if __name__ == "__main__":

    main()
