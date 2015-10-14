#! /usr/bin/env python

import subprocess
import os.path
import sys
import platform

build_tools = os.path.join('.', 'tools', 'waf')
sys.path.append(build_tools)

APPNAME = 'stechec2'
VERSION = '2012'

top = '.'
out = 'build'

def options(opt):
    opt.load('compiler_cxx')
    opt.load('unittest_gtest')
    opt.load('ruby')

    opt.add_option('--enable-debug', action = 'store_true', default = False,
                   help = 'build a debug version', dest = 'debug')
    opt.add_option('--enable-asan', dest='asan', action='store_true',
                   help="Build with GCC's address sanitizer")
    opt.add_option('--enable-gcov', dest='gcov', action='store_true',
                   help='Instrument build to compute code coverage')
    opt.add_option('--enable-werror', action = 'store_true', default = False,
                   help = 'interpret warnings as errors', dest = 'werror')

    opt.recurse('games')
    opt.recurse('tools')

def configure(conf):
    conf.load('compiler_cxx')
    conf.load('unittest_gtest')
    conf.load('ruby')

    # Warning flags
    conf.check_cxx(cxxflags = '-Wall')
    conf.check_cxx(cxxflags = '-Wextra')

    conf.env.append_value('CXXFLAGS', ['-Wall', '-Wextra',
                                       '-Wno-variadic-macros'])

    if 'clang' in conf.env.CXX[0]:
        conf.env.append_value('CXXFLAGS', ['-Wno-return-type-c-linkage'])

    # Check for C++0x
    conf.check_cxx(cxxflags = '-std=c++14')
    conf.env.append_value('CXXFLAGS', '-std=c++14')

    # Debug / Release
    if conf.options.debug:
        conf.check_cxx(cxxflags = '-g')
        conf.env.append_value('DEFINES', '__DEBUG__')
        conf.env.append_value('CXXFLAGS', ['-g'])
        conf.env.append_value('CPPFLAGS', ['-DNDEBUG'])
    else:
        conf.check_cxx(cxxflags = '-O2')
        conf.check_cxx(cxxflags = '-ffast-math')
        conf.env.append_value('CXXFLAGS', ['-O2', '-ffast-math'])

    if conf.options.asan:
        conf.check_cxx(cxxflags='-fsanitize=address',
                       linkflags='-fsanitize=address')
        conf.env.append_value('CXXFLAGS', ['-fsanitize=address'])
        conf.env.append_value('LINKFLAGS', ['-fsanitize=address'])

    if conf.options.gcov:
        conf.check_cxx(cxxflags='-fprofile-arcs -ftest-coverage',
                       linkflags='-fprofile-arcs')
        conf.env.append_value('CXXFLAGS',
                              ['-fprofile-arcs', '-ftest-coverage'])
        conf.env.append_value('LINKFLAGS', ['-fprofile-arcs'])
        conf.find_program('gcovr', var='GCOVR')

    # ZeroMQ and C++ binding (cppzmq)
    conf.check_cfg(package = 'libzmq', uselib_store = 'ZeroMQ',
                   atleast_version = '3.2.0', args = ['--cflags', '--libs'])
    conf.check(header_name='zmq.hpp')

    # Google Flags
    conf.check_cxx(lib = "gflags", mandatory = True, uselib_store = "gflags")

    # Google Flags namespace
    if conf.check_cxx(mandatory=False,
            msg='Checking for gflags namespace',
            fragment='''
               #include <gflags/gflags.h>
               using namespace gflags;
               int main() {}'''):
        conf.env.append_value('CPPFLAGS', '-DGFLAGS_NAMESPACE=gflags')
    else:
        conf.env.append_value('CPPFLAGS', '-DGFLAGS_NAMESPACE=google')

    # Ruby
    conf.check_ruby_version((1, 9))

    # -lrt
    conf.check_cxx(lib = "rt", mandatory = True, uselib_store = "rt")

    # Werror support - at the end to avoid false negatives in the checks
    if conf.options.werror:
        conf.check_cxx(cxxflags = '-Werror')
        conf.env.append_value('CXXFLAGS', '-Werror')

    # Configure games
    conf.recurse('games')

    # Configure tools
    conf.recurse('tools')

def build(bld):
    build_lib(bld)
    build_client(bld)
    build_server(bld)

    bld.recurse('games')
    bld.recurse('tools')

def coverage(ctx):
    """Compute a code coverage report (Gcov)"""
    # For some mysterious reason, "ctx" has no "env" attribute, here, so it's
    # not possible to get the GCOVR environment variable.
    subprocess.check_call(['gcovr',
                           '-r', '..',
                           '--html', '--html-details',
                           '--exclude=.*unittest-gtest.*',
                           '-o', 'gcov-report.html'],
                           cwd=os.path.join(ctx.path.abspath(), out))

def build_lib(bld):
    bld.shlib(
        source = '''
            src/lib/utils/dll.cc
            src/lib/utils/log.cc

            src/lib/net/socket.cc
            src/lib/net/server-socket.cc
            src/lib/net/client-socket.cc
            src/lib/net/message.cc
            src/lib/net/signal.cc

            src/lib/rules/action.cc
            src/lib/rules/actions.cc
            src/lib/rules/game-state.cc
            src/lib/rules/messenger.cc
            src/lib/rules/client-messenger.cc
            src/lib/rules/server-messenger.cc
            src/lib/rules/rules.cc
        ''',
        defines = ['MODULE_COLOR=ANSI_COL_PURPLE', 'MODULE_NAME="lib"'],
        includes = 'src/lib',
        target = 'stechec2',
        use = ['ZeroMQ', 'rt', 'gflags'],
        lib = ([] if platform.system()=='FreeBSD' else ['dl']),
        export_includes = 'src/lib'
    )

    for test in []:
        bld.program(
            features = 'gtest',
            source = 'src/lib/net/tests/test-%s.cc' % test,
            target = 'utils-test-%s' % test,
            use = ['stechec2']
        )

    for test in ['buffer', 'sandbox']:
        bld.program(
            features = 'gtest',
            source = 'src/lib/utils/tests/test-%s.cc' % test,
            target = 'utils-test-%s' % test,
            use = ['stechec2']
        )

    for test in ['action', 'state']:
        bld.program(
            features = 'gtest',
            source = 'src/lib/rules/tests/test-%s.cc' % test,
            target = 'rules-test-%s' % test,
            use = ['stechec2']
        )

def build_client(bld):
    bld.program(
        source = '''
            src/client/main.cc
            src/client/client.cc
        ''',
        target = 'stechec2-client',
        defines = ['MODULE_COLOR=ANSI_COL_YELLOW', 'MODULE_NAME="client"',
            'MODULE_VERSION="%s"' % VERSION],
        use = ['stechec2', 'gflags']
    )

def build_server(bld):
    bld.program(
        source = '''
            src/server/main.cc
            src/server/server.cc
        ''',
        target = 'stechec2-server',
        defines = ['MODULE_COLOR=ANSI_COL_RED', 'MODULE_NAME="server"',
            'MODULE_VERSION="%s"' % VERSION],
        use = ['stechec2', 'gflags']
    )
