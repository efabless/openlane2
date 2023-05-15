# Nix-based Installation
Nix is a package manager for Linux and macOS allowing for *cachable* and *reproducible* builds, and is the primary build system for OpenLane.

### Installing Nix
You can install Nix by following the instructions at https://nixos.org/download.html.

Or more simply, on Ubuntu, run the following in your Terminal:

```sh
sudo apt-get install -y curl
sh <(curl -L https://nixos.org/nix/install) --no-daemon
```

```{note}
On systemd-based Linux systems, you can replace `--no-daemon` with `--daemon`.
```

Or on macOS:

```sh
sh <(curl -L https://nixos.org/nix/install)
```

And follow the instructions in your terminal. This should take around five minutes.

Make sure to close all terminals after you're done with this step.

### Setting up the binary cache
Cachix allows the reproducible Nix builds to be stored on a cloud server so you do not have to build OpenLane's dependencies from scratch on every computer, which will take a long time.

First, you want to install Cachix by running the following in your terminal:

```sh
nix-env -f "<nixpkgs>" -iA cachix
```

Then set up the OpenLane binary cache as follows:

```sh
cachix use openlane
```

``````{note}
If `cachix use openlane` fails, re-run it as follows:

```sh
sudo env PATH="$PATH" cachix use openlane
```

``````

### Cloning OpenLane
With git installed, just run the following:

```sh
git clone https://github.com/efabless/openlane2
```

That's it. Whenever you want to use OpenLane, `nix-shell` in the repository root directory and you'll have a full OpenLane environment. The first time might take around 10 minutes while binaries are pulled from the cache.

To quickly test your installation, simply run `openlane --smoke-test` in the nix shell.