#include <iostream>
#include "serial_port_win.h"

SerialPort::SerialPort(const char* name, DWORD baud) {
    h_ = CreateFileA(name, GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                     OPEN_EXISTING, 0, nullptr);       // e.g. "\\\\.\\COM3"
    SetupComm(h_, 4096, 4096);                         // driver buffer sizes

    DCB dcb{}; dcb.DCBlength = sizeof(dcb);
    GetCommState(h_, &dcb);
    dcb.BaudRate = baud; dcb.ByteSize = 8;
    dcb.Parity = NOPARITY; dcb.StopBits = ONESTOPBIT;
    SetCommState(h_, &dcb);

    COMMTIMEOUTS t{}; t.ReadIntervalTimeout = 50;
    t.ReadTotalTimeoutConstant = 50;
    SetCommTimeouts(h_, &t);
}

SerialPort::~SerialPort() {
    if (h_ != INVALID_HANDLE_VALUE) CloseHandle(h_);
}

size_t SerialPort::read(uint8_t* buf, size_t max) {
    DWORD bytes_read = 0;
    std::cout << "current buffer: " << buf << std::endl;
    ReadFile(h_, buf, (DWORD)max, &bytes_read, nullptr);
    return (size_t)bytes_read;
}