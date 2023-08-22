# Windows 10+

OpenLane 2 supports Windows 10 version 1903 or higher, and Windows 11.

To use GUI, you will need Windows 10 Build 19044 or higher, or Windows 11.

## Setting up WSL2

OpenLane relies on the Windows Subsystem for Linux to run binaries on Windows.

1. Follow [official Microsoft documentation for WSL located here](https://docs.microsoft.com/en-us/windows/wsl/install) to install WSL 2.
2. Click the Windows icon, type in "Windows PowerShell" and open it.

:::{figure} ../../../_static/installation/powershell.png
:::

3. Install Ubuntu using the following command: `wsl --install -d Ubuntu`
4. Check the version of WSL using the following command:

It should produce the following output:

```powershell
PS C:\Users\user> wsl --list --verbose
NAME                   STATE           VERSION
* Ubuntu                 Running         2
```

5. Launch "Ubuntu" from your Start Menu.

:::{figure} ../../../_static/installation/wsl.png
:::

## Installing Nix
You can install Nix by following the instructions at https://nixos.org/download.html.

```sh
sudo apt-get install -y curl
sh <(curl -L https://nixos.org/nix/install) --no-daemon --yes
```

Enter your password if prompted. This should take around 5 minutes.

Make sure to close the Ubuntu terminal after you're done with this step and
start it again.

```{include} _common.md
```
