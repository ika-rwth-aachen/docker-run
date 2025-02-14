<img src="https://github.com/ika-rwth-aachen/docker-run/raw/main/assets/logo.png" height=130 align="right">

# *docker-run* – ``docker run`` and ``docker exec`` with useful defaults

<p align="center">
  <img src="https://img.shields.io/github/license/ika-rwth-aachen/docker-run"/>
  <a href="https://pypi.org/project/docker-run-cli/"><img src="https://img.shields.io/badge/python-v3.7--v3.12-blue.svg"/></a>
  <a href="https://pypi.org/project/docker-run-cli/"><img src="https://img.shields.io/pypi/v/docker-run-cli?label=PyPI"/></a>
  <a href="https://pypi.org/project/docker-run-cli/"><img src="https://img.shields.io/pypi/dm/docker-run-cli?color=blue&label=PyPI%20downloads"/></a>
</p>

*docker-run* is a CLI tool for simplified interaction with Docker images. Use it to easily start and attach to Docker containers with useful predefined arguments.

> [!IMPORTANT]  
> This repository is open-sourced and maintained by the [**Institute for Automotive Engineering (ika) at RWTH Aachen University**](https://www.ika.rwth-aachen.de/).  
> **DevOps, Containerization and Orchestration of Software-Defined Vehicles** are some of many research topics within our [*Vehicle Intelligence & Automated Driving*](https://www.ika.rwth-aachen.de/en/competences/fields-of-research/vehicle-intelligence-automated-driving.html) domain.  
> If you would like to learn more about how we can support your advanced driver assistance and automated driving efforts, feel free to reach out to us!  
> :email: ***opensource@ika.rwth-aachen.de***

<p align="center">
  <img src="https://github.com/ika-rwth-aachen/docker-run/raw/main/assets/teaser.png" width=550>
</p>

While *docker-run* can be used with any Docker image, we recommend to also check out our other tools for Docker and ROS.
- [*docker-ros*](https://github.com/ika-rwth-aachen/docker-ros) automatically builds minimal container images of ROS applications <a href="https://github.com/ika-rwth-aachen/docker-ros"><img src="https://img.shields.io/github/stars/ika-rwth-aachen/docker-ros?style=social"/></a>
- [*docker-ros-ml-images*](https://github.com/ika-rwth-aachen/docker-ros-ml-images) provides machine learning-enabled ROS Docker images <a href="https://github.com/ika-rwth-aachen/docker-ros-ml-images"><img src="https://img.shields.io/github/stars/ika-rwth-aachen/docker-ros-ml-images?style=social"/></a>


## Quick Demo

The following quickly launches the GUI application `xeyes` to demonstrate how `docker-run` takes care of X11 forwarding from container to host. The `--verbose` flag prints the underlying `docker run` command that is run under the hood.

```bash
docker-run --verbose 607qwq/xeyes
```


## Functionality

`docker-run` is designed to be used the same way as the official [`docker run`](https://docs.docker.com/engine/reference/commandline/run/) and [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) commands.

In general, you can pass the same arguments to `docker-run` as you would pass to `docker run`, e.g.

```bash
docker-run --volume $(pwd):/volume ubuntu ls /volume
```

In addition to the arguments you are passing, `docker-run` however also enables the following features by default. Most of these default features can be disabled, see [Usage](#usage).
- container removal after exit (`--rm`)
- interactive tty (`--interactive --tty`)
- current directory name as container name (`--name`)
- relative bind mounts (`--volume [./RELATIVE_PATH>]:[TARGET_PATH]`)
- GPU support (`--gpus all` / `--runtime nvidia`)
- X11 GUI forwarding

If a container with matching name is already running, `docker-run` will execute a command in that container via `docker exec` instead. This lets you quickly attach to a running container without passing any command, e.g.

```bash
docker-run --name my-running-container
```

Unlike with `docker run`, you can also set the Docker image via the `--image` arguments, see [Usage](#usage). This may be required for more complex use cases.


## Installation

```bash
pip install docker-run-cli

# (optional) shell auto-completion
source $(activate-python-docker-run-shell-completion 2> /dev/null)
```

> [!WARNING]  
> Outside of a virtual environment, *pip* may default to a user-site installation of executables to `~/.local/bin`, which may not be present in your shell's `PATH`.  If running `docker-run` errors with `docker-run: command not found`, add the directory to your path. [*(More information)*](https://packaging.python.org/en/latest/tutorials/installing-packages/#installing-to-the-user-site)  
> ```bash
> echo "export PATH=\$HOME/.local/bin:\$PATH" >> ~/.bashrc
> source ~/.bashrc
> ```


## Usage

```
usage: docker-run [--help] [--image IMAGE] [--loc] [--mwd] [--name NAME]
                  [--no-gpu] [--no-it] [--no-name] [--no-rm] [--no-tz]
                  [--no-x11] [--verbose] [--version]

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
  --name NAME    container name; generates `docker exec` command if already
                 running
  --no-gpu       disable automatic GPU support
  --no-it        disable automatic interactive tty
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
pip install docker-run-cli[<PLUGIN_NAME>]

# install all plugins
pip install docker-run-cli[plugins]
```

| Plugin | Description |
| --- | --- |
| [`docker-ros`](https://pypi.org/project/docker-run-docker-ros) | extra functionality for Docker images built by [*docker-ros*](https://github.com/ika-rwth-aachen/docker-ros) |
