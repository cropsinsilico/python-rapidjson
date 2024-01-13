set -e
export ASAN_OPTIONS=symbolize=1
export ASAN_SYMBOLIZER_PATH=$(which llvm-symbolizer)
pip install --config-settings=cmake.define.RAPIDJSON_INCLUDE_DIRS=../rapidjson/include/ \
    --config-settings=cmake.define.YGG_BUILD_ASAN:BOOL=ON \
    --config-settings=cmake.define.YGG_BUILD_UBSAN:BOOL=ON \
    -v -e .
# export DYLD_INSERT_LIBRARIES=/Users/langmm/mambaforge/envs/pyrj/lib/clang/14.0.6/lib/darwin/libclang_rt.asan_osx_dynamic.dylib
export DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
python -m pytest -svx tests/
make -C docs doctest -e PYTHON=$(which python3) -e DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
