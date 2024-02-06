cmake_minimum_required(VERSION 3.16)
set(YGGDRASIL_REQUIRE_SKBUILD ON)
set(CMAKE_VERBOSE_MAKEFILE ON)
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/ygg_options.cmake)

if (NOT DEFAULT_RAPIDJSON_INCLUDE_DIRS)
  cmake_path(APPEND CMAKE_CURRENT_SOURCE_DIR rapidjson include
             OUTPUT_VARIABLE DEFAULT_RAPIDJSON_INCLUDE_DIRS)
endif()

find_package(
  ${PYTHON_PREFIX} COMPONENTS
  Interpreter Development.Module NumPy REQUIRED)
if (${PYTHON_PREFIX}_VERSION VERSION_LESS "3.7.0")
  message(FATAL_ERROR "Only Python 3.7+ is supported.")
endif()

if (PYTHON_PREFIX STREQUAL "Python")
  Python_add_library(rapidjson MODULE rapidjson.cpp)
else()
  Python3_add_library(rapidjson MODULE rapidjson.cpp)
endif()

target_include_directories(rapidjson PUBLIC ${RAPIDJSON_INCLUDE_DIRS})
target_link_libraries(rapidjson PUBLIC ${PYTHON_PREFIX}::NumPy)

target_compile_options(
  rapidjson PUBLIC
  -DRAPIDJSON_YGGDRASIL
  -DRAPIDJSON_YGGDRASIL_PYTHON
  -DRAPIDJSON_HAS_STDSTRING
  -DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION
  -D_USE_MATH_DEFINES)
if (RAPIDJSON_EXACT_VERSION)
  target_compile_options(
    rapidjson PUBLIC
    "-DRAPIDJSON_EXACT_VERSION=${RAPIDJSON_EXACT_VERSION}")
endif()
if (ASAN_COMPILE_FLAGS)
  target_compile_options(rapidjson PUBLIC ${ASAN_COMPILE_FLAGS})
endif()
if (ASAN_LINK_FLAGS)
  target_link_options(rapidjson PUBLIC ${ASAN_LINK_FLAGS})
endif()

if (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  # Avoid warning about invalid flag for C++
  string(REPLACE "-Wstrict-prototypes" ""
         CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
  string(REPLACE "-Wstrict-prototypes" ""
         CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")

  # Ignore warnings about missing members in PyTypeObject objects
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-missing-field-initializers")

  # Add -pedantic, so we get a warning when using non-standard features, and
  # -Wno-long-long to pacify old gcc (or Apple's hybrids) that treat
  # "long long" as an error under C++ (see issue #69). C++11 is required
  # since commit
  # https://github.com/Tencent/rapidjson/commit/9965ab37f6cfae3d58a0a6e34c76112866ace0b1
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pedantic -Wno-long-long") # -std=c++11
  # Up to Python 3.7, some structures use "char*" instead of "const char*",
  # and ISO C++ forbids assigning string literal constants
  if (${PYTHON_PREFIX}_VERSION VERSION_LESS "3.7.0")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-write-strings")
  endif()
endif()

# Exact version file
cmake_path(APPEND ${CMAKE_CURRENT_SOURCE_DIR} rapidjson_exact_version.txt
           OUTPUT_VARIABLE RAPIDJSON_EXACT_VERSION_FILE)
if (EXISTS RAPIDJSON_EXACT_VERSION_FILE)
  file(READ ${RAPIDJSON_EXACT_VERSION_FILE} RAPIDJSON_EXACT_VERSION)
  string(STRIP ${RAPIDJSON_EXACT_VERSION} RAPIDJSON_EXACT_VERSION)
  target_compile_options(
    rapidjson PUBLIC
    "-DRAPIDJSON_EXACT_VERSION=${RAPIDJSON_EXACT_VERSION}")
endif()

if (NOT ${PYTHON_PREFIX}_INSTALL_DIR)
  set(${PYTHON_PREFIX}_INSTALL_DIR ".")
endif()

install(TARGETS rapidjson
        LIBRARY DESTINATION ${${PYTHON_PREFIX}_INSTALL_DIR}
	RUNTIME DESTINATION ${${PYTHON_PREFIX}_INSTALL_DIR})
