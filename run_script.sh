set -e

DONT_BUILD=""
WITH_ASAN=""
BUILD_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
	--dont-build )
	    DONT_BUILD="TRUE"
	    shift # past argument with no value
	    ;;
	--with-asan )
	    WITH_ASAN="TRUE"
	    shift # past argument with no value
	    ;;
    esac
done

if [ -n "$WITH_ASAN" ]; then
    export ASAN_OPTIONS=symbolize=1
    export ASAN_SYMBOLIZER_PATH=$(which llvm-symbolizer)
    BUILD_ARGS="${BUILD_ARGS} --config-settings=cmake.define.YGG_BUILD_ASAN:BOOL=ON --config-settings=cmake.define.YGG_BUILD_UBSAN:BOOL=ON"
fi
if [ ! -n "$DONT_BUILD" ]; then
    pip install --config-settings=cmake.define.RAPIDJSON_INCLUDE_DIRS=../rapidjson/include/ \
	$BUILD_ARGS -v -e .
fi

if [ -n "$WITH_ASAN" ]; then
    export DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
fi

python -m pytest -sv tests/ --doctest-glob="docs/*.rst" --doctest-modules docs
# make -C docs doctest -e PYTHON=$(python -c "import sys; import pathlib; print(pathlib.Path(sys.executable).resolve(strict=True))") -e DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
