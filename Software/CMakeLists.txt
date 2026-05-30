cmake_minimum_required(VERSION 3.16.0)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(Software)

# Strip flags that cause cross-compiler errors in ESP-IDF 6.0.1:
# -fuse-cxa-atexit is C++-only, IDF passes it to C files
# -Wno-old-style-declaration is C-only, IDF passes it to C++ files
string(REPLACE "-Wno-old-style-declaration" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
string(REPLACE "-fuse-cxa-atexit" "" CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")

# Also add -Wno-error at the end (last flag wins over -Werror)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wno-error")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-error")