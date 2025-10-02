cmake_minimum_required(VERSION 3.15)

project(ROOT LANGUAGES CXX C)

if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
    if(MSVC)
        add_compile_options(/utf-8 /EHsc)
        set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Release>:>")
    endif()
endif()

add_executable(winApi main.cpp)
target_compile_features(winApi PRIVATE cxx_std_20)
# 链接 pyipc对象库
target_link_libraries(winApi PRIVATE pyipc)