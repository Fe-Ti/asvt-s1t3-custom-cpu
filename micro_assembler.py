# Asembler for custom CPU with EA1 and custom ALU + 14 ext devices
# Copyright 2023 Fe-Ti aka Tim Kravchenko
"""
"""
from sys import argv
if len(argv) < 3:
    print("Fuck! U gave not enough args!1!!")
    exit(1)
def to_str(lst):
    string = ''
    for i in lst:
        string += str(i) + " "
    return string

LABEL = "LABEL"
NC = "NC"
NC_fill = 0
CONST = "CONST"
NUMBER = "NUMBER"

# ~ ref = "\\"
# ~ deref = "*"
comment_delim = ";"
label_suff = ":"
aliasing = "="
optional = "?"

class Assembler:
    def __init__(self, scheme, mnemonics):
        self.syntax_deps = scheme["syntax_deps"]
        self.mnemonics = mnemonics
        self.aliases = dict()
        self.labels = dict()
        self.linenum = 0
        self.ifile_line = 0
        self.compiled = list()
        self.romsize = scheme["rom_size"]
        self.roms = { i:list() for i in scheme["roms"] }
        self.rom_structure = dict()
        self.const_rom_name = ""
        for rom_name, rom_struct in scheme["roms"].items():
            struct = dict()
            size_left = self.romsize
            for part in rom_struct:
                part = part.split(':')
                if part[0] == CONST: # errr... only 1 rom
                    self.const_rom_name = rom_name #for constants supported :(
                size_left -= int(part[1])
                struct[part[0]] = 2**(size_left)
            self.rom_structure[rom_name] = struct

    def add_alias(self, line):
        if len(line) != 3:
            raise SyntaxError(
                f"Aliasing line must contain exactly 3 terms. Check line {self.ifile_line}"
                )
        if line[1] != aliasing or line[0] == aliasing or line[2] == aliasing:
            raise SyntaxError(
                f"Wrong aliasing syntax in line {self.ifile_line}."
                )
        if line[0] in self.aliases:
            raise SyntaxError(f"Alias {line[0]} already exists. Line {self.ifile_line}.")
        for mtype, mns in self.mnemonics.items():
            if line[2] in mns:
                self.aliases[line[0]] = line[2]
                return
        raise SyntaxError(f"Can't find mnemonic {line[2]}. Line {self.ifile_line}.")

    def add_label(self, label):
        if label not in self.labels:
            self.labels[label.strip(":")] = self.linenum
        else:
            raise SyntaxError(f"Label {label} already exists. Line {self.ifile_line}.")

    def get_mnc_info(self, mnc):
        if mnc in self.aliases:
            # ~ print(f"{mnc} = ", end="")
            mnc = self.aliases[mnc]
            # ~ print(mnc)
        for mtype, mns in self.mnemonics.items():
            if mnc in mns:
                mval = mns[mnc]
                # ~ print(f"Found {mtype} {mval} for {mnc}.")
                return mtype, mval
        raise SyntaxError(f"Can't find mnemonic {mnc}. Line {self.ifile_line}.")

    def get_rom_and_offset(self, mtype):
        rom_name = ""
        offset = 0
        for rom in self.rom_structure:
            if mtype in self.rom_structure[rom]:
                rom_name = rom
                offset = self.rom_structure[rom_name][mtype]
                break
        return rom_name, offset

    def process_line(self, line, collect_labels=False):
        # ~ if comment_delim in line:
            # ~ line = line[:line.index(comment_delim)]
        for i,term in enumerate(line):
            if line[i].startswith(comment_delim):
                line = line[:i]
                break
            line[i] = term.upper()
        # ~ print(line)
        self.ifile_line += 1
        if not line:
            return
        if aliasing in line:
            if collect_labels:
                self.add_alias(line)
            return
        i = 0
        if line[0].endswith(label_suff):
            if collect_labels:
                self.add_label(line[0])
                print(f"Added {line[0]} to labels.")
            line = line[1:]
        rom_line = { i:0 for i in self.roms }
        if not collect_labels:
            while i < len(line):
                if line[i].isdigit():
                    mval = int(line[i])
                    rom_name = self.const_rom_name
                    offset = self.rom_structure[rom_name][CONST]
                    rom_line[rom_name] += mval * offset
                    for mtype, mval in self.mnemonics[CONST].items():
                        rom_name, offset = self.get_rom_and_offset(mtype)
                        rom_line[rom_name] += mval * offset
                    i+=1
                    continue
                mtype, mval = self.get_mnc_info(line[i])
                if mtype not in self.syntax_deps:
                    rom_name, offset = self.get_rom_and_offset(mtype)
                    rom_line[rom_name] += mval * offset
                elif self.mnemonics[self.syntax_deps[mtype][0]] == LABEL:
                    if line[i+1] in self.labels:
                        mtype_next = self.syntax_deps[mtype][0]
                        mval_next = self.labels[line[i+1]]
                        rom_name, offset = self.get_rom_and_offset(mtype)
                        rom_line[rom_name] += mval * offset
                        rom_name, offset = self.get_rom_and_offset(mtype_next)
                        rom_line[rom_name] += mval_next * offset
                    else:
                        raise SyntaxError(f"Can't find label {line[i+1]}")
                    i += 1
                else:
                    mtype_next, mval_next =self.get_mnc_info(line[i+1])
                    if mtype_next in self.syntax_deps[mtype]:
                        rom_name, offset = self.get_rom_and_offset(mtype)
                        rom_line[rom_name] += mval * offset
                        rom_name, offset = self.get_rom_and_offset(mtype_next)
                        rom_line[rom_name] += mval_next * offset
                    else:
                        raise SyntaxError(f"{mtype} requires {self.syntax_deps[mtype]}.")
                    i += 1
                i += 1
            for rom_name, row in rom_line.items():
                self.roms[rom_name].append(row)
            # ~ print(f"Compiled {self.linenum} ({hex(self.linenum)}) {to_str(line)}")
            self.compiled.append(f"{self.linenum}/{hex(self.linenum)}: {to_str(line)}")
        self.linenum += 1

ms = {
    "rom_size"  : 8,
    "roms" : {
        "rom1" : ["NC:4", "SAVEFLAGS:1", "XSEL:3"],
        "rom2" : ["ADDR:8"],
        "rom3" : ["EXDEVA:4", "EXDCMD:4"],
        "rom4" : ["DEVAOVRD:1","IAD_W:3", "OPSEL:4"],
        "rom5" : ["CONST:4", "DCMDOVRD:1", "IAD_C:3"]
    },
    "syntax_deps" : {
        "EXDEVA": ["EXDCMD", "DCMDOVRD"],
        "DEVAOVRD": ["DCMDOVRD"],
        "XSEL"  : ["ADDR"],
        # ~ "IAD_C" : "IAD_W",
    },
    # ~ "formats" : [
        # ~ ["?LABEL", "OPSEL", "?C0", "?XSEL", "?"],
        # ~ ["?LABEL", "OPSEL", "?C0", "?XSEL", "?"],
    # ~ ]
}
mncs = {
    "DCMDOVRD":{
        "":0,
        "DCMDOVRD":1
    },
    "DEVAOVRD":{
        "":0,
        "DEVAOVRD":1
    },
    "SAVEFLAGS":{
        "":0,
        "SF":1
    },
    "XSEL": {
        ""      : 0,
        "JC4"   : 1,
        "JNC4"  : 2,
        "JZ"    : 3,
        "JNZ"   : 4,
        "JMP"   : 5,
    },
    "ADDR" : "LABEL",
    "EXDEVA" : {
        "DEV0" : 0,
        "DEV1" : 1,
        "DEV2" : 2,
        "DEV3" : 3,
        "DEV4" : 4,
        "DEV5" : 5,
        "DEV6" : 6,
        "DEV7" : 7,
        "DEV8" : 8,
        "DEV9" : 9,
        "DEV10" : 10,
        "DEV11" : 11,
        "DEV12" : 12,
        "DEV13" : 13,
        "DEV14" : 14,
        "DEV15" : 15
    },
    "EXDCMD" : {
        "DCMD0" : 0, # Z state on buffers FOR DEV0
        "DCMD1" : 1,
        "DCMD2" : 2,
        "DCMD3" : 3,
        "DCMD4" : 4,
        "DCMD5" : 5,
        "DCMD6" : 6,
        "DCMD7" : 7,
        "DCMD8" : 8,
        "DCMD9" : 9,
        "DCMD10" : 10,
        "DCMD11" : 11,
        "DCMD12" : 12,
        "DCMD13" : 13,
        "DCMD14" : 14,
        "DCMD15" : 15
    },
    "OPSEL" : {
        "" : 0,
        "SUM"   : 0,
        "+"     : 0,
        "SUM+1" : 8,
        "AND"   : 1,
        "&"     : 1,
        "NOT"   : 2,
        "NOT_A" : 2,
        "~A"    : 2,
        "OR"    : 3,
        "|"     : 3,
        ">>"    : 4,
        "<<"    : 5,
        "1>>"   : 12,
        "<<1"   : 13,
        "XOR"   : 6,
        "^"     : 6,
        "B>>A"  : 7,
        "A<<B"  : 15,
    },
    "IAD_W": {
        "" : 0,
        "R0" : 1,
        "R1" : 2,
        "R2" : 3,
        "R3" : 4,
        "R4" : 5,
        "RA" : 6,
        "RB" : 7
    },
    "IAD_C": {
        "" : 0,
        "C_R0"      :   1,
        "C_R1"      :   2,
        "C_R2"      :   3,
        "C_R3"      :   4,
        "C_R4"      :   5,
        "C_S"       :   6,
        "CONST_C"   :   7,
    },
    CONST: {
        "IAD_C" : 7,
    },
}
asm = Assembler(ms, mncs)
lines = list()
with open(argv[1]) as ifile:
    for line in ifile:
        lines.append(line.split())

for line in lines:
    asm.process_line(line, collect_labels=True)
print(f"File labels:")

lab_max_width = 0
for label, linenum in asm.labels.items():
    if len(label)+1 > lab_max_width:
        lab_max_width = len(label)+1
    print(f"Label: '{label}' == {linenum} ({hex(linenum)})")

asm.ifile_line = 0
asm.linenum = 0
for line in lines:
    asm.process_line(line, collect_labels=False)

line_max_width = 0
for line in asm.compiled:
    if len(line) > line_max_width:
        line_max_width = len(line)

from pathlib import Path
rom_files = { rom:open( Path(argv[2]) / (rom + ".bin"), "wb") for rom in asm.roms }
print("Writing rom files.")
for i in range(len(asm.roms["rom1"])): # Hardcoding we trust (c)
    label = ""
    for lb,ln in asm.labels.items():
        if ln == i:
            label = lb + ':'
    print(f"{label:{lab_max_width}}{asm.compiled[i]:{line_max_width}} ->", end=" ")
    for rom_name, rom in asm.roms.items():
        # ~ print(rom_name)
        rom_files[rom_name].write(rom[i].to_bytes())
        print(f"{rom[i]:b}".zfill(8), end=" ")
    print()
for rom_name, rom_file in rom_files.items():
    rom_file.close()

print(f"Assembled {asm.linenum} lines in total from {asm.ifile_line} lines of {argv[1]}")
