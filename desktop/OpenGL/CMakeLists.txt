cmake_minimum_required(VERSION 3.15)
project(Point Visualizer VERSION 1.0)

# Require C++17 or higher for std::thread and modern primitives
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add your executable and include serialib files directly
add_executable(point_visualizer
    src/main.cpp
    src/serialib.cpp
)

# Tell CMake where to look for header files
target_include_directories(point_visualizer PRIVATE src)