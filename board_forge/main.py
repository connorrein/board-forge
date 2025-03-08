import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import math
from shapely.affinity import rotate as shapely_rotate

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.board_view import BoardCanvas
from design import Design
from data.sample_pieces import SAMPLE_PIECES, get_piece
from shapely.geometry import Polygon

class GamePieceOrganizerApp:
    def __init__(self, root):
        self.root = root
        root.title("Game Piece Organizer")
        root.geometry("1000x700")
        
        # Load and set the logo/icon
        self.design = Design(slots=[])

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
        
    def add_custom_polygon(self):
        """Add a custom polygon to the board based on user input"""
        try:
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
            
            self.design.slots.append(polygon)
            self.board.update_view()
            self.status_var.set(f"Added custom polygon with {len(points)} points (scale: {scale})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add polygon: {str(e)}")
    
    def create_board_controls(self):
        """Create controls for manipulating the board"""
        board_controls = ttk.LabelFrame(self.right_frame, text="Board Controls")
        board_controls.pack(fill=tk.X, pady=(0, 10))
        
        # Visual guide dimensions
        dim_frame = ttk.Frame(board_controls)
        dim_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # ttk.Label(dim_frame, text="Guide Width:").grid(row=0, column=0, sticky=tk.W)
        #self.width_var = tk.IntVar(value=self.board_width)
        #width_entry = ttk.Spinbox(
        #    dim_frame,
        #    from_=100,
        #    to=1000,
        #    increment=10,
        #    textvariable=self.width_var,
        #    width=5,
        #    command=self.update_guide_dimensions
        #)
        #width_entry.grid(row=0, column=1, padx=5)
        
        # ttk.Label(dim_frame, text="Guide Height:").grid(row=1, column=0, sticky=tk.W)
        # self.height_var = tk.IntVar(value=self.board_height)
        # height_entry = ttk.Spinbox(
        #    dim_frame,
        #    from_=100,
        #    to=1000,
        #    increment=10,
        #    textvariable=self.height_var,
        #    width=5,
        #    command=self.update_guide_dimensions
        #)
        #height_entry.grid(row=1, column=1, padx=5)
        
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
            self.design.slots.append(piece)
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
            if 0 <= index < len(self.design.slots):
                self.design.slots.pop(index)
                self.board.selected_slot = None
                self.board.update_view()
                self.status_var.set("Removed selected slot")
    
    def clear_all_slots(self):
        """Remove all slots from the design"""
        if messagebox.askyesno("Confirm", "Are you sure you want to remove all slots?"):
            self.design.slots = []
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
        if not self.design.slots:
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
            print(f"Current design: {current_design}, slots: {len(current_design.slots)}")
            
            # Run the optimization with explicit arguments
            optimized_design = optimize_func(
                initial_design=current_design, 
                iterations=1000,  # Reduced iterations for testing
                alpha=0.99
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
            
            self.status_var.set("Optimization complete! Area minimized.")
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
        if not self.design.slots:
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
        if not self.design.slots:
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