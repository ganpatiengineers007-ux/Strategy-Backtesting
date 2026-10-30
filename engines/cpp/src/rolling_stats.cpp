#include "svl/rolling_stats.hpp"
#include <limits>

namespace svl {
std::vector<double> rolling_mean(const std::vector<double>& v, std::size_t window) {
    std::vector<double> out(v.size(), std::numeric_limits<double>::quiet_NaN());
    if (window == 0) return out;
    double sum = 0.0;
    for (std::size_t i = 0; i < v.size(); ++i) {
        sum += v[i];
        if (i >= window) sum -= v[i - window];
        if (i + 1 >= window) out[i] = sum / static_cast<double>(window);
    }
    return out;
}
}
