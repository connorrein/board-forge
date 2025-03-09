from dataclasses import dataclass
from shapely.geometry import Polygon
from shapely import affinity

@dataclass
class Piece:
    name: str
    shape: Polygon

    def __eq__(self, other):
        if isinstance(other, Piece) and self.name == other.name:
            cent1, cent2 = self.shape.centroid, other.shape.centroid
            s1, s2 = affinity.translate(self.shape, xoff=-cent1.x, yoff=-cent1.y), affinity.translate(other.shape, xoff=-cent2.x, yoff=-cent2.y)
            return s1 == s2
        return False
    
    def __hash__(self):
        return hash((self.name, self.shape))
