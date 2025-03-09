import random
import numpy as np
from shapely.affinity import translate, rotate
from board_forge.design import Design
from shapely.geometry import Polygon

# Define constants for minimum spacing and other parameters
MIN_SPACING = 10  # Minimum distance between pieces
BUFFER_EXTRA = 5  # Extra buffer for safety
GROUP_THRESHOLD = 0.1  # Threshold for grouping similar shapes
CANVAS_MARGIN = 20  # Margin from canvas edges
CANVAS_WIDTH = 600  # Default canvas width
CANVAS_HEIGHT = 450  # Default canvas height

def get_shape_signature(polygon):
    """Get a simple signature of a shape based on its area and perimeter ratio"""
    area = polygon.area
    perimeter = polygon.length
    # A simple shape signature that's somewhat invariant to scaling and rotation
    return area / (perimeter * perimeter) if perimeter > 0 else 0

def group_similar_shapes(slots):
    """Group shapes that have similar geometry"""
    if not slots:
        return []
        
    # Get signatures for all slots
    signatures = [get_shape_signature(slot) for slot in slots]
    
    # Group by similar signatures
    groups = {}
    for i, sig in enumerate(signatures):
        found_group = False
        for group_sig in groups:
            if abs(sig - group_sig) < GROUP_THRESHOLD:
                groups[group_sig].append(i)
                found_group = True
                break
        if not found_group:
            groups[sig] = [i]
    
    return list(groups.values())

def constrain_to_canvas(design: Design, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT):
    """Ensure all slots are within the canvas bounds with margin WITHOUT scaling"""
    if not design.slots:
        return design
        
    slots = design.slots.copy()
    
    # Check the total bounds of the design
    bounds = design.bounding_box.bounds
    
    # If the design is already within canvas, return as is
    if (bounds[0] >= CANVAS_MARGIN and bounds[2] <= canvas_width - CANVAS_MARGIN and
        bounds[1] >= CANVAS_MARGIN and bounds[3] <= canvas_height - CANVAS_MARGIN):
        return design
    
    # Calculate how much to shift the entire design to fit in canvas
    shift_x = 0
    shift_y = 0
    
    # Adjust x position
    if bounds[0] < CANVAS_MARGIN:
        shift_x = CANVAS_MARGIN - bounds[0]
    elif bounds[2] > canvas_width - CANVAS_MARGIN:
        shift_x = (canvas_width - CANVAS_MARGIN) - bounds[2]
    
    # Adjust y position
    if bounds[1] < CANVAS_MARGIN:
        shift_y = CANVAS_MARGIN - bounds[1]
    elif bounds[3] > canvas_height - CANVAS_MARGIN:
        shift_y = (canvas_height - CANVAS_MARGIN) - bounds[3]
    
    # If we need to shift, translate all pieces
    if shift_x != 0 or shift_y != 0:
        for i in range(len(slots)):
            slots[i] = translate(slots[i], shift_x, shift_y)
    
    # Check if design is still too large for canvas
    design = Design(slots)
    bounds = design.bounding_box.bounds
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    
    # MODIFIED: Instead of scaling, we'll just ensure all slots are within the canvas bounds
    # If the design is still too large, we'll only translate pieces that are outside
    if width > canvas_width - 2*CANVAS_MARGIN or height > canvas_height - 2*CANVAS_MARGIN:
        new_slots = []
        for slot in slots:
            slot_bounds = slot.bounds
            
            # Check if this slot is outside the canvas
            adjust_x = 0
            adjust_y = 0
            
            # Adjust position if outside left boundary
            if slot_bounds[0] < CANVAS_MARGIN:
                adjust_x = CANVAS_MARGIN - slot_bounds[0]
            # Adjust position if outside right boundary
            elif slot_bounds[2] > canvas_width - CANVAS_MARGIN:
                adjust_x = (canvas_width - CANVAS_MARGIN) - slot_bounds[2]
                
            # Adjust position if outside top boundary
            if slot_bounds[1] < CANVAS_MARGIN:
                adjust_y = CANVAS_MARGIN - slot_bounds[1]
            # Adjust position if outside bottom boundary
            elif slot_bounds[3] > canvas_height - CANVAS_MARGIN:
                adjust_y = (canvas_height - CANVAS_MARGIN) - slot_bounds[3]
                
            # Apply adjustments if needed
            if adjust_x != 0 or adjust_y != 0:
                new_slots.append(translate(slot, adjust_x, adjust_y))
            else:
                new_slots.append(slot)
        
        design = Design(new_slots)
    
    return design

def separate_overlapping_pieces(design: Design, min_distance=MIN_SPACING, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Move overlapping or too-close pieces apart to create a valid starting point"""
    modified = False
    slots = design.slots.copy()
    
    # Try up to 50 iterations to separate pieces
    for _ in range(50):
        valid = True
        
        # Check each pair of slots
        for i in range(len(slots)):
            for j in range(i + 1, len(slots)):
                distance = slots[i].distance(slots[j])
                
                # If too close or overlapping
                if distance < min_distance:
                    valid = False
                    
                    # Get centroids
                    c1 = slots[i].centroid
                    c2 = slots[j].centroid
                    
                    # Direction vector between centroids
                    dx = c2.x - c1.x
                    dy = c2.y - c1.y
                    
                    # Handle case where centroids are at the same spot
                    if abs(dx) < 0.001 and abs(dy) < 0.001:
                        dx = 1.0  # Default direction
                        dy = 0.0
                    
                    # Normalize
                    length = (dx**2 + dy**2)**0.5
                    dx /= length
                    dy /= length
                    
                    # Move amount (more if overlapping)
                    move_amount = min_distance - distance + BUFFER_EXTRA
                    
                    # Move both pieces in opposite directions
                    slots[i] = translate(slots[i], -dx * move_amount/2, -dy * move_amount/2)
                    slots[j] = translate(slots[j], dx * move_amount/2, dy * move_amount/2)
                    modified = True
        
        # If all pieces are valid, we're done
        if valid:
            break
    
    # Ensure the design stays within canvas bounds
    return constrain_to_canvas(Design(slots), canvas_width, canvas_height)


def evaluate(design: Design) -> float:
    """Evaluate the design by its bounding box area"""
    return design.bounding_box.area


def apply_random_translation(design: Design, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Move a random piece by a random amount"""
    amount = 15  # Movement amount
    idx = random.randrange(len(design.slots))
    move_x = random.uniform(-amount, amount)
    move_y = random.uniform(-amount, amount)
    
    # Get slot bounds before moving
    slot = design.slots[idx]
    min_x, min_y, max_x, max_y = slot.bounds
    
    # Constrain movement to keep within canvas
    if min_x + move_x < CANVAS_MARGIN:
        move_x = CANVAS_MARGIN - min_x
    elif max_x + move_x > canvas_width - CANVAS_MARGIN:
        move_x = canvas_width - CANVAS_MARGIN - max_x
        
    if min_y + move_y < CANVAS_MARGIN:
        move_y = CANVAS_MARGIN - min_y
    elif max_y + move_y > canvas_height - CANVAS_MARGIN:
        move_y = canvas_height - CANVAS_MARGIN - max_y
    
    translated = translate(slot, move_x, move_y)
    
    result = Design(design.slots[:idx] + [translated] + design.slots[idx + 1:])
    return constrain_to_canvas(result, canvas_width, canvas_height)


def apply_directed_translation(design: Design, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Move a piece toward the centroid of all other pieces"""
    if len(design.slots) < 2:
        return design

    idx = random.randrange(len(design.slots))

    other_slots = design.slots[:idx] + design.slots[idx+1:]
    other_centroids = [slot.centroid for slot in other_slots]
    center_x = sum(c.x for c in other_centroids) / len(other_centroids)
    center_y = sum(c.y for c in other_centroids) / len(other_centroids)
    
    # Constrain center to canvas bounds
    center_x = min(max(center_x, CANVAS_MARGIN), canvas_width - CANVAS_MARGIN)
    center_y = min(max(center_y, CANVAS_MARGIN), canvas_height - CANVAS_MARGIN)

    piece_centroid = design.slots[idx].centroid
    dir_x = center_x - piece_centroid.x
    dir_y = center_y - piece_centroid.y

    # Normalize and scale
    length = (dir_x ** 2 + dir_y ** 2) ** 0.5
    if length > 0.001:  # Avoid division by zero
        factor = random.uniform(0.2, 0.6)  # Move 20-60% of the way toward center
        move_x = dir_x * factor
        move_y = dir_y * factor
        translated = translate(design.slots[idx], move_x, move_y)
        result = Design(design.slots[:idx] + [translated] + design.slots[idx + 1:])
        return constrain_to_canvas(result, canvas_width, canvas_height)

    return design


def align_similar_shapes(design: Design, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Group and align similar shapes together WITHOUT scaling them"""
    if len(design.slots) < 2:
        return design
    
    # Group similar shapes
    shape_groups = group_similar_shapes(design.slots)
    
    # No groups found, return original design
    if not shape_groups:
        return design
        
    new_slots = design.slots.copy()
    
    # Process each group
    for group in shape_groups:
        if len(group) < 2:  # Skip singleton groups
            continue
            
        # Get the first piece in the group as reference
        ref_idx = group[0]
        ref_piece = new_slots[ref_idx]
        ref_bounds = ref_piece.bounds
        ref_width = ref_bounds[2] - ref_bounds[0]
        ref_height = ref_bounds[3] - ref_bounds[1]
        
        # Start position for this group
        start_x = max(ref_bounds[0], CANVAS_MARGIN)
        start_y = max(ref_bounds[1], CANVAS_MARGIN)
        
        # Spacing between pieces (including the piece width)
        spacing_x = ref_width + MIN_SPACING
        
        # Make sure there's enough room
        max_pieces_per_row = (canvas_width - 2*CANVAS_MARGIN) // spacing_x
        if max_pieces_per_row < 1:
            max_pieces_per_row = 1
        
        # For each piece in the group after the first one
        for i, idx in enumerate(group[1:], 1):
            # Get current piece
            piece = new_slots[idx]
            piece_bounds = piece.bounds
            
            # Calculate row and column
            row = i // max_pieces_per_row
            col = i % max_pieces_per_row
            
            # Calculate target position
            target_x = start_x + (col * spacing_x)
            target_y = start_y + (row * (ref_height + MIN_SPACING))
            
            # Calculate move to position next to the reference
            move_x = target_x - piece_bounds[0]
            move_y = target_y - piece_bounds[1]
            
            # Move the piece
            new_slots[idx] = translate(piece, move_x, move_y)
    
    result = Design(new_slots)
    return constrain_to_canvas(result, canvas_width, canvas_height)


def arrange_in_compact_grid(design: Design, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Arrange pieces in a more compact grid layout, preserving their rotation and size"""
    if len(design.slots) < 2:
        return design
    
    # Sort slots by their centroids (top to bottom, left to right)
    slots = design.slots.copy()
    slots_with_centroids = [(i, slot.centroid.x, slot.centroid.y) for i, slot in enumerate(slots)]
    
    # Get actual dimensions of each piece without averaging
    bounds = [slot.bounds for slot in slots]
    widths = [b[2] - b[0] for b in bounds]
    heights = [b[3] - b[1] for b in bounds]
    
    # Sort by y first (row), then by x (column)
    slots_with_centroids.sort(key=lambda item: (item[2], item[1]))
    
    # Create a new layout in grid formation
    new_slots = [None] * len(slots)  # Preallocate list
    start_x, start_y = CANVAS_MARGIN, CANVAS_MARGIN  # Starting position with margin
    
    # Calculate optimal number of columns based on canvas width and the actual widths
    available_width = canvas_width - 2*CANVAS_MARGIN
    max_width = max(widths) if widths else MIN_SPACING
    cols = max(1, min(int(available_width / (max_width + MIN_SPACING)), int(np.sqrt(len(slots)))))
    
    # Keep track of the width and height used in each row and column
    col_widths = [0] * cols
    row_heights = [0] * ((len(slots) + cols - 1) // cols)  # Ceiling division
    
    # First pass: determine widths and heights
    for i, (idx, _, _) in enumerate(slots_with_centroids):
        row = i // cols
        col = i % cols
        
        slot_width = widths[idx]
        slot_height = heights[idx]
        
        col_widths[col] = max(col_widths[col], slot_width)
        row_heights[row] = max(row_heights[row], slot_height)
    
    # Second pass: position pieces using determined dimensions
    for i, (idx, _, _) in enumerate(slots_with_centroids):
        row = i // cols
        col = i % cols
        
        old_slot = slots[idx]
        min_x, min_y, _, _ = old_slot.bounds
        
        # Calculate position based on column widths and row heights
        target_x = start_x
        for c in range(col):
            target_x += col_widths[c] + MIN_SPACING
            
        target_y = start_y
        for r in range(row):
            target_y += row_heights[r] + MIN_SPACING
        
        # Calculate translation to new position
        offset_x = target_x - min_x
        offset_y = target_y - min_y
        
        # Translate to new position
        new_slots[idx] = translate(old_slot, offset_x, offset_y)
    
    result = Design(new_slots)
    return constrain_to_canvas(result, canvas_width, canvas_height)


def apply_compact_arrangement(design: Design, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Try to move all pieces closer to the center to create a more compact arrangement"""
    if len(design.slots) < 2:
        return design
    
    # Find the center of all pieces (constrained to canvas)
    all_centroids = [slot.centroid for slot in design.slots]
    center_x = sum(c.x for c in all_centroids) / len(all_centroids)
    center_y = sum(c.y for c in all_centroids) / len(all_centroids)
    
    # Ensure center is within canvas
    center_x = min(max(center_x, CANVAS_MARGIN), canvas_width - CANVAS_MARGIN)
    center_y = min(max(center_y, CANVAS_MARGIN), canvas_height - CANVAS_MARGIN)
    
    # Create a new list of slots with each one moved slightly toward center
    new_slots = []
    for slot in design.slots:
        c = slot.centroid
        dir_x = center_x - c.x
        dir_y = center_y - c.y
        
        # Normalize and scale
        length = (dir_x ** 2 + dir_y ** 2) ** 0.5
        if length > 0.001:  # Avoid division by zero
            # Move only a small percentage toward center for more control
            factor = random.uniform(0.05, 0.15)  # 5-15% movement
            move_x = dir_x * factor
            move_y = dir_y * factor
            new_slots.append(translate(slot, move_x, move_y))
        else:
            new_slots.append(slot)
    
    result = Design(new_slots)
    return constrain_to_canvas(result, canvas_width, canvas_height)


def apply_full_rotation(design: Design, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Rotate a piece by 90, 180, or 270 degrees"""
    idx = random.randrange(len(design.slots))
    angle = random.choice([np.pi / 2, np.pi, 3 * np.pi / 2])  # 90, 180, or 270 degrees
    rotated = rotate(design.slots[idx], angle, origin='centroid', use_radians=True)
    
    result = Design(design.slots[:idx] + [rotated] + design.slots[idx + 1:])
    return constrain_to_canvas(result, canvas_width, canvas_height)


def apply_random_rotation(design: Design, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Rotate a piece by a small random angle"""
    amount = 1.5
    idx = random.randrange(len(design.slots))
    angle = random.uniform(-amount, amount)
    rotated = rotate(design.slots[idx], angle, origin='centroid', use_radians=True)
    
    result = Design(design.slots[:idx] + [rotated] + design.slots[idx + 1:])
    return constrain_to_canvas(result, canvas_width, canvas_height)


def apply_random_action(design: Design, phase="explore", allow_rotation=True, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Apply a random transformation to the design based on the current phase"""
    # Handle very large or outlier pieces by reorganizing
    if random.random() < 0.05:  # 5% chance to do a full reorganization
        return arrange_in_compact_grid(design, canvas_width, canvas_height)
        
    if not allow_rotation:
        # If rotation is not allowed, only use translation actions
        r = random.random()
        if r < 0.4:
            return apply_random_translation(design, canvas_width, canvas_height)
        elif r < 0.7:
            return apply_directed_translation(design, canvas_width, canvas_height)
        elif r < 0.9:
            return apply_compact_arrangement(design, canvas_width, canvas_height)
        else:
            return align_similar_shapes(design, canvas_width, canvas_height)
    
    # Default behavior with rotation allowed
    if phase == "explore":
        # During exploration, try more dramatic moves
        r = random.random()
        if r < 0.3:
            return apply_random_translation(design, canvas_width, canvas_height)
        elif r < 0.6:
            return apply_directed_translation(design, canvas_width, canvas_height)
        elif r < 0.7:
            return apply_compact_arrangement(design, canvas_width, canvas_height)
        elif r < 0.85:
            return apply_random_rotation(design, canvas_width, canvas_height)
        else:
            return apply_full_rotation(design, canvas_width, canvas_height)
    else:
        # phase == "refine"
        # During refinement, make smaller adjustments
        r = random.random()
        if r < 0.6:
            amount_save = 1.5  # Smaller movements for refinement
            idx = random.randrange(len(design.slots))
            move_x = random.uniform(-amount_save, amount_save)
            move_y = random.uniform(-amount_save, amount_save)
            
            # Get slot bounds before moving
            slot = design.slots[idx]
            min_x, min_y, max_x, max_y = slot.bounds
            
            # Constrain movement to keep within canvas
            if min_x + move_x < CANVAS_MARGIN:
                move_x = CANVAS_MARGIN - min_x
            elif max_x + move_x > canvas_width - CANVAS_MARGIN:
                move_x = canvas_width - CANVAS_MARGIN - max_x
                
            if min_y + move_y < CANVAS_MARGIN:
                move_y = CANVAS_MARGIN - min_y
            elif max_y + move_y > canvas_height - CANVAS_MARGIN:
                move_y = canvas_height - CANVAS_MARGIN - max_y
                
            translated = translate(slot, move_x, move_y)
            result = Design(design.slots[:idx] + [translated] + design.slots[idx + 1:])
            return constrain_to_canvas(result, canvas_width, canvas_height)
        elif r < 0.8:
            return apply_directed_translation(design, canvas_width, canvas_height)
        else:
            if allow_rotation:
                amount_save = 0.5
                idx = random.randrange(len(design.slots))
                angle = random.uniform(-amount_save, amount_save)
                rotated = rotate(design.slots[idx], angle, origin='centroid', use_radians=True)
                result = Design(design.slots[:idx] + [rotated] + design.slots[idx + 1:])
                return constrain_to_canvas(result, canvas_width, canvas_height)
            else:
                return apply_directed_translation(design, canvas_width, canvas_height)


def fix_isolated_piece(design: Design, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Fix any piece that's positioned far away from the rest"""
    if len(design.slots) < 2:
        return design
        
    slots = design.slots.copy()
    
    # Calculate average position of all pieces
    centroids = [slot.centroid for slot in slots]
    avg_x = sum(c.x for c in centroids) / len(centroids)
    avg_y = sum(c.y for c in centroids) / len(centroids)
    
    # Ensure center is within canvas
    avg_x = min(max(avg_x, CANVAS_MARGIN), canvas_width - CANVAS_MARGIN)
    avg_y = min(max(avg_y, CANVAS_MARGIN), canvas_height - CANVAS_MARGIN)
    
    # Find any outliers (pieces far from the average position)
    max_distance = 0
    outlier_idx = -1
    
    for i, slot in enumerate(slots):
        c = slot.centroid
        distance = ((c.x - avg_x)**2 + (c.y - avg_y)**2)**0.5
        
        # Keep track of the piece furthest from center
        if distance > max_distance:
            max_distance = distance
            outlier_idx = i
    
    # If we found a significant outlier, move it closer to the group
    if max_distance > 200 and outlier_idx >= 0:  # Threshold for "too far"
        # Get the outlier piece
        outlier = slots[outlier_idx]
        c = outlier.centroid
        
        # Calculate movement vector toward center
        dir_x = avg_x - c.x
        dir_y = avg_y - c.y
        
        # Move the piece 90% of the way to the average position
        slots[outlier_idx] = translate(outlier, dir_x * 0.9, dir_y * 0.9)
        
        result = Design(slots)
        return constrain_to_canvas(result, canvas_width, canvas_height)
    
    return design


def optimize(initial_design: Design, iterations=10000, alpha=0.99, allow_rotation=True, canvas_width=CANVAS_WIDTH, canvas_height=CANVAS_HEIGHT) -> Design:
    """Optimize the design using simulated annealing, preserving original shapes"""
    # Make a clean copy of the initial design
    design = Design([slot for slot in initial_design.slots])
    
    # Store original shapes to verify no scaling occurs
    original_areas = {i: slot.area for i, slot in enumerate(design.slots)}
    
    # Ensure design is within canvas bounds to start with
    design = constrain_to_canvas(design, canvas_width, canvas_height)
    
    # Verify no scaling occurred during initial constraint
    for i, slot in enumerate(design.slots):
        current_area = slot.area
        # If areas differ significantly, restore original shape
        if abs(current_area - original_areas[i]) / original_areas[i] > 0.01:  # 1% tolerance
            print(f"Warning: Initial constrain changed slot {i} shape. Restoring.")
            design = initial_design  # Use the original design as fallback
            break
    
    # Check for outlier pieces and fix them first
    design = fix_isolated_piece(design, canvas_width, canvas_height)
    
    # Apply different initial arrangements based on rotation preference
    if len(design.slots) > 3:
        if allow_rotation:
            # With rotation, grid layout is more effective
            design = arrange_in_compact_grid(design, canvas_width, canvas_height)
        else:
            # Without rotation, try to align similar shapes first
            design = align_similar_shapes(design, canvas_width, canvas_height)
            # Then arrange in a grid if needed
            if not design.is_valid:
                design = arrange_in_compact_grid(design, canvas_width, canvas_height)
    
    # If design is not valid, separate pieces
    if not design.is_valid:
        design = separate_overlapping_pieces(design, MIN_SPACING, canvas_width, canvas_height)
    
    best_design = design
    best_score = evaluate(best_design)

    explore_phase = int(iterations * 0.7)  # 70% exploration, 30% refinement

    t = 1.0  # Starting temperature
    no_improvement_count = 0
    max_no_improvement = iterations * 0.3  # Allow 30% of iterations without improvement
    
    # Verification function to ensure shapes don't change
    def verify_shapes(design, original_areas):
        """Verify that no shapes have been scaled"""
        for i, slot in enumerate(design.slots):
            current_area = slot.area
            # If areas differ significantly, return False
            if abs(current_area - original_areas[i]) / original_areas[i] > 0.01:  # 1% tolerance
                return False
        return True
    
    for i in range(iterations):
        if no_improvement_count > max_no_improvement:
            print("Optimization stopped early due to no improvement")
            break
            
        phase = "explore" if i < explore_phase else "refine"

        # Create a new design by applying a random action
        design_new = apply_random_action(design, phase, allow_rotation, canvas_width, canvas_height)
        
        # Double-check the design is within canvas bounds
        design_new = constrain_to_canvas(design_new, canvas_width, canvas_height)
        
        # IMPORTANT: Verify no scaling has occurred
        if not verify_shapes(design_new, original_areas):
            continue  # Skip this iteration if shapes have changed
        
        # Check if the new design is valid and evaluate it
        valid_new = design_new.is_valid
        
        if valid_new:
            score_old = evaluate(design)
            score_new = evaluate(design_new)

            # Update best design if this is better
            if score_new < best_score:
                best_design = design_new
                best_score = score_new
                no_improvement_count = 0  # Reset counter
            else:
                no_improvement_count += 1  # Increment counter

            # Simulated annealing acceptance criterion
            if score_new < score_old or random.random() < np.exp(-(score_new - score_old) / t):
                design = design_new
        else:
            # Try to fix invalid design
            fixed_design = separate_overlapping_pieces(design_new, MIN_SPACING, canvas_width, canvas_height)
            
            # Verify fixed design maintains original shapes
            if fixed_design.is_valid and verify_shapes(fixed_design, original_areas):
                score_old = evaluate(design)
                score_new = evaluate(fixed_design)
                
                # Accept the fixed design if it's better
                if score_new < score_old or random.random() < np.exp(-(score_new - score_old) / (t * 2)):
                    design = fixed_design
                    if score_new < best_score:
                        best_design = fixed_design
                        best_score = score_new
                        no_improvement_count = 0  # Reset counter
            else:
                no_improvement_count += 1  # Increment counter
                
        # Cool down the temperature
        t *= alpha
    
    # Final check to ensure our best design is valid and within canvas
    if not best_design.is_valid:
        best_design = separate_overlapping_pieces(best_design, MIN_SPACING, canvas_width, canvas_height)
    
    # Final constraint check
    best_design = constrain_to_canvas(best_design, canvas_width, canvas_height)
    
    # If there's a piece far away from others, bring it closer
    best_design = fix_isolated_piece(best_design, canvas_width, canvas_height)
    
    # Final verification that shapes haven't changed
    if not verify_shapes(best_design, original_areas):
        print("Warning: Final design has scaled pieces. Restoring original design.")
        return initial_design
    
    return best_design