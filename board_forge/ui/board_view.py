import tkinter as tk
from tkinter import ttk
from shapely.geometry import Polygon
from shapely.affinity import rotate as shapely_rotate
import math

class BoardCanvas(tk.Canvas):
    def __init__(self, parent, design=None, **kwargs):
        super().__init__(parent, bg="white", **kwargs)
        self.design = design
        self.selected_slot = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.slot_objects = {}
        self.app = None  # Will be set from main.py
        self.slot_centers = {}  # Store centers of slots for rotation
        
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<KeyPress-r>", self.rotate_selected_slot)
        
    def set_app(self, app):
        """Set the reference to the main application"""
        self.app = app
        if self.design:
            self.update_view()
    
    def update_view(self):
        """Update the canvas to reflect the current design state"""
        self.delete("all")
        
        if not self.design or not self.app:
            return
        
        # Draw each slot
        self.slot_objects = {}
        self.slot_centers = {}
        
        for i, slot in enumerate(self.design.slots):
            # Calculate center for rotation
            centroid = slot.centroid
            self.slot_centers[i] = (centroid.x, centroid.y)
            
            coords = []
            for x, y in slot.exterior.coords[:-1]:
                coords.extend([x + 10, y + 10])
            
            polygon_id = self.create_polygon(
                coords, 
                fill="lightblue", 
                outline="blue", 
                tags=f"slot_{i}"
            )
            
            self.slot_objects[polygon_id] = i
        
        # If slots exist, draw the calculated bounding box with NO? padding 
        # since we need to have a border at edge of the actual svg
        if self.design.slots:
            try:
                bb = self.design.bounding_box
                
                min_x, min_y, max_x, max_y = bb.bounds
                
                # TODO: Remove 5mm padding (can be changed later)
                # padding = 5
                # min_x -= padding
                # min_y -= padding
                # max_x += padding
                # max_y += padding
                
                padded_box = [
                    (min_x, min_y), (max_x, min_y), 
                    (max_x, max_y), (min_x, max_y), 
                    (min_x, min_y)
                ]
                
                coords = []
                for x, y in padded_box:
                    coords.extend([x + 10, y + 10])
                
                self.create_polygon(
                    coords,
                    outline="red",
                    width=2,
                    fill="",
                    tags="calculated_bb"
                )
            except Exception as e:
                print(f"Error drawing bounding box: {e}")
    
    def on_click(self, event):
        """Handle mouse click events to select slots"""
        items = self.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
        
        print(f"Items at click point: {items}")
        
        for item_id in items:
            tags = self.gettags(item_id)
            print(f"Checking item: {item_id}, tags: {tags}")
            
            # Check if it's a slot by looking at the tags
            for tag in tags:
                if tag.startswith("slot_"):
                    slot_index = int(tag.split("_")[1])
                    print(f"Found slot: {slot_index}")
                    
                    if self.selected_slot is not None:
                        self.itemconfig(f"slot_{self.selected_slot}", fill="lightblue")
                    
                    # Select this slot
                    self.selected_slot = slot_index
                    self.itemconfig(tag, fill="yellow")
                    
                    # Save drag start position
                    self.drag_start_x = event.x
                    self.drag_start_y = event.y
                    
                    if self.app:
                        self.app.status_var.set(f"Selected slot {slot_index}")
                    
                    return
        
        # If we get here, no slot was found
        if self.selected_slot is not None:
            self.itemconfig(f"slot_{self.selected_slot}", fill="lightblue")
            self.selected_slot = None
            
            if self.app:
                self.app.status_var.set("No slot selected")
            
    def item_contains_point(self, item_id, x, y):
        """Check if the given point is within a canvas item"""
        bbox = self.bbox(item_id)
        if not bbox:
            return False
            
        # Simple bounding box check first
        if not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
            return False
            
        overlapping = self.find_overlapping(x, y, x, y)
        return item_id in overlapping
    
    def on_drag(self, event):
        """Handle dragging of selected slots"""
        if self.selected_slot is not None:
            # movement delta
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            if dx == 0 and dy == 0:
                return  # no movement
                
            self.move(f"slot_{self.selected_slot}", dx, dy)
            
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # DEBUG
            print(f"Dragging slot {self.selected_slot}: dx={dx}, dy={dy}")
    
    def on_release(self, event):
        """Handle release of mouse to finalize slot movement"""
        if self.selected_slot is not None:
            slot_index = self.selected_slot
            
            tag = f"slot_{slot_index}"
            items = self.find_withtag(tag)
            
            if not items:
                print(f"Warning: Couldn't find items with tag {tag}")
                return
                
            coords = self.coords(items[0])
            
            points = []
            for i in range(0, len(coords), 2):
                points.append((coords[i] - 10, coords[i+1] - 10))
            
            # Update the actual slot in the design
            if slot_index < len(self.design.slots):
                self.design.slots[slot_index] = Polygon(points)
                
                centroid = self.design.slots[slot_index].centroid
                self.slot_centers[slot_index] = (centroid.x, centroid.y)
                
                temp_selected = self.selected_slot
                self.update_view()
                
                self.selected_slot = temp_selected
                self.itemconfig(f"slot_{temp_selected}", fill="yellow")
                
                # DEBUG
                print(f"Updated slot {slot_index} with new coordinates")
            else:
                print(f"Error: Slot index {slot_index} out of range")
    
    def rotate_selected_slot(self, event=None, angle=15):
        """Rotate the selected slot by the specified angle in degrees"""
        if self.selected_slot is None:
            return
            
        slot_index = self.selected_slot
        
        if slot_index < len(self.design.slots):
            try:
                current_polygon = self.design.slots[slot_index]
                center_x, center_y = self.slot_centers.get(slot_index, current_polygon.centroid.coords[0])
                rotated_polygon = shapely_rotate(current_polygon, angle, origin=(center_x, center_y))
    
                # update the view
                self.design.slots[slot_index] = rotated_polygon
                temp_selected = self.selected_slot
                self.update_view()
                
                self.selected_slot = temp_selected
                self.itemconfig(f"slot_{temp_selected}", fill="yellow")
                
                if self.app:
                    self.app.status_var.set(f"Rotated slot {slot_index} by {angle} degrees")
                    
                print(f"Rotated slot {slot_index} by {angle} degrees")
            except Exception as e:
                print(f"Error rotating slot: {e}")
                if self.app:
                    self.app.status_var.set(f"Error rotating slot: {e}")
    
    def add_slot(self, polygon):
        """Add a new slot to the design"""
        if self.design:
            self.design.slots.append(polygon)
            self.update_view()
            
            # DEBUG
            print(f"Added new slot, total: {len(self.design.slots)}")