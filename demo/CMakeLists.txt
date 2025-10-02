cmake_minimum_required(VERSION 3.15)

project(ROOT LANGUAGES CXX C)

if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
    option(MSVC_MT_MODE "Use /MT for MSVC release mode" OFF)
    if(MSVC)
        add_compile_options(/utf-8 /EHsc)
        # 若启用MSVC_MT_MODE release模式将使用/MT
        if(MSVC_MT_MODE)
            set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Release>:>")
        endif()
    endif()
endif()