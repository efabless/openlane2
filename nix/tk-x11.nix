# Copyright 2024 Efabless Corporation
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
# This is a modification of TK that explicitly uses X11 regardless of platform.
#
# This is important for some utilities such as Xschem which expect the X11
# version of Tk even on macOS.
{
  xorg,
  tk,
}:
(tk.override {
  enableAqua = false;
})
.overrideAttrs (self: super: {
  configureFlags =
    super.configureFlags
    ++ [
      "--with-x"
      "--x-includes=${xorg.libX11}/include"
      "--x-libraries=${xorg.libX11}/lib"
    ];

  propagatedBuildInputs =
    super.propagatedBuildInputs
    ++ [
      xorg.libX11
    ];
})
