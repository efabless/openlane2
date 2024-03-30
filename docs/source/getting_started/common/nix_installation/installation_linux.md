# Ubuntu/Other Linux

* **Minimum Requirements**
    * Quad-core CPU running at 2.0 GHz+
    * 8 GiB of RAM
    
* **Recommended Requirements**
    * 6th Gen Intel® Core CPU or later OR AMD Ryzen™️ 1000-series or later
    * 16 GiB of RAM

We will primarily support Ubuntu 20.04+ for OpenLane.

If you're looking to build a virtual machine, we recommend [Ubuntu 22.04](https://releases.ubuntu.com/jammy/).

## Installing Nix

You will need `curl` to install Nix.

To install curl on Ubuntu, simply type in the following in your terminal:

```console
$ sudo apt-get install -y curl
```

After that, simply run this command:

```console
$ sh <(curl -L https://nixos.org/nix/install) --yes --daemon --nix-extra-conf-file /dev/stdin <<EXTRA_NIX_CONF
extra-experimental-features = nix-command flakes
extra-substituters = https://openlane.cachix.org
extra-trusted-public-keys = openlane.cachix.org-1:qqdwh+QMNGmZAuyeQJTH9ErW57OWSvdtuwfBKdS254E=
EXTRA_NIX_CONF
```

Enter your password if prompted. This should take around 5 minutes.

Make sure to close all terminals after you're done with this step.

```{include} _common.md
:heading-offset: 1
```
