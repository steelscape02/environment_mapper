#ifndef UART_RECEIVER_H
#define UART_RECEIVER_H
#include "windows.h"

HANDLE open_uart_receiver(const char* device, int baudrate);
int read_uart_receiver(HANDLE hSerial, char* buffer, int buffer_size);

#endif // UART_RECEIVER_H