#!/usr/bin/env python

import sys, getopt, re

# keyed by package-name, contains the list of package dependencies
pn = {}

# keyed by package-name, contains the list of dependent packages
rev_pn = {}

show_parent_deps = False
show_verbose_messages = False

indent_str = '\t'

def parse_pn_depends(depends_file):
    try:
        fh = open(depends_file)
    except:
        print 'File %s not found' % depends_file
        print 'Generate the file with bitbake -g <recipe>'
        sys.exit()

    try:
        raw_lines = fh.read().splitlines()
    finally:
        fh.close()

    for line in raw_lines:
        line = line.rstrip()
        fields = line.split(' ')

        if len(fields) < 3 or fields[1] != '->':
            continue

        if len(fields) == 3:
            name = fields[0][1:-1]
            depend = fields[2][1:-1]

            if not pn.has_key(name):
                pn[name] = []

            pn[name].append(depend)

        elif len(fields) == 4:
            if fields[0] == fields[2]:
                continue

            name = fields[0][1:-1]
            depend = fields[2][1:-1]

            if pn.has_key(depend) and name in pn[depend]:
                if show_verbose_messages:
                    print '\n*** Found loop dependency'
                    print '\t', name, '->', depend
                    print '\t', depend, '->', name, '\n'

                continue

            if not pn.has_key(name):
                pn[name] = []
                pn[name].append(depend)
            elif not depend in pn[name]:
                pn[name].append(depend)


def build_reverse_dependencies():
    for key in pn:
        for name in pn[key]:
            if not rev_pn.has_key(name):
                rev_pn[name] = []

            rev_pn[name].append(key)


def list_packages():
    for key in sorted(pn):
        print key

    print '\n',


def list_deps_recurse(package, parent_deps, depth, max_depth):
    if depth > max_depth:
        return;

    if pn.has_key(package):
        tab_str = indent_str * depth

        for dep in sorted(pn[package]):
            if show_parent_deps or dep not in parent_deps:
                print tab_str, dep
                list_deps_recurse(dep, pn[package], depth + 1, max_depth)


def list_deps(package, max_depth):
    if pn.has_key(package):
        print '\nPackage [', package, '] depends on'
        list_deps_recurse(package, (), 1, max_depth)

    elif rev_pn.has_key(package):
        print 'Package [', package, '] has no dependencies'

    else:
        print 'Package [', package, '] not found'

    print '\n',


def list_reverse_deps_recurse(package, depth, max_depth):
    if depth > max_depth:
        return;

    if rev_pn.has_key(package):
        tab_str = indent_str * depth

        for dep in sorted(rev_pn[package]):
            print tab_str, dep
            list_reverse_deps_recurse(dep, depth + 1, max_depth)


def list_reverse_deps(package, max_depth):
    if rev_pn.has_key(package):
        print '\nPackage [', package, '] is needed by'
        list_reverse_deps_recurse(package, 1, max_depth)

    elif pn.has_key(package):
        print 'No package depends on [', package, ']'

    else:
        print 'Package [', package, '] not found'

    print '\n',


def collect_deps_flat(src, d, package, depth, max_depth):
    if depth > max_depth:
        return;

    if src.has_key(package):
        for dep in src[package]:
            if dep not in d:
                d.append(dep)
                collect_deps_flat(src, d, dep, depth + 1, max_depth)


def list_deps_flat(package, max_depth):
    d = []

    if pn.has_key(package):
        for dep in pn[package]:
            if dep not in d:
                d.append(dep)
                collect_deps_flat(pn, d, dep, 2, max_depth)

        print '\nPackage [', package, '] depends on'
        for dep in sorted(d):
            print '\t', dep

    elif rev_pn.has_key(package):
        print 'Package [', package, '] has no dependencies'

    else:
        print 'Package [', package, '] not found'

    print '\n',


def list_reverse_deps_flat(package, max_depth):
    d = []

    if rev_pn.has_key(package):
        for dep in rev_pn[package]:
            if dep not in d:
                d.append(dep)
                collect_deps_flat(rev_pn, d, dep, 2, max_depth)

        print '\nPackage [', package, '] is needed by'
        for dep in sorted(d):
            print '\t', dep

    elif pn.has_key(package):
        print 'No package depends on [', package, ']'

    else:
        print 'Package [', package, '] not found'

    print '\n',


def package_glob(package):
    if '?' not in package and '*' not in package:
        return [package]

    packages = set()
    for pkg, deps in pn.iteritems():
        packages.add(pkg)
        for dep in deps:
            packages.add(dep)
    for pkg, rdeps in rev_pn.iteritems():
        packages.add(pkg)
        for rdep in rdeps:
            packages.add(rdep)

    package = re.compile(package.replace('.', '\.')\
                                .replace('?', '.')\
                                .replace('*', '.*'))
    matches = []
    for pkg in packages:
        match = package.match(pkg)
        if match and match.group(0) == pkg:
            matches.append(pkg)

    return matches


def usage():
    print '\nUsage: %s [options] [package]\n' % (sys.argv[0])
    print 'Displays OE build dependencies for a given package or recipe.'
    print 'Uses the pn-depends.dot file for its raw data.'
    print 'Generate a pn-depends.dot file by running bitbake -g <recipe>.\n'
    print 'Options:'
    print '-h, --help\tShow this help message and exit'
    print '-v, --verbose\tShow error messages such as recursive dependencies'
    print '-r, --reverse-deps'
    print '\t\tShow reverse dependencies, i.e. packages dependent on package'
    print '-t, --tree\tTree output instead of default flat output'
    print '-d <depth>, --depth=<depth'
    print '\t\tMaximum depth to follow dependencies, default is infinite'
    print '-s, --show-parent-deps'
    print '\t\tShow child package dependencies that are already listed'
    print '\t\tas direct parent dependencies.'
    print '-f <file>, --file=<file>'
    print '\t\tUse the dependencies from a different file. Useful for comparing'
    print '\t\tthe pn-depends.dot files from multiple `bitbake -g` runs.\n'
    print "Provide a package name from the generated pn-depends.dot file."
    print "You can use wildcards: ? = any character, * = any string."
    print 'Run the program without a package name to get a list of'
    print 'available package names.\n'


if __name__ == '__main__':

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvrtd:sf:',
                        ['help', 'verbose', 'reverse-deps', 'tree', 'depth=',
                         'show-parent-deps', 'file='])

    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)


    depth = 1000
    reverse = False
    flat = True
    depends_file = 'pn-depends.dot'

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()

        elif o in ('-v', '--verbose'):
            show_verbose_messages = True

        elif o in ('-r', '--reverse-deps'):
            reverse = True

        elif o in ('-t', '--tree'):
            flat = False

        elif o in ('-s', '--show-parent-deps'):
            show_parent_deps = True

        elif o in ('-d', '--depth'):
            try:
                depth = int(a, 10)
            except ValueError:
                print 'Bad depth argument: ', a
                usage()
                sys.exit(1)

        elif o in ('-f', '--file'):
            depends_file = a

        else:
            assert False, 'unhandled option'


    parse_pn_depends(depends_file)
    build_reverse_dependencies()

    if len(args) > 0:
        pkgs = package_glob(args[0])
    else:
        list_packages()
        sys.exit()

    if len(pkgs) == 1:
        if reverse:
            if flat:
                list_reverse_deps_flat(pkgs[0], depth)
            else:
                list_reverse_deps(pkgs[0], depth)
        else:
            if flat:
                list_deps_flat(pkgs[0], depth)
            else:
                list_deps(pkgs[0], depth)
    elif len(pkgs) > 1:
        for pkg in sorted(pkgs):
            print pkg
        print
    else:
        print 'No package found matching [', args[0], ']'

