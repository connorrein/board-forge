from dataclasses import dataclass
from typing import List
from shapely import unary_union
from shapely.geometry import Polygon, box
from svgwrite import Drawing
from piece import Piece

PADDING = 10

@dataclass
class Design:
    pieces: List[Piece]


    @property
    def bounding_box(self) -> Polygon:
        unified = unary_union([p.shape for p in self.pieces])
        min_x, min_y, max_x, max_y = unified.bounds
        return box(min_x - PADDING, min_y - PADDING, max_x + PADDING, max_y + PADDING)


    @property
    def is_valid(self) -> bool:
        """Check if all slots maintain a minimum distance from each other"""
        min_distance = 10.0
        for i in range(len(self.pieces)):
            for j in range(i + 1, len(self.pieces)):
                if self.pieces[i].shape.distance(self.pieces[j].shape) < min_distance:
                    return False
        return True


    def to_svg(self) -> Drawing:
        stroke_width = 0.05

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
        for piece in self.pieces:
            dwg.add(dwg.polygon(
                points=list(piece.shape.exterior.coords),
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
