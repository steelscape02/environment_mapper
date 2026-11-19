#include "uart_receiver.h"
#include "VisualizerConfig.h"
#include "windows.h"
#include <stdio.h>

using namespace std;

HANDLE open_uart_receiver(const char* device, int baudrate) {
    // Open the UART device
    HANDLE hSerial = CreateFileA(device, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hSerial == INVALID_HANDLE_VALUE) {
        printf("Error opening serial port %s\n", device);
        return INVALID_HANDLE_VALUE;
    }

    // Set the parameters for the serial port
    DCB dcbSerialParams = {0};
    dcbSerialParams.DCBlength = sizeof(dcbSerialParams);
    if (!GetCommState(hSerial, &dcbSerialParams)) {
        printf("Error getting serial port state\n");
        CloseHandle(hSerial);
        return INVALID_HANDLE_VALUE;
    }

    dcbSerialParams.BaudRate = baudrate;
    dcbSerialParams.ByteSize = 8;
    dcbSerialParams.StopBits = ONESTOPBIT;
    dcbSerialParams.Parity = NOPARITY;

    if (!SetCommState(hSerial, &dcbSerialParams)) {
        printf("Error setting serial port state\n");
        CloseHandle(hSerial);
        return INVALID_HANDLE_VALUE;
    }

    return hSerial; // Return the handle
}

int read_uart_receiver(HANDLE hSerial, char* buffer, int buffer_size) {
    DWORD bytesRead;
    if (!ReadFile(hSerial, buffer, buffer_size, &bytesRead, NULL)) {
        printf("Error reading from serial port\n");
        return -1;
    }
    return (int)bytesRead; // Return the number of bytes read
}