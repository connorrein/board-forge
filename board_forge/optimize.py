import random
import numpy as np
from shapely.affinity import translate, rotate
from board_forge.design import Design


def evaluate(design: Design) -> float:
    return design.bounding_box.area


def apply_random_translation(design: Design) -> Design:
    amount = 10  # increased for better optimization
    idx = random.randrange(len(design.slots))
    move_x = random.uniform(-amount, amount)
    move_y = random.uniform(-amount, amount)
    translated = translate(design.slots[idx], move_x, move_y)
    return Design(design.slots[:idx] + [translated] + design.slots[idx + 1:])


def apply_directed_translation(design: Design) -> Design:
    # Move a piece toward the centroid of all pieces
    if len(design.slots) < 2:
        return design

    idx = random.randrange(len(design.slots))

    other_slots = design.slots[:idx] + design.slots[idx+1:]
    other_centroids = [slot.centroid for slot in other_slots]
    center_x = sum(c.x for c in other_centroids) / len(other_centroids)
    center_y = sum(c.y for c in other_centroids) / len(other_centroids)

    piece_centroid = design.slots[idx].centroid
    dir_x = center_x - piece_centroid.x
    dir_y = center_y - piece_centroid.y

    # Normalize and scale
    length = (dir_x ** 2 + dir_y ** 2) ** 0.5
    if length > 0.001:  # Avoid division by zero
        amount = 15
        move_x = dir_x / length * random.uniform(0, amount)
        move_y = dir_y / length * random.uniform(0, amount)
        translated = translate(design.slots[idx], move_x, move_y)
        return Design(design.slots[:idx] + [translated] + design.slots[idx + 1:])

    return design


def apply_full_rotation(design: Design) -> Design:
    idx = random.randrange(len(design.slots))
    angle = random.choice([np.pi / 2, np.pi, 3 * np.pi / 2])  # 90, 180, or 270 degrees
    rotated = rotate(design.slots[idx], angle, origin='centroid', use_radians=True)
    return Design(design.slots[:idx] + [rotated] + design.slots[idx + 1:])


def apply_random_rotation(design: Design) -> Design:
    amount = 1.5
    idx = random.randrange(len(design.slots))
    angle = random.uniform(-amount, amount)
    rotated = rotate(design.slots[idx], angle, origin='centroid', use_radians=True)
    return Design(design.slots[:idx] + [rotated] + design.slots[idx + 1:])


def apply_random_action(design: Design, phase="explore") -> Design:
    if phase == "explore":
        # During exploration, try more dramatic moves
        r = random.random()
        if r < 0.3:
            return apply_random_translation(design)
        elif r < 0.6:
            return apply_directed_translation(design)
        elif r < 0.8:
            return apply_random_rotation(design)
        else:
            return apply_full_rotation(design)
    else:
        # phase == "refine"
        # During refinement, make smaller adjustments
        r = random.random()
        if r < 0.7:
            amount_save = 1
            idx = random.randrange(len(design.slots))
            move_x = random.uniform(-amount_save, amount_save)
            move_y = random.uniform(-amount_save, amount_save)
            translated = translate(design.slots[idx], move_x, move_y)
            return Design(design.slots[:idx] + [translated] + design.slots[idx + 1:])
        else:
            amount_save = 0.5
            idx = random.randrange(len(design.slots))
            angle = random.uniform(-amount_save, amount_save)
            rotated = rotate(design.slots[idx], angle, origin='centroid', use_radians=True)
            return Design(design.slots[:idx] + [rotated] + design.slots[idx + 1:])


def optimize(initial_design: Design, iterations=10000, alpha=0.99) -> Design:
    design = initial_design

    best_design = initial_design
    best_score = evaluate(best_design)

    explore_phase = int(iterations * 0.7)  # 70% exploration, 30% refinement

    t = 1
    for i in range(iterations):
        phase = "explore" if i < explore_phase else "refine"

        design_new = apply_random_action(design, phase)
        if design_new.is_valid:
            score_old = evaluate(design)
            score_new = evaluate(design_new)

            if score_new < best_score:
                best_design = design_new
                best_score = score_new

            if score_new < score_old:
                design = design_new
            elif np.exp(-(score_new - score_old) / t) < random.random():
                design = design_new

        t *= alpha

    return best_design
