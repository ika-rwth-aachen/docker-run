<img src="https://github.com/ika-rwth-aachen/docker-run/raw/main/assets/logo.png" height=130 align="right">

# docker-run

Use `docker-run` to easily start and attach to Docker containers with useful predefined arguments.

## Installation

```bash
# $ docker-run/
pip install docker-run
source $(activate-python-docker-run-shell-completion 2> /dev/null)
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
usage: docker-run [--help] [--image IMAGE] [--mwd] [--name NAME] [--no-gpu]
                  [--no-it] [--no-loc] [--no-name] [--no-rm] [--no-tz]
                  [--no-x11] [--verbose] [--version]

Executes `docker run` with the following features enabled by default, each of
which can be disabled individually: container removal after exit, interactive
tty, current directory name as container name, GPU support, X11 GUI
forwarding. Passes any additional arguments to `docker run`. Executes `docker
exec` instead if a container with the specified name (`--name`) is already
running.

optional arguments:
  --help         show this help message and exit
  --image IMAGE  image name (may also be specified without --image as last
                 argument before command)
  --mwd          mount current directory at same path
  --name NAME    container name; generates `docker exec` command if already
                 running
  --no-gpu       disable automatic GPU support
  --no-it        disable automatic interactive tty
  --no-loc       disable automatic locale
  --no-name      disable automatic container name (current directory)
  --no-rm        disable automatic container removal
  --no-tz        disable automatic timezone
  --no-x11       disable automatic X11 GUI forwarding
  --verbose      print generated command
  --version      show program's version number and exit
```

## Plugins

`docker-run` can be extended through plugins. Plugins are installed as optional dependencies.

```bash
# install specific plugin <PLUGIN_NAME>
pip install docker-run[<PLUGIN_NAME>]

# install all plugins
pip install docker-run[plugins]
```

| Plugin | Description |
| --- | --- |
| [`docker-ros`](https://pypi.org/project/docker-run-docker-ros) | extra functionality for Docker images built by [*docker-ros*](https://github.com/ika-rwth-aachen/docker-ros) |
