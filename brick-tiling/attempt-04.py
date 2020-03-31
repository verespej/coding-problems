#!/bin/python3

# Test: Use Grid class

import os
import sys
import time

DEBUG = False

class Grid:
    _grid = None

    def __init__(self, *args, **kwargs):
        grid_to_copy = kwargs.get('grid_to_copy')
        if grid_to_copy:
            if not isinstance(grid_to_copy, Grid):
                raise Exception('grid_to_copy must be an instance of Grid')
            self._grid = [[val for val in row] for row in grid_to_copy._grid]
            return

        row_count = kwargs.get('row_count')
        col_count = kwargs.get('col_count')
        if row_count and col_count:
            self._grid = [[1] * col_count for row in range(row_count)]
            return

        raise Exception('Must specify kwargs')

    def __getitem__(self, row, col):
        return self._grid[row][col]

    @property
    def row_count(self):
        return len(self._grid)

    @property
    def col_count(self):
        return len(self._grid[0])

    def are_all_spaces_occupied(self):
        for row in self._grid:
            if sum(row) > 0:
                return False
        return True

    def flip_horz(self):
        for row in self._grid:
            row.reverse()

    def invert(self):
        self._grid.reverse()

    def is_space_within_grid_bounds(self, row, col):
        return 0 <= row and row < self.row_count and 0 <= col and col < self.col_count

    def is_space_free(self, row, col):
        return self.is_space_within_grid_bounds(row, col) and self._grid[row][col] == 1

    def is_space_occupied(self, row, col):
        return not self.is_space_within_grid_bounds(row, col) or self._grid[row][col] == 0

    def mark_space_free(self, row, col):
        if self.is_space_free(row, col):
            raise Exception('Space is already free')
        self._grid[row][col] = 1

    def mark_spaces_free(self, spaces):
        for point in spaces:
            self.mark_space_free(point[0], point[1])

    def mark_space_occupied(self, row, col):
        if self.is_space_occupied(row, col):
            raise Exception('Space is already occupied')
        self._grid[row][col] = 0

    def mark_spaces_occupied(self, spaces):
        for point in spaces:
            self.mark_space_occupied(point[0], point[1])

    def print_rows(self, *args, **kwargs):
        print_func = kwargs.pop('print_func', print)
        for row in self._grid:
            print_func(''.join([str(val) for val in row]), **kwargs)

    def __str__(self):
        return str(self._grid)

def can_place_tile_on_grid(grid, tile):
    for point in tile:
        if grid.is_space_occupied(point[0], point[1]):
            return False
    return True

def generate_tiles_for_point(row, col):
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
    if grid.is_space_occupied(row, col):
        return []
    all_tiles = generate_tiles_for_point(row, col)
    return [t for t in all_tiles if can_place_tile_on_grid(grid, t)]

def generate_placeable_tiles_for_grid(grid):
    placeable_tiles = []
    for row in range(grid.row_count):
        for col in range(grid.col_count):
            if grid.is_space_free(row, col):
                placeable_tiles = placeable_tiles + \
                    generate_placeable_tiles_for_point(grid, row, col)
    return placeable_tiles

# Modifies grid
def get_contiguous_section(grid, starting_point):
    row = starting_point[0]
    col = starting_point[1]

    if not grid.is_space_within_grid_bounds(row, col):
        raise Exception('Starting point outside bounds of grid')
    if grid.is_space_occupied(row, col):
        raise Exception('Starting point already occupied')

    grid.mark_space_occupied(row, col)
    result = [starting_point]
    if grid.is_space_free(row - 1, col):
        result = result + get_contiguous_section(grid, (row - 1, col))
    if grid.is_space_free(row + 1, col):
        result = result + get_contiguous_section(grid, (row + 1, col))
    if grid.is_space_free(row, col - 1):
        result = result + get_contiguous_section(grid, (row, col - 1))
    if grid.is_space_free(row, col + 1):
        result = result + get_contiguous_section(grid, (row, col + 1))

    return result

def el_find_first_free_space(grid, starting_point):
    for row in range(starting_point[0], grid.row_count):
        initial_col = starting_point[1] if row == starting_point[0] else 0
        for col in range(initial_col, grid.col_count):
            if grid.is_space_free(row, col):
                return (row, col)
    return None

def create_copy_of_grid_with_placed_tile(grid, tile):
    new_grid = Grid(grid)
    new_grid.mark_spaces_occupied(tile)
    return new_grid

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
    grid_copy = Grid(grid_to_copy=grid)
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

def debug_print(text, indent=0):
    if DEBUG:
        print('{}{}'.format(' ' * (2 * indent), text))

# Optimization: For each grid, if we already know the number of solutions for it's contiguous sections, use those values

grid_solution_cache = {}
def add_grid_to_cache(grid, solutions_count):
    grid_solution_cache[str(grid)] = solutions_count

def add_non_solvable_grid_to_cache(grid):
    # Normal
    add_grid_to_cache(grid, 0)

    # Inverted
    grid.invert()
    add_grid_to_cache(grid, 0)

    # Inverted and flipped
    grid.flip_horz()
    add_grid_to_cache(grid, 0)

    # Flipped
    grid.invert()
    add_grid_to_cache(grid, 0)

    # Back to normal - leave it how it arrived
    grid.flip_horz()

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
    debug_print('Exploring grid:', indent=depth)
    grid.print_rows(print_func=debug_print, indent=depth)

    if grid.are_all_spaces_occupied():
        return 1

    solutions_count = 0
    remaining_tiles = [tile for tile in remaining_tiles if can_place_tile_on_grid(grid, tile)]
    for i in range(len(remaining_tiles)):
        tile = remaining_tiles[i]

        grid.mark_spaces_occupied(tile)

        cached_solution_count = get_cached_grid_solution_count(grid)
        if cached_solution_count is not None:
            cache_hits += 1
            solutions_count += cached_solution_count
            debug_print('Cache hit, adding {} for:'.format(cached_solution_count), depth)
            grid.print_rows(print_func=debug_print, indent=depth + 1)
        elif can_solve_grid(grid):
            solution_count_for_child = count_solutions_for_grid(grid, remaining_tiles[i:], depth + 1)
            solutions_count += solution_count_for_child
            debug_print('Explored child, adding {}'.format(solution_count_for_child), depth)
        else:
            add_non_solvable_grid_to_cache(grid)
            debug_print('No solution for child, so skipping:', depth)
            grid.print_rows(print_func=debug_print, indent=depth + 1)

        grid.mark_spaces_free(tile)

    debug_print('Total solutions: {}'.format(solutions_count), depth)
    add_grid_to_cache(grid, solutions_count)
    return solutions_count

def print_stat(title, indent, measurements):
    s = sum(measurements)
    l = len(measurements)
    print('{}{}: {} / {} = {}'.format(' ' * indent, title, s, l, s / l))

def brick_tiling(text_grid_representation):
    grid = Grid(row_count=len(text_grid_representation), col_count=len(text_grid_representation[0]))
    for i in range(len(text_grid_representation)):
        for j in range(len(text_grid_representation[0])):
            if text_grid_representation[i][j] == '#':
                grid.mark_space_occupied(i, j)

    placeable_tiles = generate_placeable_tiles_for_grid(grid)

    perf_start = time.time()
    count = count_solutions_for_grid(grid, placeable_tiles, 0)
    perf_end = time.time()

    print('{} / {}'.format(count, el_solutions_evaluated))
    print('cache hits: {}'.format(cache_hits))
    print('cache size: {}'.format(len(grid_solution_cache)))
    print('total time: {}'.format(perf_end - perf_start))
    # print_stat('perf_can_solve_grid', 0, perf_can_solve_grid)
    print_stat('perf_deep_copy', 2, perf_deep_copy)
    print_stat('perf_find_first_free_space', 2, perf_find_first_free_space)
    print_stat('perf_get_contiguous_section', 2, perf_get_contiguous_section)
    print_stat('perf_can_solve_contiguous_section', 2, perf_can_solve_contiguous_section)
    # print_stat('perf_is_grid_solved', 0, perf_is_grid_solved)
    print('contig section cache hits: {}'.format(contig_section_cache_hits))
    print('contig section cache size: {}'.format(len(contig_section_cache)))

    return 0


# test_data_row_count = 12
# test_data_col_count = 8
# test_data = ['.' * test_data_col_count for _ in range(test_data_row_count)]
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
    # [
    #     '....',
    #     '....',
    #     '....',
    #     '....'
    # ]
    # [
    #     '......',
    #     '......'
    # ],
    # [
    #     '######',
    #     '######'
    # ],
    # [
    #     '..',
    #     '..',
    #     '..',
    #     '..',
    #     '..',
    #     '..',
    #     '..',
    #     '..'
    # ],
    # [
    #     '...',
    #     '.##'
    # ],
    # [
    #     '....',
    #     '....',
    #     '..##',
    #     '.###',
    #     '.###'
    # ],
    # [
    #     '....',
    #     '....',
    #     '..#.',
    #     '.##.',
    #     '.#..'
    # ]
    # [
    #     '....',
    #     '....',
    #     '..#.',
    #     '..#.',
    #     '....',
    #     '#..#',
    #
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
