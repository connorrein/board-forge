from dataclasses import dataclass
from typing import List
from shapely import unary_union
from shapely.geometry import Polygon, box
from svgwrite import Drawing

PADDING = 10

@dataclass
class Design:
    slots: List[Polygon]


    @property
    def bounding_box(self) -> Polygon:
        unified = unary_union(self.slots)
        min_x, min_y, max_x, max_y = unified.bounds
        return box(min_x - PADDING, min_y - PADDING, max_x + PADDING, max_y + PADDING)


    @property
    def is_valid(self) -> bool:
        # Check slots don't overlap
        for i, slot1 in enumerate(self.slots):
            for slot2 in self.slots[i + 1:]:
                if slot1.intersects(slot2):
                    return False

        return True


    def to_svg(self) -> Drawing:
        stroke_width = 0.05

        bb = self.bounding_box
        dwg = Drawing(
            size=(f"{bb.bounds[2] - bb.bounds[0]}mm", f"{bb.bounds[3] - bb.bounds[1]}mm"),
            viewBox=f"{bb.bounds[0]} {bb.bounds[1]} {bb.bounds[2] - bb.bounds[0]} {bb.bounds[3] - bb.bounds[1]}"
        )

        # Bounding box with rounded corners
        dwg.add(dwg.rect(
            insert=(bb.bounds[0], bb.bounds[1]),
            size=(bb.bounds[2] - bb.bounds[0], bb.bounds[3] - bb.bounds[1]),
            rx=PADDING,
            ry=PADDING,
            fill='none',
            stroke='black',
            stroke_width=stroke_width
        ))

        # Slots
        for slot in self.slots:
            dwg.add(dwg.polygon(
                points=list(slot.exterior.coords),
                fill='none',
                stroke='black',
                stroke_width=stroke_width
            ))

        return dwg
