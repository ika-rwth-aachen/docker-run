# docker-run
Use `docker-run` to start docker container with predefined default arguments via cli. This primarily includes GUI forewarding.

## Installation
You can add `docker-run` to your `PATH` after you have cloned the repo. For this you only need to execute:
```bash
mkdir -p ~/.local/bin
cp docker-run $HOME/.local/bin/docker-run
cp generateDockerCommand.py $HOME/.local/bin/generateDockerCommand.py
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

## Usage

```
usage: generateDockerCommand.py [-h] [--dev] [--verbose] [--no-isolated] [--no-gpu] [--no-it] [--no-x11] [--no-rm] [--name NAME] [--image IMAGE] [--cmd [CMD [CMD ...]]]

Generates a `docker run` with the following properties enabled by default: interactive tty, remove container after stop, GUI forwarding, GPU support, timezone. Generates a `docker exec` command to attach to a running container, if `--name` is specified. Note that the command is printed to
`stderr`.

optional arguments:
  -h, --help            show this help message and exit
  --dev                 Mount current directory into `/home/lutix/ws/src/target`
  --verbose             Print generated command
  --no-isolated         Disable automatic network isolation
  --no-gpu              Disable automatic GPU support
  --no-it               Disable automatic interactive tty
  --no-x11              Disable automatic X11 GUI forwarding
  --no-rm               Disable automatic container removal
  --name NAME           Container name; generates `docker exec` command if already running
  --image IMAGE         Image name
  --cmd [CMD [CMD ...]]
                        Command to execute in container
```

## Additional feature
Images stored in the ika GitLab registry are automatically updated when needed.
- `$GITLAB_ACCESS_TOKEN`, `$GITLAB_PROJECT_ID` and `$GITLAB_REGISTRY_ID` are need to be set

Example:
```bash
GITLAB_ACCESS_TOKEN=abcd GITLAB_PROJECT_ID=1000 GITLAB_REGISTRY_ID=10 docker-run gitlab.ika.rwth-aachen.de:5050/automated-driving/docker/ros1 bash
```