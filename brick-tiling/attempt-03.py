#!/bin/python3

# Test: Cache grid, check if subspace is solvable

import os
import sys
import time

DEBUG = False

def deep_copy_grid(grid):
    return [[val for val in row] for row in grid]

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

def generate_tiles_for_point(grid, row, col):
    # In generating these, the target point, (row, col), is always the
    # elbow.
    return [
        # "Sideways" L's
        ((row + 1, col), (row, col), (row, col + 1), (row, col + 2)),
        ((row - 1, col), (row, col), (row, col - 1), (row, col - 2)),
        ((row - 1, col), (row, col), (row, col + 1), (row, col + 2)),
        ((row + 1, col), (row, col), (row, col - 1), (row, col - 2)),
        # "Vertical" L's
        ((row, col + 1), (row, col), (row - 1, col), (row - 2, col)),
        ((row, col - 1), (row, col), (row + 1, col), (row + 2, col)),
        ((row, col + 1), (row, col), (row + 1, col), (row + 2, col)),
        ((row, col - 1), (row, col), (row - 1, col), (row - 2, col))
    ]

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

def el_find_first_free_space(grid, starting_point):
    for i in range(starting_point[0], len(grid)):
        initial_j = starting_point[1] if i == starting_point[0] else 0
        for j in range(initial_j, len(grid[i])):
            if grid[i][j] == 0:
                return (i, j)
    return None

def can_place_tile_on_grid(grid, tile):
    for point in tile:
        if grid[point[0]][point[1]] == 1:
            return False
    return True

def create_copy_of_grid_with_placed_tile(grid, tile):
    new_grid = deep_copy_grid(grid)
    for point in tile:
        if grid[point[0]][point[1]] == 1:
            raise Exception('Invalid placement')
        new_grid[point[0]][point[1]] = 1
    return new_grid

def add_tile_to_grid(grid, tile):
    for point in tile:
        if grid[point[0]][point[1]] == 1:
            raise Exception('Cannot add')
        grid[point[0]][point[1]] = 1

def remove_tile_from_grid(grid, tile):
    for point in tile:
        if grid[point[0]][point[1]] == 0:
            raise Exception('Cannot remove')
        grid[point[0]][point[1]] = 0

contig_section_cache = {}
def add_contig_section_to_cache(contiguous_section, can_solve):
    max_n = max([point[0] for point in contiguous_section])

    def invert(cs):
        return [(max_n - point[0], point[1]) for point in cs]

    def rotate_90(cs):
        return [(point[1], max_n - point[0]) for point in cs]

    # for _ in range(4):
    #     key = str(contiguous_section)
    #     contig_section_cache[key] = can_solve
    #     contiguous_section = rotate_90(contiguous_section)

    key = str(contiguous_section)
    contig_section_cache[key] = can_solve

    inverted = invert(contiguous_section)
    key = str(inverted)
    contig_section_cache[key] = can_solve

    # for _ in range(4):
    #     key = str(inverted)
    #     contig_section_cache[key] = can_solve
    #     contiguous_section = rotate_90(inverted)

def get_cached_contig_section_result(contiguous_section):
    key = str(contiguous_section)
    return contig_section_cache[key] if key in contig_section_cache else None

def noramlize_contiguous_section(contiguous_section):
    contiguous_section.sort()
    min_n = contiguous_section[0][0]
    min_m = min([point[1] for point in contiguous_section])
    return [(point[0] - min_n, point[1] - min_m) for point in contiguous_section]

contig_section_cache_hits = 0
def can_solve_contiguous_section(contiguous_section):
    global contig_section_cache_hits
    TILE_SIZE = 4

    normalized_cs = noramlize_contiguous_section(contiguous_section)

    cached_result = get_cached_contig_section_result(contiguous_section)
    if cached_result is not None:
        contig_section_cache_hits += 1
        return cached_result

    if len(normalized_cs) % TILE_SIZE != 0:
        add_contig_section_to_cache(contiguous_section, False)
        return False

    shape_test_grid = []
    for i in range(20 + 2):
        shape_test_grid.append([1] * (8 + 2))
    for point in normalized_cs:
        shape_test_grid[point[0] + 1][point[1] + 1] = 0

    # Check for 3 points in a row without a free vertical space (violates L shape)
    for row in range(1, len(shape_test_grid) - 1):
        line_count = 0
        for col in range(1, len(shape_test_grid[0]) - 1):
            point_free = shape_test_grid[row][col] == 0
            above_occupied = shape_test_grid[row - 1][col] == 1
            below_occupied = shape_test_grid[row + 1][col] == 1
            if point_free and above_occupied and below_occupied:
                line_count += 1
            else:
                line_count = 0
            if line_count >= 3:
                add_contig_section_to_cache(contiguous_section, False)
                return False

    # Check for 3 points in a col without a free horizontal space (violates L shape)
    for col in range(1, len(shape_test_grid[0]) - 1):
        line_count = 0
        for row in range(1, len(shape_test_grid) - 1):
            point_free = shape_test_grid[row][col] == 0
            left_occupied = shape_test_grid[row][col - 1] == 1
            right_occupied = shape_test_grid[row][col + 1] == 1
            if point_free and left_occupied and right_occupied:
                line_count += 1
            else:
                line_count = 0
            if line_count >= 3:
                add_contig_section_to_cache(contiguous_section, False)
                return False

    # three_in_horz_line = True
    # three_in_vert_line = True
    # for point in contiguous_section[1:]:
    #     if point[0] != contiguous_section[0][0]:
    #         is_horz_line = False
    #     if point[1] != contiguous_section[0][1]:
    #         is_vert_line = False
    # if is_horz_line or is_vert_line:
    #     return False

    # TODO: Is square?
    # Could keep map of no-solution shapes?

    add_contig_section_to_cache(contiguous_section, True)
    return True

perf_deep_copy = []
perf_find_first_free_space = []
perf_get_contiguous_section = []
perf_can_solve_contiguous_section = []
def can_solve_grid(grid):
    perf_start = time.time()
    grid_copy = deep_copy_grid(grid)
    perf_deep_copy.append(time.time() - perf_start)

    perf_start = time.time()
    free_space = el_find_first_free_space(grid_copy, (0, 0))
    perf_find_first_free_space.append(time.time() - perf_start)
    while free_space:
        perf_start = time.time()
        contiguous_section = get_contiguous_section(grid_copy, free_space)
        perf_get_contiguous_section.append(time.time() - perf_start)

        perf_start = time.time()
        can_solve = can_solve_contiguous_section(contiguous_section)
        perf_can_solve_contiguous_section.append(time.time() - perf_start)
        if not can_solve:
            return False

        perf_start = time.time()
        free_space = el_find_first_free_space(grid_copy, free_space)
        perf_find_first_free_space.append(time.time() - perf_start)

    return True

def is_grid_filled(grid):
    for row in grid:
        for col in row:
            if col == 0:
                return False
    return True

def print_indent(text, indent):
    if DEBUG:
        print('{}{}'.format(' ' * (2 * indent), text))

def print_grid(grid, indent):
    for row in grid:
        print_indent(''.join([str(val) for val in row]), indent)

# Optimization: For each grid, if we already know the number of solutions for it's contiguous sections, use those values

grid_solution_cache = {}
def add_grid_to_cache(grid, solutions_count):
    grid_solution_cache[str(grid)] = solutions_count

def add_non_solvable_grid_to_cache(grid):
    def flip_horz(g):
        for row in g:
            row.reverse()

    # Normal
    add_grid_to_cache(grid, 0)

    # Inverted
    grid.reverse()
    add_grid_to_cache(grid, 0)

    # Inverted and flipped
    flip_horz(grid)
    add_grid_to_cache(grid, 0)

    # Flipped
    grid.reverse()
    add_grid_to_cache(grid, 0)

    # Back to normal - leave it how it arrived
    flip_horz(grid)

def get_cached_grid_solution_count(grid):
    key = str(grid)
    return grid_solution_cache[key] if key in grid_solution_cache else None

# perf_can_solve_grid = []
# perf_is_grid_solved = []
el_solutions_evaluated = 0
cache_hits = 0
def count_solutions_for_grid(grid, remaining_tiles, depth):
    global el_solutions_evaluated
    global cache_hits

    el_solutions_evaluated += 1
    print_indent('Exploring grid:', depth)
    print_grid(grid, depth)

    if is_grid_filled(grid):
        return 1

    solutions_count = 0
    remaining_tiles = [tile for tile in remaining_tiles if can_place_tile_on_grid(grid, tile)]
    for i in range(len(remaining_tiles)):
        tile = remaining_tiles[i]

        add_tile_to_grid(grid, tile)

        cached_solution_count = get_cached_grid_solution_count(grid)
        if cached_solution_count is not None:
            cache_hits += 1
            solutions_count += cached_solution_count
            print_indent('Cache hit, adding {} for:'.format(cached_solution_count), depth)
            print_grid(grid, depth + 1)
        elif can_solve_grid(grid):
            solution_count_for_child = count_solutions_for_grid(grid, remaining_tiles[i:], depth + 1)
            solutions_count += solution_count_for_child
            print_indent('Explored child, adding {}'.format(solution_count_for_child), depth)
        else:
            add_non_solvable_grid_to_cache(grid)
            print_indent('No solution for child, so skipping:', depth)
            print_grid(grid, depth + 1)

        remove_tile_from_grid(grid, tile)

    print_indent('Total solutions: {}'.format(solutions_count), depth)
    add_grid_to_cache(grid, solutions_count)
    return solutions_count

def print_stat(title, indent, measurements):
    s = sum(measurements)
    l = len(measurements)
    print('{}{}: {} / {} = {}'.format(' ' * indent, title, s, l, s / l))

def brick_tiling(text_grid_representation):
    grid = []
    for i in range(len(text_grid_representation)):
        grid.append([])
        for j in range(len(text_grid_representation[0])):
            grid[i].append(0 if text_grid_representation[i][j] == '.' else 1)

    placeable_tiles = generate_placeable_tiles_for_grid(grid)

    perf_start = time.time()
    count = count_solutions_for_grid(grid, placeable_tiles, 0)
    perf_end = time.time()

    print('{} / {}'.format(count, el_solutions_evaluated))
    # print('cache hits: {}'.format(cache_hits))
    # print('cache size: {}'.format(len(grid_solution_cache)))
    print('total time: {}'.format(perf_end - perf_start))
    # # print_stat('perf_can_solve_grid', 0, perf_can_solve_grid)
    # print_stat('perf_deep_copy', 2, perf_deep_copy)
    # print_stat('perf_find_first_free_space', 2, perf_find_first_free_space)
    # print_stat('perf_get_contiguous_section', 2, perf_get_contiguous_section)
    # print_stat('perf_can_solve_contiguous_section', 2, perf_can_solve_contiguous_section)
    # # print_stat('perf_is_grid_solved', 0, perf_is_grid_solved)
    # print('contig section cache hits: {}'.format(contig_section_cache_hits))
    # print('contig section cache size: {}'.format(len(contig_section_cache)))

    return 0

height = 12
width = 8

row_data = '.' * width
# test_data = [row_data for i in range(height)]
# test_data = [
# '........',
# '........'
# ] # 4
# test_data = [
# '.....',
# '.....',
# '..#..',
# '.....',
# '.#...',
# '.....'
# ] # 40
# test_data = [
# '###..',
# '.....',
# '.....'
# ] # 3
# test_data = [
# '..#',
# '...',
# '...',
# '...',
# '...',
# '..#'
# ] # 2

test_cases = []
# test_cases.append([
#     '....',
#     '....'
# ])
# test_cases.append([
#     '###.#...',
#     '#...###.'
# ])
# test_cases.append([
#     '###....#',
#     '#....###'
# ])
# test_cases.append([
#     '###.....',
#     '#.......'
# ])
# test_cases.append([
#     '........',
#     '........'
# ])
# test_cases.append([
#     '....',
#     '....',
#     '....',
#     '....'
# ])
# test_cases.append([
#     '......',
#     '......'
# ])
# test_cases.append([
#     '######',
#     '######'
# ])
# test_cases.append([
#     '..',
#     '..',
#     '..',
#     '..',
#     '..',
#     '..',
#     '..',
#     '..'
# ])
# test_cases.append([
#     '...',
#     '.##'
# ])
# test_cases.append([
#     '....',
#     '....',
#     '..##',
#     '.###',
#     '.###'
# ])
# test_cases.append([
#     '....',
#     '....',
#     '..#.',
#     '.##.',
#     '.#..'
# ])
# test_cases.append([
#     '....',
#     '....',
#     '..#.',
#     '..#.',
#     '....',
#     '#..#',
# ])
test_cases.append([
    '....',
    '....',
    '....',
    '....',
    '....',
    '....',
    '....',
    '....'
])
    # [
    #     '........',
    #     '........',
    #     '........',
    #     '........',
    #     '........',
    #     '........',
    #     '........',
    #     '........'
    # ]

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
