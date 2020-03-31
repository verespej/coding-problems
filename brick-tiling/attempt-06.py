#!/bin/python3

import os
import time

DEBUG = True

def debug_print(text, indent=0):
    if DEBUG:
        print('{}{}'.format(' ' * (2 * indent), text))

# At a high level, the problem is approached as follows:
# 1. Flatten the problem grid into a single-dimensional array, such that
#    each space in the array represents a point on the grid.
# 2. Mark the blocked spaces from the problem grid as occupied in the
#    1-d array.
# 3. Create all possible L-shaped tiles that could be placed on the grid.
# 4. Turn each tile into a partial solution. A partial solution is
#    basically an empty grid with the points of the tile marked as occupied.
# 5. Select solutions by identifying combinations of partial solutions
#    with no conflicts. That is, a valid solution is one in which any column
#    in the selected set sums to exactly 1.

def get_solution_point_from_grid_point(grid, grid_point):
    col_count = len(grid[0])
    row = grid_point[0]
    col = grid_point[1]

    return (row * col_count) + col

def create_partial_solution(grid, occupied_grid_points):
    row_count = len(grid)
    col_count = len(grid[0])

    flattened_grid = [0] * row_count * col_count
    for grid_point in occupied_grid_points:
        flattened_point = get_solution_point_from_grid_point(grid, grid_point)
        flattened_grid[flattened_point] = 1
    return flattened_grid

def do_partial_solutions_conflict(ps1, ps2):
    for i in range(len(ps1)):
        if ps1[i] == 1 and ps2[i] == 1:
            return True
    return False

def generate_partial_solutions_for_grid_point(grid, grid_point):
    # Generate all L shapes for a given (row, col) point.
    # The approach here is to always have the target point, (row, col), be the elbow of the L.
    row = grid_point[0]
    col = grid_point[1]
    tiles = [
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

    grid_row_count = len(grid)
    grid_col_count = len(grid[0])
    def is_in_bounds(tile):
        for point in tile:
            is_row_out_of_bounds = point[0] < 0 or point[0] >= grid_row_count
            is_col_out_of_bounds = point[1] < 0 or point[1] >= grid_col_count
            if is_row_out_of_bounds or is_col_out_of_bounds:
                return False
        return True

    return [
        create_partial_solution(grid, tile)
        for tile in tiles
        if is_in_bounds(tile)
    ]

def partial_solution_to_bitmap(partial_solution):
    bm = 0
    # Note: The low entries in the array end up in the high bits of the map
    for i in range(len(partial_solution)):
        if partial_solution[i] == 1:
            bm |= 1 << i
    return bm

perf_create_cache_key = []
def create_cache_key_for_partial_solution_set(partial_solutions):
    start = time.time()
    bitmap_strs = [str(partial_solution_to_bitmap(pm)) for pm in partial_solutions]
    bitmap_strs.sort()
    result = '.'.join(bitmap_strs)
    perf_create_cache_key.append(time.time() - start)
    return result

result_cache = {}
cache_hits = 0
recursion_count = 0
def count_solutions(partial_solutions):
    points_to_fill_count = len(partial_solutions[0])

    global recursion_count
    recursion_count += 1

    global cache_hits
    cache_key = create_cache_key_for_partial_solution_set(partial_solutions)
    if cache_key in result_cache:
        cache_hits += 1
        return result_cache[cache_key]

    # How many partial solutions cover a given point
    point_coverage_counts = [
        sum([ps[col] for ps in partial_solutions])
        for col in range(points_to_fill_count)
    ]
    min_point_coverage = min(point_coverage_counts)

    if min_point_coverage == 0:
        # Some points aren't covered by any of the remaining partial solutions,
        # so there aren't any solutions with the partials selected thus far
        result_cache[cache_key] = 0
        return 0

    # Select a point with minimal coverage
    index_of_min_covered_point = next(
        i for i in range(points_to_fill_count)
        if point_coverage_counts[i] == min_point_coverage
    )

    solutions_count = 0
    partial_solutions_with_min_covered_point = [
        ps for ps in partial_solutions
        if ps[index_of_min_covered_point] == 1
    ]
    for selected_ps in partial_solutions_with_min_covered_point:
        indexes_of_points_covered_by_selected_ps = [
            i for i in range(points_to_fill_count)
            if selected_ps[i] == 1
        ]

        if len(indexes_of_points_covered_by_selected_ps) == points_to_fill_count:
            # This partial solution fills all the remaining points needing to be
            # filled, so we've found a solution

            # TODO: How to set cache here?

            solutions_count += 1
            continue

        # Remove partial solutions that overlap with the selected partial solution and
        # from each of those, remove the points covered by the selected partial solution.
        reduced_partial_solutions = [
            [ps[i] for i in range(len(ps)) if i not in indexes_of_points_covered_by_selected_ps]
            for ps in partial_solutions # TODO: Exclude the ones already looked at in this loop
            if not do_partial_solutions_conflict(ps, selected_ps)
        ]

        if not reduced_partial_solutions:
            # We still have unfilled points, but no more partial solutions to
            # select, so there aren't any solutions with this set of selections
            continue

        solutions_count += count_solutions(reduced_partial_solutions)

    result_cache[cache_key] = solutions_count
    return solutions_count

def brick_tiling(grid):
    perf_start = time.time()

    grid_row_count = len(grid)
    grid_col_count = len(grid[0])

    blocked_grid_points = [
        (row, col)
        for row in range(grid_row_count)
        for col in range(grid_col_count)
        if grid[row][col] == '#'
    ]
    blocked_points_partial_solution = create_partial_solution(grid, blocked_grid_points)

    # 1. For each tile, create a partial solution
    # 2. Filter out the partial solutions that include points blocked on the board
    # 3. For each partial solution, remove the columns corresponding with points blocked on the board
    partial_solutions = [
        [partial_solution[i] for i in range(len(partial_solution)) if blocked_points_partial_solution[i] != 1]
        for row in range(grid_row_count)
        for col in range(grid_col_count)
        for partial_solution in generate_partial_solutions_for_grid_point(grid, (row, col))
        if not do_partial_solutions_conflict(partial_solution, blocked_points_partial_solution)
    ]

    if not partial_solutions:
        return 1

    count = count_solutions(partial_solutions)

    perf_end = time.time()
    debug_print('Final result: {}'.format(count))
    debug_print('Time: {}'.format(perf_end - perf_start))
    debug_print('Recursion count: {}'.format(recursion_count))
    debug_print('Cache hits: {}'.format(cache_hits))
    debug_print('Create cache key time: {}'.format(sum(perf_create_cache_key)))

    return count


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
# test_cases.append([
# '......',
# '......',
# '......',
# '......',
# '......',
# '......',
# '......',
# '......'
# ])
# test_cases.append([
# '.....',
# '.....',
# '....#',
# '.....',
# '.....',
# '.....',
# '.....',
# '.....',
# '.....',
# '.....',
# '.....',
# '.....',
# '.....'
# ])
# test_cases.append([
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........'
# ])

# test_cases.append([
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........',
#     '........'
# ])

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
