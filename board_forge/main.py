import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, Menu
import os
import sys
import math
from shapely.affinity import rotate as shapely_rotate

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.board_view import BoardCanvas
from design import Design
from data.sample_pieces import SAMPLE_PIECES, get_piece
from shapely.geometry import Polygon
from piece import Piece
from data.piece_dimensions import piece_dims

class GamePieceOrganizerApp:
    def __init__(self, root):
        self.root = root
        root.title("Game Piece Organizer")
        root.geometry("1000x700")
        
        # Load and set the logo/icon
        self.design = Design(pieces=[])

        self.board_width = 300
        self.board_height = 400
        
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "board_forge", "data", "logo.png")
            if not os.path.exists(logo_path):
                logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "data", "logo.png")
                        
            print(f"Attempting to load logo from: {logo_path}")
            self.logo_image = tk.PhotoImage(file=logo_path)
            self.logo = tk.PhotoImage(file=logo_path)
            logo = tk.PhotoImage(file=logo_path)
            root.iconphoto(True, logo)  # Set window icon
            
            self.logo_image = self.logo_image.subsample(13, 13)  # Reduce to 1/8 of original size
            
            # Create a label to display the logo
            logo_label = ttk.Label(self.header_frame, image=self.logo_image)
            logo_label.pack(side=tk.LEFT, padx=5)
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        
        # Create board canvas
        self.board_frame = ttk.LabelFrame(self.left_frame, text="Board Design")
        self.board_frame.pack(fill=tk.BOTH, expand=True)
        
        self.board = BoardCanvas(self.board_frame, self.design, width=600, height=500)
        self.board.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.board.set_app(self)
        
        # Create controls
        self.context_menu = Menu(root, tearoff=0)
        self.piece_list = self.create_piece_display()
        
        self.create_piece_selector()
        self.create_board_controls()
        self.create_optimization_controls()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            root, 
            textvariable=self.status_var,
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_piece_display(self):
        display_frame = ttk.LabelFrame(self.right_frame, text="Piece List")

        display_frame.pack(fill=tk.X, pady=(0, 10))
        listbox = tk.Listbox(display_frame, width=40, height=10)
        listbox.pack(padx=20, pady=20)
        listbox.bind("<Double-Button-1>", self.show_context_menu)

        
        for piece in self.design.pieces:
            listbox.insert(tk.END, piece.name)

        self.add_image_button = tk.Button(display_frame, text="Add from File", command=self.add_from_image)
        self.add_image_button.pack(pady=5)
        
        self.context_menu.add_command(label="Rename", command=self.rename_piece)
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.context_menu.add_command(label="Make Copy", command=self.copy_selected)
        self.context_menu.add_command(label="Add to board", command=self.add_selected)

        return listbox

    def show_context_menu(self, event=None):
        try:
            self.piece_list.selection_clear(0, tk.END)
            self.piece_list.selection_set(self.piece_list.nearest(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass
    
    def add_from_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg")])
        num_pieces = simpledialog.askinteger("Number of Piece Selection", "How many pieces in your image?")
        if file_path:
            name = file_path.split("/")[-1]  # Extracts filename
            dims = piece_dims(file_path, num_pieces=num_pieces)
            for i, (width,height) in enumerate(dims):
                piece = Piece(f'{name} {i}', [(0,0), (width, 0), (height, 0), (width, height)])
                self.design.pieces.append(piece)
                self.piece_list.insert(tk.END, piece.name)
    
    def add_selected(self):
        selected_index = self.piece_list.curselection()
        if selected_index:
            index = selected_index[0]
            self.add_custom_polygon(custom=False, polygon=self.design.pieces[index].shape)

    def delete_selected(self):
        selected_index = self.piece_list.curselection()
        if selected_index:
            index = selected_index[0]
            del self.design.pieces[index]
            self.piece_list.delete(index)

    def copy_selected(self):
        selected_index = self.piece_list.curselection()
        if selected_index:
            index = selected_index[0]
            piece = self.design.pieces[index]
            copy_name = f"{piece.name} (Copy)"
            piece_copy = Piece(copy_name, piece.shape)
            self.design.pieces.append(piece_copy)
            self.piece_list.insert(tk.END, piece_copy.name)

    def rename_piece(self, event=None):
        selected_index = self.piece_list.curselection()
        if selected_index:
            index = selected_index[0]
            old_name = self.design.pieces[index].name
            new_name = simpledialog.askstring("Rename Piece", f"Rename '{old_name}' to:")
            if new_name:
                self.design.pieces[index].name = new_name
                self.piece_list.delete(index)
                self.piece_list.insert(index, new_name)
    
    def create_piece_selector(self):
        """Create the custom polygon input panel"""
        piece_frame = ttk.LabelFrame(self.right_frame, text="Game Pieces")
        piece_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Instructions
        ttk.Label(piece_frame, text="Enter polygon points (x,y pairs):").pack(padx=5, pady=(5,0))
        
        self.points_text = tk.Text(piece_frame, height=5, width=25)
        self.points_text.pack(fill=tk.X, padx=5, pady=5)
        self.points_text.insert(tk.END, "0,0\n50,0\n50,50\n0,50")
        
        # Add a tooltip or example
        ttk.Label(piece_frame, text="Format: x,y (one pair per line)").pack(padx=5)
        
        scale_frame = ttk.Frame(piece_frame)
        scale_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(scale_frame, text="Scale:").pack(side=tk.LEFT)
        
        self.scale_var = tk.DoubleVar(value=1.0)
        scale_entry = ttk.Spinbox(
            scale_frame,
            from_=0.1,
            to=5.0,
            increment=0.1,
            textvariable=self.scale_var,
            width=5
        )
        scale_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        add_btn = ttk.Button(
            piece_frame,
            text="Add to Board",
            command=self.add_custom_polygon
        )
        add_btn.pack(fill=tk.X, padx=5, pady=5)
        
    def add_custom_polygon(self, custom=True, polygon=None):
        """Add a custom polygon to the board based on user input"""
        try:
            if custom:
                points_text = self.points_text.get("1.0", tk.END).strip()
                
                points = []
                for line in points_text.split('\n'):
                    if line.strip():
                        x, y = map(float, line.strip().split(','))
                        points.append((x, y))
                
                if len(points) < 3:
                    messagebox.showinfo("Error", "A polygon needs at least 3 points")
                    return
                    
                scale = self.scale_var.get()
                scaled_points = [(x * scale, y * scale) for x, y in points]
                
                # Create the polygon
                polygon = Polygon(scaled_points)
            # Find a good position for the new polygon
            # Calculate the offset for the new piece
            # First, find the bounds of the new polygon
            min_x, min_y, max_x, max_y = polygon.bounds
            width = max_x - min_x
            height = max_y - min_y
            
            # Calculate the grid size for placement
            grid_size = max(width, height) + 10  # Add some spacing
            
            # Get the canvas dimensions
            canvas_width = self.board.winfo_width() or 600  # Default if not yet rendered
            canvas_height = self.board.winfo_height() or 500  # Default if not yet rendered
            
            # Maximum number of pieces per row based on canvas width
            max_per_row = max(1, int((canvas_width - 40) / grid_size))
            
            # Calculate position based on the number of existing pieces
            slot_index = len(self.design.pieces)
            row = slot_index // max_per_row
            col = slot_index % max_per_row
            
            # Calculate the translation needed
            # Start with a consistent initial position for all pieces
            offset_x = 20 + col * grid_size  # Start with left margin
            offset_y = 20 + row * grid_size  # Start with top margin
            
            # Move the polygon to the absolute position (not relative to its min bounds)
            from shapely.affinity import translate
            polygon = translate(polygon, offset_x - min_x, offset_y - min_y)
            
            # Create the piece and add to the pieces list
            piece = Piece(name="Unnamed Piece", shape=polygon)
            self.design.pieces.append(piece)
            self.piece_list.insert(tk.END, piece.name)
            
            self.board.update_view()
            self.status_var.set(f"Added custom polygon with {len(polygon.exterior.coords)} points")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add polygon: {str(e)}")
        
    def create_board_controls(self):
        """Create controls for manipulating the board"""
        board_controls = ttk.LabelFrame(self.right_frame, text="Board Controls")
        board_controls.pack(fill=tk.X, pady=(0, 10))
        
        # Visual guide dimensions
        dim_frame = ttk.Frame(board_controls)
        dim_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Rotation Controls
        rotation_frame = ttk.Frame(board_controls)
        rotation_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(rotation_frame, text="Rotation:").pack(side=tk.LEFT)
        
        # Rotation angle entry
        self.rotation_var = tk.IntVar(value=15)
        rotation_entry = ttk.Spinbox(
            rotation_frame,
            from_=1,
            to=180,
            increment=15,
            textvariable=self.rotation_var,
            width=5
        )
        rotation_entry.pack(side=tk.LEFT, padx=5)
        
        # Rotation buttons
        rotate_buttons = ttk.Frame(board_controls)
        rotate_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        rotate_ccw_btn = ttk.Button(
            rotate_buttons,
            text="↺ Rotate CCW",
            command=lambda: self.rotate_selected_slot(counterclockwise=True)
        )
        rotate_ccw_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        rotate_cw_btn = ttk.Button(
            rotate_buttons,
            text="Rotate CW ↻",
            command=lambda: self.rotate_selected_slot(counterclockwise=False)
        )
        rotate_cw_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        remove_btn = ttk.Button(
            board_controls,
            text="Remove Selected Slot",
            command=self.remove_selected_slot
        )
        remove_btn.pack(fill=tk.X, padx=5, pady=5)
        
        clear_btn = ttk.Button(
            board_controls,
            text="Clear All Slots",
            command=self.clear_all_slots
        )
        clear_btn.pack(fill=tk.X, padx=5, pady=5)
    
    def create_optimization_controls(self):
        """Create controls for optimization"""
        opt_frame = ttk.LabelFrame(self.right_frame, text="Optimization")
        opt_frame.pack(fill=tk.X)
        
        # Add checkbox for rotation control
        self.allow_rotation_var = tk.BooleanVar(value=True)
        rotation_check = ttk.Checkbutton(
            opt_frame,
            text="Allow rotation during optimization",
            variable=self.allow_rotation_var
        )
        rotation_check.pack(fill=tk.X, padx=5, pady=5)
        
        # Button to run optimization
        optimize_btn = ttk.Button(
            opt_frame,
            text="Optimize Slot Placement",
            command=self.run_optimization
        )
        optimize_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Export buttons
        export_frame = ttk.Frame(opt_frame)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        export_svg_btn = ttk.Button(
            export_frame,
            text="Export SVG",
            command=self.export_svg
        )
        export_svg_btn.pack(fill=tk.X, pady=(0, 5))
        
        validate_btn = ttk.Button(
            export_frame,
            text="Validate Design",
            command=self.validate_design
        )
        validate_btn.pack(fill=tk.X)
    
    def add_piece_to_board(self):
        """Add the selected piece to the board"""
        piece_name = self.piece_var.get()
        if not piece_name:
            messagebox.showinfo("Error", "Please select a piece type")
            return
            
        scale = self.scale_var.get()
        
        try:
            piece = get_piece(piece_name, scale)
            
            # Add it to the design and update the view
            self.design.pieces.append(piece)
            self.board.update_view()
            self.status_var.set(f"Added {piece_name} (scale: {scale})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add piece: {str(e)}")
    
    def update_guide_dimensions(self):
        """Update the visual guide dimensions"""
        self.board_width = self.width_var.get()
        self.board_height = self.height_var.get()
        
        self.board.update_view()
        self.status_var.set(f"Updated guide dimensions to {self.board_width}x{self.board_height}")
    
    def remove_selected_slot(self):
        """Remove the currently selected slot"""
        if hasattr(self.board, 'selected_slot') and self.board.selected_slot is not None:
            index = self.board.selected_slot
            if 0 <= index < len(self.design.pieces):
                self.design.pieces.pop(index)
                self.board.selected_slot = None
                self.board.update_view()
                self.status_var.set("Removed selected slot")
    
    def clear_all_slots(self):
        """Remove all slots from the design"""
        if messagebox.askyesno("Confirm", "Are you sure you want to remove all slots?"):
            self.design.pieces = []
            if hasattr(self.board, 'selected_slot'):
                self.board.selected_slot = None
            self.board.update_view()
            self.status_var.set("Cleared all slots")
            
    def rotate_selected_slot(self, counterclockwise=False):
        """Rotate the selected slot"""
        if not hasattr(self.board, 'selected_slot') or self.board.selected_slot is None:
            self.status_var.set("No slot selected for rotation")
            return
        
        angle = self.rotation_var.get()
        if counterclockwise:
            angle = -angle
        
        self.board.rotate_selected_slot(angle=angle)
    
    def run_optimization(self):
        """Run the optimization algorithm on the current slots"""
        if not self.design.pieces:
            messagebox.showinfo("Error", "No slots to optimize")
            return
    
        try:
            # Import optimization module
            import board_forge.optimize as optimize_module
            print(f"Optimize module: {optimize_module}")
            print(f"Optimize module dir: {dir(optimize_module)}")
            
            # Update status
            self.status_var.set("Running optimization... Please wait.")
            self.root.update()
            
            # Get the optimize function - make sure we're accessing the function correctly
            optimize_func = optimize_module.optimize
            print(f"Optimize function: {optimize_func}")
            
            # Make a copy of the current design
            current_design = self.design
            print(f"Current design: {current_design}, slots: {len(current_design.pieces)}")

            # Get rotation preference
            allow_rotation = self.allow_rotation_var.get()
            
            # Run the optimization with explicit arguments
            optimized_design = optimize_func(
                initial_design=current_design, 
                iterations=1000,  # Reduced iterations for testing
                alpha=0.99,
                allow_rotation=allow_rotation  # Pass the rotation preference
            )
            
            print(f"Optimization completed, result: {optimized_design}")
            
            # Update the design with the optimized one
            self.design = optimized_design
            
            # Update the board view
            self.board.design = self.design
            self.board.update_view()
            
            # Reset any selection state
            if hasattr(self.board, 'selected_slot'):
                self.board.selected_slot = None
            
            rotation_status = "with" if allow_rotation else "without"
            self.status_var.set(f"Optimization complete {rotation_status} rotation! Area minimized.")
        except ImportError as e:
            error_msg = f"Import error: {e}"
            print(error_msg)
            messagebox.showerror("Optimization Error", error_msg)
        except AttributeError as e:
            error_msg = f"Attribute error: {e}"
            print(error_msg)
            messagebox.showerror("Optimization Error", error_msg)
        except Exception as e:
            error_msg = f"Error running optimization: {e}\nType: {type(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            messagebox.showerror("Optimization Error", error_msg)
        
    def export_svg(self):
        """Export the current design as SVG files"""
        if not self.design.pieces:
            messagebox.showinfo("Error", "No slots to export")
            return
            
        try:
            from tkinter import filedialog
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                initialfile='out.svg',
                defaultextension=".svg",
                filetypes=[("SVG files", "*.svg"), ("All files", "*.*")],
                title="Save SVG file"
            )
            
            if not file_path:  # User cancelled
                return
                
            print(f"Attempting to save SVG to: {file_path}")
            svg_drawing = self.design.to_svg()
            
            # Save the SVG file
            svg_drawing.save(pretty=True)
            with open(file_path,'w') as f:
                f.write(svg_drawing.tostring())
            
            # TODO: DEBUGGING
            import os
            if os.path.exists(file_path):
                print(f"SUCCESS: File exists at {file_path}")
                print(f"File size: {os.path.getsize(file_path)} bytes")
            else:
                print(f"ERROR: File does not exist at {file_path} after save operation")

            self.status_var.set(f"SVG exported to {file_path}")
            messagebox.showinfo("Export Complete", f"SVG successfully saved to:\n{file_path}")
            
        except ImportError as e:
            messagebox.showerror("Export Error", f"Missing required package: {e}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Export Error", f"Failed to export SVG: {str(e)}")
    
    def validate_design(self):
        """Validate that the current design is valid (no overlaps, etc.)"""
        if not self.design.pieces:
            messagebox.showinfo("Validation", "No slots to validate")
            return
            
        try:
            is_valid = self.design.is_valid
            if is_valid:
                messagebox.showinfo("Validation", "Design is valid! No overlapping slots.")
            else:
                messagebox.showerror("Validation Failed", "Some slots are overlapping.")
        except Exception as e:
            messagebox.showerror("Validation Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = GamePieceOrganizerApp(root)
    root.mainloop()