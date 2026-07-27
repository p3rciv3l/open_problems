#include <stdint.h>
#include <stdio.h>

static unsigned index_of(int x, int y) {
    return (unsigned)((y + 2) * 5 + (x + 2));
}

static unsigned alive_at_time_one(uint32_t state, int x, int y) {
    unsigned count = 0;
    for (int dy = -1; dy <= 1; ++dy) {
        for (int dx = -1; dx <= 1; ++dx) {
            if (dx || dy) {
                count += (state >> index_of(x + dx, y + dy)) & 1u;
            }
        }
    }
    unsigned alive = (state >> index_of(x, y)) & 1u;
    return count == 3 || (alive && count == 2);
}

int main(void) {
    uint64_t counts[26] = {0};
    for (uint32_t state = 0; state < (1u << 25); ++state) {
        unsigned neighbor_count = 0;
        unsigned center = 0;
        for (int y = -1; y <= 1; ++y) {
            for (int x = -1; x <= 1; ++x) {
                unsigned alive = alive_at_time_one(state, x, y);
                if (x || y) {
                    neighbor_count += alive;
                } else {
                    center = alive;
                }
            }
        }
        if (neighbor_count == 3 || (center && neighbor_count == 2)) {
            ++counts[__builtin_popcount(state)];
        }
    }
    for (unsigned weight = 0; weight <= 25; ++weight) {
        printf("%s%llu", weight ? " " : "",
               (unsigned long long)counts[weight]);
    }
    putchar('\n');
    return 0;
}
