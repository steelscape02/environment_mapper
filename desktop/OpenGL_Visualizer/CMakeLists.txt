cmake_minimum_required(VERSION 3.25)
project(EnvMapper VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF) 

configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/VisualizerConfig.h.in"
    "${CMAKE_CURRENT_BINARY_DIR}/VisualizerConfig.h"
)
add_executable(EnvMapper
    src/main.cpp
    src/framereceiver.cpp
    src/serial_port_win.cpp
)

target_compile_features(EnvMapper PRIVATE cxx_std_23)

target_include_directories(EnvMapper PRIVATE
    "${PROJECT_SOURCE_DIR}/inc"
    "${PROJECT_BINARY_DIR}"
)