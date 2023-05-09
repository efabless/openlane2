from decimal import Decimal
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, Tuple, List, Union

from ..state import Path, DesignFormat


@dataclass
class Instance:
    location: Tuple[Decimal, Decimal]
    orientation: Union[Literal["N"], Literal["S"]]


@dataclass
class Macro:
    gds: Path
    lef: List[Path]
    instances: Dict[str, Instance] = field(default_factory=lambda: {})

    nl: List[Path] = field(default_factory=lambda: [])
    rtl: List[Path] = field(default_factory=lambda: [])
    spice: List[Path] = field(default_factory=lambda: [])
    lib: Dict[str, List[Path]] = field(default_factory=lambda: {})
    spef: Dict[str, List[Path]] = field(default_factory=lambda: {})
    sdf: Dict[str, List[Path]] = field(default_factory=lambda: {})
    json_h: Optional[Path] = None
    odb: Optional[Path] = None

    def view_by_df(
        self, df: DesignFormat
    ) -> Union[Path, List[Path], Dict[str, List[Path]]]:
        return getattr(self, df.value.id)
