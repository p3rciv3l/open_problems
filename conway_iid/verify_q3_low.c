#include <stdint.h>
#include <stdio.h>

static uint64_t time_one_masks[25];
static uint64_t time_two_masks[9];

static int index_of(int x, int y, int radius) {
    return (y + radius) * (2 * radius + 1) + x + radius;
}

static unsigned next_cell(uint64_t state, uint64_t mask, int center) {
    unsigned neighbors = (unsigned)__builtin_popcountll(state & mask);
    return neighbors == 3 ||
           (neighbors == 2 && ((state >> center) & 1u));
}

static int origin_alive_at_time_three(uint64_t initial) {
    uint64_t time_one = 0;
    uint64_t time_two = 0;
    for (int y = -2; y <= 2; ++y) {
        for (int x = -2; x <= 2; ++x) {
            int output = index_of(x, y, 2);
            if (next_cell(initial, time_one_masks[output],
                          index_of(x, y, 3))) {
                time_one |= 1ull << output;
            }
        }
    }
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            int output = index_of(x, y, 1);
            if (next_cell(time_one, time_two_masks[output],
                          index_of(x, y, 2))) {
                time_two |= 1ull << output;
            }
        }
    }
    unsigned neighbors =
        (unsigned)__builtin_popcountll(time_two & ~(1ull << 4));
    return neighbors == 3 ||
           (neighbors == 2 && ((time_two >> 4) & 1u));
}

static void initialize_masks(void) {
    for (int y = -2; y <= 2; ++y) {
        for (int x = -2; x <= 2; ++x) {
            int output = index_of(x, y, 2);
            for (int dy = -1; dy <= 1; ++dy) {
                for (int dx = -1; dx <= 1; ++dx) {
                    if (dx || dy) {
                        time_one_masks[output] |=
                            1ull << index_of(x + dx, y + dy, 3);
                    }
                }
            }
        }
    }
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            int output = index_of(x, y, 1);
            for (int dy = -1; dy <= 1; ++dy) {
                for (int dx = -1; dx <= 1; ++dx) {
                    if (dx || dy) {
                        time_two_masks[output] |=
                            1ull << index_of(x + dx, y + dy, 2);
                    }
                }
            }
        }
    }
}

int main(void) {
    initialize_masks();
    for (unsigned weight = 0; weight <= 5; ++weight) {
        uint64_t count = 0;
        if (weight == 0) {
            count = (uint64_t)origin_alive_at_time_three(0);
        } else {
            uint64_t state = (1ull << weight) - 1;
            const uint64_t limit = 1ull << 49;
            while (state < limit) {
                count += (uint64_t)origin_alive_at_time_three(state);
                uint64_t low_bit = state & (0ull - state);
                uint64_t incremented = state + low_bit;
                state = incremented +
                        (((incremented ^ state) / low_bit) >> 2);
            }
        }
        printf("%u %llu\n", weight, (unsigned long long)count);
    }
    return 0;
}
