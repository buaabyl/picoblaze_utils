#!/bin/python
# -*- coding:utf-8 -*-
#  
#  Copyright 2013 buaa.byl@gmail.com
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#

#
# this is fake c compiler.
# I write this script for easy write assembly code.
# So this "compiler" is a translator, not a really compiler.
#

import os
import sys
import re
import time
import traceback
import hashlib
import types
import subprocess
import getopt
from StringIO import StringIO

#gnu style use 2 spaces as tab
NR_SPACES_OF_TAB = 2

#index of each line
IDX_LEVEL   = 0
IDX_LINENO  = 1
IDX_TYPE    = 2
IDX_CODE    = 3

class MetaInfo(object):
    def __init__(self):
        self.level = 0
        self.lineno = 0
        self.lines = []
        self.filename = ''

class ParseException(BaseException):
    def __init__(self, msg):
        self.msg = msg

def file_get_contents(fn):
    f = open(fn, "r")
    d = f.read()
    f.close()
    return d

def file_put_contents(fn, d):
    f = open(fn, "w")
    f.write(d)
    f.close()

def resolve_lineno(text):
    lst_line = []
    lines = text.split('\n')
    filename = ''
    lineno   = 1

    for line in lines:
        res = re.match(r'#line (\d+) "(.*)"', line)
        if res:
            filename = res.groups()[1]
            lineno = int(res.groups()[0])
            continue

        if not re.match(r'^[ \t]*$', line):
            lst_line.append('#line %d "%s"' % (lineno, filename))

        lst_line.append(line)

        lineno += 1

    return lst_line

def popen(args, stdin=None):
    p = subprocess.Popen(args,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines = True)

    stdout_text, stderr_text = p.communicate(stdin)
    p.wait()

    return (p.returncode, stdout_text, stderr_text)

def _parse_param(param):
    param = re.sub(r'[ ]+', '', param)

    if len(param) == 0:
        return param
    elif re.match(r'^s[0-9A-F]$', param):
        return param
    elif re.match(r'^[&]s[0-9A-F]$', param):
        return param[1:]
    else:
        try:
            res = {'val':0}
            text = 'val = %s' % param
            exec(text, {}, res)
            return res['val']
        except SyntaxError as e:
            traceback.print_exc()
            raise ParseException("Unknown format")

def _parse_param_list(params):
    params = re.split(r'[,]', params)

    #param must be register or digit or assignment
    lst_param = []
    for param in params:
        lst_param.append(_parse_param(param))

    return lst_param

def prepare(info, line):
    info.lineno += 1

    info.level = 0
    for c in line:
        if c != ' ':
            break
        info.level += 1

    info.level /= NR_SPACES_OF_TAB

    line = re.sub(r'^[ \t]+', '', line)

    return line

def parse_macro(info, line):
    line = re.sub(r'[; ]+$', '', line)

    res = re.match(r'#include "(.*)"', line)
    if res:
        return True
    
    res = re.match(r'#line (\d+) "(.*)"', line)
    if res:
        info.filename = res.groups()[1]
        info.lineno = int(res.groups()[0]) - 1
        return True

    return False

def parse_block(info, line):
    line = re.sub(r'[; ]+$', '', line)

    if line == '{':
        info.lines.append([info.level, info.lineno, 'block', line])
        #info.level += 1
        return True

    if line == '}':
        #info.level -= 1
        info.lines.append([info.level, info.lineno, 'block', line])
        return True

    return False

def parse_return(info, line):
    line = re.sub(r'[; ]+$', '', line)

    if line == 'return':
        info.lines.append([info.level, info.lineno, 'return', []])
        return True

    res = re.match(r'return (.*)', line)
    if res:
        param = _parse_param(res.groups()[0])
        if int(param) != 0:
            param = 'enable'
        else:
            param = 'disable'

        info.lines.append([info.level, info.lineno, 'return', param])
        return True

    return False 

def parse_do(info, line):
    line = re.sub(r'[; ]+$', '', line)

    if line == 'do':
        info.lines.append([info.level, info.lineno, 'do', []])
        return True

    return False

def parse_break(info, line):
    line = re.sub(r'[; ]+$', '', line)
    
    if line in ['break', 'continue']:
        info.lines.append([info.level, info.lineno, line, []])
        return True

    return False

def parse_condition(info, line):
    end_while = False
    #check if end with ';'
    if re.match(r'.+[;]+[ \t]*$', line):
        end_while = True 

    line = re.sub(r'[; ]+$', '', line)

    if line == 'else':
        info.lines.append([info.level, info.lineno, 'else', []])
        return True

    #fmt: if (!var)
    res = re.match(r'(if|else if|while) \(! (.+)\)', line)
    if res:
        cond    = res.groups()[0]
        param0  = res.groups()[1]
        compare = '=='
        param1  = '0'
        info.lines.append([info.level, info.lineno, cond,
            [compare, _parse_param(param0), _parse_param(param1)]])
        return True

    #fmt: if (a & b)
    res = re.match(r'(if|else if|while) \((.+) (&|\|\^|) (.+)\)', line)
    if res:
        cond    = res.groups()[0]
        param0  = res.groups()[1]
        compare = res.groups()[2]
        param1  = res.groups()[3]

        if cond == 'while' and end_while:
            info.lines.append([info.level, info.lineno, 'dowhile',
                [compare, _parse_param(param0), _parse_param(param1)]])
            return True

        info.lines.append([info.level, info.lineno, cond,
            [compare, _parse_param(param0), _parse_param(param1)]])
        return True

    #fmt: if (a < b)
    res = re.match(r'(if|else if|while) \((.+) (>|<|==|!=|>=|<=) (.+)\)', line)
    if res:
        cond    = res.groups()[0]
        param0  = res.groups()[1]
        compare = res.groups()[2]
        param1  = res.groups()[3]

        if cond == 'while' and end_while:
            info.lines.append([info.level, info.lineno, 'dowhile',
                [compare, _parse_param(param0), _parse_param(param1)]])
            return True

        info.lines.append([info.level, info.lineno, cond,
            [compare, _parse_param(param0), _parse_param(param1)]])
        return True

    #fmt: if (1)
    res = re.match(r'(if|else if|while) \((s[0-9a-fA-F]|\d+)\)', line)
    if res:
        cond    = res.groups()[0]
        param0  = res.groups()[1]
        compare = '!='
        param1  = '0'

        if cond == 'while' and end_while:
            info.lines.append([info.level, info.lineno, 'dowhile',
                [compare, _parse_param(param0), _parse_param(param1)]])
            return True

        info.lines.append([info.level, info.lineno, cond,
            [compare, _parse_param(param0), _parse_param(param1)]])
        return True

    return False 

def parse_assign(info, line):
    line = re.sub(r'[; ]+$', '', line)

    #fmt: a += b
    res = re.match(r'(.+) (=|\+=|-=|<<=|>>=|&=|\|=|\^=) (.+)', line)
    if res:
        param0  = res.groups()[0]
        assign  = res.groups()[1]
        param1  = res.groups()[2]
        info.lines.append([info.level, info.lineno, 'assign',
            [assign, _parse_param(param0), _parse_param(param1)]])
        return True

    #fmt: a++
    res = re.match(r'(.+) (\+\+|--)', line)
    if res:
        param0  = res.groups()[0]
        assign  = res.groups()[1]
        assign  = {'++':'+=', '--':'-='}[assign]

        info.lines.append([info.level, info.lineno, 'assign',
            [assign, _parse_param(param0), 1]])
        return True

    return False 

def parse_funcdecl(info, line):
    #ignore normal function declare
    if re.match(r'(\w+) (\w+)\(([^\(\)]*)\);$', line):
        return True

    #parse __attribute__ ((...))
    res = re.match(r'(\w+) (\w+)\((.*)\) (.*);$', line)
    if info.level == 0 and res:
        ret = res.groups()[0]
        name = res.groups()[1]
        params = res.groups()[2]
        attributes = res.groups()[3]
        info.lines.append([info.level, info.lineno, 'funcdecl', 
            [name, ret, params, attributes]])
        return True

    return False 

def parse_funcdef(info, line):
    line = re.sub(r'[; ]+$', '', line)

    res = re.match(r'(\w+) (\w+)\((.*)\)$', line)
    if info.level == 0 and res:
        ret = res.groups()[0]
        name = res.groups()[1]
        params = res.groups()[2]
        info.lines.append([info.level, info.lineno, 'funcdef', 
            [name, ret, params]])
        info.lines.append([info.level, info.lineno, 'file', 
            [info.filename]])
        return True

    return False 

def parse_funccall(info, line):
    line = re.sub(r'[; ]+$', '', line)

    res = re.match(r'(\w+)\((.*)\)$', line)
    if res:
        fun = res.groups()[0]
        params = res.groups()[1]

        if len(params) == 0:
            info.lines.append([info.level, info.lineno, 'funccall', [fun]])
            return True

        if fun in ['input', 'output', 'store', 'fetch']:
            info.lines.append([info.level, info.lineno, 'funccall',
                [fun, _parse_param_list(params)]])
        else:
            info.lines.append([info.level, info.lineno, 'funccall',
                [fun, [params]]])
        return True

    return False 

def parse(text):
    lines = text.split('\n')
    info = MetaInfo()

    #build parser list
    lst_parser = [
            parse_macro,
            parse_block,
            parse_return,
            parse_do,
            parse_break,
            parse_condition,
            parse_assign,
            parse_funcdecl,
            parse_funcdef,
            parse_funccall,
    ]

    #parse codes
    for line in lines:
        line = prepare(info, line)

        if re.match(r'^[ \t;]+$', line) or len(line) == 0:
            continue

        line = re.sub(r'[\t ]+', ' ', line)

        #try all know parser
        unknown = True
        for parser in lst_parser:
            #print parser.__name__
            if parser(info, line):
                unknown = False
                break

        if unknown:
            msg = 'Unknown format "%d:%s"' % (info.lineno, line)
            raise ParseException(msg)

    return info

def dump_parse(lines, no_title=False, f=sys.stdout):
    show_title = not no_title

    if show_title:
        f.write('/* %5s %6s %10s */' % ('level', 'lineno', 'type'))
        f.write('\n')
        f.write('/*%s*/' % ('*'*80))
        f.write('\n')

    for level, lineno, t, code in lines:
        f.write('/* %5d %6d %10s */ %s%s' % \
                (level, lineno, t, '    ' * level, code))
        f.write('\n')
    f.write('\n')

def convert_list_to_block(info):
    #return value format:
    #   (
    #       {
    #           function_name : [
    #               (label, [
    #                       (level, lineno, type, code),
    #                       ......
    #               ]
    #               ),
    #               ......
    #           ],
    #           ......
    #       },
    #       {
    #           function_name : attribute,
    #           ......
    #       }
    #   )
    body = []
    map_function = {}
    map_attribute = {}

    #group by function
    for line in info.lines:
        level, lineno, t, code = line
        if t == 'funcdecl':
            name = code[0]
            attributes = code[3]
            res = re.match('__attribute__ \(\((.+)\W*\((.+)\)\)\)', attributes)
            if res:
                clear_attrs = []
                attrs = res.groups()
                for attr in attrs:
                    attr = re.sub('^[ ]+', '', attr)
                    attr = re.sub('[ ]+$', '', attr)
                    if re.match(r'"(.+)"', attr):
                        clear_attrs.append(re.match(r'"(.+)"', attr).groups()[0])
                    else:
                        clear_attrs.append(attr)

                map_attribute[name] = clear_attrs
            else:
                msg = 'Unknow attribute format "%s"' % attribute
                raise ParseException(msg)
        elif t == 'funcdef':
            name = code[0]
            body = [line]
            map_function[name] = body
        elif t == 'file':
            body.insert(0, line)
        elif t == 'block':
            continue
        else:
            body.append(line)

    ##debug
    #for name, body in map_function.iteritems():
    #    print 'DEBUG:', name, 'has', len(body), 'lines'
    #print

    #group by level
    label_prefix = ''
    label_id = 0

    for name in map_function:
        curr_level = 0
        body = map_function[name]

        #convert body to list of block
        lst_block = []

        begin = 0
        i = 0
        for i in range(len(body)):
            line = body[i]
            level, lineno, t, code = line

            if t == 'file':
                fpath = code[0]
                label_prefix = 'L_%s_' % hashlib.md5(fpath).hexdigest()
                i += 1

            elif level != curr_level or t in ['do', 'dowhile', 'while', 'if',
                    'else if', 'else', 'break', 'continue']:
                if i - begin > 0 and len(body[begin:i]) > 0:
                    #generate label
                    label = label_prefix + str(label_id)
                    label_id += 1
                    
                    #save previous lines
                    lst_block.append((label, body[begin:i]))

                #preapre next
                curr_level = level
                begin = i
                i += 1

                if t in ['do', 'dowhile', 'while', 'if']:
                    if i - begin > 0 and len(body[begin:i]) > 0:
                        #generate label
                        label = label_prefix + str(label_id)
                        label_id += 1

                        #save current line
                        lst_block.append((label, body[begin:i]))

                    begin = i
                    i += 1
            else:
                i += 1

        if i - begin > 0 and len(body[begin:i]) > 0:
            label = label_prefix + str(label_id)
            label_id += 1

            lst_block.append((label, body[begin:i]))

        #replace body to list of block
        map_function[name] = lst_block

    ##debug
    #for name, body in map_function.iteritems():
    #    l = 0
    #    for label, block in body:
    #        l += len(block)
    #    print 'DEBUG:', name, 'has', l, 'lines'
    #print

    return (map_function, map_attribute)

def dump_blocks(map_function, f=sys.stdout):
    #debug
    for name in map_function:
        lst_block = map_function[name]
        f.write(name)
        f.write('\n')
        no_title = False
        for block in lst_block:
            f.write(' %s:' % block[0])
            f.write('\n')
            dump_parse(block[1], no_title, f)
            no_title = True

def convert_condition_to_ifgoto(map_function):
    #because 'if'/'do'/'while' is in single line block,
    #so easy to modify it.

    for name in map_function:
        lst_block = map_function[name]

        stack_label = []
        prev_level = 0

        map_pair = {}

        stack_cond_level = []
        stack_cond_label = []

        #find level-pair, such like 'do' and 'while', '{' and '}'
        #and convert 'do-while'/'while' to 'if, cond, label(true), label(false)'
        #and convert 'if' to 'if, cond, label(true), label(false)'
        for idx_block in range(len(lst_block)):
            #get current info
            label, block = lst_block[idx_block]
            level = block[0][0]

            #get next info
            idx_next_block = idx_block + 1
            if idx_next_block < len(lst_block):
                label_next, block_next = lst_block[idx_next_block]
                level_next = block_next[0][0]
            else:
                label_next = None
                block_next = None
                level_next = -1

            #check
            if level > 0 and label_next:
                if level < level_next:#next block is lowest
                    stack_label.append((level, idx_block, label))
                    if block[0][2] in ['do', 'while']:
                        stack_cond_level.append(level_next)
                        stack_cond_label.append(label)
                elif level > level_next:#next block is higest
                    while True:
                        (old_level, old_idx, old_label) = stack_label.pop(-1)

                        child_level = level

                        #check while
                        old_block = lst_block[old_idx][1]
                        level, lineno, t1, code = old_block[0]
                        if t1 == 'do':
                            child_level = stack_cond_level.pop(-1)
                            stack_cond_label.pop(-1)
                        elif t1 in ['while', 'if']:
                            if t1 == 'while':
                                child_level = stack_cond_level.pop(-1)
                                stack_cond_label.pop(-1)

                            code.append('(NEXT)')

                            #find next same level code
                            label_bb = ''
                            if len(stack_cond_label) > 0:
                                level_insde_loop = stack_cond_level[-1]
                                for tmp_label, tmp_block in lst_block[idx_next_block:]:
                                    tmp_level = tmp_block[0][0]
                                    if tmp_level == level:
                                        #match same level first
                                        label_bb = tmp_label
                                        break
                                    elif tmp_level == level_insde_loop:
                                        #match previous loop body
                                        label_bb = tmp_label
                                        break

                            if label_bb != '':
                                code.append(label_bb)
                            elif len(stack_cond_label) > 0:
                                code.append(stack_cond_label[-1])
                            else:
                                code.append(label_next)

                            old_block[0][2] = 'if'
                        else:
                            msg = 'Unknown condition "%s"' % str(t1)
                            raise ParseException(msg)

                        level, lineno, t, code = block[0]
                        if t1 == 'while':
                            block.append([child_level, lineno, 'goto', [old_label]])

                        #check do-while
                        level, lineno, t, code = block_next[0]
                        if t == 'dowhile':
                            map_pair[label_next] = old_label
                            block_next[0][2] = 'if'
                            code.append(old_label)
                            code.append('(NEXT)')
                        else:
                            map_pair[old_label] = label_next

                        if old_level == level_next:
                            break
                        elif old_level < level_next:
                            raise ParseException('Not pair levels!')

            elif level > 1 and label_next == None:
                (old_level, old_idx, old_label) = stack_label.pop(-1)

                #check while
                old_block = lst_block[old_idx][1]
                level, lineno, t, code = old_block[0]
                if t in ['if', 'while']:
                    code.append('(NEXT)')
                    code.append('(END)')
                    old_block[0][2] = 'if'

                level, lineno, t, code = block[0]
                block.append([level, lineno, 'goto', [old_label]])

                map_pair[old_label] = '(END)'

            pass#end of for idx_block in range(len(lst_block)):

def find_next_label(lst_block, level):
    label_bb = '(END)'
    for tmp_label, tmp_block in lst_block:
        tmp_level = tmp_block[0][0]
        if tmp_level <= level:
            label_bb = tmp_label
            break
    return label_bb

def find_prev_label(lst_block, level):
    label_bb = '(HEAD)'
    for tmp_label, tmp_block in reversed(lst_block):
        tmp_level = tmp_block[0][0]
        if tmp_level <= level:
            label_bb = tmp_label
            break
    return label_bb

def find_next_endif_label(lst_block, level):
    label_bb = '(END)'
    for tmp_label, tmp_block in lst_block:
        tmp_level = tmp_block[0][IDX_LEVEL]
        if tmp_level <= level and tmp_block[0][IDX_TYPE] == 'endif':
            label_bb = tmp_label
            break
    return label_bb

def find_next_endwhile_label(lst_block):
    label_bb = '(END)'
    for tmp_label, tmp_block in lst_block:
        if tmp_block[0][IDX_TYPE] in ['endwhile', 'dowhile']:
            label_bb = tmp_label
            break
    return label_bb

def find_prev_loop_label(lst_block):
    label_bb = '(END)'
    for tmp_label, tmp_block in reversed(lst_block):
        if tmp_block[0][IDX_TYPE] in ['while', 'do']:
            label_bb = tmp_label
            break
    return label_bb

def find_blockidx_of_label(lst_block, label):
    for i in range(len(lst_block)):
        if lst_block[i][0] == label:
            return i
        i += 1

    return None

def convert_condition_to_ifgoto2(map_function):
    print

    label_prefix = 'JOIN_'
    label_id = 0

    #append endfunc to every block
    for name in map_function:
        lst_block = map_function[name]
        end_label = label_prefix + str(label_id)
        label_id += 1

        first_line = lst_block[0][1][0]

        end_block = [first_line[IDX_LEVEL], first_line[IDX_LINENO],
                'endfunc', []]

        lst_block.append((end_label, [end_block]))

    #insert join or endif block to control-graphic
    #
    #   if          ->  if
    #       ...     ->      ...
    #               ->  ifjoin
    #   else        ->  else
    #       ...     ->      ...
    #               ->  endif
    #
    for name in map_function:
        lst_block = map_function[name]

        map_forward = {}
        map_backward = {}

        idx_block = 0
        while idx_block < len(lst_block):
            label, block = lst_block[idx_block]

            first_line = block[0]
            level = first_line[IDX_LEVEL]

            if first_line[IDX_TYPE] in ['if', 'else', 'else if', 'while']:
                if idx_block+1 < len(lst_block):
                    label_t_next = lst_block[idx_block+1][0]
                else:
                    label_t_next = '(END)'
                label_f_next = find_next_label(lst_block[idx_block+1:], level)

                #append true and false branch label
                first_line[IDX_CODE].append(label_t_next)
                first_line[IDX_CODE].append(label_f_next)

                #append node
                i_block = find_blockidx_of_label(lst_block, label_f_next)
                if i_block:
                    join_label = label_prefix + str(label_id)
                    label_id += 1

                    i_type = 'ifjoin'
                    if first_line[IDX_TYPE] in ['if', 'else if', 'else']:
                        if lst_block[i_block][1][0][IDX_TYPE] not in ['else', 'else if']:
                            i_type = 'endif'
                    elif first_line[IDX_TYPE] == 'while':
                        i_type = 'endwhile'

                    join_block = [first_line[IDX_LEVEL], first_line[IDX_LINENO],
                            i_type, [label]]

                    lst_block.insert(i_block, (join_label, [join_block]))

            elif first_line[IDX_TYPE] == 'dowhile':
                label_t_next = find_prev_label(lst_block[:idx_block], level)
                if idx_block+1 < len(lst_block):
                    label_f_next = lst_block[idx_block+1][0]
                else:
                    label_f_next = '(END)'

                first_line[IDX_CODE].append(label_t_next)
                first_line[IDX_CODE].append(label_f_next)

            idx_block += 1

    #resolved label for else and else-if which will jump to endif
    for name in map_function:
        lst_block = map_function[name]

        for idx_block in range(len(lst_block)):
            label, block = lst_block[idx_block]
            first_line = block[0]
            level = first_line[IDX_LEVEL]
            if first_line[IDX_TYPE] == 'ifjoin':
                label_bb = find_next_endif_label(lst_block[idx_block+1:], level)
                first_line[IDX_CODE].append(label_bb)

            elif first_line[IDX_TYPE] == 'continue':
                #find while or do
                label_bb = find_prev_loop_label(lst_block[:idx_block])
                first_line[IDX_CODE].append(label_bb)

            elif first_line[IDX_TYPE] == 'break':
                #find while or do
                label_bb = find_prev_loop_label(lst_block[:idx_block])
                #extract false branch label of while or do
                block_loop_idx = find_blockidx_of_label(lst_block, label_bb)
                loop_block = lst_block[block_loop_idx][1][0]
                label_f_target = loop_block[IDX_CODE][-1]

                first_line[IDX_CODE].append(label_f_target)

    ##debug
    #for name in map_function:
    #    lst_block = map_function[name]

    #    for idx_block in range(len(lst_block)):
    #        label, block = lst_block[idx_block]
    #        print label + ':'

    #        for line in block:
    #            print ' '*line[IDX_LEVEL], line[IDX_TYPE], line[IDX_CODE]
    #        print

def generate_assembly(map_function, map_attribute, f=sys.stdout):
    isr_table = {}
    isr_routine = {}

    #boot section
    f.write(';%s' % ('-' * 60))
    f.write('\n')
    f.write('address 0x000')
    f.write('\n')
    f.write('boot:')
    f.write('\n')

    f.write('  call init')
    f.write('\n')

    f.write('loop:')
    f.write('\n')
    f.write('  jump loop')
    f.write('\n')
    f.write('\n')

    for name in map_function:
        lst_block = map_function[name]
        label_end = '_end_%s' % name

        #check if isr
        if name in map_attribute:
            attr = map_attribute[name]
            if attr[0] == 'at':
                f.write('address %s' % attr[1])
                f.write('\n')
            elif attr[0] == 'interrupt':
                addr = re.search(r'IRQ(\d+)', attr[1].upper()).groups()[0]
                addr = 0x3F0 + int(addr)
                isr_table[addr] = name
                isr_routine[name] = addr
            else:
                msg = 'Unknown attribute "%s"' % str(attr)
                raise ParseException(msg)

        #get source file name
        fn_source = ''
        for idx_block in range(len(lst_block)):
            lable, block = lst_block[idx_block]
            for line in block:
                level, lineno, t, code = line
                if t == 'file':
                    fn_source = code[0]
                    break

        f.write(';%s' % ('-' * 60))
        f.write('\n')

        f.write(';%s\n' % fn_source)
        f.write('%s:' % name)
        f.write('\n')

        for idx_block in range(len(lst_block)):
            lable, block = lst_block[idx_block]

            #write label
            f.write(' %s:' % lable)
            f.write('\n')

            for line in block:
                level, lineno, t, code = line

                if t not in ['file']:
                    f.write(' ;%s:%d' % (fn_source, lineno))
                    f.write('\n')

                #code fmt endwhile: do_label
                if t in ['endwhile']:
                    f.write('  '*level)
                    f.write('  ;%s' % (t))
                    f.write('\n')

                    f.write('  '*level)
                    f.write('  jump %s' % code[0])
                    f.write('\n')
                    continue

                #code fmt ifjoin: if_label, endif_label
                if t in ['ifjoin']:
                    f.write('  '*level)
                    f.write('  ;%s' % t)
                    f.write('\n')

                    #check jump-jump
                    label_bb = code[-1]
                    block_next_idx = find_blockidx_of_label(lst_block, label_bb)
                    while True:
                        block_next = lst_block[block_next_idx][1][0]
                        if block_next[IDX_TYPE] == 'endif':
                            block_next_idx += 1
                        elif block_next[IDX_TYPE] == 'ifjoin':
                            label_bb = block_next[IDX_CODE][-1]
                            block_next_idx = find_blockidx_of_label(lst_block, label_bb)
                        else:
                            break
                    label_bb

                    f.write('  '*level)
                    f.write('  jump %s' % label_bb)
                    f.write('\n')
                    continue

                elif t in ['endif']:
                    f.write('  '*level)
                    f.write('  ;%s of %s' % (t, code[-1]))
                    f.write('\n')
                    continue

                elif t in ['else']:
                    f.write('  '*level)
                    f.write('  ;%s' % t)
                    f.write('\n')
                    continue

                elif t in ['do', 'endfunc']:
                    f.write('  '*level)
                    f.write('  ;%s' % (t))
                    f.write('\n')
                    continue

                elif t in ['break', 'continue']:
                    f.write('  ' * level)
                    f.write('  ;%s' % (t))
                    f.write('\n')

                    f.write('  ' * level)
                    f.write('  jump %s' % code[0])
                    f.write('\n')

                elif t == 'file':
                    pass
                    #f.write('  ' * level)
                    #f.write('  ;%s' % code[0])
                    #f.write('\n')

                elif t == 'funcdef':
                    f.write('  ' * level)
                    f.write('  ;%s %s (%s)' % \
                            (code[1], code[0], code[2]))
                    f.write('\n')

                elif t == 'funccall':
                    if code[0] in ['enable_interrupt', 'disable_interrupt']:
                        f.write('  ' * level)
                        f.write('  %s' % code[0].replace('_', ' '))
                        f.write('\n')
                    elif code[0] in ['input', 'output', 'fetch', 'store']:
                        if type(code[1][0]) == types.IntType:
                            f.write('  ' * level)
                            f.write('  %s %s, %d' % (code[0], code[1][1], code[1][0]))
                            f.write('\n')
                        else:
                            f.write('  ' * level)
                            f.write('  %s %s, (%s)' % (code[0], code[1][1], code[1][0]))
                            f.write('\n')
                    elif code[0] in ['__asm__', 'asm', 'assembly']:
                        f.write('  ' * level)
                        inline_asm = re.search(r'"(.+)"', code[1][0]).groups()[0]
                        f.write('  %s' % inline_asm)
                        f.write('\n')
                    elif code[0] == 'psm':
                        #split text
                        inline_asm = re.search(r'"(.+)"', code[1][0]).groups()[0]
                        #clear params and convert to list
                        other_asm = code[1][0][len(inline_asm) + 2:]
                        other_asm = re.sub(r'^[, ]+', '', other_asm)
                        other_asm = re.sub(r'[ &]+', '', other_asm)
                        other_asm = other_asm.split(',')
                        
                        #replace
                        i = 1
                        for sym in other_asm:
                            inline_asm = inline_asm.replace("%%%d" % i, sym)
                            i += 1

                        f.write('  ' * level)
                        f.write('  %s' % inline_asm)
                        f.write('\n')
                    elif code[0] in map_function:
                        f.write('  ' * level)
                        f.write('  call %s' % code[0])
                        f.write('\n')
                    else:
                        msg = 'Unknown instruction "%s"' % (str(line))
                        raise ParseException(msg)

                elif t in ['if', 'else if', 'while', 'dowhile']:
                    compare = code[0]
                    param0  = code[1]
                    param1  = code[2]

                    #check if const value
                    if type(param0) == types.IntType and \
                            type(param1) == types.IntType:
                        res = {'val':0}
                        text = 'val = %s %s %s' % (param0, compare, param1)
                        exec(text, {}, res)
                        if res['val'] == True or res['val'] != 0:
                            param0  = 's0'
                            compare = '=='
                            param1  = 's0'
                        else:
                            param0  = 's0'
                            compare = '!='
                            param1  = 's0'
                    elif type(param0) == types.IntType and \
                            type(param1) != types.IntType:
                        msg = 'Param0 must be register when Param1 is digit! "%s"' % \
                                (str(line))
                        raise ParseException(msg)

                    label_t = code[3]
                    label_f = code[4]

                    f.write('  ' * level)
                    f.write('  ;%s (%s %s %s), %s, %s' % \
                            (t, param0, compare, param1, label_t, label_f))
                    f.write('\n')

                    f.write('  ' * level)
                    f.write('  compare %s, %s' % (str(param0), str(param1)))
                    f.write('\n')

                    if compare == '==':
                        flage_t = 'Z'
                        flage_f = 'NZ'
                    elif compare == '!=':
                        flage_t = 'NZ'
                        flage_f = 'Z'
                    elif compare == '<':
                        flage_t = 'C'
                        flage_f = 'NC'
                    elif compare == '>=':
                        flage_t = 'NC'
                        flage_f = 'C'
                    else:
                        msg = 'Not support "%s"' % str(line)
                        raise ParseException(msg)

                    #optimize jump
                    if idx_block + 1 < len(lst_block):
                        next_block_label = lst_block[idx_block + 1][0]

                        #check jump-jump
                        label_bb = label_f
                        while True:
                            block_next_idx = find_blockidx_of_label(lst_block, label_bb)
                            block_next = lst_block[block_next_idx][1][0]
                            if block_next[IDX_TYPE] == 'ifjoin':
                                label_bb = block_next[IDX_CODE][-1]
                            else:
                                break
                        label_f = label_bb

                        label_bb = label_t
                        while True:
                            block_next_idx = find_blockidx_of_label(lst_block, label_bb)
                            block_next = lst_block[block_next_idx][1][0]
                            if block_next[IDX_TYPE] == 'ifjoin':
                                label_bb = block_next[IDX_CODE][-1]
                            else:
                                break
                        label_t = label_bb

                        if next_block_label == label_f:
                            f.write('  ' * level)
                            f.write('  jump %s, %s' % (flage_t, label_t))
                            f.write('\n')
                            continue

                        elif next_block_label == label_t:
                            f.write('  ' * level)
                            f.write('  jump %s, %s' % (flage_f, label_f))
                            f.write('\n')
                            continue

                    f.write('  ' * level)
                    f.write('  jump %s, %s' % (flage_f, label_f))
                    f.write('\n')

                    f.write('  ' * level)
                    f.write('  jump %s, %s' % (flage_t, label_t))
                    f.write('\n')

                elif t == 'goto':
                    f.write('  ' * level)
                    f.write('  ;end of while')
                    f.write('\n')
                    f.write('  ' * level)
                    f.write('  jump %s' % code[0])
                    f.write('\n')

                elif t == 'assign':
                    assign_type = code[0]
                    param0  = code[1]
                    param1  = code[2]
                    if assign_type == '=':
                        f.write('  ' * level)
                        f.write('  move %s, %s' % (param0, str(param1)))
                        f.write('\n')
                    elif assign_type == '+=':
                        f.write('  ' * level)
                        f.write('  add %s, %s' % (param0, str(param1)))
                        f.write('\n')
                    elif assign_type == '-=':
                        f.write('  ' * level)
                        f.write('  sub %s, %s' % (param0, str(param1)))
                        f.write('\n')
                    elif assign_type == '<<=':
                        while param1 > 0:
                            f.write('  ' * level)
                            f.write('  sl0 %s' % param0)
                            f.write('\n')
                            param1 -= 1
                    elif assign_type == '>>=':
                        while param1 > 0:
                            f.write('  ' * level)
                            f.write('  sr0 %s' % param0)
                            f.write('\n')
                            param1 -= 1
                    elif assign_type == '&=':
                        f.write('  ' * level)
                        f.write('  and %s, %s' % (param0, str(param1)))
                        f.write('\n')
                    elif assign_type == '|=':
                        f.write('  ' * level)
                        f.write('  or %s, %s' % (param0, str(param1)))
                        f.write('\n')
                    elif assign_type == '^=':
                        f.write('  ' * level)
                        f.write('  xor %s, %s' % (param0, str(param1)))
                        f.write('\n')
                    else:
                        msg = 'Unknown operator "%s"' % (str(line))
                        raise ParseException(msg)

                elif t == 'return':
                    f.write('  ' * level)
                    if code:
                        f.write('  returni %s' % code)
                        f.write('\n')
                    else:
                        f.write('  return')
                        f.write('\n')

                else:
                    msg = 'Unknown instruction "%s"' % (str(line))
                    raise ParseException(msg)


            f.write('\n')
            pass

        f.write('%s:' % label_end)
        f.write('\n')
        if name in isr_routine:
            f.write('  returni enable')
        else:
            f.write('  return')
        f.write('\n')

        f.write('\n')
        f.write('\n')
        pass

    f.write('\n')
    f.write(';ISR')
    f.write('\n')
    for addr in sorted(isr_table):
        f.write('address 0x%03X' % addr)
        f.write('\n')
        f.write('jump    %s' % isr_table[addr])
        f.write('\n')
    pass

usage = '''
usage : %s [option] file

 -h         help
 -I         include path
 -o <file>  output file name
 -g         dump mid-information
''' % os.path.split(sys.argv[0])[1]

def parse_commandline():
    format_s = 'I:o:gh'
    format_l = []
    opts, args = getopt.getopt(sys.argv[1:], format_s, format_l)

    map_options = {}
    for (k, v) in opts:
        map_options[k] = v

    if '-h' in map_options:
        print usage
        sys.exit(-1)

    return map_options, args

if __name__ == '__main__':
    try:
        map_options, lst_args = parse_commandline()
        if len(lst_args) == 0:
            print 'Error : need source file!'
            print
            print usage
            sys.exit(-1)

        if '-o' not in map_options:
            fn_out = os.path.splitext(lst_args[0])[0] + '.s'
            map_options['-o'] = fn_out
        else:
            fn_out = os.path.splitext(map_options['-o'])[0] + '.s'
        map_options['path_noext'] = fn_out

        #preprocess
        args = ['mcpp.exe']
        if '-I' in map_options:
            args.extend(['-I', map_options['-I']])
            
        args.extend(['-e', 'utf-8', '-z', lst_args[0]])

        (returncode, stdout_text, stderr_text) = popen(args)
        if returncode == 0:
            if '-g' in map_options:
                print 'wrote %d bytes to "mcpp.stdout"' % len(stdout_text)
                fn = '%s.mcpp.tmp' % map_options['path_noext']
                file_put_contents(fn, stdout_text)
        else:
            print stderr_text
            raise ParseException('mcpp.exe error')

        #let lineno correct
        lst_line = resolve_lineno(stdout_text)
        stdout_text = '\n'.join(lst_line)

        #format style
        args = ['astyle.exe', '--style=gnu', '--suffix=none']
        (returncode, stdout_text, stderr_text) = popen(args, stdout_text)
        if returncode == 0:
            if '-g' in map_options:
                print 'wrote %d bytes to "astyle.stdout"' % len(stdout_text)
                fn = '%s.astyle.tmp' % map_options['path_noext']
                file_put_contents(fn, stdout_text)
        else:
            print stderr_text
            raise ParseException('astyle.exe error')

        #parse text
        text = stdout_text
        info = parse(text)

        #group lines
        (map_function, map_attribute) = convert_list_to_block(info)
        if '-g' in map_options:
            fn = '%s.pass1.tmp' % map_options['path_noext']
            f = open(fn, 'w')
            dump_blocks(map_function, f)
            f.close()

        #expand loop
        convert_condition_to_ifgoto2(map_function)
        if '-g' in map_options:
            fn = '%s.pass2.tmp' % map_options['path_noext']
            f = open(fn, 'w')
            dump_blocks(map_function, f)
            f.close()

        #dump result
        f = open(map_options['-o'], 'w')
        generate_assembly(map_function, map_attribute, f)
        print 'wrote %d bytes to "%s"' % (f.tell(), map_options['-o'])
        f.close()


    except ParseException as e:
        traceback.print_exc()
        print e.msg


