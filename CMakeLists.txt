cmake_minimum_required(VERSION 3.20)
project(native)

find_package(PkgConfig)

include(CheckSymbolExists)

pkg_check_modules(AVFORMAT REQUIRED IMPORTED_TARGET libavformat)
pkg_check_modules(AVFILTER REQUIRED IMPORTED_TARGET libavfilter)
pkg_check_modules(AVUTIL REQUIRED IMPORTED_TARGET libavutil)
pkg_check_modules(AVCODEC REQUIRED IMPORTED_TARGET libavcodec)

add_library(native SHARED
    yttl/audio_decode.c
)

target_link_libraries(native PUBLIC
    PkgConfig::AVFORMAT
    PkgConfig::AVFILTER
    PkgConfig::AVUTIL
    PkgConfig::AVCODEC
)

check_symbol_exists(asprintf "stdio.h" have_asprintf)
if (${have_asprintf})
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DHAVE_ASPRINTF=1")
endif()

install(
    TARGETS native
    LIBRARY DESTINATION ${SKBUILD_PLATLIB_DIR}/yttl
    RUNTIME DESTINATION ${SKBUILD_PLATLIB_DIR}/yttl
    ARCHIVE DESTINATION ${SKBUILD_PLATLIB_DIR}/yttl
    FRAMEWORK DESTINATION ${SKBUILD_PLATLIB_DIR}/yttl
    RESOURCE DESTINATION ${SKBUILD_PLATLIB_DIR}/yttl
)
# Temporary fix for https://github.com/scikit-build/scikit-build-core/issues/374
install(
    TARGETS native
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/yttl
    RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/yttl
    ARCHIVE DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/yttl
    FRAMEWORK DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/yttl
    RESOURCE DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/yttl
)
install(
    FILES $<TARGET_RUNTIME_DLLS:native>
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/yttl
)
