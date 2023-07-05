# macOS 11+

## Installing Dependencies

First install [Homebrew](https://brew.sh/) then run script below to install the required packages:

```sh
brew install make python python-tk
brew install --cask docker
```

## Configuring Docker

Under **Preferences** > **Resources** > **File Sharing**, make sure `/Users` is mounted as follows, as using OpenLane 2+ with Docker requires access to your home folder.

:::{figure} ../../../_static/installation/mac_docker_settings.png
:::

It may also be prudent to enable Full Disk Access permissions for Docker: Under **System Settings** > **Privacy** > **Full Disk Access**, tick Docker as shown: 

:::{figure} ../../../_static/installation/mac_docker_privacy.png
:::


```{include} installation_common_section.md
```
