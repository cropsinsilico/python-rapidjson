set -e
export ASAN_OPTIONS=symbolize=1
export ASAN_SYMBOLIZER_PATH=$(which llvm-symbolizer)
pip install --config-settings=cmake.define.RAPIDJSON_INCLUDE_DIRS=../rapidjson/include/ \
    --config-settings=cmake.define.YGG_BUILD_ASAN:BOOL=ON \
    --config-settings=cmake.define.YGG_BUILD_UBSAN:BOOL=ON \
    -v -e .
# export DYLD_INSERT_LIBRARIES=/Users/langmm/mambaforge/envs/pyrj/lib/clang/14.0.6/lib/darwin/libclang_rt.asan_osx_dynamic.dylib
export DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
export PYTHON=$(python -c "import sys; import pathlib; print(pathlib.Path(sys.executable).resolve(strict=True))")
python -m pytest -sv tests/ --doctest-glob="docs/*.rst" --doctest-modules docs
# python -m pytest -svx tests/test_normalizer.py::test_invalid_schema --doctest-glob="docs/*.rst" --doctest-modules docs
# make -C docs doctest -e PYTHON=$(python -c "import sys; import pathlib; print(pathlib.Path(sys.executable).resolve(strict=True))") -e DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
