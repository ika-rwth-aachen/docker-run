#!/usr/bin/env python

import argparse
import subprocess
import tempfile
import os


def parseArguments():

    parser = argparse.ArgumentParser()

    parser.add_argument('--no-isolated', action='store_true', default=True, help='Do not run isolated')
    parser.add_argument('--no-gpu', action='store_true', help='Do not use GPUs')
    parser.add_argument('--no-x11', action='store_true', help='Do not use GUI forwarding')

    args, unknown = parser.parse_known_args()

    return args, unknown


def runCommand(str, *args, **kwargs) -> str:
    # wrapper around subprocess.xyz(*args, **kwargs)

    try:
        output = subprocess.run(str, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError as e:
        print("An error has occurred while running the command: ", e)
        exit(1)

    return output.stdout.decode(), output.stderr.decode()

def buildDockerRunCommand(args, unknown_args) -> str:
    # build cmd

    OS = subprocess.run(['uname', '-s'], capture_output=True).stdout.decode()
    ARCH = subprocess.run(['uname', '-m'], capture_output=True).stdout.decode()

    runningContainers = runCommand('docker ps --format "{{.Names}}"')[0]
    runningContainers = runningContainers.split('\n')
    for i, u_arg in enumerate(unknown_args):
        if '--name' in u_arg:
            if ' ' in u_arg:
                name = u_arg.split(' ')[1]
            else:
                name = unknown_args[i+1]
            if name in runningContainers:
                docker_command = ['docker', 'exec', '-it', name, 'bash']
                return docker_command

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
            DISPLAY="XY" # TODO

        docker_command += ['-e', f'DISPLAY={DISPLAY}']
        docker_command += ['-e', 'QT_X11_NO_MITSHM=1']
        docker_command += ['-e', f'XAUTHORITY={XAUTH.name}']
        docker_command += ['-v', f'{XAUTH.name}:{XAUTH.name}']
        docker_command += ['-v', f'{XSOCK}:{XSOCK}']
    
    docker_command += unknown_args

    return docker_command


def main():

    args, unknown_args = parseArguments()
    cmd = buildDockerRunCommand(args, unknown_args)
    print(' '.join(cmd))
    #return ' '.join(cmd)


if __name__ == "__main__":

    main()
