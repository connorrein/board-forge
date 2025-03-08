from dataclasses import dataclass
from typing import List
from shapely.geometry import Polygon, box

@dataclass
class Design:
    length: float
    width: float
    slots: List[Polygon]


    def is_valid(self) -> bool:
        if self.length <= 0 or self.width <= 0:
            return False

        # Check if all slots are within the board
        bounds = box(0, 0, self.length, self.width)
        if not all(slot.within(bounds) for slot in self.slots):
            return False

        # Check slots don't overlap
        for i, slot1 in enumerate(self.slots):
            for slot2 in self.slots[i + 1:]:
                if slot1.intersects(slot2):
                    return False

        return True
