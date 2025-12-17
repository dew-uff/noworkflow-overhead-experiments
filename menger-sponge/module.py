from math import floor

def outside_unit_cube(triple):
    x, y, z = triple
    if x < 0 or y < 0 or z < 0:
        return 1
    if x > 1 or y > 1 or z > 1:
        return 1
    return 0

def in_sponge( triple, level ):
    """Determine whether a point lies inside the Menger sponge
    after the number of iterations given by 'level.' """
    x, y, z = triple
    if outside_unit_cube(triple):
        return 0
    if x == 1 or y == 1 or z == 1:
        return 1
    for i in range(level):
        x *= 3
        y *= 3
        z *= 3

        # A point is removed if two of its coordinates
        # lie in middle thirds.
        count = 0
        if int(floor(x)) % 3 == 1:
            count += 1
        if int(floor(y)) % 3 == 1:
            count += 1
        if int(floor(z)) % 3 == 1:
            count += 1
        if count >= 2:
            return 0

    return 1
