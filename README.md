<img src="assets/logo.png" height=130 align="right">

# docker-run

Use `docker-run` to easily start and attach to Docker containers with useful predefined arguments.

## Installation

Add `docker-run` to your `PATH` to enable to use it from anywhere.

```bash
# $ docker-run/
mkdir -p ~/.local/bin
cp docker-run generateDockerCommand.py ~/.local/bin/
sudo cp _docker-run /etc/bash_completion.d/docker-run
source /etc/bash_completion
```

## Functionality

`docker-run` is designed to be used the same way as the official [`docker run`](https://docs.docker.com/engine/reference/commandline/run/) and [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) commands.

In general, you can pass the same arguments to `docker-run` as you would pass to `docker run`, e.g.

```bash
docker-run --volume $(pwd):/volume ubuntu ls /volume
```

In addition to the arguments you are passing, `docker-run` however also enables the following features by default. Each of these default features can be disabled, see [Usage](#usage).
- container removal after exit (`--rm`)
- interactive tty (`--interactive --tty`)
- current directory name as container name (`--name`)
- GPU support (`--gpus all` / `--runtime nvidia`)
- X11 GUI forwarding

If a container with matching name is already running, `docker-run` will execute a command in that container via `docker exec` instead. This lets you quickly attach to a running container without passing any command, e.g.

```bash
docker-run --name my-running-container
```

Unlike with `docker run`, you can also set the Docker image and command via `--image` and `--cmd` arguments, see [Usage](#usage). This may be required for more complex use cases.

## Usage

```
usage: docker-run [--help] [--mwd] [--verbose] [--no-gpu] [--no-it] [--no-x11]
                  [--no-rm] [--no-user] [--no-name] [--name NAME]
                  [--image IMAGE] [--cmd [CMD ...]]

Executes `docker run` with the following features enabled by default, each of
which can be disabled individually: container removal after exit, interactive
tty, current directory name as container name, GPU support, X11 GUI
forwarding. Passes any additional arguments to `docker run`. Executes `docker
exec` instead if a container with the specified name (`--name`) is already
running.

optional arguments:
  --help           show this help message and exit
  --mwd            mount current directory into `/docker-ros/ws/src/target`
  --verbose        print generated command
  --no-gpu         disable automatic GPU support
  --no-it          disable automatic interactive tty
  --no-x11         disable automatic X11 GUI forwarding
  --no-rm          disable automatic container removal
  --no-user        disable parsing local user ids into container
  --no-name        disable automatic container name (current directory)
  --name NAME      container name; generates `docker exec` command if already
                   running
  --image IMAGE    image name
  --cmd [CMD ...]  command to execute in container
```
