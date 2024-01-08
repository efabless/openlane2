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

# Copyright (c) 2003-2023 Eelco Dolstra and the Nixpkgs/NixOS contributors

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

{ lib
, clangStdenv
, fetchFromGitHub
, libsForQt5
, which
, perl
, python3
, ruby
, gnused
, curl
, gcc
, libgit2
}:

clangStdenv.mkDerivation {
  name = "klayout";

  src = fetchFromGitHub {
    owner = "KLayout";
    repo = "klayout";
    rev = "5961eab84bd2d394f3ca94f9482622180d796010";
    sha256 = "sha256-omeWS72J6mbA5mxsqwmsq1ytuhHa0rLZ+ErN66o+fiY=";
  };

  patches = [
    ./patches/klayout/abspath.patch
  ];

  postPatch = ''
    substituteInPlace src/klayout.pri --replace "-Wno-reserved-user-defined-literal" ""
    patchShebangs .
  '';

  nativeBuildInputs = [
    which
    perl
    python3
    ruby
    gnused
    libsForQt5.wrapQtAppsHook
  ];

  buildInputs = with libsForQt5; [
    qtbase
    qtmultimedia
    qttools
    qtxmlpatterns
    curl
    gcc
    libgit2
  ];

  propagatedBuildInputs = [
    ruby
  ];

  configurePhase = ''
    if [ "${if clangStdenv.isDarwin then "1" else "0" }" = "1" ]; then
      export LDFLAGS="-headerpad_max_install_names"
    fi
    ./build.sh\
      -prefix $out/lib\
      -without-qtbinding\
      -python $(which python3)\
      -ruby $(which ruby)\
      -expert\
      -verbose\
      -dry-run
  '';

  buildPhase = ''
    echo "Using $NIX_BUILD_CORES threads…"
    make -j$NIX_BUILD_CORES -C build-release PREFIX=$out
  '';

  installPhase = ''
    mkdir -p $out/bin
    make  -C build-release install
    if [ "${if clangStdenv.isDarwin then "1" else "0" }" = "1" ]; then
      cp $out/lib/klayout.app/Contents/MacOS/klayout $out/bin/
    else
      cp $out/lib/klayout $out/bin/
    fi
  '';

  # The automatic Qt wrapper overrides makeWrapperArgs
  preFixup =
    if clangStdenv.isDarwin then ''
      python3 ${./supporting/klayout/patch_binaries.py} $out/lib $out/lib/pymod/klayout $out/bin/klayout
    '' else "";

  meta = with lib; {
    description = "High performance layout viewer and editor with support for GDS and OASIS";
    license = with licenses; [ gpl2Plus ];
    homepage = "https://www.klayout.de/";
    changelog = "https://www.klayout.de/development.html#${version}";
    platforms = platforms.linux ++ platforms.darwin;
  };
}
