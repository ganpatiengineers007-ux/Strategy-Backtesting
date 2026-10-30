#include "svl/rolling_stats.hpp"
#include <cassert>
#include <cmath>

int main() {
    auto r = svl::rolling_mean({1, 2, 3, 4, 5}, 3);  // parity: Python reference ke saath same
    assert(std::isnan(r[0]) && std::isnan(r[1]));
    assert(std::fabs(r[2] - 2.0) < 1e-12 && std::fabs(r[3] - 3.0) < 1e-12 && std::fabs(r[4] - 4.0) < 1e-12);
    return 0;
}
