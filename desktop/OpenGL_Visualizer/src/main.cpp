using namespace std;

#include "VisualizerConfig.h"
#include "uart_receiver.h"
#include <iostream>
#include <chrono>
#include <thread>

int main() {
    cout << "UART Test Program: Version " << EnvMapper_VERSION_MAJOR << "." << EnvMapper_VERSION_MINOR << endl;

    HANDLE hSerial = open_uart_receiver("COM9", 115200);
    if (hSerial == INVALID_HANDLE_VALUE) {
        cout << "Error opening UART receiver" << endl;
        return -1;
    }

    //wait for 5 seconds before reading
    this_thread::sleep_for(chrono::seconds(5));

    char buffer[1024];
    int bytes_read = read_uart_receiver(hSerial, buffer, sizeof(buffer));
    if (bytes_read > 0) {
        cout << "Received " << bytes_read << " bytes: " << buffer << endl;
    }

    return 0;
}

