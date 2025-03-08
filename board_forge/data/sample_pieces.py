from shapely.geometry import Polygon

SAMPLE_PIECES = {
    "meeple": Polygon([
        (0, 0), (10, 0), (10, 20), (15, 25), (15, 40), (5, 40), (5, 25), (0, 20)
    ]),
    
    "cube": Polygon([
        (0, 0), (20, 0), (20, 20), (0, 20)
    ]),
    
    "disc": Polygon([
        (15, 0), (19, 3), (22, 7), (23, 12), (22, 17), (19, 21),
        (15, 24), (9, 24), (5, 21), (2, 17), (1, 12), (2, 7), (5, 3), (9, 0)
    ]),
    
    "card": Polygon([
        (0, 0), (63, 0), (63, 88), (0, 88)
    ]),
    
    "resource_token": Polygon([
        (0, 0), (30, 0), (30, 30), (0, 30)
    ]),
    
    "hexagon_tile": Polygon([
        (25, 0), (75, 0), (100, 43), (75, 86), (25, 86), (0, 43)
    ]),
    
    "triangle_token": Polygon([
        (0, 0), (40, 0), (20, 35)
    ]),
    
    "player_marker": Polygon([
        (0, 0), (10, 0), (15, 5), (15, 25), (5, 25), (0, 20)
    ]),
}

CATAN_PIECES = {
    "settlement": SAMPLE_PIECES["meeple"],
    "road": Polygon([(0, 0), (30, 0), (30, 5), (0, 5)]),
    "city": Polygon([(0, 0), (15, 0), (15, 10), (25, 10), (25, 20), (0, 20)]),
    "hex_tile": SAMPLE_PIECES["hexagon_tile"],
    "number_token": SAMPLE_PIECES["disc"]
}

CHESS_PIECES = {
    "pawn": Polygon([(10, 0), (15, 0), (15, 20), (20, 25), (5, 25), (10, 20)]),
    "rook": Polygon([(5, 0), (20, 0), (20, 5), (25, 5), (25, 25), (0, 25), (0, 5), (5, 5)]),
    "knight": Polygon([(5, 0), (20, 0), (25, 10), (20, 25), (10, 20), (5, 25), (0, 15), (0, 5)]),
    "bishop": Polygon([(10, 0), (15, 0), (20, 10), (15, 25), (10, 25), (5, 10)]),
    "queen": Polygon([(10, 0), (20, 0), (25, 10), (20, 20), (15, 30), (10, 30), (5, 20), (0, 10), (5, 0)]),
    "king": Polygon([(10, 0), (20, 0), (25, 10), (20, 20), (25, 30), (20, 35), (10, 35), (5, 30), (10, 20), (5, 10)])
}

def scale_polygon(polygon, factor):
    return Polygon([(x * factor, y * factor) for x, y in polygon.exterior.coords])

def get_piece(piece_name, scale=1.0):
    if piece_name in SAMPLE_PIECES:
        return scale_polygon(SAMPLE_PIECES[piece_name], scale)
    
    for collection in [CATAN_PIECES, CHESS_PIECES]:
        if piece_name in collection:
            return scale_polygon(collection[piece_name], scale)
    
    return scale_polygon(SAMPLE_PIECES["cube"], scale)