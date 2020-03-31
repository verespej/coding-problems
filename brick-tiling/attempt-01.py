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
def has_invalid_contiguous_sections(grid):
    contiguous_sections = []

    free_space = find_first_free_space(grid)
    while free_space:
        contiguous_sections.append(get_contiguous_section(grid, free_space))
        free_space = find_first_free_space(grid)

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

perf_can_add_tile_to_set = []
def can_add_tile_to_set(grid, tile_set, tile):
    start_time = time.time()
    for points in tile:
        if grid[points[0]][points[1]] == 1:
            return False

    for tile_from_set in tile_set:
        if are_tiles_overlapping(tile_from_set, tile):
            return False

    result = can_fill_all_sections_after_placing_tile(grid, tile_set, tile)
    end_time = time.time()
    global perf_can_add_tile_to_set
    perf_can_add_tile_to_set.append(end_time - start_time)
    return result

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

perf_count_solutions_first_ops = []
solutions_evaluated = 0
shape_cache = {}
def count_solutions(grid, solution_set, remaining_tiles, target_length):
    time_start = time.time()
    grid_after_placing_tiles = copy.deepcopy(grid)
    for tile in solution_set:
        for point in tile:
            grid_after_placing_tiles[point[0]][point[1]] = 1
    flattened = [str(col) for row in grid_after_placing_tiles for col in row]
    shape_cache_key = ''.join(flattened)
    time_end = time.time()
    global perf_count_solutions_first_ops
    perf_count_solutions_first_ops.append(time_end - time_start)

    global solutions_evaluated
    global shape_cache
    if shape_cache_key in shape_cache:
        return shape_cache[shape_cache_key]

    if len(solution_set) == target_length:
        # print_solution(solution_set, len(grid), len(grid[0]))
        solutions_evaluated += 1
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
        else:
            solutions_evaluated += 1
        #     print_solution(solution_set + [next_tile], len(grid), len(grid[0]))

    # Once we've seen a particular shape, cache the count of solutions for it
    # print('{} : {}'.format(shape_cache_key, solutions_count))
    shape_cache[shape_cache_key] = solutions_count

    return solutions_count

def create_compatibility_bitmap(tiles):
    compatibility_bitmap = [0] * len(tiles)
    for i in range(len(tiles)):
        for j in range(len(tiles)):
            if i == j or not are_tiles_overlapping(tiles[i], tiles[j]):
                compatibility_bitmap[i] |= 1 << j
    return compatibility_bitmap

def are_compatible(compatibility_bitmap, selected_indexes):
    compatibility_mask = -1
    solution_mask = 0
    for i in selected_indexes:
        compatibility_mask &= compatibility_bitmap[i]
        solution_mask |= 1 << i
    return (compatibility_mask & solution_mask) == solution_mask

def count_solution_sets(compatibility_bitmap, selected, remaining, required_count):
    compatible = are_compatible(compatibility_bitmap, selected)
    enough_remaining = len(selected) + len(remaining) >= required_count
    # print('s: {} r: {} c: {} e: {}'.format(selected, remaining, compatible, enough_remaining))
    if not compatible or not enough_remaining:
        return 0
    elif len(selected) == required_count:
        return 1

    count = 0
    for i in range(len(remaining)):
        count += count_solution_sets(
            compatibility_bitmap,
            selected + [remaining[i]],
            remaining[i + 1:],
            required_count
        )
    return count

def create_compatibility_map(tiles):
    compatibility_map = []
    for i in range(len(tiles)):
        compatibility_map.append([])
        for j in range(len(tiles)):
            compatibility_map[i].append(1 if i == j or not are_tiles_overlapping(tiles[i], tiles[j]) else 0)
    return compatibility_map

def are_compatible_2(compatibility_map, selected_indexes):
    for i in selected_indexes:
        for j in selected_indexes:
            if not compatibility_map[i][j]:
                return False
    return True

def count_solution_sets_2(compatibility_map, selected, remaining, required_count):
    compatible = are_compatible_2(compatibility_map, selected)
    enough_remaining = len(selected) + len(remaining) >= required_count
    # print('s: {} r: {} c: {} e: {}'.format(selected, remaining, compatible, enough_remaining))
    if not compatible or not enough_remaining:
        return 0
    elif len(selected) == required_count:
        return 1

    count = 0
    for i in range(len(remaining)):
        count += count_solution_sets_2(
            compatibility_map,
            selected + [remaining[i]],
            remaining[i + 1:],
            required_count
        )
    return count

# def generate_base_tile_point_sets_for_point(row, col):
#     # In generating these, the target point, (row, col), is always the
#     # elbow.
#     return [
#         # "Sideways" L's
#         frozenset({(row + 1, col), (row, col), (row, col + 1), (row, col + 2)}),
#         frozenset({(row - 1, col), (row, col), (row, col - 1), (row, col - 2)}),
#         frozenset({(row - 1, col), (row, col), (row, col + 1), (row, col + 2)}),
#         frozenset({(row + 1, col), (row, col), (row, col - 1), (row, col - 2)}),
#         # "Vertical" L's
#         frozenset({(row, col + 1), (row, col), (row - 1, col), (row - 2, col)}),
#         frozenset({(row, col - 1), (row, col), (row + 1, col), (row + 2, col)}),
#         frozenset({(row, col + 1), (row, col), (row + 1, col), (row + 2, col)}),
#         frozenset({(row, col - 1), (row, col), (row - 1, col), (row - 2, col)})
#     ]

# def generate_base_tile_point_sets_for_grid(grid):
#     blocked_points = set()
#     for i in range(len(grid)):
#         for j in range(len(grid[i])):
#             if grid[i][j] == '#':
#                 blocked_points.add({i, j})

#     result = set()
#     for i in range(len(grid)):
#         for j in range(len(grid[i])):
#             base_tile_point_sets = generate_base_tile_point_sets_for_point(i, j)
#             base_tile_point_sets = [ps for ps in base_tile_point_sets if ps.isdisjoint(blocked_points)]
#             result = result.union(base_tile_point_sets)

#     return result

# def create_list_of_merged_compatible_pairs(point_sets):
#     compatibile_pairs = []
#     for s1 in point_sets:
#         for s2 in point_sets:
#             if s1.isdisjoint(s2):
#                 compatibile_pairs.append(s1.union(s2))
#     print(len(compatibile_pairs))
#     return compatibile_pairs

# def create_compatibility_layers(point_sets, num_layers):
#     layers = [point_sets]
#     for i in range(1, num_layers):
#         layers.append(
#             create_list_of_merged_compatible_pairs(layers[i - 1])
#         )
#     return layers

# def count_solution_sets_3(compatibility_layers, layer, required_layers_bitmap, point_set):
#     fulfilled_requirement = layer > len(compatibility_layers)
#     if fulfilled_requirement:
#         return 1

#     current_layer_required = required_layers_bitmap & (1 << layer)
#     if not current_layer_required:
#         return count_solution_sets_3(compatibility_layers, layer + 1, required_layers_bitmap, point_set)

#     count = 0
#     for ps in compatibility_layers[layer]:
#         if point_set.disjoint(ps):
#             count += count_solution_sets_3(
#                 compatibility_layers,
#                 layer + 1,
#                 required_layers_bitmap,
#                 point_set.union(ps)
#             )
#     return count

def brick_tiling(grid):
    # placeable_tiles = generate_placeable_tiles_for_grid(grid)
    # required_tile_count = get_free_space_count_for_grid(grid) / 4
    # compatibility_map = create_compatibility_map(placeable_tiles)

    # grid = [
    #     '....',
    #     '....',
    #     '..#.',
    #     '###.',
    # ]
    print('elimination:')

    perf_prep_start = time.time()
    converted_grid = []
    for i in range(len(grid)):
        converted_grid.append([])
        for j in range(len(grid[0])):
            converted_grid[i].append(0 if grid[i][j] == '.' else 1)
    placeable_tiles = generate_placeable_tiles_for_grid(converted_grid)
    required_tile_count = get_free_space_count_for_grid(converted_grid) / TILE_LENGTH
    perf_prep_end = time.time()

    perf_count_solutions_start = time.time()
    count = count_solutions(converted_grid, [], placeable_tiles, required_tile_count)
    print('{} / {}'.format(count, solutions_evaluated))
    perf_count_solutions_end = time.time()
    print('perf_prep time: {}'.format(perf_prep_end - perf_prep_start))
    print('perf_count_solutions time: {}'.format(perf_count_solutions_end - perf_count_solutions_start))
    print('perf_can_add_tile_to_set: {}'.format(sum(perf_can_add_tile_to_set)))
    print('perf_count_solutions_first_ops: {}'.format(sum(perf_count_solutions_first_ops)))



    # print('compatibility_bitmap:')
    # perf_beg = time.time()
    # placeable_tiles = generate_placeable_tiles_for_grid(converted_grid)
    # compatibility_bitmap = create_compatibility_bitmap(placeable_tiles)
    # required_tile_count = len([1 for row in converted_grid for entry in row if entry == 0]) / TILE_LENGTH
    # print(required_tile_count)
    # count = count_solution_sets(compatibility_bitmap, [], range(len(compatibility_bitmap)), required_tile_count)
    # print(count)
    # perf_end = time.time()
    # print('time: {}'.format(perf_end - perf_beg))




    # perf_beg = time.time()
    # point_sets = generate_base_tile_point_sets_for_grid(grid)
    # compatibility_layers = create_compatibility_layers(point_sets, 5)
    # for i in range(len(compatibility_layers)):
    #     print(len(compatibility_layers[i]))
    # # layers_approach_result = layers_approach = count_solution_sets_3(compatibility_layers, 0, required_tile_count, set())
    # layers_approach_result = 'x'
    # perf_end = time.time()
    # layers_approach_time = perf_end - perf_beg
    # print('{}, {}'.format(layers_approach_result, layers_approach_time))

    # print('{} : {} : {}'.format(original_approach, bitmap_approach, map_approach))
    # print('{} : {} : {}'.format(original_approach_time, bitmap_approach_time, map_approach_time))

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

test_cases = [
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
    # ]
    # [
    #     '....',
    #     '....',
    #     '....',
    #     '....'
    # ]
    # [
    #     '....',
    #     '....',
    #     '....',
    #     '....',
    #     '....',
    #     '....'
    # ]
    [
        '....',
        '....',
        '....',
        '....',
        '....',
        '....',
        '....',
        '....'
    ]
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
