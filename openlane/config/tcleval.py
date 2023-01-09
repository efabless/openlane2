import os
import tkinter
import tempfile
from decimal import Decimal, InvalidOperation

from .config import Config


def env_from_tcl(env_in: dict, tcl_in_path: str) -> Config:
    tcl_in = open(tcl_in_path).read()
    interpreter = tkinter.Tcl()

    initial_env = os.environ.copy()
    env_out = Config(env_in)

    with tempfile.NamedTemporaryFile("r+") as f:
        env_str = ""
        for key, value in env_in.items():
            env_str += f"set ::env({key}) {{{value}}}\n"
        tcl_script = f"""
        {env_str}
        {tcl_in}
        set f [open {f.name} WRONLY]
        foreach key [array names ::env] {{
            puts $f "$key $::env($key)"
        }}
        close $f 
        """

        interpreter.eval(tcl_script)

        f.seek(0)
        env_strings = f.read()

        for line in env_strings.splitlines():
            key, value = line.split(" ", 1)
            try:
                value = Decimal(value)
            except InvalidOperation:
                pass
            if initial_env.get(key) is None:
                env_out[key] = value

    return env_out
