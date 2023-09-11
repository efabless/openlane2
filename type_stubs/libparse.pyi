from io import TextIOWrapper
from typing import List

class LibertyAst(object):
    id: str
    value: str
    args: List[str]
    children: List[LibertyAst]

    def find(self, name: str) -> LibertyAst: ...

class LibertyParser(object):
    ast: LibertyAst
    def __init__(self, file: TextIOWrapper) -> None: ...
