#!/bin/python3

import copy
import os
import sys
import time

def can_occupy_space(grid, row, col):
    grid_height = len(grid)
    grid_width = len(grid[0])
    if row < 0 or grid_height <= row or col < 0 or grid_width <= col:
        return False
    if grid[row][col] == '#':
        return False
    return True


def can_place_tile(grid, tile):
    blocked_points = [p for p in tile if not can_occupy_space(grid, p[0], p[1])]
    return not blocked_points



def generate_placeable_tiles_for_point(grid, row, col):
    all_tiles = generate_tiles_for_point(grid, row, col)
    return [t for t in all_tiles if can_place_tile(grid, t)]

def generate_placeable_tiles_for_grid(grid):
    placeable_tiles = []
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            placeable_tiles = placeable_tiles + \
                generate_placeable_tiles_for_point(grid, i, j)
    return placeable_tiles

def are_tiles_overlapping(tile1, tile2):
    # Could make this more efficient, but tile size is fixed at 4
    for point1 in tile1:
        for point2 in tile2:
            if point1 == point2:
                return True
    return False

# Modifies grid
def get_contiguous_section(grid, starting_point):
    row = starting_point[0]
    col = starting_point[1]

    if row < 0 or row > len(grid) or col < 0 or col > len(grid[0]):
        raise Exception('Starting point outside bounds of grid')
    if grid[row][col] == 1:
        raise Exception('Starting point already occupied')

    grid[row][col] = 1
    result = [starting_point]
    if 0 <= row - 1 and grid[row - 1][col] == 0:
        result = result + get_contiguous_section(grid, (row - 1, col))
    if row + 1 < len(grid) and grid[row + 1][col] == 0:
        result = result + get_contiguous_section(grid, (row + 1, col))
    if 0 <= col - 1 and grid[row][col - 1] == 0:
        result = result + get_contiguous_section(grid, (row, col - 1))
    if col + 1 < len(grid[0]) and grid[row][col + 1] == 0:
        result = result + get_contiguous_section(grid, (row, col + 1))

    return result

def find_first_free_space(grid):
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == 0:
                return (i, j)
    return None

# Modifies grid
def get_contiguous_sections(grid):
    contiguous_sections = []

    free_space = find_first_free_space(grid)
    while free_space:
        contiguous_sections.append(get_contiguous_section(grid, free_space))
        free_space = find_first_free_space(grid)

    return contiguous_sections

# Modifies grid
def has_invalid_contiguous_sections(grid):
    contiguous_sections = get_contiguous_sections(grid)

    for contiguous_section in contiguous_sections:
        if len(contiguous_section) % TILE_LENGTH != 0:
            return True

        same_row = True
        same_col = True
        for point in contiguous_section[1:]:
            if point[0] != contiguous_section[0][0]:
                same_row = False
            if point[1] != contiguous_section[0][1]:
                same_col = False
        if same_row or same_col:
            return True

    return False

TILE_LENGTH = 4
def can_fill_all_sections_after_placing_tile(grid, tile_set, tile):
    grid_after_placing_tiles = copy.deepcopy(grid)
    merged_tile_set = tile_set + [tile]
    for tile in merged_tile_set:
        for point in tile:
            grid_after_placing_tiles[point[0]][point[1]] = 1

    return not has_invalid_contiguous_sections(grid_after_placing_tiles)

def can_add_tile_to_set(grid, tile_set, tile):
    for points in tile:
        if grid[points[0]][points[1]] == 1:
            return False

    for tile_from_set in tile_set:
        if are_tiles_overlapping(tile_from_set, tile):
            return False

    return can_fill_all_sections_after_placing_tile(grid, tile_set, tile)

def get_free_space_count_for_grid(grid):
    return len([1 for row in grid for entry in row if entry == 0])

def print_solution(solution_set, height, width):
    grid = [['-' for x in range(width)] for y in range(height)]
    symbol = chr(ord('A') - 1)
    for tile in solution_set:
        symbol = chr(ord(symbol) + 1)
        for point in tile:
            grid[point[0]][point[1]] = symbol
    for row in grid:
        print(' '.join(row))
        print('')
    print('\n----------\n')

shape_cache = {}
def count_solutions(grid, solution_set, remaining_tiles, target_length):
    grid_after_placing_tiles = copy.deepcopy(grid)
    contiguous_sections = get_contiguous_sections(grid)
    for tile in solution_set:
        for point in tile:
            grid_after_placing_tiles[point[0]][point[1]] = 1
    flattened = [str(col) for row in grid_after_placing_tiles for col in row]
    shape_cache_key = ''.join(flattened)

    global shape_cache
    if shape_cache_key in shape_cache:
        return shape_cache[shape_cache_key]

    if len(solution_set) == target_length:
        # print_solution(solution_set, len(grid), len(grid[0]))
        return 1

    solutions_count = 0
    for i in range(len(remaining_tiles)):
        next_tile = remaining_tiles[i]
        if can_add_tile_to_set(grid, solution_set, next_tile):
            solutions_count += count_solutions(
                grid,
                solution_set + [next_tile],
                remaining_tiles[i:],
                target_length
            )
        # else:
        #     print_solution(solution_set + [next_tile], len(grid), len(grid[0]))

    # Once we've seen a particular shape, cache the count of solutions for it
    # print('{} : {}'.format(shape_cache_key, solutions_count))
    shape_cache[shape_cache_key] = solutions_count

    return solutions_count





def generate_tiles_for_point(grid, row, col):
    # In generating these, the target point, (row, col), is always the
    # elbow.
    return [
        # "Sideways" L's
        frozenset((row + 1, col), (row, col), (row, col + 1), (row, col + 2)),
        frozenset((row - 1, col), (row, col), (row, col - 1), (row, col - 2)),
        frozenset((row - 1, col), (row, col), (row, col + 1), (row, col + 2)),
        frozenset((row + 1, col), (row, col), (row, col - 1), (row, col - 2)),
        # "Vertical" L's
        frozenset((row, col + 1), (row, col), (row - 1, col), (row - 2, col)),
        frozenset((row, col - 1), (row, col), (row + 1, col), (row + 2, col)),
        frozenset((row, col + 1), (row, col), (row + 1, col), (row + 2, col)),
        frozenset((row, col - 1), (row, col), (row - 1, col), (row - 2, col))
    ]

def copy_grid_and_fill_points(grid, points):
    new_grid = copy.deepcopy(grid)
    for point in points:
        new_grid[point[0]][point[1]] = 1
    return new_grid

def get_incremented_point(point, max_height, max_width):
    m = (point[1] + 1) % max_width
    n = point[0] if m != 0 else point[0] + 1
    return (n, m) if n < max_height else None

def get_next_free_point(grid, previous_point):
    max_height = len(grid)
    max_width = len(grid[0])
    next_point = get_incremented_point(previous_point or (0, -1), max_height, max_width)
    while next_point:
        if grid[next_point[0]][next_point[1]] == 0:
            return next_point
        next_point = get_incremented_point(next_point, max_height, max_width)

    return None

cache = {}
def count_solutions(grid):
    global cache
    key = ?
    if key in cache:
        return cache[key]

    free_point = get_next_free_point(grid, None)
    while free_point:
        free_point = get_next_free_point(grid, free_point)

    cache[key] = ?
    return cache[key]


def brick_tiling(text_grid):
    grid = []
    for i in range(len(text_grid)):
        grid.append([])
        for j in range(len(text_grid[0])):
            grid[i].append(0 if text_grid[i][j] == '.' else 1)

    perf_beg = time.time()
    placeable_tiles = generate_placeable_tiles_for_grid(grid)
    required_tile_count = get_free_space_count_for_grid(grid) / TILE_LENGTH
    count = count_solutions(grid, [], placeable_tiles, required_tile_count)
    print(count)
    perf_end = time.time()
    print('time: {}'.format(perf_end - perf_beg))

    return 0

# max height = 20
# max width = 8
test_cases = [
    [
        '........'
    ],
    [
        '........',
        '........'
    ],
    [
        '........',
        '........',
        '........'
    ],
    # [
    #     '........',
    #     '........',
    #     '........',
    #     '........'
    # ],
    # [
    #     '....',
    #     '....',
    #     '....',
    #     '....',
    #     '....',
    #     '....',
    #     '....',
    #     '....'
    # ]
]

for test_case in test_cases:
    brick_tiling(test_case)


# if __name__ == '__main__':
#     fptr = open(os.environ['OUTPUT_PATH'], 'w')

#     t = int(input())

#     for t_itr in range(t):
#         nm = input().split()

#         n = int(nm[0])

#         m = int(nm[1])

#         grid = []

#         for _ in range(n):
#             grid_item = input()
#             grid.append(grid_item)

#         result = brick_tiling(grid)

#         fptr.write(str(result) + '\n')

#     fptr.close()
