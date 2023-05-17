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
from collections import UserString
import re
import os
import glob
import fnmatch
from enum import Enum
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple, Union, Optional

Keys = SimpleNamespace(
    pdk_root="PDK_ROOT",
    pdk="PDK",
    pdkpath="PDKPATH",
    scl="STD_CELL_LIBRARY",
    design_dir="DESIGN_DIR",
)

PROCESS_INFO_ALLOWLIST = [
    Keys.pdk,
    Keys.scl,
    f"{Keys.scl}_OPT",
]


Scalar = Union[str, int, float, bool, None]
Valid = Union[Scalar, dict, list]


class InvalidConfig(Exception):
    pass


class Expr(object):
    class SyntaxError(Exception):
        pass

    class Token(object):
        class Type(Enum):
            VAR = 0
            NUMBER = 1
            OP = 2
            LPAREN = 3
            RPAREN = 4

        def __init__(self, type: "Expr.Token.Type", value: str) -> None:
            self.type: Expr.Token.Type = type
            self.value: str = value

        def __repr__(self):
            return f"<Token:{self.type} '{self.value}'>"

        def prec_assoc(self) -> Tuple[int, bool]:
            """
            Returns (precedence, is_left_assoc)
            """

            if self.value in ["**"]:
                return (20, False)
            elif self.value in ["*", "/"]:
                return (10, True)
            elif self.value in ["+", "-"]:
                return (0, True)
            else:
                raise TypeError(
                    f"pre-assoc not supported for non-token operators: '{self.value}'"
                )

    @staticmethod
    def tokenize(expr: str) -> List["Expr.Token"]:
        rx_list = [
            (re.compile(r"^\$(\w+)"), Expr.Token.Type.VAR),
            (re.compile(r"^(-?\d+\.?\d*)"), Expr.Token.Type.NUMBER),
            (re.compile(r"^(\*\*)"), Expr.Token.Type.OP),
            (re.compile(r"^(\+|\-|\*|\/)"), Expr.Token.Type.OP),
            (re.compile(r"^(\()"), Expr.Token.Type.LPAREN),
            (re.compile(r"^(\))"), Expr.Token.Type.RPAREN),
            (re.compile(r"^\s+"), None),
        ]
        tokens = []
        str_so_far = expr
        while not str_so_far.strip() == "":
            found = False

            for element in rx_list:
                rx, type = element
                m = rx.match(str_so_far)
                if m is None:
                    continue
                found = True
                if type is not None:
                    tokens.append(Expr.Token(type, m[1]))
                str_so_far = str_so_far[len(m[0]) :]
                break

            if not found:
                raise SyntaxError(
                    f"Unexpected token at the start of the following string '{str_so_far}'."
                )
        return tokens

    @staticmethod
    def evaluate(expression: str, vars: Dict[str, str]) -> float:
        tokens: List["Expr.Token"] = Expr.tokenize(expression)
        ETT = Expr.Token.Type

        # Infix to Postfix
        postfix: List["Expr.Token"] = []
        opstack: List["Expr.Token"] = []
        for token in tokens:
            if token.type == ETT.OP:
                prec, assoc = token.prec_assoc()

                top_prec = None
                try:
                    top_prec, _ = opstack[-1].prec_assoc()
                except TypeError:
                    pass
                except IndexError:
                    pass

                while top_prec is not None and (
                    (assoc and prec <= top_prec) or (not assoc and prec < top_prec)
                ):
                    postfix.append(opstack.pop())
                    top_prec = None
                    try:
                        top_prec, _ = opstack[-1].prec_assoc()
                    except IndexError:
                        pass
                opstack.append(token)
            elif token.type == ETT.LPAREN:
                opstack.append(token)
            elif token.type == ETT.RPAREN:
                top = opstack[-1]
                while top.type != ETT.LPAREN:
                    postfix.append(top)
                    opstack.pop()
                    top = opstack[-1]
                opstack.pop()  # drop the LPAREN
            else:
                postfix.append(token)

        while len(opstack):
            postfix.append(opstack[-1])
            opstack.pop()

        # Evaluate
        eval_stack = []
        for token in postfix:
            if token.type == ETT.NUMBER:
                eval_stack.append(float(token.value))
            elif token.type == ETT.VAR:
                try:
                    value = vars[token.value]
                    eval_stack.append(float(value))
                except KeyError:
                    raise SyntaxError(
                        f"Configuration variable '{token.value}' not found."
                    )
                except Exception:
                    raise SyntaxError(
                        f"Invalid non-numeric value '{value}' for variable ${token.value}."
                    )
            elif token.type == ETT.OP:
                try:
                    number1 = eval_stack[-2]
                    number2 = eval_stack[-1]
                    eval_stack.pop()
                    eval_stack.pop()

                    result = 0.0
                    if token.value == "**":
                        result = number1**number2
                    elif token.value == "*":
                        result = number1 * number2
                    elif token.value == "/":
                        result = number1 / number2
                    elif token.value == "+":
                        result = number1 + number2
                    elif token.value == "-":
                        result = number1 + number2

                    eval_stack.append(result)
                except IndexError:
                    raise SyntaxError(
                        f"Not enough operands for operator '{token.value}'."
                    )

        if len(eval_stack) > 1:
            raise SyntaxError("Expression does not reduce to one value.")
        elif len(eval_stack) == 0:
            raise SyntaxError("Expression is empty.")

        return eval_stack[0]


ref_rx = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)")


def process_string(value: str, state: dict) -> Union[None, str, List[str]]:
    global ref_rx
    EXPR_PREFIX = "expr::"
    REF_PREFIX = "ref::"

    DIR_PREFIX = "dir::"
    PDK_DIR_PREFIX = "pdk_dir::"

    mutable: str = value

    if value.startswith(DIR_PREFIX):
        mutable = value.replace(DIR_PREFIX, f"ref::${Keys.design_dir}/")
    elif value.startswith(PDK_DIR_PREFIX):
        mutable = value.replace(PDK_DIR_PREFIX, f"ref::${Keys.pdkpath}/")

    if mutable.startswith(EXPR_PREFIX):
        try:
            return f"{Expr.evaluate(value[len(EXPR_PREFIX):], state)}"
        except SyntaxError as e:
            raise InvalidConfig(f"Invalid expression '{value}': {e}")
    elif mutable.startswith(REF_PREFIX):
        reference = mutable[len(REF_PREFIX) :]
        match = ref_rx.match(reference)
        if match is None:
            raise InvalidConfig(f"Invalid reference string '{reference}'")

        reference_variable = match[1]
        try:
            found = state[reference_variable]
            if found is None:
                return None

            if type(found) != str and not isinstance(found, UserString):
                if type(found) in [int, float]:
                    raise InvalidConfig(
                        f"Referenced variable {reference_variable} is a number and not a string: use expr::{match[0]} if you want to reference this number."
                    )
                else:
                    raise InvalidConfig(
                        f"Referenced variable {reference_variable} is not a string: {type(found)}."
                    )

            found = str(found)

            replaced = reference.replace(match[0], found)

            found_abs = os.path.abspath(found)
            full_abspath = os.path.abspath(replaced)

            # Resolve globs for paths that are inside the exposed directory
            if full_abspath.startswith(found_abs):
                files = glob.glob(full_abspath)
                files_escaped = [file.replace("$", r"\$") for file in files]
                files_escaped.sort()
                if len(files_escaped) == 1:
                    return files_escaped[0]
                elif len(files_escaped) > 1:
                    return files_escaped

            return full_abspath
        except KeyError:
            raise InvalidConfig(
                f"Referenced variable '{reference_variable}' not found."
            )
    else:
        return mutable


def process_scalar(key: str, value: Scalar, state: dict) -> Valid:
    result: Valid = value
    if isinstance(value, str):
        result = process_string(value, state)
    elif value is None:
        result = ""
    elif not (
        isinstance(value, bool)
        or isinstance(value, int)
        or isinstance(value, float)
        or isinstance(value, Decimal)
    ):
        raise InvalidConfig(f"Invalid value type {type(value)} for key '{key}'.")

    return result


def process_config_dict_recursive(config_in: Dict[str, Any], state: dict):
    PDK_PREFIX = "pdk::"
    SCL_PREFIX = "scl::"

    for key, value in config_in.items():
        withhold = False
        if not isinstance(key, str):
            raise InvalidConfig(f"Invalid key {key}: must be a string.")
        if isinstance(value, dict):
            if key.startswith(PDK_PREFIX):
                withhold = True
                pdk_match = key[len(PDK_PREFIX) :]
                if fnmatch.fnmatch(state[Keys.pdk], pdk_match):
                    process_config_dict_recursive(value, state)
            elif key.startswith(SCL_PREFIX):
                withhold = True
                scl_match = key[len(SCL_PREFIX) :]
                if state[Keys.scl] is not None and fnmatch.fnmatch(
                    state[Keys.scl], scl_match
                ):
                    process_config_dict_recursive(value, state)
        elif isinstance(value, list):
            valid = True
            processed = []
            for i, item in enumerate(value):
                current_key = f"{key}[{i}]"
                processed.append(f"{process_scalar(current_key, item, state)}")

            if not valid:
                raise InvalidConfig(
                    f"Invalid value for key '{key}': Arrays must consist only of strings."
                )
            value = " ".join(processed)
        else:
            value = process_scalar(key, value, state)

        if not withhold:
            state[key] = value


def process_config_dict(config_in: dict, exposed_variables: Dict[str, str]):
    state = dict(exposed_variables)
    process_config_dict_recursive(config_in, state)
    return state


def extract_process_vars(config_in: Dict[str, str]) -> Dict[str, str]:
    return {
        key: config_in[key]
        for key in PROCESS_INFO_ALLOWLIST
        if config_in.get(key) is not None and config_in.get(key) != ""
    }


def resolve(
    config_dict: Dict[str, Any],
    design_dir: str,
    only_extract_process_info: bool = False,
    exposing: Optional[List[str]] = None,
    pdk: Optional[str] = None,
    pdkpath: Optional[str] = None,
    scl: Optional[str] = None,
):
    if exposing is None:
        exposing = []

    exposed_dict = {}

    implicitly_exposed = [
        Keys.pdk,
        Keys.pdkpath,
        Keys.scl,
        Keys.design_dir,
    ]
    if only_extract_process_info:
        implicitly_exposed = [Keys.design_dir]

        # So we don't crash on conditional processing:
        def coalesce(variable_name: str):
            nonlocal implicitly_exposed, exposed_dict
            if os.environ.get(variable_name) is not None:
                implicitly_exposed += [variable_name]
            else:
                exposed_dict[variable_name] = ""

        for variable in [
            Keys.pdk,
            Keys.pdkpath,
            Keys.scl,
        ]:
            coalesce(variable)

    base_vars = {
        Keys.pdk: pdk,
        Keys.pdkpath: pdkpath,
        Keys.scl: scl,
        Keys.design_dir: design_dir,
    }
    base_vars_clean = {k: v for k, v in base_vars.items() if v is not None}

    env_copy = os.environ.copy()
    env_copy.update(base_vars_clean)

    exposed = list(exposing) + implicitly_exposed
    for key in exposed:
        if value := env_copy.get(key):
            exposed_dict[key] = value

    for key in implicitly_exposed:
        if exposed_dict.get(key) is None:
            raise ValueError(
                f"{key} environment variable must be set.",
            )

    resolved = process_config_dict(config_dict, exposed_dict)
    if only_extract_process_info:
        resolved = extract_process_vars(resolved)

    resolved.update(base_vars_clean)
    return resolved
