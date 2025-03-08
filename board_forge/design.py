from dataclasses import dataclass
from typing import List
from shapely.geometry import Polygon

@dataclass
class Design:
    length: float
    width: float
    slots: List[Polygon]
