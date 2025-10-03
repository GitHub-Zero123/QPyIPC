cmake_minimum_required(VERSION 3.11)

# Python IPC库 By Zero123
project(PY_IPC LANGUAGES CXX C)

if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
    if(MSVC)
        add_compile_options(/utf-8 /EHsc)
    endif()
endif()

# 默认使用内置nlohmann/json
option(PY_IPC_USE_INTERNAL_NLOHMANN_JSON "Use internal nlohmann/json implementation" ON)
# 是否编译demo程序
option(PY_IPC_BUILD_DEMOS "Build demo programs" OFF)

# 通过link pyipc使用
add_library(pyipc OBJECT src/pyipc.cpp)

if(PY_IPC_USE_INTERNAL_NLOHMANN_JSON)
    target_include_directories(pyipc PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/libs)
endif()

target_include_directories(pyipc PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_features(pyipc PUBLIC cxx_std_20)

if(PY_IPC_BUILD_DEMOS)
    add_subdirectory(demo)
endif()