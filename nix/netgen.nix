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
  tcl,
  tk,
  m4,
  python3,
  rev ? "bf67d3c2754a6cdcd6cc5fe7e69ea1fddd855dd2",
  sha256 ? "sha256-XcpGB7jeBbC15HlMpY4JkERc0csS5CxMuSVu6dORbLY=",
}:
clangStdenv.mkDerivation {
  name = "netgen";
  src = fetchFromGitHub {
    owner = "RTimothyEdwards";
    repo = "netgen";
    inherit rev;
    inherit sha256;
  };

  configureFlags = [
    "--with-tk=${tk}"
    "--with-tcl=${tcl}"
  ];

  NIX_CFLAGS_COMPILE = "-Wno-implicit-function-declaration -Wno-parentheses -Wno-macro-redefined";

  buildInputs = [
    tcl
    tk
    m4
    python3
  ];

  meta = with lib; {
    description = "Complete LVS tool for comparing SPICE or verilog netlists";
    homepage = "http://opencircuitdesign.com/netgen/";
    # The code is technically distributed under GPLv1(!!)+
    license = licenses.gpl2Plus;
    platforms = platforms.unix;
  };
}
