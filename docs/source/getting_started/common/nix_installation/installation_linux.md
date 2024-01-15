# Ubuntu/Other Linux

We will primarily support Ubuntu 20.04+ for OpenLane.

If you're looking to build a virtual machine, we recommend [Ubuntu 22.04](https://releases.ubuntu.com/jammy/).

## Installing Nix

You can install Nix by following the instructions at https://nixos.org/download.html.

For example, on Ubuntu, run the following your terminal.

```sh
sudo apt-get install -y curl
sh <(curl -L https://nixos.org/nix/install) --daemon --yes
```

```{tip}
If you're using a non-systemd based Linux, you will need to pass `--no-daemon`
instead of `--daemon`. If you do not know what any of that means, you may
safely ignore this tip box.
```

Enter your password if prompted. This should take around 5 minutes.

Make sure to close all terminals after you're done with this step.

```{include} _common.md
:heading-offset: 1
```
