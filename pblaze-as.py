#!/usr/bin/env python2
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
# 2013.08.12    first release
#
#== warning ==
#   digit in pbcc generated asm, 10 means 10dec,
#   but in kcpsm3.exe 10 means 0x10.
# 
#
#== instruction set summary ==
#=== kcpsm3 instruction set ===
#
#   04000 (18'b000100000000000000): input
#   06000 (18'b000110000000000000): fetch
#   0A000 (18'b001010000000000000): and
#   0C000 (18'b001100000000000000): or
#   0E000 (18'b001110000000000000): xor
#   12000 (18'b010010000000000000): test
#   14000 (18'b010100000000000000): compare
#   18000 (18'b011000000000000000): add
#   1A000 (18'b011010000000000000): addcy
#   1C000 (18'b011100000000000000): sub
#   1E000 (18'b011110000000000000): subcy
#   20000 (18'b100000000000000000): sla
#   20002 (18'b100000000000000010): rl
#   20004 (18'b100000000000000100): slx
#   20006 (18'b100000000000000110): sl0
#   20007 (18'b100000000000000111): sl1
#   20008 (18'b100000000000001000): sra
#   2000A (18'b100000000000001010): srx
#   2000C (18'b100000000000001100): rr
#   2000E (18'b100000000000001110): sr0
#   2000F (18'b100000000000001111): sr1
#   2A000 (18'b101010000000000000): return
#   2C000 (18'b101100000000000000): output
#   2E000 (18'b101110000000000000): store
#   30000 (18'b110000000000000000): call
#   34000 (18'b110100000000000000): jump
#   38000 (18'b111000000000000000): returni
#   3C000 (18'b111100000000000000): disable
#   3C001 (18'b111100000000000001): enable
#   
#   +===================================+
#   |1|1|1|1|1|1|1|1| | | | | | | | | | |
#   |7|6|5|4|3|2|1|0|9|8|7|6|5|4|3|2|1|0|
#   +---------+-+-------+---------------+
#   |0 0 0 0 0|0|x x x x|k k k k k k k k| load sX, kk
#   |         |1|       |y y y y 0 0 0 0| load sX, sY
#   +---------+-+-------+---------------+
#   |0 0 0 0 1|                         |            
#   +---------+-+-------+---------------+
#   |0 0 0 1 0|0|x x x x|k k k k k k k k| input sX, kk
#   |         |1|       |y y y y 0 0 0 0| input sX, sY
#   +---------+-+-------+---------------+
#   |0 0 0 1 1|0|x x x x|k k k k k k k k| fetch sX, kk
#   |         |1|       |y y y y 0 0 0 0| fetch sX, sY
#   +---------+-+-------+---------------+
#   |0 0 1 0 0|                         |            
#   +---------+-+-------+---------------+
#   |0 0 1 0 1|0|x x x x|k k k k k k k k| and sX, kk
#   |         |1|       |y y y y 0 0 0 0| and sX, sY
#   +---------+-+-------+---------------+
#   |0 0 1 1 0|0|x x x x|k k k k k k k k| or  sX, kk
#   |         |1|       |y y y y 0 0 0 0| or  sX, sY
#   +---------+-+-------+---------------+
#   |0 0 1 1 1|0|x x x x|k k k k k k k k| xor sX, kk
#   |         |1|       |y y y y 0 0 0 0| xor sX, sY
#   +---------+-+-------+---------------+
#   |0 1 0 0 0|                         |            
#   +---------+-+-------+---------------+
#   |0 1 0 0 1|0|x x x x|k k k k k k k k| test sX, kk
#   |         |1|       |y y y y 0 0 0 0| test sX, sY
#   +---------+-+-------+---------------+
#   |0 1 0 1 0|0|x x x x|k k k k k k k k| compare sX, kk
#   |         |1|       |y y y y 0 0 0 0| compare sX, sY
#   +---------+-+-------+---------------+
#   |0 1 0 1 1|                         |            
#   +---------+-+-------+---------------+
#   |0 1 1 0 0|0|x x x x|k k k k k k k k| add   sX, kk
#   |         |1|       |y y y y 0 0 0 0| add   sX, sY
#   +---------+-+-------+---------------+
#   |0 1 1 0 1|0|x x x x|k k k k k k k k| addcy sX, kk
#   |         |1|       |y y y y 0 0 0 0| addcy sX, sY
#   +---------+-+-------+---------------+
#   |0 1 1 1 0|0|x x x x|k k k k k k k k| sub   sX, kk
#   |         |1|       |y y y y 0 0 0 0| sub   sX, sY
#   +---------+-+-------+---------------+
#   |0 1 1 1 1|0|x x x x|k k k k k k k k| subcy sX, kk
#   |         |1|       |y y y y 0 0 0 0| subcy sX, sY
#   +---------+-+-------+---------------+
#   |1 0 0 0 0|0|x x x x|0 0 0 0 0 0 0 0| sla   sX
#   |         | |       |        0 0 1 0| rl    sX
#   |         | |       |        0 1 0 0| slx   sX
#   |         | |       |        0 1 1 0| sl0   sX
#   |         | |       |        0 1 1 1| sl1   sX
#   |         | |       |        1 0 0 0| sra   sX
#   |         | |       |        1 0 1 0| srx   sX
#   |         | |       |        1 1 0 0| rr    sX
#   |         | |       |        1 1 1 0| sr0   sX
#   |         | |       |        1 1 1 1| sr1   sX
#   +---------+-+-------+---------------+
#   |1 0 0 0 1|                         |            
#   |1 0 0 1 0|                         |            
#   |1 0 0 1 1|                         |            
#   |1 0 1 0 0|                         |            
#   +---------+-----+-------------------+
#   |1 0 1 0 1|0 0 0|0 0 0 0 0 0 0 0 0 0| return
#   |         |1 0 0|                   | return z
#   |         |1 0 1|                   | return nz
#   |         |1 1 0|                   | return c
#   |         |1 1 1|                   | return nc
#   +---------+-+---+---+---------------+
#   |1 0 1 1 0|0|x x x x|k k k k k k k k| output sX, kk
#   |         |1|       |y y y y 0 0 0 0| output sX, sY
#   +---------+-+-------+---------------+
#   |1 0 1 1 1|0|x x x x|k k k k k k k k| store  sX, kk
#   |         |1|       |y y y y 0 0 0 0| store  sX, sY
#   +---------+-+---+---+---------------+
#   |1 1 0 0 0|0 0 0|a a a a a a a a a a| call
#   |         |1 0 0|                   | call z
#   |         |1 0 1|                   | call nz
#   |         |1 1 0|                   | call c
#   |         |1 1 1|                   | call nc
#   +---------+-----+-------------------+
#   |1 1 0 0 1|                         |            
#   +---------+-----+-------------------+
#   |1 1 0 1 0|0 0 0|a a a a a a a a a a| jump    aaa
#   |         |1 0 0|                   | jump z  aaa
#   |         |1 0 1|                   | jump nz aaa
#   |         |1 1 0|                   | jump c  aaa
#   |         |1 1 1|                   | jump nc aaa
#   +---------+-----+-------------------+
#   |1 1 0 1 1|                         |            
#   +---------+-----+-----------------+-+
#   |1 1 1 0 0|0 0 0 0 0 0 0 0 0 0 0 0|0| returni disable
#   |         |                       |1| returni enable
#   +---------+-----------------------+-+
#   |1 1 1 1 0|0 0 0 0 0 0 0 0 0 0 0 0|0| disable interrupt
#   |         |                       |1| enable interrupt
#   +---------+-----------------------+-+
#   |1 1 1 1 1|                         |            
#   +-----------------------------------+
#   |1|1|1|1|1|1|1|1| | | | | | | | | | |
#   |7|6|5|4|3|2|1|0|9|8|7|6|5|4|3|2|1|0|
#   +===================================+
#
#=== kcpsm6 instruction set ===
# kcpsm6 jump,call,return condition flags is the same,
# except instruction absolute 'jump', 'call', 'return'.
#
#                    flags
#                    * ** 
#   return    : 18'b10_0101_0000_0000_0000
#   return nc : 18'b11_1101_0000_0000_0000
#   return nz : 18'b11_0101_0000_0000_0000
#   return  z : 18'b11_0001_0000_0000_0000
#   return  c : 18'b11_1001_0000_0000_0000
#                    * ** 
#
#   +--------------------+
#   |=  condition flag  =|
#   +--------+---+---+---+
#   |bits    | 16| 15| 14|
#   +--------+---+---+---+
#   |abs-jmp |  0|  0|  0|
#   |abs-cal |  0|  0|  0|
#   |abs-ret |  0|  0|  1|
#   +--------+---+---+---+
#   |z-jmp   |  1|  0|  0|
#   |nz-jmp  |  1|  0|  1|
#   |c-jmp   |  1|  1|  0|
#   |nc-jmp  |  1|  1|  1|
#   +--------+---+---+---+
#
#   02000 (18'b00_0010_0000_0000_0000): and
#   04000 (18'b00_0100_0000_0000_0000): or
#   06000 (18'b00_0110_0000_0000_0000): xor
#   08000 (18'b00_1000_0000_0000_0000): input
#   0A000 (18'b00_1010_0000_0000_0000): fetch
#   0C000 (18'b00_1100_0000_0000_0000): test
#   10000 (18'b01_0000_0000_0000_0000): add
#   12000 (18'b01_0010_0000_0000_0000): addcy
#   14000 (18'b01_0100_0000_0000_0000): sla
#   14002 (18'b01_0100_0000_0000_0010): rl
#   14004 (18'b01_0100_0000_0000_0100): slx
#   14006 (18'b01_0100_0000_0000_0110): sl0
#   14007 (18'b01_0100_0000_0000_0111): sl1
#   14008 (18'b01_0100_0000_0000_1000): sra
#   1400A (18'b01_0100_0000_0000_1010): srx
#   1400C (18'b01_0100_0000_0000_1100): rr
#   1400E (18'b01_0100_0000_0000_1110): sr0
#   1400F (18'b01_0100_0000_0000_1111): sr1
#   18000 (18'b01_1000_0000_0000_0000): sub
#   1A000 (18'b01_1010_0000_0000_0000): subcy
#   1C000 (18'b01_1100_0000_0000_0000): compare
#   20000 (18'b10_0000_0000_0000_0000): call
#   21000 (18'b10_0001_0000_0000_0000): return
#   22000 (18'b10_0010_0000_0000_0000): jump
#   28000 (18'b10_1000_0000_0000_0000): disable
#   28001 (18'b10_1000_0000_0000_0001): enable
#   29000 (18'b10_1001_0000_0000_0000): returni
#   2C000 (18'b10_1100_0000_0000_0000): output
#   2E000 (18'b10_1110_0000_0000_0000): store
#
#   +===================================+
#   |1|1|1|1|1|1|1|1| | | | | | | | | | |
#   |7|6|5|4|3|2|1|0|9|8|7|6|5|4|3|2|1|0|
#   +---------+-+-------+---------------+
#   |0 0 0 0 0|1|x x x x|k k k k k k k k| load sX, kk
#   |         |0|       |y y y y 0 0 0 0| load sX, sY
#   +---------+-+-------+---------------+
#   |0 0 0 0 1|1|x x x x|k k k k k k k k| and sX, kk
#   |         |0|       |y y y y 0 0 0 0| and sX, sY
#   +---------+-+-------+---------------+
#   |0 0 0 1 0|1|x x x x|k k k k k k k k| or  sX, kk
#   |         |0|       |y y y y 0 0 0 0| or  sX, sY
#   +---------+-+-------+---------------+
#   |0 0 0 1 1|1|x x x x|k k k k k k k k| xor sX, kk
#   |         |0|       |y y y y 0 0 0 0| xor sX, sY
#   +---------+-+-------+---------------+
#   |0 0 1 0 0|1|x x x x|k k k k k k k k| input sX, kk
#   |         |0|       |y y y y 0 0 0 0| input sX, sY
#   +---------+-+-------+---------------+
#   |0 0 1 0 1|1|x x x x|k k k k k k k k| fetch sX, kk
#   |         |0|       |y y y y 0 0 0 0| fetch sX, sY
#   +---------+-+-------+---------------+
#   |0 0 1 1 0|1|x x x x|k k k k k k k k| test sX, kk
#   |         |0|       |y y y y 0 0 0 0| test sX, sY
#   +---------+-+-------+---------------+
#   |0 0 1 1 1|                         |
#   +---------+-+-------+---------------+
#   |0 1 0 0 0|1|x x x x|k k k k k k k k| add sX, kk
#   |         |0|       |y y y y 0 0 0 0| add sX, sY
#   +---------+-+-------+---------------+
#   |0 1 0 0 1|1|x x x x|k k k k k k k k| addcy sX, kk
#   |         |0|       |y y y y 0 0 0 0| addcy sX, sY
#   +---------+-+-------+---------------+
#   |0 1 0 1 0|0|x x x x|0 0 0 0 0 0 0 0| sla   sX
#   |         | |       |        0 0 1 0| rl    sX
#   |         | |       |        0 1 0 0| slx   sX
#   |         | |       |        0 1 1 0| sl0   sX
#   |         | |       |        0 1 1 1| sl1   sX
#   |         | |       |        1 0 0 0| sra   sX
#   |         | |       |        1 0 1 0| srx   sX
#   |         | |       |        1 1 0 0| rr    sX
#   |         | |       |        1 1 1 0| sr0   sX
#   |         | |       |        1 1 1 1| sr1   sX
#   +---------+-+-------+---------------+
#   |0 1 0 1 1|                         |
#   +---------+-+-------+---------------+
#   |0 1 1 0 0|1|x x x x|k k k k k k k k| sub   sX, kk
#   |         |0|       |y y y y 0 0 0 0| sub   sX, sY
#   +---------+-+-------+---------------+
#   |0 1 1 0 1|1|x x x x|k k k k k k k k| subcy sX, kk
#   |         |0|       |y y y y 0 0 0 0| subcy sX, sY
#   +---------+-+-------+---------------+
#   |0 1 1 1 0|1|x x x x|k k k k k k k k| compare sX, kk
#   |         |0|       |y y y y 0 0 0 0| compare sX, sY
#   +-+-------+-+-------+---------------+
#   |1|0 0 0|0 0|0 0 a a a a a a a a a a| call
#   | |1 0 0|   |                       | call z
#   | |1 0 1|   |                       | call nz
#   | |1 1 0|   |                       | call c
#   | |1 1 1|   |                       | call nc
#   +-+-----+---+-----------------------+
#   |1|0 0 1|0 1|0 0 0 0 0 0 0 0 0 0 0 0| return  <-- bit14 is '1'!
#   | |1 0 0|   |                       | return z
#   | |1 0 1|   |                       | return nz
#   | |1 1 0|   |                       | return c
#   | |1 1 1|   |                       | return nc
#   +-------+---+-----------------------+
#   |1|0 0 0|1 0|1 0 a a a a a a a a a a| jump    aaa
#   | |1 0 0|   |                       | jump z  aaa
#   | |1 0 1|   |                       | jump nz aaa
#   | |1 1 0|   |                       | jump c  aaa
#   | |1 1 1|   |                       | jump nc aaa
#   +-+-----+---+-----------------------+
#   |1 0 0 0 1 1|                       |
#   |1 0 0 1 1 1|                       |
#   +-----------+-------+---------------+
#   |1 0 1 0 0 0|0 0 0 0 0 0 0 0 0 0 0|0| disable interrupt
#   |           |                     |1| enable interrupt
#   +-----------+---------------------+-+
#   |1 0 1 0 0 1|0 0 0 0 0 0 0 0 0 0 0|0| returni disable
#   |           |                     |1| returni enable
#   +---------+-+-------+-------------+-+
#   |1 0 1 1 0|1|x x x x|k k k k k k k k| output sX, kk
#   |         |0|       |y y y y 0 0 0 0| output sX, sY
#   +---------+-+-------+---------------+
#   |1 0 1 1 1|1|x x x x|k k k k k k k k| store  sX, kk
#   |         |0|       |y y y y 0 0 0 0| store  sX, sY
#   +---------+-+-------+---------------+
#   |1 1 0 0 1 1|                       |
#   |1 1 0 1 1 1|                       |
#   |1 1 1 0 1 1|                       |
#   |1 1 1 1 1 1|                       |
#   +-----------------------------------+
#   |1|1|1|1|1|1|1|1| | | | | | | | | | |
#   |7|6|5|4|3|2|1|0|9|8|7|6|5|4|3|2|1|0|
#   +===================================+
import re
import os
import sys
import types
import getopt
import json
import time
import copy

#///////////////////////////////////////////////////////////////////////////////
class DefaultException(BaseException):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class PSMPPException(BaseException):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg


#///////////////////////////////////////////////////////////////////////////////
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

#///////////////////////////////////////////////////////////////////////////////
def file_get_contents(filename):
    fin = open(filename)
    text = fin.read()
    fin.close()
    return text

def file_put_contents(filename, s):
    fout = open(filename, 'w')
    fout.write(s)
    fout.close()


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

def explode_18bits(v18):
    l = []
    for i in range(18):
        if v18 & (1 << i):
            l.append('1')
        else:
            l.append('0')
    l.reverse()
    return l


#///////////////////////////////////////////////////////////////////////////////
#parse interface
def _parse_preprocessor_macro(s):
    for regex in lst_regex_preprocess :
        if regex.match(s):
            return regex.search(s).groups()

    return None

def _parse_instruction(s):
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
def _convert_digit(s):
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

def _convert_char(elem):
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

def _convert_symbol(elem, symbols):
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
def _preprocess_embedded(result, symbols):
    embedded_code = result.groups()[1]
    try:
        exec(embedded_code, {}, symbols)
    except:
        print '"%s" is illegal!' % result.string
        print
        raise

def _preprocess_macro(result, lst_inner_asm, symbols):
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
        _preprocess_normal(instructions, lst_inner_asm, symbols)

        #jump
        if ((label_true != '') and (label_true.lower() != 'null')):
            instructions = ['jump', F_TRUE, label_true]
            _preprocess_normal(instructions, lst_inner_asm, symbols)

            if ((label_false != '') and (label_false.lower() != 'null')):
                instructions = ['jump', label_false]
                _preprocess_normal(instructions, lst_inner_asm, symbols)

        elif ((label_false != '') and (label_false.lower() != 'null')):
            instructions = ['jump', F_FALSE, label_false]
            _preprocess_normal(instructions, lst_inner_asm, symbols)

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
                v = _convert_digit(v)
            symbols[result[1]] = v

    elif result[0] == 'undef':
        if len(result) == 1:
            raise
        elif result[1] in symbols:
            del symbols[result[1]]

def _preprocess_normal(instructions, lst_inner_asm, symbols):
    newinstructions = []
    i = 0
    nr_elems = len(instructions)
    while i < nr_elems:
        elem = instructions[i]
        #check char such like : 'c'
        new_elem = _convert_char(elem)
        if new_elem:
            newinstructions.append(new_elem)
            i += 1
            continue

        #check macro
        new_elem = _convert_symbol(elem, symbols)
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
                newinstructions.append(_convert_digit(elem))
            else:
                msg = '"%s" not a macro or register name!' % str(elem)
                raise DefaultException(msg)
        else:
            newinstructions.append(elem)

        i += 1

    #end of for elem in instructions:

    lst_inner_asm.append(newinstructions)

def _format_digit(inst, d):
    #convert string to int if need.
    d = _convert_digit(d)

    #output string
    if inst.upper() in ['ADDRESS', 'JUMP']:
        return '%03X' % d
    else:
        return '%02X' % d

def _format_asm(lines):
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
                newinstructions.append(_format_digit(instructions[0], elem))
            else:
                newinstructions.append(elem)

        #end of for elem in instructions:

        lst_kcpsm3_asm.append(newinstructions)
    return lst_kcpsm3_asm

def _dump_symbols(symbols):
    lst_buffer = []
    for sym in sorted(symbols):
        lst_buffer.append('%-20s : %s' % (sym, repr(symbols[sym])))
    return '\n'.join(lst_buffer)

class PSMBlock(object):
    def __init__(self):
        self.labels     = []
        self.address    = -1
        self.codes      = []

    def __len__(self):
        return len(self.codes)

def _convert_list_to_blocks(lines):
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

def _arrange_address_to_rom(lst_blocks):
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

def _convert_label_to_address(lst_blocks):
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
                if l in map_label_address:
                    lst_instructions[-1] = map_label_address[l]
                    continue

                try:
                    lst_instructions[-1] = _convert_digit(l)
                except:
                    msg = 'not found label "%s"!' % l
                    raise PSMPPException(msg)

    return map_label_address

def _combine_blocks_to_list(lst_blocks):
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

def _parse_register_name(s):
    # (rX)
    if re.match(r'^\(s[0-9a-fA-F]+\)$', s):
        return int(s[2], 16)
    # rX
    elif re.match(r'^s[0-9a-fA-F]+$', s):
        return int(s[1], 16)

    msg = 'Unknow register name "' + s + '"'
    raise PSMPPException(msg)

def _parse_cond_flag3(opname, cond, cfg):
    m = cfg['cond']
    if not cond:
        return m['jump']

    cond = cond.lower()
    if cond not in m:
        msg = 'Unknow condition "' + cond + '"'
        raise PSMPPException(msg)
    return m[cond]

def _parse_cond_flag6(opname, cond, cfg):
    m = cfg['cond']
    if not cond and opname == 'return':
        return m['return']
    if not cond:
        return m['jump']

    cond = cond.lower()
    if cond not in m:
        msg = 'Unknow condition "' + cond + '"'
        raise PSMPPException(msg)
    return m[cond]

def _assembly_alu(opcode, instruction, cfg):
    sX = instruction[1]
    sY = instruction[2]
    KK = instruction[2]

    objhex = opcode
    objhex = objhex | (_parse_register_name(sX) << 8)

    if type(sY) == types.IntType:
        objhex = objhex | KK
    elif type(sY) == types.StringType:
        objhex = objhex | (_parse_register_name(sY) << 4)
    else:
        raise PSMPPException('Unknow type of parameters')

    #difference of bit-12:
    # +------+---------+---------+
    # |value |0        |1        |
    # +------+---------+---------+
    # |kcpsm3|immediate|register |
    # |kcpsm6|register |immediate|
    # +------+---------+---------+
    if type(sY) == types.IntType and '--kcpsm6' in cfg:
        objhex = objhex | 0x01000
    if type(sY) == types.StringType and '--kcpsm3' in cfg:
        objhex = objhex | 0x01000

    return objhex

def _assembly_control(opcode, instruction, cfg):
    if len(instruction) == 1:
        cond = None
        AAA  = 0
    elif len(instruction) == 2:
        if instruction[0] == 'return':
            cond = instruction[1]
            AAA  = 0
        elif instruction[0] == 'returni':
            cond = None
            AAA  = int(instruction[1] == 'enable')
        elif instruction[1] == 'interrupt':
            cond = None
            AAA  = int(instruction[0] == 'enable')
        else:
            cond = None
            AAA  = instruction[1]

    elif len(instruction) == 3:
        cond = instruction[1]
        AAA  = instruction[2]

    else:
        raise PSMPPException('Too many parameters')

    if '--kcpsm6' in cfg:
        objhex = opcode | AAA
        if instruction[0] == 'return':
            objhex = objhex + _parse_cond_flag6(instruction[0], cond, cfg)
        else:
            objhex = objhex | _parse_cond_flag6(instruction[0], cond, cfg)
    else:
        objhex = opcode | _parse_cond_flag3(instruction[0], cond, cfg) | AAA

    return objhex

def _assembly_shift(opcode, instruction, cfg):
    objhex  = opcode | (_parse_register_name(instruction[1]) << 8)
    return objhex

def _get_kcpsm3_assembler():
    kcpsm3_cond = {'z':0x01000,'nz':0x1400,'c':0x01800,'nc':0x01C00, 'jump':0}
    kcpsm3_opcodes = { \
        'load'      :(0x00000, _assembly_alu),
        'move'      :(0x00000, _assembly_alu),
        'mov'       :(0x00000, _assembly_alu),

        'input'     :(0x04000, _assembly_alu),
        'fetch'     :(0x06000, _assembly_alu),

        'and'       :(0x0A000, _assembly_alu),
        'or'        :(0x0C000, _assembly_alu),
        'xor'       :(0x0E000, _assembly_alu),

        'test'      :(0x12000, _assembly_alu),# and
        'compare'   :(0x14000, _assembly_alu),# sub
        'add'       :(0x18000, _assembly_alu),
        'addcy'     :(0x1A000, _assembly_alu),
        'sub'       :(0x1C000, _assembly_alu),
        'subcy'     :(0x1E000, _assembly_alu),

        'output'    :(0x2C000, _assembly_alu),
        'store'     :(0x2E000, _assembly_alu),

        'return'    :(0x2A000, _assembly_control),
        'call'      :(0x30000, _assembly_control),
        'jump'      :(0x34000, _assembly_control),
        'returni'   :(0x38000, _assembly_control),
        'enable'    :(0x3C001, _assembly_control),
        'disable'   :(0x3C000, _assembly_control),

        'sla'       :(0x20000, _assembly_shift),
        'rl'        :(0x20002, _assembly_shift),
        'slx'       :(0x20004, _assembly_shift),
        'sl0'       :(0x20006, _assembly_shift),
        'sl1'       :(0x20007, _assembly_shift),

        'sra'       :(0x20008, _assembly_shift),
        'srx'       :(0x2000A, _assembly_shift),
        'rr'        :(0x2000C, _assembly_shift),
        'sr0'       :(0x2000E, _assembly_shift),
        'sr1'       :(0x2000F, _assembly_shift),
        'inst'      :(0, lambda opcode, insts, cfg: insts[1])
    }
    return (kcpsm3_cond, kcpsm3_opcodes)

def _get_kcpsm6_assembler():
    kcpsm6_cond = {'z':0x10000,'nz':0x14000,'c':0x18000,'nc':0x1C000, 'return':0x04000, 'jump':0}
    kcpsm6_opcodes = { \
        'load'      :(0x00000, _assembly_alu),
        'move'      :(0x00000, _assembly_alu),
        'mov'       :(0x00000, _assembly_alu),

        'input'     :(0x08000, _assembly_alu),
        'fetch'     :(0x0A000, _assembly_alu),

        'and'       :(0x02000, _assembly_alu),
        'or'        :(0x04000, _assembly_alu),
        'xor'       :(0x06000, _assembly_alu),

        'test'      :(0x0C000, _assembly_alu),# and
        'testcy'    :(0x0E000, _assembly_alu),# andcy
        'add'       :(0x10000, _assembly_alu),
        'addcy'     :(0x12000, _assembly_alu),

        'sla'       :(0x14000, _assembly_shift),
        'rl'        :(0x14002, _assembly_shift),
        'slx'       :(0x14004, _assembly_shift),
        'sl0'       :(0x14006, _assembly_shift),
        'sl1'       :(0x14007, _assembly_shift),

        'sra'       :(0x14008, _assembly_shift),
        'srx'       :(0x1400A, _assembly_shift),
        'rr'        :(0x1400C, _assembly_shift),
        'sr0'       :(0x1400E, _assembly_shift),
        'sr1'       :(0x1400F, _assembly_shift),

        'sub'       :(0x18000, _assembly_alu),
        'subcy'     :(0x1A000, _assembly_alu),
        'compare'   :(0x1C000, _assembly_alu),# sub
        'comparecy' :(0x1E000, _assembly_alu),# subcy

        'output'    :(0x2C000, _assembly_alu),
        'store'     :(0x2E000, _assembly_alu),

        'call'      :(0x20000, _assembly_control),
        'return'    :(0x21000, _assembly_control),
        'jump'      :(0x22000, _assembly_control),
        'disable'   :(0x28000, _assembly_control),
        'enable'    :(0x28001, _assembly_control),
        'returni'   :(0x29000, _assembly_control),

        'inst'      :(0, lambda opcode, insts, cfg: insts[1])
    }
    return (kcpsm6_cond, kcpsm6_opcodes)

def parse_commandline(argv):
    s_config = 'ghi:o:36'
    l_config = ['help', 'psm', 'hex', 'obj', 'mem']
    try:  
        opts, args = getopt.getopt(argv[1:], s_config, l_config)

        #convert to map
        map_config = {}
        for (k, v) in opts:
            map_config[k] = v

        #check if output help
        if '-h' in map_config or '--help' in map_config:
            print_usage(True)
            sys.exit(0)

        if '-6' in map_config:
            map_config['--kcpsm6'] = True
            print 'kcpsm6 mode'
        elif '-3' in map_config:
            map_config['--kcpsm3'] = True
            print 'kcpsm3 mode'
        else:
            map_config['--kcpsm3'] = True
            print 'default kcpsm3 mode'

        #check output mode
        if not ('--psm' in map_config or '--hex' in map_config or '--obj' in map_config):
            map_config['--obj'] = True
            print 'default obj output mode'
            #raise PSMPPException('Unknow output mode!')

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
        map_config['--noext'] = name_without_ext
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
        print_usage()
        sys.exit(-1)
    except getopt.GetoptError:  
        raise

    return map_config

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
                _preprocess_embedded(res, symbols)
                continue

            #check comment, remove comments
            line = re.sub(r';(.*)$', '', line)

            #just ignore '|'
            line = re.sub(r'\|(.*)', '', line)

            #skip all whitespace line
            if re.match('^[\t ]*$', line):
                continue

            #check and process preprocess macro
            result = _parse_preprocessor_macro(line)
            if result:
                _preprocess_macro(result, lst_inner_asm, symbols)
                continue

            #process normal text
            instructions = _parse_instruction(line)
            if instructions:
                _preprocess_normal(instructions, lst_inner_asm, symbols)

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

def dump_hex(lines, cfg):
    lst_blocks = _convert_list_to_blocks(lines)
    _arrange_address_to_rom(lst_blocks)
    map_label_address = _convert_label_to_address(lst_blocks)
    nr_codes, lst_assembly = _combine_blocks_to_list(lst_blocks)

    if '--kcpsm6' in cfg:
        cond_lut, lut = _get_kcpsm6_assembler()
    else:
        cond_lut, lut = _get_kcpsm3_assembler()
    cfg['cond'] = cond_lut

    text = []
    for instruction in lst_assembly:
        try:
            opname = instruction[0]
            if opname not in lut:
                print instruction
                raise PSMPPException('Unsupport instruction!')

            opcode, generator = lut[opname]
            objhex = generator(opcode, instruction, cfg)

            text.append(objhex)

        except:
            print 'Error:', instruction
            raise

    print 'codes %d of 1024 rom (%d%%)'  % (nr_codes, (nr_codes * 100 / 1024))

    return (map_label_address, text)

def dump_asm(lines):
    #convert digit to string.
    lines = _format_asm(lines) 
    text = []

    text.append(';' + '-'*60)
    text.append(';generate by pblaze-as.py')
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

def dump_ximem(rom):
    n = len(rom)
    erom = copy.deepcopy(rom)
    for i in xrange(n,1024):
        erom.append(0)

    n = len(erom)
    l = ['@00000000']
    rec = ''

    for i in xrange(n):
        if (i % 8) == 0:
            if i != 0:
                l.append(rec)
                rec = ''
        rec = rec + '%05x ' % erom[i]
    if rec != '':
        l.append(rec)

    return l

def pblaze_as(argv):
    if len(argv) <= 1:
        print_usage()
        return

    map_config = parse_commandline(argv)

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
            text = dump_asm(lines)
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

    if '--hex' in map_config or '--obj' in map_config or '--mem' in map_config:
        try:
            (map_label_address, lst_hexvalues) = dump_hex(lines, map_config)
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

            if map_config['-o'] == '-':
                print hexstring
            else:
                file_put_contents(map_config['-o'], hexstring)
                print 'wrote %d bytes to "%s"' % \
                        (len(hexstring), map_config['-o'])

        if '--mem' in map_config:
            l = dump_ximem(lst_hexvalues)
            d = '\n'.join(l)
            fn = map_config['--noext'] + '.mem'
            file_put_contents(fn, d)
            print 'wrote %d bytes to "%s"' % \
                    (len(d), fn)

        if '--obj' in map_config:
            map_object = {}
            map_object['ctime']     = map_config['--st_ctime']
            map_object['mtime']     = map_config['--st_mtime']
            map_object['labels']    = map_label_address
            map_object['object']    = lst_hexvalues
            map_object['object-hex']= lst_hexstring
            map_object['pblaze-cc'] = lst_info

            text_json = json.dumps(map_object, sort_keys=True, indent=4)
            file_put_contents(map_config['-o'], text_json)
            print 'wrote %d bytes to "%s"' % \
                (len(text_json), map_config['-o'])

    if '-g' in map_config:
        if len(lines) > 0:
            json_filename = map_config['--noext'] + '.parsed'
            text_json = json.dumps(lines, indent=4)
            file_put_contents(json_filename, text_json)
            print 'wrote %d bytes to "%s"' % \
                    (len(text_json), json_filename)

        if len(symbols) > 0:
            sym_filename = map_config['--noext'] + '.symbol'
            s = _dump_symbols(symbols)
            file_put_contents(sym_filename, s)
            print 'wrote %d bytes to "%s"' % \
                    (len(s), sym_filename)

        if len(lst_labels) > 0:
            labelsstring = '\n'.join(lst_labels)
            labels_filename = map_config['--noext'] + '.labels'
            file_put_contents(labels_filename, labelsstring)
            print 'wrote %d bytes to "%s"' % \
                    (len(labelsstring), labels_filename)

    print

def _dump_opcode_bits():
    m = {}
    for k,v in _get_kcpsm3_assembler()[1].iteritems():
        m[v[0]] = k

    print 'KCPSM3:'
    for k in sorted(m):
        print " %05X (18'b%s): %s"  % (k, ''.join(explode_18bits(k)), m[k])

    m = {}
    for k,v in _get_kcpsm6_assembler()[1].iteritems():
        m[v[0]] = k

    print 'KCPSM6:'
    for k in sorted(m):
        print " %05X (18'b%s): %s"  % (k, ''.join(explode_18bits(k)), m[k])

def print_usage(more=False):
    print "usage: %s [option] [file]" % os.path.split(sys.argv[0])[1]
    
    print "  -h           print this help"
    print "  -3           kcpsm3 mode"
    print "  -6           kcpsm6 mode"
    print "  -i <file>    Select input <file>"
    print "  -o <file>    Place output into <file>, '-' is stdout"
    print "      --psm    Output kcpsm3 assembly"
    print "      --obj    Output kcpsm3 assembly object"
    print "      --hex    Output kcpsm3 binary (hex)"
    print "      --mem    Output kcpsm3 binary (mem)"
    if not more:
        return
    
    print "assembly feature:"
    print "    1. digit"
    print "        Support 3 format: 0(dec), [1-9]...(dec), 0x...(hex), 0...(oct)"
    print ""
    print "    2. macro"
    print "        `include \"file.s\"           -   include other file"
    print "        `define  macro   [value]    -   define macro"
    print "        `undef   macro              -   undef macro"
    print "        `nop                        -   wait one instruct"
    print "        `cond (ra == rb),   L_TRUE, L_FALSE"
    print "        `cond (ra == rb),   NULL, L_FALSE"
    print "    3. embedded python code, modify macro value"
    print "        ;#!python ...               -   embedded python code"


if __name__ == '__main__':
    pblaze_as(sys.argv)

