from dataclasses import dataclass
from typing import List
from shapely import unary_union
from shapely.geometry import Polygon, box


@dataclass
class Design:
    slots: List[Polygon]


    @property
    def bounding_box(self) -> Polygon:
        unified = unary_union(self.slots)
        min_x, min_y, max_x, max_y = unified.bounds
        return box(min_x, min_y, max_x, max_y)


    def is_valid(self) -> bool:
        # Check slots don't overlap
        for i, slot1 in enumerate(self.slots):
            for slot2 in self.slots[i + 1:]:
                if slot1.intersects(slot2):
                    return False

        return True
