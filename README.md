<img src="assets/logo.png" height=130 align="right">

# docker-run

Use `docker-run` to easily start and attach to Docker containers with useful predefined arguments.

## Installation

Add `docker-run` to your `PATH` to enable to use it from anywhere.

```bash
# $ docker-run/
mkdir -p ~/.local/bin
cp docker-run generateDockerCommand.py ~/.local/bin/
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
usage: generateDockerCommand.py [-h] [--dev] [--verbose] [--no-gpu] [--no-it] [--no-x11] [--no-rm] [--name NAME] [--image IMAGE] [--cmd [CMD [CMD ...]]]

Generates a `docker run` with the following properties enabled by default: interactive tty, remove container after stop, GUI forwarding, GPU support, timezone. Generates a `docker exec` command to attach to a running container, if `--name` is specified. Note that the command is printed to
`stderr`.

optional arguments:
  -h, --help            show this help message and exit
  --dev                 Mount current directory into `/home/lutix/ws/src/target`
  --verbose             Print generated command
  --no-gpu              Disable automatic GPU support
  --no-it               Disable automatic interactive tty
  --no-x11              Disable automatic X11 GUI forwarding
  --no-rm               Disable automatic container removal
  --name NAME           Container name; generates `docker exec` command if already running
  --image IMAGE         Image name
  --cmd [CMD [CMD ...]]
                        Command to execute in container
```

## Additional Features

### Image Auto-Update

If the environment variables `$GITLAB_ACCESS_TOKEN`, `$GITLAB_PROJECT_ID`, and `$GITLAB_REGISTRY_ID` are set, `docker-run` will check for new versions of the specified image and give you the option to pull.
