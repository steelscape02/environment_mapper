#include "coordinate_decoder.h"
using namespace std;

std::optional<Point> decode(const Frame& frame) {
    if (frame.length != 12) return std::nullopt;   // wrong size, reject
    Point p;

    //TODO: Audit for position of x, y, z in the payload. This is assuming they are in order and packed.
    //TODO: Convert payload comps for x and y to azimuth and elevation.
    memcpy(&p.x, &frame.payload[0], 4);
    memcpy(&p.y, &frame.payload[4], 4);
    // x y azimuth elev conv


    memcpy(&p.z, &frame.payload[8], 8);
    return p;
}