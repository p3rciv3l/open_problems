// Exact exhaustive verifier for the 6x10 -> 4x8 -> 2x6 certificate.
#include <algorithm>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
constexpr long long kNeg = std::numeric_limits<long long>::min() / 4;
struct Certificate {
  long long total;
  long long maximum;
  std::vector<std::vector<std::vector<long long>>> layers;
};

Certificate ReadCertificate(const std::string& path) {
  std::ifstream input(path);
  if (!input) throw std::runtime_error("cannot open certificate");
  std::stringstream tokens;
  std::string line;
  while (std::getline(input, line))
    tokens << line.substr(0, line.find('#')) << '\n';
  Certificate result;
  std::string word;
  if (!(tokens >> word >> result.total) || word != "total_weight")
    throw std::runtime_error("missing total_weight");
  if (!(tokens >> word >> result.maximum) || word != "maximum_live_weight")
    throw std::runtime_error("missing maximum_live_weight");
  for (const auto& [width, height] :
       {std::pair{6, 10}, std::pair{4, 8}, std::pair{2, 6}}) {
    int actual_width, actual_height;
    if (!(tokens >> word >> actual_width >> actual_height) || word != "layer" ||
        actual_width != width || actual_height != height)
      throw std::runtime_error("wrong layer geometry");
    std::vector<std::vector<long long>> layer(
        height, std::vector<long long>(width));
    for (auto& row : layer)
      for (long long& weight : row)
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

std::vector<std::vector<long long>> RowScores(
    const std::vector<std::vector<long long>>& weights) {
  const int width = weights.front().size();
  std::vector<std::vector<long long>> scores(
      weights.size(), std::vector<long long>(1 << width));
  for (int y = 0; y < static_cast<int>(weights.size()); ++y)
    for (int bits = 0; bits < (1 << width); ++bits)
      for (int x = 0; x < width; ++x)
        if ((bits >> x) & 1) scores[y][bits] += weights[y][x];
  return scores;
}

void Advance(const std::vector<long long>& source,
             std::vector<long long>& target,
             const std::vector<std::vector<long long>>& score0,
             const std::vector<std::vector<long long>>& score1,
             const std::vector<std::vector<long long>>& score2,
             int input_row) {
  std::fill(target.begin(), target.end(), kNeg);
  for (int state = 0; state < (1 << 20); ++state) {
    if (source[state] == kNeg) continue;
    const int old0 = state & 63, old1 = (state >> 6) & 63;
    const int next0 = (state >> 12) & 15, next1 = (state >> 16) & 15;
    for (int row = 0; row < 64; ++row) {
      const int next2 = LifeRow(old0, old1, row, 6);
      const int last = LifeRow(next0, next1, next2, 4);
      const int out = old1 | (row << 6) | (next1 << 12) | (next2 << 16);
      target[out] =
          std::max(target[out], source[state] + score0[input_row][row] +
                                       score1[input_row - 2][next2] +
                                       score2[input_row - 4][last]);
    }
  }
}

long long ExhaustiveMaximum(const Certificate& certificate) {
  const auto score0 = RowScores(certificate.layers[0]);
  const auto score1 = RowScores(certificate.layers[1]);
  const auto score2 = RowScores(certificate.layers[2]);
  std::vector<long long> short_states(1 << 16, kNeg);
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
  std::vector<long long> states(1 << 20, kNeg), scratch(1 << 20, kNeg);
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
  for (int row = 4; row < 10; ++row) {
    Advance(states, scratch, score0, score1, score2, row);
    states.swap(scratch);
  }
  return *std::max_element(states.begin(), states.end());
}
}  // namespace

int main(int argc, char** argv) {
  try {
    const Certificate certificate =
        ReadCertificate(argc == 2 ? argv[1] : "pyramid_6x10.cert");
    long long total = 0;
    for (const auto& layer : certificate.layers)
      for (const auto& row : layer)
        total = std::accumulate(row.begin(), row.end(), total);
    if (total != certificate.total)
      throw std::runtime_error("total does not match weights");
    const long long maximum = ExhaustiveMaximum(certificate);
    if (maximum != certificate.maximum)
      throw std::runtime_error("maximum does not match exhaustive DP");
    const long long divisor = std::gcd(maximum, total);
    std::cout << "{\"initial_slices\":1152921504606846976,"
              << "\"maximum_live_weight\":" << maximum
              << ",\"total_weight\":" << total << ",\"density_bound\":\""
              << maximum / divisor << '/' << total / divisor << "\"}\n";
  } catch (const std::exception& error) {
    std::cerr << "verification failed: " << error.what() << '\n';
    return 1;
  }
}
