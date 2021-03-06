import sys
import os
import re
import javalang
import logging
import traceback
import itertools

global found_parent

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0


re_string = re.escape("\"") + '.*?' + re.escape("\"")


def getFunctions(filestring, comment_inline_pattern=".*?$"):

    method_string = []
    method_pos = []
    method_name = []

    global found_parent
    found_parent = []

    tree = None

    try:
        tree = javalang.parse.parse(filestring)
        package = tree.package
        if package is None:
            package = 'DefaultPackage'
        else:
            package = package.name
            # print package,'####'
    except Exception as e:
        # logging.warning('Traceback:' + traceback.print_exc())
        return (None, None, [])

    file_string_split = filestring.split('\n')
    # print(file_string_split)
    nodes = itertools.chain(tree.filter(
        javalang.tree.ConstructorDeclaration), tree.filter(javalang.tree.MethodDeclaration))

    for path, node in nodes:
        # print(type(node))
        # print '---------------------------------------'
        name = '.'+node.name
        for i, var in enumerate(reversed(path)):
            # print var, i, len(path)-3
            if isinstance(var, javalang.tree.ClassDeclaration):
                # print 'One Up:',var,var.name
                if len(path)-3 == i:  # Top most
                    name = '.'+var.name+check_repetition(var, var.name)+name
                else:
                    name = '$'+var.name+check_repetition(var, var.name)+name
            if isinstance(var, javalang.tree.ClassCreator):
                # print 'One Up:',var,var.type.name
                name = '$'+var.type.name + \
                    check_repetition(var, var.type.name)+name
            if isinstance(var, javalang.tree.InterfaceDeclaration):
                # print 'One Up:',var,var.name
                name = '$'+var.name+check_repetition(var, var.name)+name
        # print i,var,len(path)
        # print path
        # while len(path) != 0:
        #  print path[:-1][-1]
        args = []
        for t in node.parameters:
            dims = []
            if len(t.type.dimensions) > 0:
                for e in t.type.dimensions:
                    dims.append("[]")
            dims = "".join(dims)
            args.append(t.type.name+dims)
        args = ",".join(args)

        fqn = ("%s%s(%s)") % (package, name, args)
        # print "->",fqn

        (init_line, b) = node.position
        method_body = []
        closed = 0
        openned = 0

        # print '###################################################################################################'
        # print (init_line,b)
        # print 'INIT LINE -> ',file_string_split[init_line-1]
        # print '---------------------'

        for line in file_string_split[init_line-1:]:
            # if len(line) == 0:
            #     continue
            # print '+++++++++++++++++++++++++++++++++++++++++++++++++++'
            # print line
            # print comment_inline_pattern
            line_re = re.sub(comment_inline_pattern, '',
                             line, flags=re.MULTILINE)
            line_re = re.sub(re_string, '', line_re, flags=re.DOTALL)

            # print line
            # print '+++++++++++++++++++++++++++++++++++++++++++++++++++'

            closed += line_re.count('}')
            openned += line_re.count('{')
            if (closed - openned) == 0 and openned > 0:
                method_body.append(line)
                break
            else:
                method_body.append(line)

        # print '\n'.join(method_body)

        end_line = init_line + len(method_body) - 1
        method_body = '\n'.join(method_body)

        method_pos.append((init_line, end_line))
        method_string.append(method_body)

        method_name.append(fqn)

    if (len(method_pos) != len(method_string)):
        # logging.warning("File " + file_path + " cannot be parsed. (3)")
        return (None, None, method_name)
    else:
        # logging.warning("File " + file_path + " successfully parsed.")
        return (method_pos, method_string, method_name)


def check_repetition(node, name):
    before = -1
    i = 0
    for (obj, n, value) in found_parent:
        if obj is node:
            if value == -1:
                return ''
            else:
                return '_'+str(value)
        else:
            i += 1
        if n == name:
            before += 1
    found_parent.append((node, name, before))
    if before == -1:
        return ''
    else:
        return '_'+str(before)


def method_extractor(file):
    methodsInfo = []

    FORMAT = '[%(levelname)s] (%(threadName)s) %(message)s'
    # logging.basicConfig(level=logging.DEBUG, format=FORMAT)

    config = ConfigParser()

    # parse existing file
    try:
        config.read(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'config.ini'))
    except IOError:
        print('ERROR - Config settings not found. Usage: $python this-script.py config-file.ini')
        sys.exit()

    # config.get('Language', 'separators').strip('"').split(' ')
    separators = "; . [ ] ( ) ~ ! - + & * / % < > ^ | ? { } = # , \" \\ : $ ' ` @"
    comment_inline = re.escape(config.get('Language', 'comment_inline'))
    comment_inline_pattern = comment_inline + '.*?$'

    # allFilesInFolder = GetFiles.getAllFilesUsingFolderPath(folderPath)

    # print(allFilesInFolder)
    return getFunctions(file, comment_inline_pattern)
