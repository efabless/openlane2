# Windows 10+

```{include} ../wsl/_wsl.md
:relative-images:
```

## Installing Nix

You can install Nix by following the instructions at https://nixos.org/download.html.

```sh
sudo apt-get install -y curl
sh <(curl -L https://nixos.org/nix/install) --no-daemon --yes
```

Enter your password if prompted. This should take around 5 minutes.

Make sure to close the Ubuntu terminal after you're done with this step and
start it again.

```{include} _common.md.part
:heading-offset: 1
```
