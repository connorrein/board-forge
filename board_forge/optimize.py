import random
import numpy as np
from shapely.affinity import translate, rotate
from board_forge.design import Design


def evaluate(design: Design) -> float:
    return design.bounding_box.area


def apply_random_translation(design: Design) -> Design:
    amount = 1
    idx = random.randrange(len(design.slots))
    move_x = random.uniform(-amount, amount)
    move_y = random.uniform(-amount, amount)
    translated = translate(design.slots[idx], move_x, move_y)
    return Design(design.slots[:idx] + [translated] + design.slots[idx + 1:])


def apply_random_rotation(design: Design) -> Design:
    amount = 0.5
    idx = random.randrange(len(design.slots))
    angle = random.uniform(-amount, amount)
    rotated = rotate(design.slots[idx], angle, origin='centroid', use_radians=True)
    return Design(design.slots[:idx] + [rotated] + design.slots[idx + 1:])


def apply_random_action(design: Design) -> Design:
    if random.random() < 0.5:
        return apply_random_translation(design)
    else:
        return apply_random_rotation(design)


def optimize(initial_design: Design, iterations=10000, alpha=0.99) -> Design:
    design = initial_design

    t = 1
    for _ in range(iterations):
        design_new = apply_random_action(design)
        if design_new.is_valid:
            score_old = evaluate(design)
            score_new = evaluate(design_new)
            if score_new < score_old:
                design = design_new
            elif np.exp(-(score_new - score_old) / t) < random():
                design = design_new
        t *= alpha

    return design
