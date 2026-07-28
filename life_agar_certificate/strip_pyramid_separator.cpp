// Exact max-weight separator for 6xH -> 4x(H-2) -> 2x(H-4), 5 <= H <= 20.
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace {
constexpr long long kNeg = std::numeric_limits<long long>::min() / 4;

int LifeRow(int above, int middle, int below, int width) {
  int output = 0;
  for (int x = 1; x < width - 1; ++x) {
    const int center = (middle >> x) & 1;
    int neighbors = 0;
    for (int dx = -1; dx <= 1; ++dx) {
      neighbors += (above >> (x + dx)) & 1;
      neighbors += (middle >> (x + dx)) & 1;
      neighbors += (below >> (x + dx)) & 1;
    }
    neighbors -= center;
    if (neighbors == 3 || (center && neighbors == 2))
      output |= 1 << (x - 1);
  }
  return output;
}

std::string Decimal(unsigned __int128 value) {
  if (value == 0) return "0";
  std::string result;
  while (value) {
    result.push_back('0' + value % 10);
    value /= 10;
  }
  std::reverse(result.begin(), result.end());
  return result;
}
}  // namespace

int main(int argc, char** argv) {
  if (argc < 3) return 2;
  const int height = std::stoi(argv[1]);
  const int first_count = 3 * ((height + 1) / 2);
  const int second_count = 2 * ((height - 1) / 2);
  const int orbit_count = first_count + second_count + (height - 3) / 2;
  if (height < 5 || height > 20 || argc != orbit_count + 2) return 2;
  std::vector<long long> weights(orbit_count);
  for (int index = 0; index < orbit_count; ++index)
    weights[index] = std::stoll(argv[index + 2]);
  const auto orbit = [&](int layer, int x, int y) {
    if (layer == 0)
      return std::min(x, 5 - x) + 3 * std::min(y, height - 1 - y);
    if (layer == 1)
      return first_count + std::min(x, 3 - x) +
             2 * std::min(y, height - 3 - y);
    return first_count + second_count + std::min(y, height - 5 - y);
  };

  std::vector<std::vector<long long>> score0(
      height, std::vector<long long>(64));
  std::vector<std::vector<long long>> score1(
      height - 2, std::vector<long long>(16));
  std::vector<std::vector<long long>> score2(
      height - 4, std::vector<long long>(4));
  for (int y = 0; y < height; ++y)
    for (int bits = 0; bits < 64; ++bits)
      for (int x = 0; x < 6; ++x)
        if ((bits >> x) & 1) score0[y][bits] += weights[orbit(0, x, y)];
  for (int y = 0; y < height - 2; ++y)
    for (int bits = 0; bits < 16; ++bits)
      for (int x = 0; x < 4; ++x)
        if ((bits >> x) & 1) score1[y][bits] += weights[orbit(1, x, y)];
  for (int y = 0; y < height - 4; ++y)
    for (int bits = 0; bits < 4; ++bits)
      for (int x = 0; x < 2; ++x)
        if ((bits >> x) & 1) score2[y][bits] += weights[orbit(2, x, y)];

  std::vector<long long> short_scores(1 << 16, kNeg);
  std::vector<unsigned __int128> short_paths(1 << 16);
  for (int row0 = 0; row0 < 64; ++row0)
    for (int row1 = 0; row1 < 64; ++row1)
      for (int row2 = 0; row2 < 64; ++row2) {
        const int next0 = LifeRow(row0, row1, row2, 6);
        const int state = row1 | (row2 << 6) | (next0 << 12);
        const long long score = score0[0][row0] + score0[1][row1] +
                                score0[2][row2] + score1[0][next0];
        if (score > short_scores[state]) {
          short_scores[state] = score;
          short_paths[state] =
              row0 | (static_cast<unsigned __int128>(row1) << 6) |
              (static_cast<unsigned __int128>(row2) << 12);
        }
      }

  std::vector<long long> scores(1 << 20, kNeg), next_scores(1 << 20, kNeg);
  std::vector<unsigned __int128> paths(1 << 20), next_paths(1 << 20);
  for (int state = 0; state < (1 << 16); ++state) {
    if (short_scores[state] == kNeg) continue;
    const int row1 = state & 63, row2 = (state >> 6) & 63;
    const int next0 = (state >> 12) & 15;
    for (int row3 = 0; row3 < 64; ++row3) {
      const int next1 = LifeRow(row1, row2, row3, 6);
      const int out = row2 | (row3 << 6) | (next0 << 12) | (next1 << 16);
      const long long score =
          short_scores[state] + score0[3][row3] + score1[1][next1];
      if (score > scores[out]) {
        scores[out] = score;
        paths[out] =
            short_paths[state] | (static_cast<unsigned __int128>(row3) << 18);
      }
    }
  }

  for (int y = 4; y < height; ++y) {
    std::fill(next_scores.begin(), next_scores.end(), kNeg);
    for (int state = 0; state < (1 << 20); ++state) {
      if (scores[state] == kNeg) continue;
      const int old0 = state & 63, old1 = (state >> 6) & 63;
      const int next0 = (state >> 12) & 15, next1 = (state >> 16) & 15;
      for (int row = 0; row < 64; ++row) {
        const int next2 = LifeRow(old0, old1, row, 6);
        const int last = LifeRow(next0, next1, next2, 4);
        const int out = old1 | (row << 6) | (next1 << 12) | (next2 << 16);
        const long long score = scores[state] + score0[y][row] +
                                score1[y - 2][next2] + score2[y - 4][last];
        if (score > next_scores[out]) {
          next_scores[out] = score;
          next_paths[out] =
              paths[state] | (static_cast<unsigned __int128>(row) << (6 * y));
        }
      }
    }
    scores.swap(next_scores);
    paths.swap(next_paths);
  }
  const auto best = std::max_element(scores.begin(), scores.end());
  const int state = best - scores.begin();
  std::cout << *best << ' ' << Decimal(paths[state]) << '\n';
}
