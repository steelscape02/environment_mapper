#pragma once
#include "framereceiver.h"
#include <optional>
#include "point.h"

std::optional<Point> decode(const Frame& frame);