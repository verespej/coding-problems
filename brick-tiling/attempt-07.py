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

class PartialSolution:
    _bitarray = None
    _bitmap = None
    _occupied_points = None

    def __init__(self, num_points, occupied_points):
        self._bitarray = [0] * num_points
        self._bitmap = 0
        self._occupied_points = sorted(occupied_points)

        for point in self._occupied_points:
            self._bitarray[point] = 1
            self._bitmap |= 1 << point

    def __getitem__(self, index):
        return 1 if self._bitmap & (1 << index) else 0
        # return self._bitarray[index]

    @classmethod
    def create_from_grid(cls, grid, occupied_grid_points):
        row_count = len(grid)
        col_count = len(grid[0])
        occupied_flat_points = [
            (grid_point[0] * col_count) + grid_point[1]
            for grid_point in occupied_grid_points
        ]
        return cls(row_count * col_count, occupied_flat_points)

    @property
    def uid(self):
        return self._bitmap

    @property
    def num_points(self):
        return len(self._bitarray)

    @property
    def occupied_points(self):
        return self._occupied_points

    def create_copy(self, exclude_points=[]):
        filtered = [
            self._bitarray[i] for i in range(len(self._bitarray))
            if i not in exclude_points
        ]
        return PartialSolution(
            len(filtered),
            [i for i in range(len(filtered)) if filtered[i] == 1]
        )

    def has_overlap(self, other):
        # print('has_overlap')
        # print('{:b}'.format(self._bitmap).rjust(len(self._bitarray), '0'))
        # print('{:b}'.format(other._bitmap).rjust(len(self._bitarray), '0'))
        # print()
        return self._bitmap & other._bitmap != 0
        # for i in range(len(self._bitarray)):
        #     if self._bitarray[i] == 1 and other._bitarray[i] == 1:
        #         return True
        # return False

    # def remove_points(self, points_to_exclude):
    #     # TODO: for bitmap
    #     self._bitarray = [
    #         self._bitarray[point] for point in range(len(self._bitarray))
    #         if point not in points_to_exclude
    #     ]
    #     for point in self._occupied_points:
    #         self._bitarray[point] = 1
    #         self._bitmap |= 1 << point

    def __str__(self):
        return str(self._bitarray)


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
        PartialSolution.create_from_grid(grid, tile)
        for tile in tiles
        if is_in_bounds(tile)
    ]

perf_create_cache_key = []
def create_cache_key_for_partial_solution_set(partial_solutions):
    start = time.time()
    uids = [str(pm.uid) for pm in partial_solutions]
    uids.sort()
    result = '.'.join(uids)
    perf_create_cache_key.append(time.time() - start)
    return result

result_cache = {}
cache_hits = 0
recursion_count = 0
def count_solutions(partial_solutions):
    points_to_fill_count = partial_solutions[0].num_points

    global recursion_count
    recursion_count += 1

    global cache_hits
    cache_key = create_cache_key_for_partial_solution_set(partial_solutions)
    if cache_key in result_cache:
        cache_hits += 1
        return result_cache[cache_key]

    # How many partial solutions cover a given point
    point_coverage_counts = [
        sum([ps[point] for ps in partial_solutions])
        for point in range(points_to_fill_count)
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
        if len(selected_ps.occupied_points) == points_to_fill_count:
            # This partial solution fills all the remaining points needing to be
            # filled, so we've found a solution

            # TODO: How to set cache here?

            solutions_count += 1
            continue

        # Remove partial solutions that overlap with the selected partial solution
        # Note: We create copies because we're going to remove columns and don't want
        # to change the originals since we'll revisit back to them as we continue in
        # the loop
        # Remove the points covered by the selected partial solution.

        # TODO: Can we exclude ones already looked at in this loop?
        # TODO: Can maybe save comp if we just count for the reduced_partial_solutions check
        # and then do the creates after if we don't skip this iteration
        reduced_partial_solutions = [
            ps.create_copy(exclude_points=selected_ps.occupied_points)
            for ps in partial_solutions
            if not ps.has_overlap(selected_ps)
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
    blocked_points_partial_solution = PartialSolution.create_from_grid(grid, blocked_grid_points)

    # For each tile, create a partial solution and filter out the
    # ones that have points that're blocked on the base grid
    # For each partial solution, remove points that're blocked on the base grid
    partial_solutions = [
        partial_solution.create_copy(exclude_points=blocked_points_partial_solution.occupied_points)
        for row in range(grid_row_count)
        for col in range(grid_col_count)
        for partial_solution in generate_partial_solutions_for_grid_point(grid, (row, col))
        if not partial_solution.has_overlap(blocked_points_partial_solution)
    ]

    if not partial_solutions:
        return 1

    count = count_solutions(partial_solutions)

    perf_end = time.time()
    debug_print('============')
    debug_print('FINAL RESULT: {}'.format(count))
    debug_print('------------')
    debug_print('Time: {}'.format(perf_end - perf_start))
    debug_print('Recursion count: {}'.format(recursion_count))
    debug_print('Cache hits: {}'.format(cache_hits))
    debug_print('Create cache key time: {}'.format(sum(perf_create_cache_key)))

    return count

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
