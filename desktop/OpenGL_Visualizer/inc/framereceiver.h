#pragma once
#include <cstdint>
#include <cstddef>

struct Frame {
    uint8_t payload[32];
    uint8_t length = 0;
};

class FrameReceiver {
public:
    bool feed(uint8_t byte);
    const Frame& frame() const { return frame_; }
private:
    enum class State { Sync, Length, Payload, Checksum } state_ = State::Sync;
    Frame frame_;
    uint8_t idx_ = 0;
    uint8_t running_sum_ = 0;
};