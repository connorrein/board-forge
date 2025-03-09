from dataclasses import dataclass
from shapely.geometry import Polygon

@dataclass
class Piece:
    name: str
    shape: Polygon
