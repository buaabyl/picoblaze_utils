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
import os
import sys
import json
import getopt
from mako.template import Template

tpl = '''\
`timescale 1 ps / 1ps

/* 
 * == pblaze-as ==
 * source : ${project}.s
 * create : ${ctime}
 * modify : ${mtime}
 */
/* 
 * == pblaze-ld ==
 * target : kcpsm3
 */

module ${project} (address, instruction, clk);
input [9:0] address;
input clk;
output [17:0] instruction;

RAMB16_S18 #(
    .INIT(18'h00000),

    // The following INIT_xx declarations specify the initial contents of the RAM
    // Address 0 to 255
%for (row, v) in group0_data:
    .INIT_${row}(256'h${v}),
%endfor

    // Address 256 to 511
%for (row, v) in group1_data:
    .INIT_${row}(256'h${v}),
%endfor

    // Address 512 to 767
%for (row, v) in group2_data:
    .INIT_${row}(256'h${v}),
%endfor

    // Address 768 to 1023
%for (row, v) in group3_data:
    .INIT_${row}(256'h${v}),
%endfor

    // The next set of INITP_xx are for the parity bits
    // Address 0 to 255
%for (row, v) in group0_parity:
    .INITP_${row}(256'h${v}),
%endfor

    // Address 256 to 511
%for (row, v) in group1_parity:
    .INITP_${row}(256'h${v}),
%endfor

    // Address 512 to 767
%for (row, v) in group2_parity:
    .INITP_${row}(256'h${v}),
%endfor

    // Address 768 to 1023
%for (row, v) in group3_parity:
    .INITP_${row}(256'h${v}),
%endfor

    // Output value upon SSR assertion
    .SRVAL(18'h000000),
    .WRITE_MODE("WRITE_FIRST")
) ram_1024_x_18(
    .DI  (16'h0000),
    .DIP  (2'b00),
    .EN (1'b1),
    .WE (1'b0),
    .SSR (1'b0),
    .CLK (clk),
    .ADDR (address),
    .DO (instruction[15:0]),
    .DOP (instruction[17:16])
);

endmodule
'''

def file_get_contents(filename):
    fin = open(filename)
    text = fin.read()
    fin.close()
    return text

def file_put_contents(filename, s):
    fout = open(filename, 'w')
    fout.write(s)
    fout.close()

usage = '''\
usage: %s [option] [file]

  -h                print this help
  -o <file>         Place output into <file>, '-' is stdout.
''' % os.path.split(sys.argv[0])[1]

class PBLDException(BaseException):
    def __init__(self, msg):
        self.msg = msg

def parse_commandline():
    s_config = 'ho:'
    l_config = ['help']

    try:
        opts, args = getopt.getopt(sys.argv[1:], s_config, l_config)
        #convert to map
        map_config = {}
        for (k, v) in opts:
            map_config[k] = v

        if ('-h' in map_config) or ('--help' in map_config) or len(args) == 0:
            print usage
            sys.exit(0)

        if '-o' not in map_config:
            name_without_path = os.path.split(args[0])[1]
            name_without_ext = os.path.splitext(name_without_path)[0]
            map_config['-o'] = name_without_ext + '.v'
        else:
            name_without_path = os.path.split(map_config['-o'])[1]
            name_without_ext = os.path.splitext(name_without_path)[0]

        map_config['--project'] = name_without_ext

        if len(args) != 1:
            raise PBLDException('Just support one object file!')

        map_config['-i'] = args[0]

    except PBLDException as e:
        print e.msg
        print
        print usage
        sys.exit(-1)

    return map_config

def load_object(map_config):
    #load object
    s = file_get_contents(map_config['-i'])
    map_object = json.loads(s)

    #fill zero to fix 1024
    n_padding = 1024 - len(map_object['object'])
    if n_padding > 0:
        print 'append %d zero to rom' % n_padding
        for i in range(n_padding):
            map_object['object'].append(0)

    return map_object

def convert_to_blockram(map_object):
    #split to data and parity
    row_data    = 0
    row_parity  = 0
    lst_data    = []
    lst_parity  = []

    n = len(map_object['object'])
    lst_d_cols = []
    lst_p_cols = []
    for i in range(n):
        #bit17_16 save to p
        #bit15_00 save to d
        v = map_object['object'][i]
        p = (v & 0x30000) >> 16
        d = v & 0xFFFF
        lst_d_cols.append(d)
        lst_p_cols.append(p)

        #convert to 256'h format
        if (i % 16) == 15:
            #prepare
            lst_d_cols.reverse()
            row = '%02X' % row_data
            row_data += 1
            #digit to string
            s = ''.join(['%04X' % tmp for tmp in lst_d_cols])
            #append
            lst_data.append((row, s))
            lst_d_cols = []

        if (i % 128) == 127:
            #convert 2bits to 4bits mode
            lst_tmp_p = []
            for j in range(64):
                tmp = lst_p_cols[2*j + 0] | (lst_p_cols[2*j + 1] << 2);
                lst_tmp_p.append(tmp)
            #preapre
            lst_tmp_p.reverse()
            row = '%02X' % row_parity
            row_parity += 1
            #digit to string
            s = ''.join(['%01X' % tmp for tmp in lst_tmp_p])
            #append
            lst_parity.append((row, s))
            lst_p_cols = []

    return (lst_data, lst_parity)

def render(map_config, map_object, lst_data, lst_parity):
    n = len(lst_data)
    step = n / 4
    group0_data = lst_data[0*step:1*step]
    group1_data = lst_data[1*step:2*step]
    group2_data = lst_data[2*step:3*step]
    group3_data = lst_data[3*step:4*step]

    n = len(lst_parity)
    step = n / 4
    group0_parity = lst_parity[0*step:1*step]
    group1_parity = lst_parity[1*step:2*step]
    group2_parity = lst_parity[2*step:3*step]
    group3_parity = lst_parity[3*step:4*step]

    tmpl = Template(tpl)
    text = tmpl.render(
            project=map_config['--project'],
            ctime=map_object['ctime'],
            mtime=map_object['mtime'],
            group0_data=group0_data,
            group1_data=group1_data,
            group2_data=group2_data,
            group3_data=group3_data,
            group0_parity=group0_parity,
            group1_parity=group1_parity,
            group2_parity=group2_parity,
            group3_parity=group3_parity)
    return text

if __name__ == '__main__':
    map_config = parse_commandline()
    map_object = load_object(map_config)
    (lst_data, lst_parity) = convert_to_blockram(map_object)
    text = render(map_config, map_object, lst_data, lst_parity)

    #insert pblaze-cc information
    lst_text = []
    lst_text.append('/*')
    lst_text.append(' * == pblaze-cc ==')
    if 'pblaze-cc' in map_object:
        for (k, v) in map_object['pblaze-cc']:
            lst_text.append(' * %s : %s' % (k, v))
    lst_text.append(' */')
    text = '\n'.join(lst_text) + '\n' + text

    if map_config['-o'] == '-':
        print text
    else:
        file_put_contents(map_config['-o'], text)
        print 'wrote %d bytes to "%s"' % \
            (len(text), map_config['-o'])

    print

