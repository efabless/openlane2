# Windows 10+

* **Minimum Requirements**
    * Windows 10 version 2004 (Build 19041 and higher)
    * Quad-core CPU running at 2.0 GHz+
    * 8 GiB of RAM
    
* **Recommended**
    * Windows 11
    * 6th Gen Intel® Core CPU or later OR AMD Ryzen™️ 1000-series or later
    * 16 GiB of RAM

## Setting up WSL

1. Follow [official Microsoft documentation for WSL located here](https://docs.microsoft.com/en-us/windows/wsl/install) to install the WSL 2.


```{note}
OpenLane 2 *requires* WSL2. Make sure that you're using Windows 11, or
Windows 10 is up-to-date.
```

1. If you have an installation of WSL2 from 2023 or earlier, follow [Microsoft's official documention to enable `systemd`](https://learn.microsoft.com/en-us/windows/wsl/systemd)
    * `systemd` is enabled by default for installations of WSL2 from mid-2023 or later.

1. Click the Windows icon, type in "Windows PowerShell" and open it.

    ![The Windows 11 Start Menu with "powershell" typed into the search box, showing "Windows PowerShell" as the first match](../wsl/powershell.webp)

1. Install Ubuntu using the following command: `wsl --install -d Ubuntu`

1. Check the version of WSL using following command: `wsl --list --verbose`

    It should produce the following output:

    ```powershell
    PS C:\Users\user> wsl --list --verbose
    NAME                   STATE           VERSION
    * Ubuntu                 Running         2
    ```

1. Launch "Ubuntu" from your Start Menu.

    ![The Windows 11 Start Menu showing a search for the "Ubuntu" app, next to which is a window of the Windows Terminal which opens after clicking it](../wsl/wsl.webp)

## Installing Nix

To install Nix, you first need to install `curl`:

```console
$ sudo apt-get install -y curl
```

Then install Nix by running the following command:

```console 
$ sh <(curl -L https://nixos.org/nix/install) --yes --daemon --nix-extra-conf-file /dev/stdin <<EXTRA_NIX_CONF
extra-experimental-features = nix-command flakes
extra-substituters = https://openlane.cachix.org
extra-trusted-public-keys = openlane.cachix.org-1:qqdwh+QMNGmZAuyeQJTH9ErW57OWSvdtuwfBKdS254E=
EXTRA_NIX_CONF
```

Enter your password if prompted. This should take around 5 minutes.

Make sure to close the Ubuntu terminal after you're done with this step and
start it again.

```{include} _common.md
:heading-offset: 1
```
