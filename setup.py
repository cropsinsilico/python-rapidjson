import os.path
import sys
from skbuild import setup


if sys.version_info < (3, 6):
    raise NotImplementedError("Only Python 3.6+ is supported.")

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))

rj_include_dir = './rapidjson/include'
with_asan = False

for idx, arg in enumerate(sys.argv[:]):
    if arg.startswith('--rj-include-dir='):
        sys.argv.pop(idx)
        rj_include_dir = arg.split('=', 1)[1]
        break
else:
    if not os.path.isdir(os.path.join(ROOT_PATH, 'rapidjson', 'include')):
        raise RuntimeError("RapidJSON sources not found: if you cloned the"
                           " git repository, you should initialize the"
                           " rapidjson submodule as explained in the"
                           " README.rst; in all other cases you may"
                           " want to report the issue.")
for idx, arg in enumerate(sys.argv[:]):
    if arg == '--with-asan':
        sys.argv.pop(idx)
        with_asan = True
        break

other_setup_options = {
    'cmake_install_dir': '.',
    'cmake_args': [],
    'packages': ['rapidjson'],
}
if with_asan:
    other_setup_options['cmake_args'] += [
        '-DYGG_BUILD_ASAN:BOOL=ON',
        '-DYGG_BUILD_UBSAN:BOOL=ON',
    ]
if user_rj:
    other_setup_options['cmake_args'].append(
        f'-DRAPIDJSON_INCLUDE_DIRS={rj_include_dir}'
    )

if os.path.exists('rapidjson_exact_version.txt'):
    with open('rapidjson_exact_version.txt', encoding='utf-8') as f:
        other_setup_options['cmake_args'].append(
            f'-DRAPIDJSON_EXACT_VERSION={f.read().strip()}'
        )


# cxx = sysconfig.get_config_var('CXX')
# print(f"SETUP.PY CXX = {cxx}")
# if cxx and 'g++' in cxx:
#     # Avoid warning about invalid flag for C++
#     for varname in ('CFLAGS', 'OPT'):
#         value = sysconfig.get_config_var(varname)
#         if value and '-Wstrict-prototypes' in value:
#             value = value.replace('-Wstrict-prototypes', '')
#             sysconfig.get_config_vars()[varname] = value

#     # Add -pedantic, so we get a warning when using non-standard features, and
#     # -Wno-long-long to pacify old gcc (or Apple's hybrids) that treat
#     # "long long" as an error under C++ (see issue #69). C++11 is required
#     # since commit
#     # https://github.com/Tencent/rapidjson/commit/9965ab37f6cfae3d58a0a6e34c76112866ace0b1
#     extension_options['extra_compile_args'] = [
#         '-pedantic', '-Wno-long-long', '-std=c++11']

#     # Up to Python 3.7, some structures use "char*" instead of "const char*",
#     # and ISO C++ forbids assigning string literal constants
#     if sys.version_info < (3, 7):
#         extension_options['extra_compile_args'].append('-Wno-write-strings')

setup(
    **other_setup_options
)
