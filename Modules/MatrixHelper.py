import copy
def rotateMatrix(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def flip_horizontal(matrix):
    return [row[::-1] for row in matrix]