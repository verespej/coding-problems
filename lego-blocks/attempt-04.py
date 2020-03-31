#!/bin/python3

import os
import sys

# Provides an array containing the total number of possible configurations
# for a row of each width up to the requested width. For the range [1,b],
# the formula is:
#
# R(w,b) = 2 x R(w-1,b)
#
# where:
#  w = width
#  b = max block size
#
# For the range (b,...], the formula is:
#
# R(w,b) = SUM_i_w_-_b_-_1_w_-_1(R(i,b))
#
# where SUM_i_w_-_b_-_1_w_-_1 = sum from w-b-1 to w-1. Or, in other words,
# thesum of the last b entries.
def get_row_config_counts(width, max_block_size, mod):
    row_config_counts = [0, 1]
    for i in range(len(row_config_counts), max_block_size + 1):
        next_val = (2 *row_config_counts[-1]) % mod
        row_config_counts.append(next_val)

    for i in range(len(row_config_counts), width + 1):
        sumation_group = row_config_counts[-max_block_size:]
        row_config_count = sum(sumation_group) % mod
        row_config_counts.append(row_config_count)

    return row_config_counts

# Provides an array containing the total number of possible configurations
# for each width up to the specified width, at the specified height. The
# formula is:
#
# T(h,w,b) = R(w,b)^h
#
# where:
#  h = height
#  w = target width
#  b = max block width
#  R(w,b) = number of possible row configs (see get_row_config_counts)
def get_total_counts(height, width, max_block_size, mod):
    row_config_counts = get_row_config_counts(width, max_block_size, mod)
    total_counts = []
    for i in range(len(row_config_counts)):
        total_count = pow(row_config_counts[i], height, mod)
        total_counts.append(total_count)

    return total_counts    

# We use a recurrence relation to determine the number of configurations
# that have no slices:
#
# N(h,w,b) = T(h,w,b) - SUM_i_1_w_-_1(N(h,i) x T(h,w-i,b))
#
# where:
#  h = height
#  w = width
#  b = max block width
#  N(h,w) = number of no-slice configuratins for height h and width w
#  T(h,w) = total number of possible configurations for height h and width w
#  SUM_i_1_w_-_1 = sum over the range of 1 to w-1
#
# Note that N(h,i) x T(h,w-i) equals the number of configurations with
# slices.
def lego_blocks(height, width, max_block_size, mod):
    total_counts = get_total_counts(height, width, max_block_size, mod)

    # Initilize an array to hold history for the recurrence relation.
    # We seed it with 0 and 1 because 0 width has 0 solutions and
    # 1 width has 1 solution, regardless of height.
    no_slices_solutions_counts = [0 for col in range(width + 1)]
    no_slices_solutions_counts[1] = 1

    for current_width in range(2, width + 1):
        # This is T(h,w). We're initializing the stored result because we do
        # culumative subtraction of the values from the summation instead of
        # subtracting a single cumulative value at the end.
        no_slices_solutions_counts[current_width] = total_counts[current_width]

        # SUM_i_1_w_-_1
        for i in range(1, current_width):
            no_slices_solutions_counts[current_width] = (
                # Cumulative T(h,w)
                no_slices_solutions_counts[current_width] -
                # N(h,i) x T(h,w-i)
                no_slices_solutions_counts[i] *
                total_counts[current_width-i]
            ) % mod

    return no_slices_solutions_counts[-1] % mod

if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')

    t = int(input())

    MAX_BLOCK_SIZE = 4
    MOD = 10 ** 9 + 7

    for t_itr in range(t):
        nm = input().split()

        n = int(nm[0])

        m = int(nm[1])

        result = lego_blocks(n, m, MAX_BLOCK_SIZE, MOD)

        fptr.write(str(result) + '\n')

    fptr.close()
