#!/usr/bin/env python

import argparse
import subprocess
import tempfile
import os


def parseArguments():

    parser = argparse.ArgumentParser()

    parser.add_argument('image', type=str, help='Docker image name')
    parser.add_argument('cmd', type=str, help='Command')
    parser.add_argument('run_args', nargs=argparse.REMAINDER, action='store')
    parser.add_argument('--no-isolated', action='store_true', help='Do not run isolated')
    parser.add_argument('--no-gpu', action='store_true', help='Do not use GPUs')
    parser.add_argument('--no-x11', action='store_true', help='Do not use GUI forwarding')

    args = parser.parse_args()

    return args


def runCommand(str, *args, **kwargs) -> str:
    # wrapper around subprocess.xyz(*args, **kwargs)
    # subprocess.run oder subprocess.Popen?
    # stdout und stderr abgreifen?
    # if stderr -> exit(1)

    try:
        output = subprocess.run(str, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError as e:
        print("An error has occurred while running the command: ", e)
        exit(1)

    return output.stdout.decode(), output.stderr.decode()

def buildDockerRunCommand(args) -> str:
    # build cmd
    # running_containers = runCommand("docker ps")
    # for a in args.unknown_args:
    #     run_args.append(a)
    # cmd = "docker run "
    # for ra in run_args:
    #     cmd += "ra "
    OS = subprocess.run(['uname', '-s'], capture_output=True).stdout.decode()
    ARCH = subprocess.run(['uname', '-m'], capture_output=True).stdout.decode()

    docker_command = ['docker', 'run']

    if not args.no_gpu:
        if ARCH == "x86_64":
            docker_command += ['--gpus', 'all'] # "normal" Workstation
        elif ARCH == "aarch64":
            docker_command += ['--runtime', 'nvidia'] # Orin
        # else (e.g. Mac) -> no gpu

    if not args.no_x11:
        XSOCK='/tmp/.X11-unix'  # to support X11 forwarding in isolated containers on local host (not thorugh SSH)
        XAUTH=tempfile.NamedTemporaryFile(prefix='.docker.xauth.', delete=False)
        xauth_output = subprocess.run('xauth nlist $DISPLAY', stdout=subprocess.PIPE, shell=True, env=os.environ)
        xauth_output = "ffff" + xauth_output.stdout.decode()[4:]
        subprocess.run(f'xauth -f {XAUTH.name} nmerge - 2>/dev/null', input=xauth_output.encode(), shell=True)
        subprocess.run(['chmod', '777', XAUTH.name])

        DISPLAY=os.environ.get('DISPLAY')
        if not args.no_isolated:
            DISPLAY="172.17.0.1:" + DISPLAY.split(":")[1] # replace with docker host ip if any host is given
        if OS =='Darwin':
            DISPLAY="XY"

        docker_command += ['-e', f'DISPLAY={DISPLAY}']
        docker_command += ['-e', 'QT_X11_NO_MITSHM=1']
        docker_command += ['-e', f'XAUTHORITY={XAUTH.name}']
        docker_command += ['-v', f'{XAUTH.name}:{XAUTH.name}']
        docker_command += ['-v', f'{XSOCK}:{XSOCK}']
    
    docker_command += args.run_args
    docker_command += [args.image]
    docker_command += [args.cmd]

    return docker_command


def main():

    args = parseArguments()
    cmd = buildDockerRunCommand(args)
    #runCommand(cmd)
    print(' '.join(cmd))


if __name__ == "__main__":

    main()
