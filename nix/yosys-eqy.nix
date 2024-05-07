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
{
  lib,
  clangStdenv,
  fetchFromGitHub,
  yosys,
  libedit,
  libbsd,
  bitwuzla,
  zlib,
  yosys-sby,
  rev ? "5791c90fa6d6076b3c1ff37a3bd65e66f7748230",
  sha256 ? "sha256-zgD8jjtK3pvHxOWvCpFyIuLYsJS5AQMrSARcqjFm9Js=",
}:
clangStdenv.mkDerivation rec {
  name = "yosys-eqy";

  dylibs = [
    "eqy_combine"
    "eqy_partition"
    "eqy_recode"
  ];

  src = fetchFromGitHub {
    owner = "yosyshq";
    repo = "eqy";
    inherit rev;
    inherit sha256;
  };

  makeFlags = [
    "YOSYS_CONFIG=${yosys}/bin/yosys-config"
  ];

  buildInputs = [
    yosys.py3env
    yosys
    libedit
    libbsd
    bitwuzla
    zlib
    yosys-sby
  ];

  preConfigure = ''
    sed -i.bak "s@/usr/local@$out@" Makefile
    sed -i.bak "s@#!/usr/bin/env python3@#!${yosys.py3env}/bin/python3@" src/eqy.py
    sed -i.bak "s@\"/usr/bin/env\", @@" src/eqy_job.py
  '';

  postInstall = ''
    cp examples/spm/formal_pdk_proc.py $out/bin/eqy.formal_pdk_proc
    chmod +x $out/bin/eqy.formal_pdk_proc
  '';

  checkPhase = ''
    sed -i.bak "s@> /dev/null@@" tests/python/Makefile
    sed -i.bak "s/@//" tests/python/Makefile
    sed -i.bak "s@make -C /tmp/@make -C \$(TMPDIR)@" tests/python/Makefile
    make -C tests/python clean "EQY=${yosys.py3env}/bin/python3 $PWD/src/eqy.py"
    make -C tests/python "EQY=${yosys.py3env}/bin/python3 $PWD/src/eqy.py"
  '';

  doCheck = true;

  computed_PATH = lib.makeBinPath buildInputs;
  makeWrapperArgs = [
    "--prefix PATH : ${computed_PATH}"
  ];

  meta = with lib; {
    description = "A front-end driver program for Yosys-based formal hardware verification flows.";
    homepage = "https://github.com/yosysHQ/eqy";
    license = licenses.mit;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
