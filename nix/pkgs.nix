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

args: import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/352689710b6fa907439870e3068176134226da89.tar.gz") {
    overlays = [
        (new: old: {
            lemon-graph = old.lemon-graph.overrideAttrs (finalAttrs: previousAttrs: {
                postPatch = "sed -i 's/register //' lemon/random.h";
            });

            cbc = old.cbc.overrideAttrs(finalAttrs: previousAttrs: {
                # Clang 16's Default is C++17, which CBC does not support
                configureFlags = previousAttrs.configureFlags ++ ["CXXFLAGS=-std=c++14"]; 
            });

            spdlog-internal-fmt = (old.spdlog.overrideAttrs(finalAttrs: previousAttrs: {
                cmakeFlags = builtins.filter (flag: (!old.lib.strings.hasPrefix "-DSPDLOG_FMT_EXTERNAL" flag)) previousAttrs.cmakeFlags;
                doCheck = false;
            }));
        })
    ];
} // args
