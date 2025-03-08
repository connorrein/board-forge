import tkinter as tk
from tkinter import ttk
from data.sample_pieces import SAMPLE_PIECES, CATAN_PIECES, CHESS_PIECES, get_piece

def display_piece(canvas, polygon, name):
    canvas.delete("all")
    
    coords = []
    for x, y in polygon.exterior.coords[:-1]:
        coords.extend([x + 50, y + 50])
    
    canvas.create_polygon(coords, fill="lightblue", outline="blue")
    canvas.create_text(150, 20, text=name, font=("Arial", 14, "bold"))
    
    canvas.create_line(10, 150, 290, 150, fill="gray", dash=(2, 2))  # x-axis
    canvas.create_line(150, 10, 150, 290, fill="gray", dash=(2, 2))  # y-axis

# Create the main window
root = tk.Tk()
root.title("Game Piece Organizer - Piece Viewer")
root.geometry("800x600")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)
notebook = ttk.Notebook(main_frame)
notebook.pack(fill=tk.BOTH, expand=True)

collections = {
    "Sample Pieces": SAMPLE_PIECES,
    "Catan Pieces": CATAN_PIECES,
    "Chess Pieces": CHESS_PIECES
}

for collection_name, collection in collections.items():
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=collection_name)
    
    canvas_frame = ttk.Frame(tab)
    canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    buttons_frame = ttk.Frame(tab)
    buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
    
    canvas = tk.Canvas(canvas_frame, width=300, height=300, bg="white")
    canvas.pack(fill=tk.BOTH, expand=True)
    
    for piece_name in collection:
        piece = collection[piece_name]
        button = ttk.Button(
            buttons_frame, 
            text=piece_name,
            command=lambda c=canvas, p=piece, n=piece_name: display_piece(c, p, n)
        )
        button.pack(fill=tk.X, padx=5, pady=2)

info_frame = ttk.Frame(main_frame)
info_frame.pack(fill=tk.X)

info_label = ttk.Label(
    info_frame, 
    text="Select a piece from the buttons to view its shape.\nThese shapes will be used for creating slots in the game piece holder.",
    justify=tk.CENTER
)
info_label.pack(pady=10)

status_bar = ttk.Label(root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# Start the application
root.mainloop()