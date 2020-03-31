#!/bin/python3

# Test: Use Grid class, use short grid representation for subgrid filtering

import os
import sys
import time

DEBUG = True

# Grid({ grid_to_copy, row_count, col_count })
# [row, col]
# row_count
# col_count
# are_all_spaces_occupied()
# are_spaces_free(spaces)
# flip_horz()
# flip_vert()
# is_col_fully_occupied(col)
# is_row_fully_occupied(row)
# is_space_within_grid_bounds(row, col)
# is_space_free(row, col)
# is_space_occupied(row, col)
# mark_space_free(row, col)
# mark_spaces_free(spaces)
# mark_space_occupied(row, col)
# mark_spaces_occupied(spaces)
# print_rows(*args, { print_func, ...kwargs})
class Grid:
    _grid = None
    _subsection_offset = None

    def __init__(self, *args, **kwargs):
        grid_to_copy = kwargs.get('grid_to_copy')
        matrix_to_copy = kwargs.get('matrix_to_copy')
        row_count = kwargs.get('row_count')
        col_count = kwargs.get('col_count')

        if grid_to_copy:
            if not isinstance(grid_to_copy, Grid):
                raise Exception('grid_to_copy must be an instance of Grid')
            self._grid = [[val for val in row] for row in grid_to_copy._grid]
            self._subsection_offset = grid_to_copy._subsection_offset
        elif matrix_to_copy:
            self._grid = [[val for val in row] for row in matrix_to_copy]
        elif row_count and col_count:
            self._grid = [[1] * col_count for row in range(row_count)]

        self._subsection_offset = kwargs.get('subsection_offset', (0, 0))

    def __getitem__(self, row, col):
        return self._grid[row][col]

    @property
    def row_count(self):
        return len(self._grid)

    @property
    def col_count(self):
        return len(self._grid[0])

    @property
    def subsection_offset(self):
        return self._subsection_offset

    def are_all_spaces_occupied(self):
        # TODO: Would using any()/every() be more efficient?
        for row in self._grid:
            if sum(row) > 0:
                return False
        return True

    def are_spaces_free(self, spaces):
        # TODO: Would using any() be more efficient?
        for point in spaces:
            if not self.is_space_free(point[0], point[1]):
                return False
        return True

    def flip_horz(self):
        for row in self._grid:
            row.reverse()

    def flip_vert(self):
        self._grid.reverse()

    def invert(self):
        for row in range(self.row_count):
            for col in range(self.col_count):
                self._grid[row][col] = 1 if self._grid[row][col] == 0 else 0

    def is_col_fully_occupied(self, col):
        return (
            col < 0 or
            col >= self.col_count or
            sum([row[col] for row in self._grid]) == 0
        )

    def is_row_fully_occupied(self, row):
        return (
            row < 0 or
            row >= self.row_count or
            sum(self._grid[row]) == 0
        )

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

    def get_subsection_grids(self):
        # TODO: Should actually recurse to get minimal subsection

        row_offsets = []
        row_split_matrixes = []
        row_split_start = 0
        for row in range(self.row_count + 1):
            if self.is_row_fully_occupied(row):
                if row_split_start != row:
                    row_offsets.append(row_split_start)
                    row_split_matrixes.append(self._grid[row_split_start:row])
                row_split_start = row + 1

        subsection_grids = []
        col_split_start = 0
        for i in range(len(row_split_matrixes)):
            row_offset = row_offsets[i]
            row_split_matrix = row_split_matrixes[i]
            for col in range(self.col_count + 1):
                is_split = self.is_col_fully_occupied(col)
                if is_split:
                    if col_split_start != col:
                        subsection_grids.append(Grid(
                            matrix_to_copy=[row[col_split_start:col] for row in row_split_matrix],
                            subsection_offset=(row_offset, col_split_start)
                        ))
                    col_split_start = col + 1

        return subsection_grids

    def print_rows(self, *args, **kwargs):
        print_func = kwargs.pop('print_func', print)
        for row in self._grid:
            print_func(''.join([str(val) for val in row]), **kwargs)

    def __str__(self):
        return str(self._grid)

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
    return [t for t in all_tiles if grid.are_spaces_free(t)]

def generate_placeable_tiles_for_grid(grid):
    placeable_tiles = []
    for row in range(grid.row_count):
        for col in range(grid.col_count):
            if grid.is_space_free(row, col):
                placeable_tiles = placeable_tiles + \
                    generate_placeable_tiles_for_point(grid, row, col)
    return placeable_tiles

def create_tiles_normalized_to_offset(tiles, offset):
    return [[(point[0] - offset[0], point[1] - offset[1]) for point in tile] for tile in tiles]

def debug_print(text, indent=0):
    if DEBUG:
        print('{}{}'.format(' ' * (2 * indent), text))

# Optimization: For each grid, if we already know the number of solutions for it's contiguous sections, use those values

# grid_exploration_cache = {}
# def set_has_grid_been_explored(grid):
#     grid_exploration_cache[str(grid)] = True

# def get_has_grid_been_explored(grid):
#     return str(grid) in grid_exploration_cache

subsection_solution_cache = {}
def set_cached_subsection_solution_count(subsection_grid, solutions_count):
    subsection_solution_cache[str(subsection_grid)] = solutions_count

    subsection_grid.flip_vert()
    subsection_solution_cache[str(subsection_grid)] = solutions_count

    subsection_grid.flip_horz()
    subsection_solution_cache[str(subsection_grid)] = solutions_count

    subsection_grid.flip_vert()
    subsection_solution_cache[str(subsection_grid)] = solutions_count

    # Restore to original
    subsection_grid.flip_horz()

def get_cached_subsection_solution_count(subsection_grid):
    key = str(subsection_grid)
    return subsection_solution_cache[key] if key in subsection_solution_cache else None

# perf_is_grid_solved = []
recursion_count = 0
cache_hits = 0
def count_solutions_for_grid(grid, tiles, depth):
    global recursion_count
    global cache_hits

    recursion_count += 1

    subsection_solution_count = get_cached_subsection_solution_count(grid)
    if subsection_solution_count is not None:
        cache_hits += 1
        return subsection_solution_count

    if grid.are_all_spaces_occupied():
        set_cached_subsection_solution_count(grid, 1)
        return 1

    solutions_count = 0
    subsection_grids = grid.get_subsection_grids()
    if len(subsection_grids) > 1:
        solutions_count = 1
        for subsection_grid in subsection_grids:
            solutions_count *= count_solutions_for_grid(
                subsection_grid,
                create_tiles_normalized_to_offset(tiles, subsection_grid.subsection_offset),
                depth + 1
            )
    else:
        for i in range(len(tiles)):
            tile = tiles[i]
            if grid.are_spaces_free(tile):
                child = Grid(grid_to_copy=grid)
                child.mark_spaces_occupied(tile)
                new_solutions = count_solutions_for_grid(child, tiles[i:], depth + 1)
                solutions_count += new_solutions
                # grid.mark_spaces_free(tile)

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
    tiles = generate_placeable_tiles_for_grid(grid)

    perf_start = time.time()
    count = count_solutions_for_grid(grid, tiles, 0)
    perf_end = time.time()

    print('solution count: {}'.format(count))
    print('recursion count: {}'.format(recursion_count))
    print('cache hits: {}'.format(cache_hits))
    print('cache size: {}'.format(len(subsection_solution_cache)))
    print('total time: {}'.format(perf_end - perf_start))

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
# test_cases.append([
#     '....',
#     '....',
#     '....',
#     '....'
# ])
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
