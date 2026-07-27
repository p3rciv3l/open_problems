// Exact exhaustive verifier for a 6x6 -> 4x4 -> 2x2 Life pyramid.
#include <algorithm>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr int kNeg = std::numeric_limits<int>::min() / 4;

struct Certificate {
  int total;
  int maximum;
  std::vector<std::vector<std::vector<int>>> layers;
};

Certificate ReadCertificate(const std::string& path) {
  std::ifstream input(path);
  if (!input) throw std::runtime_error("cannot open certificate");
  std::stringstream tokens;
  std::string line;
  while (std::getline(input, line)) {
    tokens << line.substr(0, line.find('#')) << '\n';
  }
  Certificate result;
  std::string word;
  if (!(tokens >> word >> result.total) || word != "total_weight")
    throw std::runtime_error("missing total_weight");
  if (!(tokens >> word >> result.maximum) || word != "maximum_live_weight")
    throw std::runtime_error("missing maximum_live_weight");
  for (int expected : {6, 4, 2}) {
    int width, height;
    if (!(tokens >> word >> width >> height) || word != "layer" ||
        width != expected || height != expected)
      throw std::runtime_error("wrong layer geometry");
    std::vector<std::vector<int>> layer(height, std::vector<int>(width));
    for (auto& row : layer)
      for (int& weight : row)
        if (!(tokens >> weight) || weight < 0)
          throw std::runtime_error("invalid weight");
    result.layers.push_back(std::move(layer));
  }
  if (tokens >> word) throw std::runtime_error("trailing data");
  return result;
}

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

std::vector<std::vector<int>> RowScores(
    const std::vector<std::vector<int>>& weights) {
  const int width = weights.front().size();
  std::vector<std::vector<int>> scores(
      weights.size(), std::vector<int>(1 << width));
  for (int y = 0; y < static_cast<int>(weights.size()); ++y)
    for (int bits = 0; bits < (1 << width); ++bits)
      for (int x = 0; x < width; ++x)
        if ((bits >> x) & 1) scores[y][bits] += weights[y][x];
  return scores;
}

int ExhaustiveMaximum(const Certificate& certificate) {
  const auto score0 = RowScores(certificate.layers[0]);
  const auto score1 = RowScores(certificate.layers[1]);
  const auto score2 = RowScores(certificate.layers[2]);

  // Equal states have identical futures. Keeping only their largest prefix
  // score exhausts all 2^36 initial slices with exact max-plus row DP.
  std::vector<int> short_states(1 << 16, kNeg);
  for (int row0 = 0; row0 < 64; ++row0)
    for (int row1 = 0; row1 < 64; ++row1)
      for (int row2 = 0; row2 < 64; ++row2) {
        const int next0 = LifeRow(row0, row1, row2, 6);
        const int state = row1 | (row2 << 6) | (next0 << 12);
        short_states[state] =
            std::max(short_states[state], score0[0][row0] +
                                                score0[1][row1] +
                                                score0[2][row2] +
                                                score1[0][next0]);
      }

  std::vector<int> states(1 << 20, kNeg);
  for (int state = 0; state < (1 << 16); ++state) {
    if (short_states[state] == kNeg) continue;
    const int row1 = state & 63, row2 = (state >> 6) & 63;
    const int next0 = (state >> 12) & 15;
    for (int row3 = 0; row3 < 64; ++row3) {
      const int next1 = LifeRow(row1, row2, row3, 6);
      const int out = row2 | (row3 << 6) | (next0 << 12) | (next1 << 16);
      states[out] = std::max(states[out], short_states[state] +
                                             score0[3][row3] +
                                             score1[1][next1]);
    }
  }

  std::vector<int> final_states(1 << 20, kNeg);
  for (int state = 0; state < (1 << 20); ++state) {
    if (states[state] == kNeg) continue;
    const int row2 = state & 63, row3 = (state >> 6) & 63;
    const int next0 = (state >> 12) & 15, next1 = (state >> 16) & 15;
    for (int row4 = 0; row4 < 64; ++row4) {
      const int next2 = LifeRow(row2, row3, row4, 6);
      const int last0 = LifeRow(next0, next1, next2, 4);
      const int out = row3 | (row4 << 6) | (next1 << 12) | (next2 << 16);
      final_states[out] =
          std::max(final_states[out], states[state] + score0[4][row4] +
                                          score1[2][next2] + score2[0][last0]);
    }
  }

  int maximum = kNeg;
  for (int state = 0; state < (1 << 20); ++state) {
    if (final_states[state] == kNeg) continue;
    const int row3 = state & 63, row4 = (state >> 6) & 63;
    const int next1 = (state >> 12) & 15, next2 = (state >> 16) & 15;
    for (int row5 = 0; row5 < 64; ++row5) {
      const int next3 = LifeRow(row3, row4, row5, 6);
      const int last1 = LifeRow(next1, next2, next3, 4);
      maximum = std::max(maximum, final_states[state] + score0[5][row5] +
                                      score1[3][next3] + score2[1][last1]);
    }
  }
  return maximum;
}
}  // namespace

int main(int argc, char** argv) {
  try {
    const Certificate certificate =
        ReadCertificate(argc == 2 ? argv[1] : "pyramid_6x6.cert");
    int total = 0;
    for (const auto& layer : certificate.layers)
      for (const auto& row : layer)
        total = std::accumulate(row.begin(), row.end(), total);
    if (total != certificate.total)
      throw std::runtime_error("total does not match weights");
    const int maximum = ExhaustiveMaximum(certificate);
    if (maximum != certificate.maximum)
      throw std::runtime_error("maximum does not match exhaustive DP");
    const int divisor = std::gcd(maximum, total);
    std::cout << "{\"initial_slices\":68719476736,\"maximum_live_weight\":"
              << maximum << ",\"total_weight\":" << total
              << ",\"density_bound\":\"" << maximum / divisor << '/'
              << total / divisor << "\"}\n";
  } catch (const std::exception& error) {
    std::cerr << "verification failed: " << error.what() << '\n';
    return 1;
  }
}
