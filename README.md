# docker-run
Use `docker-run` to start docker container with predefined default arguments via cli. This primarily includes GUI forewarding.

## Installation
You can add `docker-run` to your `PATH` after you have cloned the repo. For this you only need to execute:
```bash
mkdir -p ~/.local/bin
cp docker-run $HOME/.local/bin/docker-run
cp generateDockerRunCommand.py $HOME/.local/bin/generateDockerRunCommand.py
```

## Functionality
In general, you can pass the same arguments to `docker-run` that you can pass to `docker run`. The syntax stays the same. For example:
```bash
docker-run -p 80:80 --user USER IMAGE_NAME CMD
```

However, there are a few things that `docker-run` does by default, unlike `docker run`. These are:

- setting container name to the current folder name
  - `--name $FOLDER`
- enables GPU support
  - `--gpus all` (amd64) / `--runtime nvidia` (arm64, Jetson Orin)
- automatically removes container after exiting
  - `--rm`
- start container interactive and allocate a pseudo-TTY
  - `-i -t`
- enables GUI forewarding

Each of these defaults can be overwritten or disabled by an argument.

In addition to these defaults, for more complicated use cases, the image name and the command to execute can also be defined explicitly using the two args:

- `--image`: image name
- `--cmd`: command to execute
## Help dialog
```
usage: generateDockerRunCommand.py [-h] [--dev] [--verbose] [--no-isolated] [--no-gpu] [--no-it] [--no-x11] [--no-rm] [--name NAME] [--image IMAGE] [--cmd [CMD ...]]

optional arguments:
  -h, --help       show this help message and exit
  --dev            Dev-Mode: Mount pwd into /home/lutix/ws/src/target
  --verbose        Print full docker run command
  --no-isolated    Do not run isolated
  --no-gpu         Do not use GPUs
  --no-it          Do not use interactive mode
  --no-x11         Do not use GUI forwarding
  --no-rm          Do not remove Container after exiting
  --name NAME      Name of the Container, which is started
  --image IMAGE    Name of Image, which is used to start the container
  --cmd [CMD ...]  Command, which is executed in the container
```

## Additional feature
Images stored in the ika GitLab registry are automatically updated when needed.
- `$GITLAB_ACCESS_TOKEN`, `$GITLAB_PROJECT_ID` and `$GITLAB_REGISTRY_ID` are need to be set

Example:
```bash
GITLAB_ACCESS_TOKEN=abcd GITLAB_PROJECT_ID=1000 GITLAB_REGISTRY_ID=10 docker-run gitlab.ika.rwth-aachen.de:5050/automated-driving/docker/ros1 bash
```