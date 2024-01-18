set -e
# export ASAN_OPTIONS=symbolize=1
# export ASAN_SYMBOLIZER_PATH=$(which llvm-symbolizer)
python setup.py develop --rj-include-dir=../rapidjson/include/ # --with-asan
## export DYLD_INSERT_LIBRARIES=/Users/langmm/mambaforge/envs/pyrj/lib/clang/14.0.6/lib/darwin/libclang_rt.asan_osx_dynamic.dylib
# export DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
python -m pytest -sv tests/
# make -C docs doctest -e PYTHON=$(which python3) -e DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
