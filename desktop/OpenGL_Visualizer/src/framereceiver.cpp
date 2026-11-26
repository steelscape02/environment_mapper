#include "framereceiver.h"
#include "windows.h"
#include <stdio.h>

using namespace std;


bool FrameReceiver::feed(uint8_t byte) {
    // switch (state_) {
    // case State::Sync:
    //     if (byte == SYNC_BYTE) { startFrame(); state_ = State::Length; }
    //     break;
    // case State::Length:
    //     if (!validLength(byte)) { state_ = State::Sync; break; }
    //     beginPayload(byte);
    //     state_ = State::Payload;
    //     break;
    // case State::Payload:
    //     storeByte(byte);
    //     if (payloadDone()) state_ = State::Checksum;
    //     break;
    // case State::Checksum:
    //     state_ = State::Sync;
    //     return checksumOk(byte);
    // }
    // return false;
}