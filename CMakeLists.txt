cmake_minimum_required(VERSION 3.16)
set(YGGDRASIL_REQUIRE_SKBUILD ON)
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/ygg_options.cmake)

if (NOT RAPIDJSON_INCLUDE_DIRS)
  cmake_path(APPEND CMAKE_CURRENT_SOURCE_DIR rapidjson include
             OUTPUT_VARIABLE RAPIDJSON_INCLUDE_DIRS)
endif()

find_package(Python3 COMPONENTS Interpreter Development.Module NumPy REQUIRED)

Python3_add_library(
  rapidjson MODULE rapidjson.cpp)
target_include_directories(
  rapidjson PUBLIC ${RAPIDJSON_INCLUDE_DIRS})
target_link_libraries(
  rapidjson PUBLIC Python3::NumPy)

target_compile_options(
  rapidjson PUBLIC
  -DRAPIDJSON_YGGDRASIL
  -DRAPIDJSON_YGGDRASIL_PYTHON
  -DRAPIDJSON_HAS_STDSTRING
  -DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION
  -D_USE_MATH_DEFINES)
if (ASAN_COMPILE_FLAGS)
  target_compile_options(rapidjson PUBLIC ${ASAN_COMPILE_FLAGS})
endif()
if (ASAN_LINK_FLAGS)
  target_link_options(rapidjson PUBLIC ${ASAN_LINK_FLAGS})
endif()

if (NOT Python_INSTALL_DIR)
  set(Python_INSTALL_DIR ".")
endif()

install(TARGETS rapidjson
        LIBRARY DESTINATION ${Python_INSTALL_DIR}
	RUNTIME DESTINATION ${Python_INSTALL_DIR})
