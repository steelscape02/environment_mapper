// serial_port_win.h / .cpp: all the Windows-specific code lives here
#include <windows.h>
#include <cstdint>
#pragma once

class SerialPort {
public:
    explicit SerialPort(const char* name, DWORD baud);  // opens + configures once
    ~SerialPort();                                       // CloseHandle
    size_t read(uint8_t* buf, size_t max);               // wraps ReadFile
private:
    HANDLE h_ = INVALID_HANDLE_VALUE;
};