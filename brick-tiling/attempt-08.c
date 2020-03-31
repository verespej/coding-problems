#include <assert.h>
#include <limits.h>
#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// srand(time(0));
// rand();

int get_partial_solution_len(int row_count, int col_count) {
    return row_count * col_count;
}

bool* allocate_partial_solution(count) {
    return (bool*) calloc(count, sizeof(bool));
}

int get_flat_point_from_2d_point(int col_count, int row, int col) {
    return (row * col_count) + col;
}

bool do_partial_solutions_conflict(
    const int len,
    const bool* ps1,
    const bool* ps2
) {
    for (int i = 0; i < len; i++) {
        if (ps1[i] == 1 && ps2[i] == 1) {
            return true;
        }
    }
    return false;
}

bool are_all_spaces_in_partial_solution_full(const bool* ps, const int ps_len) {
    for (int i = 0; i < ps_len; i++) {
        if (ps[0] == false) {
            return false;
        }
    }
    return true;
}

bool is_2d_point_in_bounds(
    const int row_bound,
    const int col_bound,
    const int row,
    const int col
) {
    return 0 <= row && row < row_bound && 0 <= col && col < col_bound;
}

bool are_2d_points_all_in_bounds(
    const int row_bound,
    const int col_bound,
    const int points[][2],
    const int num_points,
    const int row_offset,
    const int col_offset
) {
    for (int point = 0; point < num_points; point++) {
        int row = row_offset + points[point][0];
        int col = col_offset + points[point][1];
        if (!is_2d_point_in_bounds(row_bound, col_bound, row, col)) {
            return false;
        }
    }
    return true;
}

void transpose_2d_points_onto_partial_solution(
    bool* partial_solution,
    const int points[][2],
    const int num_points,
    const int col_count,
    const int row_offset,
    const int col_offset
) {
    for (int point = 0; point < num_points; point++) {
        const int row = row_offset + points[point][0];
        const int col = col_offset + points[point][1];
        const int flat_point = get_flat_point_from_2d_point(col_count, row, col);
        partial_solution[flat_point] = true;
    }
}

void remove_col_from_partial_solutions(
    bool** pses,
    int ps_count,
    int ps_len,
    int col
) {
    // If element is last, don't need to do anything because reducing
    // the count will effectively remove the column
    if (col + 1 < ps_len) {
        size_t copy_size = (ps_len - (col + 1)) * sizeof(bool);
        for (int i = 0; i < ps_count; i++) {
            memcpy(&pses[i][col], &pses[i][col + 1], copy_size);
        }
    }
}

void allocate_partial_solutions_for_grid(
    /* in */ const char** grid,
    /* in */ const int row_count,
    /* out */ bool*** partial_solutions_ref,
    /* out */ int* partial_solutions_count_ref,
    /* out */ int* partial_solution_len_ref
) {
    const int col_count = (int)strlen(grid[0]);
    int ps_len = get_partial_solution_len(row_count, col_count);

    // Create partial solution for the grid itself
    bool* grid_ps = allocate_partial_solution(ps_len);
    for (int i = 0; i < row_count; i++) {
        for (int j = 0; j < col_count; j++) {
            int dest_index = get_flat_point_from_2d_point(col_count, i, j);
            grid_ps[dest_index] = grid[i][j] == '.' ? false : true;
        }
    }

    // These are the transformations to create each of the 2-d points that
    // form all L tiles for a given 2-d point, in which the 2-d point is
    // the elbow of the L.
    const int TILE_SHAPES[8][4][2] = {
        // "Sideways" L's
        { {  1,  0 }, { 0, 0 }, {  0,  1 }, {  0,  2 } },
        { { -1,  0 }, { 0, 0 }, {  0, -1 }, {  0, -2 } },
        { { -1,  0 }, { 0, 0 }, {  0,  1 }, {  0,  2 } },
        { {  1,  0 }, { 0, 0 }, {  0, -1 }, {  0, -2 } },
        // "Vertical" L's
        { {  0,  1 }, { 0, 0 }, { -1,  0 }, { -2,  0 } },
        { {  0, -1 }, { 0, 0 }, {  1,  0 }, {  2,  0 } },
        { {  0,  1 }, { 0, 0 }, {  1,  0 }, {  2,  0 } },
        { {  0, -1 }, { 0, 0 }, { -1,  0 }, { -2,  0 } }
    };
    const int TILE_SHAPES_COUNT = (int) sizeof(TILE_SHAPES) / sizeof(*TILE_SHAPES);
    const int POINTS_PER_TILE = (int) sizeof(*TILE_SHAPES) / sizeof(**TILE_SHAPES);

    const int max_possible_partial_solutions = row_count * col_count * TILE_SHAPES_COUNT;
    bool** partial_solutions = (bool**) calloc(max_possible_partial_solutions, sizeof(bool**));
    int partial_solutions_count = 0;

    // Create the partial solutions and only save those that don't
    // conflict with spots already filled on the grid
    for (int row = 0; row < row_count; row++) {
        for (int col = 0; col < col_count; col++) {
            for (int tile = 0; tile < TILE_SHAPES_COUNT; tile++) {
                const bool is_in_bounds = are_2d_points_all_in_bounds(
                    row_count,
                    col_count,
                    TILE_SHAPES[tile],
                    POINTS_PER_TILE,
                    row,
                    col
                );
                if (is_in_bounds) {
                    bool* ps = allocate_partial_solution(ps_len);
                    transpose_2d_points_onto_partial_solution(
                        ps, TILE_SHAPES[tile], POINTS_PER_TILE, col_count, row, col
                    );

                    // Save this partial solution if its filled spots don't 
                    // conflict with grid
                    if (!do_partial_solutions_conflict(ps_len, grid_ps, ps)) {
                        partial_solutions[partial_solutions_count] = ps;
                        partial_solutions_count++;
                    } else {
                        free(ps);
                    }
                }
            }
        }
    }

    // Trim all columns that're already filled on the grid
    for (int point = 0; point < ps_len; point++) {
        if (grid_ps[point] == true) {
            remove_col_from_partial_solutions(
                partial_solutions,
                partial_solutions_count,
                ps_len,
                point
            );
            ps_len--;
        }
    }

    (*partial_solutions_ref) = partial_solutions;
    (*partial_solutions_count_ref) = partial_solutions_count;
    (*partial_solution_len_ref) = ps_len;
}

void print_partial_solution(const int len, const bool* ps) {
    for (int i = 0; i < len; i++) {
        printf("%d", (int)ps[i]);
    }
    printf("\n");
}

bool is_grid_fully_blocked(char** grid, int row_count, int col_count) {
    for (int row = 0; row < row_count; row++) {
        for (int col = 0; col < col_count; col++) {
            if (grid[row][col] == '.') {
                return false;
            }
        }
    }
    return true;
}

// int count_solutions(partial_solutions) {
//     points_to_fill_count = len(partial_solutions[0])

//     global recursion_count
//     recursion_count += 1

//     global cache_hits
//     cache_key = create_cache_key_for_partial_solution_set(partial_solutions)
//     if cache_key in result_cache:
//         cache_hits += 1
//         return result_cache[cache_key]

//     # How many partial solutions cover a given point
//     point_coverage_counts = [
//         sum([ps[col] for ps in partial_solutions])
//         for col in range(points_to_fill_count)
//     ]
//     min_point_coverage = min(point_coverage_counts)

//     if min_point_coverage == 0:
//         # Some points aren't covered by any of the remaining partial solutions,
//         # so there aren't any solutions with the partials selected thus far
//         result_cache[cache_key] = 0
//         return 0

//     # Select a point with minimal coverage
//     index_of_min_covered_point = next(
//         i for i in range(points_to_fill_count)
//         if point_coverage_counts[i] == min_point_coverage
//     )

//     solutions_count = 0
//     partial_solutions_with_min_covered_point = [
//         ps for ps in partial_solutions
//         if ps[index_of_min_covered_point] == 1
//     ]
//     for selected_ps in partial_solutions_with_min_covered_point:
//         indexes_of_points_covered_by_selected_ps = [
//             i for i in range(points_to_fill_count)
//             if selected_ps[i] == 1
//         ]

//         if len(indexes_of_points_covered_by_selected_ps) == points_to_fill_count:
//             # This partial solution fills all the remaining points needing to be
//             # filled, so we've found a solution

//             # TODO: How to set cache here?

//             solutions_count += 1
//             continue

//         # Remove partial solutions that overlap with the selected partial solution and
//         # from each of those, remove the points covered by the selected partial solution.
//         reduced_partial_solutions = [
//             [ps[i] for i in range(len(ps)) if i not in indexes_of_points_covered_by_selected_ps]
//             for ps in partial_solutions # TODO: Exclude the ones already looked at in this loop
//             if not do_partial_solutions_conflict(ps, selected_ps)
//         ]

//         if not reduced_partial_solutions:
//             # We still have unfilled points, but no more partial solutions to
//             # select, so there aren't any solutions with this set of selections
//             continue

//         solutions_count += count_solutions(reduced_partial_solutions)

//     result_cache[cache_key] = solutions_count
//     return solutions_count
// }

int brickTiling(int grid_row_count, char** grid) {
    clock_t perf_start, perf_end;

    perf_start = clock();

    const int grid_col_count = (int)strlen(grid[0]);
    printf("grid: %d x %d\n", grid_row_count, grid_col_count);

    if (is_grid_fully_blocked(grid, grid_row_count, grid_col_count)) {
        // Special case of grid having no free spaces
        return 1;
    }

    bool** partial_solutions;
    int partial_solutions_count;
    int ps_len;
    allocate_partial_solutions_for_grid(
        (const char**) grid,
        grid_row_count,
        &partial_solutions,
        &partial_solutions_count,
        &ps_len
    );

    if (partial_solutions_count < 1) {
        // Special case of spaces on board in which tiles can be placed
        return 0;
    }

    for (int i = 0; i < partial_solutions_count; i++) {
        print_partial_solution(ps_len, partial_solutions[i]);
        free(partial_solutions[i]);
    }
    free(partial_solutions);

    perf_end = clock();
    printf("Time (s): %f\n", (perf_end - perf_start) / (double)CLOCKS_PER_SEC);

    return -1;
}

int main()
{
    char *test_data[2] = {
      "....",
      "...."
    };
    brickTiling(sizeof(test_data)/sizeof(test_data[0]), test_data);
    return 0;
}

