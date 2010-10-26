#!/usr/bin/env python

import sys, getopt

# keyed by package-name, contains the list of package dependencies
pn = {}

# keyed by package-name, contains the list of dependent packages
rev_pn = {}

show_parent_deps = False

def parse_pn_depends():
	try:
		fh = open('pn-depends.dot')
	except:
		print 'File pn-depends.dot not found'
		print 'Generate the file with bitbake -g <recipe>'
		sys.exit()	

	try:
		raw_lines = fh.read().splitlines()
	finally:
		fh.close()

	for line in raw_lines:
		line = line.rstrip()
		fields = line.split(' ')

		if (len(fields) == 3 and fields[1] == '->'):
			name = fields[0][1:-1]
			depend = fields[2][1:-1]

			if not pn.has_key(name):
				pn[name] = []

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
		tab_str = '\t' * depth

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
		tab_str = '\t' * depth

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


def usage():
	print '\nUsage: %s [options] [package]\n' % (sys.argv[0])
	print 'Displays OE build dependencies for a given package or recipe.'
	print 'Uses the pn-depends.dot file for its raw data.'
	print 'Generate a pn-depends.dot file by running bitbake -g <recipe>.\n'
	print 'Options:'
	print '-h, --help\tShow this help message and exit'
	print '-r, --reverse-deps'
	print '\t\tShow reverse dependencies, i.e. packages dependent on package'
	print '-t, --tree\tTree output instead of default flat output'
	print '-d <depth>, --depth=<depth'
	print '\t\tMaximum depth to follow dependencies, default is infinite'
	print '-s, --show-parent-deps'
	print '\t\tShow child package dependencies that are already listed'
	print '\t\tas direct parent dependencies.\n'
	print "Provide a package name from the generated pn-depends.dot file."
	print 'Run the program without a package name to get a list of'
	print 'available package names.\n'


if __name__ == '__main__':

	parse_pn_depends()
	build_reverse_dependencies()

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hrtd:s', 
						['help', 'reverse-deps', 'tree', 'depth=', 'show-parent-deps'])

	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)


	depth = 1000
	reverse = False
	flat = True

	for o, a in opts:
		if o in ('-h', '--help'):
			usage()
			sys.exit()

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

		else:
			assert False, 'unhandled option'


	if len(args) > 0:
		if reverse:
			if flat:
				list_reverse_deps_flat(args[0], depth)
			else:
				list_reverse_deps(args[0], depth)
		else:
			if flat:
				list_deps_flat(args[0], depth)
			else:
				list_deps(args[0], depth)

	else:
		list_packages()

