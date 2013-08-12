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
import re
import os
import sys
import types
import getopt
import json
import time

#///////////////////////////////////////////////////////////////////////////////
#class and regular expression
class DefaultException(BaseException):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

#digits
regex_register  = re.compile(r'[\(]?(s[0-9a-fA-F])[\)]?')

regex_hex_digit = re.compile(r'0[xX][0-9a-fA-F]+')
regex_oct_digit = re.compile(r'0[0-7]+')
regex_dec_digit = re.compile(r'[1-9]+[0-9]*')

#format char: 'c' or '\n'
regex_extract_char = re.compile(r'^\'' + r'([\\]?)' + r'(.)' + r'\'$')

regex_label = re.compile(r'([a-zA-Z_][0-9a-zA-Z_]*):')

#preprocess instruct
lst_regex_preprocess = []
lst_regex_preprocess.append(re.compile(r'\W*`(cond)' + r'[ \t]*' + \
        r'\(' + \
            r'([0-9a-zA-Z_]+)' + r'[ \t]*' + \
            r'([=!><]+)' + r'[ \t]*' + \
            r'([0-9a-zA-Z_]+)' + r'[ \t]*' + \
        r'\)' + \
        r'[ \t]*' + r',' + \
        r'(.*)' + r',' + \
        r'(.*)' + r'$'))
lst_regex_preprocess.append(re.compile(r'\W*`(nop)\W*$'))
lst_regex_preprocess.append(re.compile(r'\W*`(include)\W*"([^"]+)"\W*$'))
lst_regex_preprocess.append(re.compile(r'\W*`(define)\W*([0-9a-zA-Z_-]+)\W*$'))
lst_regex_preprocess.append(re.compile(r'\W*`(define)\W*([0-9a-zA-Z_-]+)\W+(.*)$'))
lst_regex_preprocess.append(re.compile(r'\W*`(undef)\W*([0-9a-zA-Z_-]+)\W*$'))

#escap char convert map
map_escap_char = {
    'n':'\n',
    'r':'\r',
    't':'\t',
    'v':'\v',
    'a':'\a',
    'b':'\b',
    'f':'\f'
}

regex_embedded_python = re.compile(r'\W*(;#!python)\W*(.*)$')

def is_register(elem):
    res = regex_register.match(elem)
    return res

def is_cdigit(elem):
    if type(elem) == types.IntType:
        return True

    if type(elem) == types.StringType:
        if elem == '0':
            return True

    res1 = regex_hex_digit.match(elem)
    res2 = regex_oct_digit.match(elem)
    res3 = regex_dec_digit.match(elem)

    return res1 or res2 or res3

#///////////////////////////////////////////////////////////////////////////////
#parse interface
def parse_preprocessor_macro(s):
    for regex in lst_regex_preprocess :
        if regex.match(s):
            return regex.search(s).groups()

    return None

def parse_instruction(s):
    l = re.split(r'[ ,]+', s)
    newl = []

    #remove spaces
    for elem in l:
        if len(elem) == 0 or re.match(r'[\t ]+', elem):
            continue

        newl.append(re.sub(r'[\t ]+', '', elem))

    if len(newl) > 0:
        return newl
    else:
        return None

#///////////////////////////////////////////////////////////////////////////////
#element convert interface
def convert_digit(s):
    if type(s) == types.IntType:
        return s
    elif regex_hex_digit.match(s):
        return int(s, 16)
    elif regex_oct_digit.match(s):
        return int(s, 8)
    elif (s == '0') or regex_dec_digit.match(s):
        return int(s, 10)
    else:
        msg = '"%s" invalid!' % s
        raise DefaultException(msg)

def convert_char(elem):
    #check char: 'c'
    res = regex_extract_char.match(elem)
    if res:
        c = res.groups()[1]

        #convert escap char to real char
        if res.groups()[0] == '\\':
            c = map_escap_char[c]

        elem = ord(c)
        return elem
    return None

def convert_symbol(elem, symbols):
    state_indirect_access = False
    #check (sX) fomat, and get che sX names
    if re.match(r'\([0-9a-zA-Z_-]+\)', elem):
        state_indirect_access = True
        elem = re.search(r'\(([0-9a-zA-Z_-]+)\)', elem).groups()[0]

    #check if a macro name
    if elem not in symbols:
        return None

    if not state_indirect_access:
        return symbols[elem]
    else:
        return '(%s)' % symbols[elem]

#///////////////////////////////////////////////////////////////////////////////
#main entry
def preprocess_embedded(result, symbols):
    embedded_code = result.groups()[1]
    try:
        exec(embedded_code, {}, symbols)
    except:
        print '"%s" is illegal!' % result.string
        print
        raise

def preprocess_macro(result, lst_inner_asm, symbols):
    if result[0] == 'cond':
        if len(result) != 6:
            msg = 'Not enough elements "%s"' % (str(result))
            raise PSMPPException(msg)

        param0 = result[1]
        cond   = result[2]
        param1 = result[3]
        label_true = result[4]
        label_false= result[5]

        if cond == '==':
            OPERATOR    = 'compare'
            F_TRUE      = 'Z'
            F_FALSE     = 'NZ'
        elif cond == '!=':
            OPERATOR    = 'compare'
            F_TRUE      = 'NZ'
            F_FALSE     = 'Z'
        elif cond == '>=':
            OPERATOR    = 'compare'
            F_TRUE      = 'NC'
            F_FALSE     = 'C'
        elif cond == '<':
            OPERATOR    = 'compare'
            F_TRUE      = 'C'
            F_FALSE     = 'NC'
        elif cond == '&':
            OPERATOR    = 'test'
            F_TRUE      = 'NZ'
            F_FALSE     = 'Z'
        else:
            msg = 'Invalid operator "%s"' % (str(result))
            raise PSMPPException(msg)

        #extract macro to instructions
        #compare or test
        instructions = [OPERATOR, param0, param1]
        preprocess_normal(instructions, lst_inner_asm, symbols)

        #jump
        if ((label_true != '') and (label_true.lower() != 'null')):
            instructions = ['jump', F_TRUE, label_true]
            preprocess_normal(instructions, lst_inner_asm, symbols)

            if ((label_false != '') and (label_false.lower() != 'null')):
                instructions = ['jump', label_false]
                preprocess_normal(instructions, lst_inner_asm, symbols)

        elif ((label_false != '') and (label_false.lower() != 'null')):
            instructions = ['jump', F_FALSE, label_false]
            preprocess_normal(instructions, lst_inner_asm, symbols)

        else:
            msg = 'Invalid format "%s"' % (str(result))
            raise PSMPPException(msg)

    elif result[0] == 'nop':
        lst_inner_asm.append(['load', 's0', 's0'])

    elif result[0] == 'include':
        tmplines = file_get_contents(result[1]).split('\n')
        new_tmplines = preprocess(tmplines, symbols)
        lst_inner_asm.extend(new_tmplines)

    elif result[0] == 'define':
        if len(result) == 1:
            raise
        elif len(result) == 2:
            symbols[result[1]] = '"Not-define"'
        else:
            v = result[2]
            if is_cdigit(v):
                v = convert_digit(v)
            symbols[result[1]] = v

    elif result[0] == 'undef':
        if len(result) == 1:
            raise
        elif result[1] in symbols:
            del symbols[result[1]]

def preprocess_normal(instructions, lst_inner_asm, symbols):
    newinstructions = []
    i = 0
    nr_elems = len(instructions)
    while i < nr_elems:
        elem = instructions[i]
        #check char such like : 'c'
        new_elem = convert_char(elem)
        if new_elem:
            newinstructions.append(new_elem)
            i += 1
            continue

        #check macro
        new_elem = convert_symbol(elem, symbols)
        if new_elem is not None:
            newinstructions.append(new_elem)
            i += 1
            continue
        
        #normal symbol
        if i > 0:#check op name except 'jump' and 'call'
            if instructions[0] in ['jump', 'call', 'return',
                    'returni', 'enable', 'disable']:
                newinstructions.append(elem)
            elif is_register(elem):
                newinstructions.append(elem)
            elif is_cdigit(elem):
                newinstructions.append(convert_digit(elem))
            else:
                msg = '"%s" not a macro or register name!' % str(elem)
                raise DefaultException(msg)
        else:
            newinstructions.append(elem)

        i += 1

    #end of for elem in instructions:

    lst_inner_asm.append(newinstructions)

def preprocess(lines, symbols):
    '''
    return list, and digit is IntType.
    [
        [instruct, op, ...],
        ...
    ]
    '''
    lst_inner_asm = []
    try:
        for line in lines:
            #check embedded python code
            res = regex_embedded_python.match(line)
            if res:
                preprocess_embedded(res, symbols)
                continue

            #check comment, remove comments
            line = re.sub(r';(.*)$', '', line)

            #just ignore '|'
            line = re.sub(r'\|(.*)', '', line)

            #skip all whitespace line
            if re.match('^[\t ]*$', line):
                continue

            #check and process preprocess macro
            result = parse_preprocessor_macro(line)
            if result:
                preprocess_macro(result, lst_inner_asm, symbols)
                continue

            #process normal text
            instructions = parse_instruction(line)
            if instructions:
                preprocess_normal(instructions, lst_inner_asm, symbols)

        #end of for line in lines:
    except PSMPPException as e:
        print e.msg
        print
        print 'Dump:'
        for ins in lst_inner_asm:
            print '', ins

        print '-' * 80
        for sym in sorted(symbols):
            print '%-30s : %s' % (sym, repr(symbols[sym]))
        print '-' * 80
        raise

    except DefaultException as e:
        print 'Dump:'
        for ins in lst_inner_asm:
            print '', ins

        print '-' * 80
        for sym in sorted(symbols):
            print '%-30s : %s' % (sym, repr(symbols[sym]))
        print '-' * 80
        raise

    return lst_inner_asm

def format_digit(inst, d):
    #convert string to int if need.
    d = convert_digit(d)

    #output string
    if inst.upper() in ['ADDRESS', 'JUMP']:
        return '%03X' % d
    else:
        return '%02X' % d

def format_asm(lines):
    lst_kcpsm3_asm = []
    for line in lines:
        if len(line) == 0:
            continue

        instructions = line
        if len(instructions) == 0:
            lst_kcpsm3_asm.append([])
            continue

        newinstructions = []
        newinstructions.append(instructions[0])

        #format digit
        for elem in instructions[1:]:
            #format digit, convert if need.
            if is_cdigit(elem):
                newinstructions.append(format_digit(instructions[0], elem))
            else:
                newinstructions.append(elem)

        #end of for elem in instructions:

        lst_kcpsm3_asm.append(newinstructions)
    return lst_kcpsm3_asm

def dump_symbols(symbols):
    lst_buffer = []
    for sym in sorted(symbols):
        lst_buffer.append('%-20s : %s' % (sym, repr(symbols[sym])))
    return '\n'.join(lst_buffer)

def generate_kcpsm3_asm(lines):
    #convert digit to string.
    lines = format_asm(lines) 
    text = []

    text.append(';' + '-'*60)
    text.append(';generate by kcpsm3pp.py')
    text.append(';' + '-'*60)

    #all values in lines is string now!
    for lst_instructions in lines:
        #label is no indent! code is 4 indent.
        indent = '    '
        if len(lst_instructions) > 0:
            if re.match(r'[0-9a-zA-Z_-]+:', lst_instructions[0]):
                indent = ''

        if lst_instructions[0].upper() == 'ADDRESS' or indent == '':
            text.append('')

        #format operators
        ops = ''
        length = len(lst_instructions[1:])
        for i in range(length):
            s = lst_instructions[1:][i]
            if i + 1 < length:
                ops += '%-4s' % (s+',')
            else:
                ops += '%-4s' % s

        #generate result
        text.append('%s%-8s %s' % (indent, lst_instructions[0], ops))
    return '\n'.join(text)

class PSMBlock(object):
    def __init__(self):
        self.labels     = []
        self.address    = -1
        self.codes      = []

    def __len__(self):
        return len(self.codes)

map_group0 = {\
        'load'  :0x00,
        'move'  :0x00,#extend: same as load
        'mov'   :0x00,#extend: same as load

        'store' :0x17,
        'fetch' :0x03,

        'input' :0x02,
        'output':0x16,

        'and'   :0x05,
        'or'    :0x06,
        'xor'   :0x07,

        'test'  :0x09,#temporary and

        'add'   :0x0c,
        'addcy' :0x0d,
        'sub'   :0x0e,
        'subcy' :0x0f,

        'compare':0x0a,#temporary sub
        }

map_group1 = {\
        'return':0x15,
        'call'  :0x18,
        'jump'  :0x1a,
        }

map_group2 = {\
        'returni':0x1c,#interrupt
        'enable' :0x1e,#interrupt
        'disable':0x1e,#interrupt
        }

map_group3 = {\
        'sla':[0x10, 0x0],
        'rl' :[0x10, 0x2],
        'slx':[0x10, 0x4],
        'sl0':[0x10, 0x6],
        'sl1':[0x10, 0x7],

        'sra':[0x10, 0x8],
        'srx':[0x10, 0xa],
        'rr' :[0x10, 0xc],
        'sr0':[0x10, 0xe],
        'sr1':[0x10, 0xf],
        }

def convert_list_to_blocks(lines):
    #split to blocks, group by address or label
    lst_blocks = []

    inst_block = PSMBlock()
    lst_blocks.append(inst_block)

    for lst_instructions in lines:
        if lst_instructions[0] == 'address':
            address = lst_instructions[1]
            if len(inst_block.codes) > 0:
                inst_block = PSMBlock()
                lst_blocks.append(inst_block)
            inst_block.address = address
        elif regex_label.match(lst_instructions[0]):
            res = regex_label.search(lst_instructions[0])
            label = res.groups()[0]
            if len(inst_block.codes) > 0:
                inst_block = PSMBlock()
                lst_blocks.append(inst_block)
            inst_block.labels.append(label)
        else:
            inst_block.codes.append(lst_instructions)

    return lst_blocks

def arrange_address_to_rom(lst_blocks):
    #arrange codes to rom address
    address = 0
    for i in range(len(lst_blocks)):
        inst_block = lst_blocks[i]
        if inst_block.address != -1:
            if inst_block.address < address:
                raise PSMPPException('Can not arrange codes, you special addre too small')
            else:
                address = inst_block.address
        else:
            inst_block.address = address

        address += len(inst_block)

def convert_label_to_address(lst_blocks):
    #remember all label address
    map_label_address = {}
    for i in range(len(lst_blocks)):
        inst_block = lst_blocks[i]
        for l in inst_block.labels:
            if l in map_label_address:
                msg = 'duplicate label "%s"!' % l
                raise PSMPPException(msg)
            map_label_address[l] = inst_block.address

    #replace label to real address
    for i in range(len(lst_blocks)):
        inst_block = lst_blocks[i]
        for lst_instructions in inst_block.codes:
            if lst_instructions[0] in ['jump', 'call']:
                l = lst_instructions[-1]
                if l not in map_label_address:
                    msg = 'not found label "%s"!' % l
                    raise PSMPPException(msg)
                lst_instructions[-1] = map_label_address[l]
    return map_label_address

def combine_blocks_to_list(lst_blocks):
    nr_codes = 0

    #combine codes
    lst_assembly = []
    address = 0
    for inst_block in lst_blocks:
        #append nop
        if inst_block.address > address:
            for i in range(inst_block.address - address):
                #lst_assembly.append(['load', 's0', 's0'])
                lst_assembly.append(['load', 's0', 0])

        nr_codes += len(inst_block.codes)

        #insert codes
        lst_assembly.extend(inst_block.codes)
        address = inst_block.address + len(inst_block)

    return nr_codes, lst_assembly

def assembly_group0(lst_instructions):
    sX = lst_instructions[1]
    sY = lst_instructions[2]
    KK = lst_instructions[2]

    b17_13  = 0
    b12     = 0#using (sY) not const value
    b11_8   = 0#target register
    b7_0    = 0#source register or value

    b17_13  = map_group0[lst_instructions[0]] << 13
    b11_8 = int(sX[1], 16) << 8

    if type(sY) == types.StringType:
        b12  = 1 << 12
        if re.match(r'^\(s[0-9a-fA-F]+\)$', sY):
            b7_0 = int(sY[len('(s')], 16) << 4
        elif re.match(r'^s[0-9a-fA-F]+$', sY):
            b7_0 = int(sY[len('s')], 16) << 4
        else:
            raise PSMPPException('Unknow type of parameters')
    elif type(sY) == types.IntType:
        b12  = 0
        b7_0 = KK
    else:
        raise PSMPPException('Unknow type of parameters')

    objhex = b17_13 | b12 | b11_8 | b7_0
    return objhex

def assembly_group1(lst_instructions):
    b17_13  = 0
    b12_10  = 0#jump condition
    b9_0    = 0#address
    if lst_instructions[0] == 'return':
        if len(lst_instructions) == 2:
            cond = lst_instructions[1]
        else:
            cond = None
        AAA = None
    elif len(lst_instructions) == 2:
        cond = None
        AAA  = lst_instructions[1]
    elif len(lst_instructions) == 3:
        cond = lst_instructions[1]
        AAA  = lst_instructions[2]
    else:
        cond = None
        AAA  = None

    b17_13  = map_group1[lst_instructions[0]] << 13

    if cond:
        b12_10 = {'z':0x4,'nz':0x5,'c':0x6,'nc':0x7}[cond.lower()]
        b12_10 <<= 10

    if AAA:
        b9_0 = int(AAA)

    objhex = b17_13 | b12_10 | b9_0
    return objhex

def assembly_group2(lst_instructions):
    b17_13  = map_group2[lst_instructions[0]] << 13
    b12_1   = 0
    b0      = 0

    if lst_instructions[0] == 'returni':
        if lst_instructions[1] == 'enable':
            b0 = 1
        else:
            b0 = 0
    elif lst_instructions[0] == 'enable':
        b0 = 1
    elif lst_instructions[0] == 'disable':
        b0 = 0

    objhex = b17_13 | b12_1 | b0
    return objhex

def assembly_group3(lst_instructions):
    sX      = lst_instructions[1]
    b17_13  = map_group3[lst_instructions[0]][0] << 13
    b12     = 0
    b11_8   = int(sX[len('s')], 16) << 8
    b7_4    = 0
    b3_0    = map_group3[lst_instructions[0]][1]

    objhex  = b17_13 | b12 | b11_8 | b7_4 | b3_0
    return objhex

def generate_kcpsm3_hex(lines):
    lst_blocks = convert_list_to_blocks(lines)
    arrange_address_to_rom(lst_blocks)
    map_label_address = convert_label_to_address(lst_blocks)
    nr_codes, lst_assembly = combine_blocks_to_list(lst_blocks)

    text = []
    for lst_instructions in lst_assembly:
        try:
            if lst_instructions[0] in map_group0:
                objhex = assembly_group0(lst_instructions)
            elif lst_instructions[0] in map_group1:
                objhex = assembly_group1(lst_instructions)
            elif lst_instructions[0] in map_group2:
                objhex = assembly_group2(lst_instructions)
            elif lst_instructions[0] in map_group3:
                objhex = assembly_group3(lst_instructions)
            else:
                print lst_instructions
                raise PSMPPException('unsupport instruction!')

            text.append(objhex)
        except IndexError:
            print 'Error: parameters not enough for ', lst_instructions
            raise
        except:
            print 'Error:', lst_instructions
            raise

    print 'codes %d of 1024 rom (%d%%)'  % (nr_codes, (nr_codes * 100 / 1024))

    return (map_label_address, text)

usage = '''\
usage: %s [option] [file]

  -h                print this help
  -i <file>         Select input <file>
  -o <file>         Place output into <file>, '-' is stdout.
      --psm         Output kcpsm3 assembly
      --obj         Output kcpsm3 assembly with meta info
      --hex         Output kcpsm3 binary (hex)

assembly feature:
    1. digit
        Support 3 format: 0(dec), [1-9]...(dec), 0x...(hex), 0...(oct)

    2. macro
        `include "file.s"           -   include other file
        `define  macro   [value]    -   define macro
        `undef   macro              -   undef macro
        `nop                        -   wait one instruct
        `cond (ra == rb),   L_TRUE, L_FALSE
        `cond (ra == rb),   NULL, L_FALSE
    3. embedded python code, modify macro value
        ;#!python ...               -   embedded python code
''' % os.path.split(sys.argv[0])[1]

class PSMPPException(BaseException):
    def __init__(self, msg):
        self.msg = msg
        pass

def parse_commandline():
    s_config = 'hi:o:'
    l_config = ['help', 'psm', 'hex', 'obj']
    try:  
        opts, args = getopt.getopt(sys.argv[1:], s_config, l_config)

        #convert to map
        map_config = {}
        for (k, v) in opts:
            map_config[k] = v

        #check if output help
        if '-h' in map_config or '--help' in map_config:
            print usage
            sys.exit(0)

        #check output mode
        if not ('--psm' in map_config or '--hex' in map_config or '--obj' in map_config):
            raise PSMPPException('Unknow output mode!')

        #check input file name
        if '-i' not in map_config:
            if args and len(args) == 1:
                map_config['-i'] = args[0]
            else:
                raise PSMPPException('no source file found!')

        #get source file time
        t = os.stat(map_config['-i'])
        map_config['--st_ctime'] = time.ctime(t.st_ctime)
        map_config['--st_mtime'] = time.ctime(t.st_mtime)

        #check output file name
        name_without_path = os.path.split(map_config['-i'])[1]
        name_without_ext = os.path.splitext(name_without_path)[0]
        if not '-o' in map_config:
            if '--psm' in map_config:
                map_config['-o'] = name_without_ext + '.psm'
            elif '--hex' in map_config:
                map_config['-o'] = name_without_ext + '.hex'
            elif '--obj' in map_config:
                map_config['-o'] = name_without_ext + '.obj'

    except PSMPPException as e:
        print 'PSMPPException:', e.msg
        print
        print usage
        sys.exit(-1)
    except getopt.GetoptError:  
        raise

    return map_config

def dump_metainfo(map_config, symbols, lines):
    #dump symbols
    sym_filename = map_config['-o'] + '.symbol'
    s = dump_symbols(symbols)
    file_put_contents(sym_filename, s)
    print 'wrote %d bytes to "%s"' % \
            (len(s), sym_filename)

    #dump codes
    json_filename = map_config['-o'] + '.json'
    text_json = json.dumps(lines, indent=4)
    file_put_contents(json_filename, text_json)
    print 'wrote %d bytes to "%s"' % \
            (len(text_json), json_filename)

def file_get_contents(filename):
    fin = open(filename)
    text = fin.read()
    fin.close()
    return text

def file_put_contents(filename, s):
    fout = open(filename, 'w')
    fout.write(s)
    fout.close()

if __name__ == '__main__':
    map_config = parse_commandline()

    #parse source
    symbols = {}
    buf = file_get_contents(map_config['-i'])

    #get pblaze-cc information
    lst_info = re.findall(r';#!pblaze-cc (\w+) : ([^\n]+)', buf)

    #preprocess
    lines = preprocess(buf.split('\n'), symbols)

    #generate psm
    if '--psm' in map_config:
        try:
            text = generate_kcpsm3_asm(lines)
        except PSMPPException as e:
            print e.msg
            sys.exit(-1)

        if map_config['-o'] == '-':
            print text
        else:
            #dump assembly
            file_put_contents(map_config['-o'], text)
            print 'wrote %d bytes to "%s"' % \
                    (len(text), map_config['-o'])

            dump_metainfo(map_config, symbols, lines)

    elif ('--hex' in map_config) or ('--obj' in map_config):
        try:
            (map_label_address, lst_hexvalues) = generate_kcpsm3_hex(lines)
        except PSMPPException as e:
            print e.msg
            sys.exit(-1)

        #convert to ascii hex file
        lst_hexstring = []
        for d in lst_hexvalues:
            lst_hexstring.append('%05X' % d)

        #format label
        lst_labels_address = sorted(map_label_address.items(), key = lambda x:x[1])
        lst_labels = []
        for (k, v) in lst_labels_address:
            lst_labels.append(' (%05X, %s)' % (v, k))

        #output
        if '--hex' in map_config:
            hexstring    = '\n'.join(lst_hexstring)
            labelsstring = '\n'.join(lst_labels)

            if map_config['-o'] == '-':
                print hexstring
            else:
                #dump assembly
                file_put_contents(map_config['-o'], hexstring)
                print 'wrote %d bytes to "%s"' % \
                        (len(hexstring), map_config['-o'])

                labels_filename = map_config['-o'] + '.labels'
                file_put_contents(labels_filename, labelsstring)
                print 'wrote %d bytes to "%s"' % \
                        (len(labelsstring), labels_filename)

                dump_metainfo(map_config, symbols, lines)

        else:
            map_object = {}
            map_object['ctime']  = map_config['--st_ctime']
            map_object['mtime']  = map_config['--st_mtime']
            map_object['labels'] = map_label_address
            map_object['object'] = lst_hexvalues
            map_object['pblaze-cc'] = lst_info

            text_json = json.dumps(map_object, indent=4)
            file_put_contents(map_config['-o'], text_json)
            print 'wrote %d bytes to "%s"' % \
                (len(text_json), map_config['-o'])

