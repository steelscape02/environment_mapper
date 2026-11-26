#include "VisualizerConfig.h"
#include "framereceiver.h"
#include "serial_port_win.h"

#include <iostream>
#include <chrono>
#include <thread>

int main() {
    std::cout << "UART Test Program: Version " <<
        EnvMapper_VERSION_MAJOR << "." <<
        EnvMapper_VERSION_MINOR <<
        std::endl;

    SerialPort port("\\\\.\\COM9", 115200);
    FrameReceiver rx;
    uint8_t buf[64];

    for (;;) {
        size_t n = port.read(buf, sizeof(buf));
        for (size_t i = 0; i < n; ++i) {
            
            if (rx.feed(buf[i]) > 0) {
            }
        }
    }
}

