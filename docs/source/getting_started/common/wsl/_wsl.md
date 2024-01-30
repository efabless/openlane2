A recent version of Windows 10 or Windows 11 is required, for more information consult Microsoft's documentation.

The following is the recommended installation method under Windows. Other virtualization-based methods, such as VMWare, are not supported, and some such as VirtualBox are known to impair the operation of OpenLane.

# Setting up WSL

1. Follow [official Microsoft documentation for WSL located here](https://docs.microsoft.com/en-us/windows/wsl/install) to install the WSL 2. Make sure your OS version supports WSL 2.
1. Follow [official steps to Install Docker Desktop on Windows located here](https://docs.docker.com/desktop/install/windows-install/).
1. Make sure that `WSL 2 Docker engine` is enabled and `Settings` -> `Resource` -> `WSL Integration` is enabled
1. Make sure that option `Start Docker Desktop when you login` is enabled in `Docker Desktop` -> `Settings`

![](./wsl_docker_settings.png)

5. Click the Windows icon, type in "Windows PowerShell" and open it.

![](./powershell.png)

6. Install Ubuntu using the following command: `wsl --install -d Ubuntu`
1. Check the version of WSL using following command: `wsl --list --verbose`

It should produce the following output:

```powershell
PS C:\Users\user> wsl --list --verbose
NAME                   STATE           VERSION
* Ubuntu                 Running         2
docker-desktop         Running         2
docker-desktop-data    Running         2
```

If you get following output, then you need to launch **Docker Desktop on Windows** from the start menu.

```powershell
PS C:\Users\user> wsl --list --verbose
NAME                   STATE           VERSION
* Ubuntu                 Running         2
docker-desktop         Stopped         2
docker-desktop-data    Stopped         2
```

Same goes for if you get an output that looks like this

```powershell
PS C:\Users\user> docker run hello-world

The command 'docker' could not be found in this WSL 2 distro.
We recommend to activate the WSL integration in Docker Desktop settings.

For details about using Docker Desktop with WSL 2, visit:

https://docs.docker.com/go/wsl2/
```

8. Launch "Ubuntu" from your Start Menu.

![](./wsl.png)

9. Follow the steps shown below.

```{include} ../_ubuntu_packages.md
:heading-offset: 1

```
