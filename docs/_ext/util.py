#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2024 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import pathlib
from typing import Union


def debug(*args, **kwargs):
    if os.getenv("SPHINX_DEBUG") == "1":
        print(*args, **kwargs)


def rimraf(path: Union[str, os.PathLike]):
    try:
        shutil.rmtree(path)
    except NotADirectoryError:
        pathlib.Path(path).unlink(missing_ok=True)
    except FileNotFoundError:
        pass


def mkdirp(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)
