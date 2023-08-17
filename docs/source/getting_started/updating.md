# Updating OpenLane

## Nix
Just `git pull`. No, seriously, that's it. Your next `nix-shell` invocation will be using the updated OpenLane.

## Docker/Python
Run following command to update OpenLane:

```
python3 -m pip install --upgrade --no-cache-dir openlane
```