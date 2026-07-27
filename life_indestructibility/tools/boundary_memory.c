#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STATE_COUNT (1u << 25)
#define SAFE_COUNT (1u << 24)
#define CENTER_BIT (1u << 12)
#define BASE_ACTIONS 4
#define CUSTOM_MASK 0x0006aeu

static uint8_t row_table[2][32][32][32];

static uint32_t expand_state(uint32_t compact, int protected_value) {
    return (compact & (CENTER_BIT - 1)) |
           ((uint32_t)protected_value << 12) |
           ((compact >> 12) << 13);
}

static uint32_t compact_state(uint32_t state) {
    return (state & (CENTER_BIT - 1)) | ((state >> 13) << 12);
}

static uint32_t base_transition(uint32_t state, int action) {
    uint32_t output = 0;
    int side = action == 1 || action == 2;
    int cap = action == 1 || action == 3 ? 31 : 0;
    for (int y = 0; y < 5; y++) {
        int above = y ? (int)((state >> (5 * (y - 1))) & 31) : cap;
        int current = (state >> (5 * y)) & 31;
        int below = y < 4
            ? (int)((state >> (5 * (y + 1))) & 31)
            : cap;
        output |= (uint32_t)row_table[side][above][current][below] << (5 * y);
    }
    return output;
}

static int outer_index(int x, int y) {
    if (y == -1) return x + 1;
    if (y == 5) return 18 + x;
    if (x == -1) return 7 + 2 * y;
    return 8 + 2 * y;
}

static int cell(uint32_t state, uint32_t outer, int x, int y) {
    if (0 <= x && x < 5 && 0 <= y && y < 5)
        return (state >> (5 * y + x)) & 1;
    return (outer >> outer_index(x, y)) & 1;
}

static uint32_t custom_transition(uint32_t state, uint32_t outer) {
    uint32_t output = 0;
    for (int y = 0; y < 5; y++) {
        for (int x = 0; x < 5; x++) {
            int neighbors = 0;
            for (int dy = -1; dy <= 1; dy++)
                for (int dx = -1; dx <= 1; dx++)
                    if (dx || dy)
                        neighbors += cell(state, outer, x + dx, y + dy);
            int alive = (state >> (5 * y + x)) & 1;
            if (neighbors == 3 || (alive && neighbors == 2))
                output |= 1u << (5 * y + x);
        }
    }
    return output;
}

static uint32_t transition(uint32_t state, int action) {
    if (action < BASE_ACTIONS) return base_transition(state, action);
    return custom_transition(state, CUSTOM_MASK);
}

static void initialize_rows(void) {
    for (int side = 0; side < 2; side++) {
        for (int above = 0; above < 32; above++) {
            for (int current = 0; current < 32; current++) {
                for (int below = 0; below < 32; below++) {
                    int output = 0;
                    for (int x = 0; x < 5; x++) {
                        int neighbors = 0;
                        int rows[3] = {above, current, below};
                        for (int row = 0; row < 3; row++)
                            for (int xx = x - 1; xx <= x + 1; xx++)
                                neighbors += xx < 0 || xx >= 5
                                    ? side
                                    : (rows[row] >> xx) & 1;
                        int alive = (current >> x) & 1;
                        neighbors -= alive;
                        if (neighbors == 3 || (alive && neighbors == 2))
                            output |= 1 << x;
                    }
                    row_table[side][above][current][below] = output;
                }
            }
        }
    }
}

static int generate_one(int protected_value, const char *path) {
    int32_t *head = malloc((size_t)STATE_COUNT * sizeof(*head));
    int32_t *next = malloc(
        (size_t)SAFE_COUNT * BASE_ACTIONS * sizeof(*next)
    );
    uint32_t *predecessor = malloc(
        (size_t)SAFE_COUNT * BASE_ACTIONS * sizeof(*predecessor)
    );
    uint32_t *queue = malloc((size_t)STATE_COUNT * sizeof(*queue));
    uint8_t *rank = malloc((size_t)STATE_COUNT);
    uint8_t *action = malloc((size_t)STATE_COUNT);
    if (!head || !next || !predecessor || !queue || !rank || !action)
        return 2;
    memset(head, 0xff, (size_t)STATE_COUNT * sizeof(*head));
    memset(rank, 0xff, (size_t)STATE_COUNT);
    memset(action, 0xff, (size_t)STATE_COUNT);

    uint32_t edge = 0;
    for (uint32_t compact = 0; compact < SAFE_COUNT; compact++) {
        uint32_t state = expand_state(compact, protected_value);
        for (int candidate_action = 0;
             candidate_action < BASE_ACTIONS;
             candidate_action++) {
            uint32_t successor = transition(state, candidate_action);
            predecessor[edge] = state;
            next[edge] = head[successor];
            head[successor] = edge++;
        }
    }

    uint32_t begin = 0;
    uint32_t end = 0;
    for (uint32_t state = 0; state < STATE_COUNT; state++) {
        if (!!(state & CENTER_BIT) != protected_value) {
            rank[state] = 0;
            queue[end++] = state;
        }
    }

    while (begin < end) {
        uint32_t successor = queue[begin++];
        for (int32_t current_edge = head[successor];
             current_edge != -1;
             current_edge = next[current_edge]) {
            uint32_t state = predecessor[current_edge];
            if (rank[state] != UINT8_MAX) continue;
            rank[state] = rank[successor] + 1;
            for (int candidate_action = 0;
                 candidate_action < BASE_ACTIONS;
                 candidate_action++) {
                if (transition(state, candidate_action) == successor) {
                    action[state] = candidate_action;
                    break;
                }
            }
            queue[end++] = state;
        }
    }

    if (!protected_value) {
        for (uint32_t compact = 0; compact < SAFE_COUNT; compact++) {
            uint32_t state = expand_state(compact, protected_value);
            if (rank[state] != UINT8_MAX) continue;
            uint32_t successor = custom_transition(state, CUSTOM_MASK);
            if (rank[successor] != UINT8_MAX) {
                rank[state] = rank[successor] + 1;
                action[state] = BASE_ACTIONS;
                queue[end++] = state;
            }
        }
        while (begin < end) {
            uint32_t successor = queue[begin++];
            for (int32_t current_edge = head[successor];
                 current_edge != -1;
                 current_edge = next[current_edge]) {
                uint32_t state = predecessor[current_edge];
                if (rank[state] != UINT8_MAX) continue;
                rank[state] = rank[successor] + 1;
                for (int candidate_action = 0;
                     candidate_action < BASE_ACTIONS;
                     candidate_action++) {
                    if (transition(state, candidate_action) == successor) {
                        action[state] = candidate_action;
                        break;
                    }
                }
                queue[end++] = state;
            }
        }
    }

    FILE *output = fopen(path, "wb");
    if (!output) return 3;
    uint8_t max_rank = 0;
    for (uint32_t compact = 0; compact < SAFE_COUNT; compact++) {
        uint32_t state = expand_state(compact, protected_value);
        if (rank[state] == UINT8_MAX || action[state] == UINT8_MAX) return 4;
        if (rank[state] > 15 || action[state] > 15) return 5;
        if (rank[state] > max_rank) max_rank = rank[state];
        fputc((action[state] << 4) | rank[state], output);
    }
    fclose(output);
    printf(
        "protected=%d states=%u max_rank=%u outer_actions=%d\n",
        protected_value,
        SAFE_COUNT,
        max_rank,
        protected_value ? BASE_ACTIONS : BASE_ACTIONS + 1
    );
    free(head);
    free(next);
    free(predecessor);
    free(queue);
    free(rank);
    free(action);
    return 0;
}

static int verify_one(int protected_value, const char *path) {
    FILE *input = fopen(path, "rb");
    if (!input) return 6;
    uint8_t *certificate = malloc(SAFE_COUNT);
    if (!certificate) return 2;
    if (fread(certificate, 1, SAFE_COUNT, input) != SAFE_COUNT) return 7;
    if (fgetc(input) != EOF) return 8;
    fclose(input);
    for (uint32_t compact = 0; compact < SAFE_COUNT; compact++) {
        uint32_t state = expand_state(compact, protected_value);
        uint8_t packed = certificate[compact];
        uint8_t rank = packed & 15;
        uint8_t action = packed >> 4;
        if (!rank || action >= BASE_ACTIONS + !protected_value) return 9;
        uint32_t successor = transition(state, action);
        if (!!(successor & CENTER_BIT) == protected_value) {
            uint8_t successor_rank = certificate[compact_state(successor)] & 15;
            if (successor_rank + 1 != rank) return 10;
        } else if (rank != 1) {
            return 11;
        }
    }
    free(certificate);
    printf("verified protected=%d states=%u\n", protected_value, SAFE_COUNT);
    return 0;
}

int main(int argc, char **argv) {
    initialize_rows();
    if (argc == 4 && strcmp(argv[1], "generate") == 0) {
        int status = generate_one(1, argv[2]);
        return status ? status : generate_one(0, argv[3]);
    }
    if (argc == 4 && strcmp(argv[1], "verify") == 0) {
        int status = verify_one(1, argv[2]);
        return status ? status : verify_one(0, argv[3]);
    }
    fprintf(stderr, "usage: %s generate|verify LIVE_CERT DEAD_CERT\n", argv[0]);
    return 1;
}
