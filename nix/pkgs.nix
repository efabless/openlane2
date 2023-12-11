# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

let
    newpkgs = import (
    fetchTarball "https://github.com/NixOS/nixpkgs/archive/3b79cc4bcd9c09b5aa68ea1957c25e437dc6bc58.tar.gz"
    ) {};
in args: import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/0218941ea68b4c625533bead7bbb94ccce52dceb.tar.gz") {
    overlays = [
        (new: old: {
            # aarch64-related
            clp = old.clp.overrideAttrs(finalAttrs: previousAttrs: {
                meta = {
                    platforms = previousAttrs.meta.platforms ++ ["aarch64-linux"];
                };
            });

            # Darwin-related
            lemon-graph = old.lemon-graph.overrideAttrs (finalAttrs: previousAttrs: {
                meta = { broken = false; };
                doCheck = false;
            });
            
            or-tools = old.or-tools.overrideAttrs (finalAttrs: previousAttrs: {
                meta = {
                    platforms = previousAttrs.meta.platforms ++ old.lib.platforms.darwin;
                };
                doCheck = false;
            });

            python3 = old.python3.override {
                packageOverrides = (pFinalAttrs: pPreviousAttrs: {
                    mdformat = pPreviousAttrs.mdformat.overrideAttrs (finalAttrs: previousAttrs: {
                        postPatch = ''
                            sed -i 's/primary_marker = "-"/primary_marker = "*"/' src/mdformat/renderer/_util.py
                        '';
                        pytestCheckPhase = "true";
                    });
                });
            };

            # # Hack to get GHDL to maybe work on macOS- use at your own risk
            # ghdl-llvm = if old.stdenv.isDarwin then newpkgs.ghdl-llvm.overrideAttrs (finalAttrs: previousAttrs: {
            #     meta = {
            #         platforms = previousAttrs.meta.platforms ++ old.lib.platforms.darwin;
            #     };
            # }) else (old.ghdl-llvm);
        })
    ];
} // args
