#pragma once
#include <cstddef>
#include <vector>

namespace svl {
// Pehle (window-1) entries NaN; baaki rolling mean.
std::vector<double> rolling_mean(const std::vector<double>& values, std::size_t window);
}
