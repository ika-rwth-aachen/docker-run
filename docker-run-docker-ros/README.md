# docker-run-docker-ros

[`docker-run`](https://pypi.org/project/docker-run/) plugin for Docker images built by [*docker-ros*](https://github.com/ika-rwth-aachen/docker-ros).

## Installation

```bash
pip install docker-run[docker-ros]
```

## Usage

```
usage: docker-run [--help] [--image IMAGE] [--loc] [--mwd] [--mws]
                  [--name NAME] [--no-gpu] [--no-it] [--no-name] [--no-rm]
                  [--no-tz] [--no-user] [--no-x11] [--verbose] [--version]

Executes `docker run` with the following features enabled by default, each of
which can be disabled individually: container removal after exit, interactive
tty, current directory name as container name, GPU support, X11 GUI
forwarding. Passes any additional arguments to `docker run`. Executes `docker
exec` instead if a container with the specified name (`--name`) is already
running.

options:
  --help         show this help message and exit
  --image IMAGE  image name (may also be specified without --image as last
                 argument before command)
  --loc          enable automatic locale
  --mwd          mount current directory at same path
  --mws          [docker-ros] mount current directory into ROS workspace at
                 `/docker-ros/ws/src/target`
  --name NAME    container name; generates `docker exec` command if already
                 running
  --no-gpu       disable automatic GPU support
  --no-it        disable automatic interactive tty
  --no-name      disable automatic container name (current directory)
  --no-rm        disable automatic container removal
  --no-tz        disable automatic timezone
  --no-user      [docker-ros] disable passing local UID/GID into container
  --no-x11       disable automatic X11 GUI forwarding
  --verbose      print generated command
  --version      show program's version number and exit
```
