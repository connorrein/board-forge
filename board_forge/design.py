from dataclasses import dataclass
from typing import List
from shapely import unary_union
from shapely.geometry import Polygon, box
from svgwrite import Drawing
from piece import Piece

PADDING = 10
SLOT_PADDING = 1  # 1mm padding for slots

@dataclass
class Design:
    slots: List[Polygon]

    def get_padded_slots(self) -> List[Piece]:
        """Return slots with added padding of SLOT_PADDING mm on each side"""
        return [s.buffer(SLOT_PADDING) for s in self.slots]

    @property
    def bounding_box(self) -> Polygon:
        # Use padded slots to calculate the bounding box
        padded_slots = self.get_padded_slots()
        # Extract the shape objects from the Piece objects
        slot_shapes = [slot for slot in padded_slots]
        if not slot_shapes:  # Handle empty case
            return box(0, 0, 10, 10)  # Default small box
        unified = unary_union(slot_shapes)
        unified = unary_union(self.slots)
        min_x, min_y, max_x, max_y = unified.bounds
        return box(min_x - PADDING, min_y - PADDING, max_x + PADDING, max_y + PADDING)

    @property
    def is_valid(self) -> bool:
        """Check if all slots maintain a minimum distance from each other,
        taking into account the SLOT_PADDING applied to each slot"""
        min_distance = 10.0
        for i in range(len(self.slots)):
            for j in range(i + 1, len(self.slots)):
                if self.slots[i].distance(self.slots[j]) < min_distance:
                    return False
        return True

    def to_svg(self) -> Drawing:
        stroke_width = 0.05

        # Get padded slots for display
        padded_slots = self.get_padded_slots()
        
        # Use the original bounding box property
        bb = self.bounding_box

        dwg = Drawing(
            size=(f"{bb.bounds[2] - bb.bounds[0]}mm", f"{(bb.bounds[3] - bb.bounds[1]) * 2}mm"),
            viewBox=f"{bb.bounds[0]} {bb.bounds[1]} {bb.bounds[2] - bb.bounds[0]} {(bb.bounds[3] - bb.bounds[1]) * 2}"
        )

        # Top piece
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

        # Bottom piece
        dwg.add(dwg.rect(
            insert=(bb.bounds[0], bb.bounds[3]),
            size=(bb.bounds[2] - bb.bounds[0], bb.bounds[3] - bb.bounds[1]),
            rx=PADDING,
            ry=PADDING,
            fill='none',
            stroke='black',
            stroke_width=stroke_width
        ))

        return dwg