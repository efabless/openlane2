1. In your terminal, clone OpenLane as follows

   ```bash
   git clone https://github.com/efabless/openlane2
   ```

1. Start a shell with OpenLane and its underlying utilities installed

   ```bash
   nix-shell openlane2/shell.nix
   ```

1. Copy and run the `spm` example under a folder named `my_designs`

   ```bash
   mkdir my_designs
   cd my_designs/
   openlane --run-example spm
   ```
