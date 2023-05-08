from decimal import Decimal
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, Tuple, List, Union

from .config import Path


@dataclass
class Instance:
    location: Tuple[Decimal, Decimal]
    orientation: Union[Literal["N"], Literal["S"]]


@dataclass
class Macro:
    module: str
    gds: Path
    instances: Dict[str, Instance] = field(default_factory=lambda: {})

    nl: List[Path] = field(default_factory=lambda: [])
    rtl: List[Path] = field(default_factory=lambda: [])
    lef: List[Path] = field(default_factory=lambda: [])
    spice: List[Path] = field(default_factory=lambda: [])
    lib: Dict[str, List[Path]] = field(default_factory=lambda: {})
    spef: Dict[str, List[Path]] = field(default_factory=lambda: {})
    sdf: Dict[str, List[Path]] = field(default_factory=lambda: {})
    json_h: Optional[Path] = None
    odb: Optional[Path] = None
