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
# ~ aliasing = "="
# ~ optional = "?"

class Assembler:
    def __init__(self, scheme, mnemonics):
        self.mnemonics = mnemonics
        self.aliases = dict()
        self.labels = dict()
        self.linenum = 0
        self.ifile_line = 0
        self.compiled = list()
        self.romsize = scheme["rom_size"]
        self.roms = { i:list() for i in scheme["roms"] }
        self.scheme = scheme
        self.rom_parts = dict()
        for rom_name, rom in scheme["roms"].items():
            for part in rom:
                if part in self.rom_parts:
                    self.rom_parts[part] += rom[part]
                else:
                    print(part, self.rom_parts, rom)
                    self.rom_parts[part] = rom[part]
        self.assembled = list()

    def add_label(self, label):
        if label not in self.labels:
            self.labels[label.strip(":")] = self.linenum
        else:
            raise SyntaxError(f"Label {label} already exists. Line {self.ifile_line}.")

    def assemble_roms(self):
        for rom_line_parts in self.assembled:
            rom_line = 0
            offset = 0
            for part, value in rom_line_parts.items():
                rom_line += value*2**offset
                offset += self.rom_parts[part]
            for rom_name, rom in self.roms.items():
                rom.append(rom_line % (2**self.romsize))
                rom_line = rom_line // (2**self.romsize)
            print(f"ROM line equals {rom_line}")
        return self.roms

    def process_line(self, line, collect_labels = False):
        line = line.lower()
        for i,char in enumerate(line):
            if line[i] == comment_delim:
                line = line[:i]
                break
        self.ifile_line += 1
        
        line = line.split()
        if not line:
            return
        i = 0
        if line[0].endswith(label_suff):
            if collect_labels:
                self.add_label(line[0])
                print(f"Added {line[0]} to labels.")
            line = line[1:]
        if not collect_labels:
            rom_line = {part:0 for part in self.rom_parts}
            print(rom_line)
            if line[0] not in self.mnemonics["instructions"]:
                raise SyntaxError(f"Can't find mnemonic {line[0]}. Line {self.ifile_line}.")
            instr_info = self.mnemonics["instructions"][line[0]]
            instr_args = instr_info["args"]
            instr_args_list = list(instr_args)
            instr_values = instr_info["values"]
            for valname in instr_values:
                rom_line[valname] = instr_values[valname]
            if (len(line)-1) != len(instr_args):
                raise SyntaxError(f"Not enough positional arguments in line {self.ifile_line}: {len(line)-1} instead of {len(instr_args)}.")
            args = line[1:]
            offset = 0
            coefficient = 1
            for i, arg_name in enumerate(instr_args):
                arg_prop = instr_args[arg_name]
                if i > 0:
                    print(arg_prop)
                    offset += instr_args[instr_args_list[i-1]][0]
                    coefficient = 2**offset
                if NUMBER in arg_prop:
                    if args[i].isdigit():
                        if args[i].startswith('0'):
                            rom_line["ARGS"] += coefficient * int(args[i], 8)
                        else:
                            rom_line["ARGS"] += coefficient * (int(args[i]))
                    elif args[i].lower().startswith("0x"):
                       rom_line["ARGS"] += coefficient * (int(args[i], 16))
                elif LABEL in arg_prop:
                    if args[i] in self.labels:
                        rom_line["ARGS"] += coefficient * (self.labels[args[i]])
                    else:
                        raise SyntaxError(f"Can't find label {args[i]} in line {self.ifile_line}.")
                else:
                    if args[i] not in self.mnemonics["constants"]:
                        raise SyntaxError(f"Unknown constant {args[i]} in line {self.ifile_line}.")
                    else:
                        rom_line["ARGS"] += coefficient * (self.mnemonics["constants"][args[i]])
            self.assembled.append(rom_line)
            self.compiled.append(f"{self.linenum}/{hex(self.linenum)}: {to_str(line)}")
        self.linenum += 1
        

ms = {
    "rom_size"  : 8,
    "roms" : {
        "cmdrom":{"CMD":8},
        "argrom1":{"ARGS":8},
        "argrom2":{"ARGS":4, "XSEL":4}
    },
}

mncs = {
    "ARG" : "args",
    "instructions" : {
        "set" : {
            "values" : {
                "CMD" : 0x0,
                },
            "args" : {
                "destination":[4],
                "constant":[4, NUMBER]
            }
        },
        "mov" : {
            "values" : {
                "CMD" : 0x1,
                },
            "args" : {
                "destination":[4],
                "source":[4]
            }
        },
        "jmp" : {
            "values" : {
                "CMD" : 0x2,
                "XSEL" : 0x5,
                },
            "args" : {
                "destination":[12, LABEL],
            }
        },
        "jc4" : {
            "values" : {
                "CMD" : 0x3,
                "XSEL": 0x1,
                },
            "args" : {
                "destination":[12, LABEL],
            }
        },
        "jnc4" : {
            "values" : {
                "CMD" : 0x4,
                "XSEL": 0x2,
                },
            "args" : {
                "destination":[12, LABEL],
            }
        },
        "jz" : {
            "values" : {
                "CMD" : 0x5,
                "XSEL": 0x3,
                },
            "args" : {
                "destination":[12, LABEL],
            }
        },
        "jnz" : {
            "values" : {
                "CMD" : 0x6,
                "XSEL": 0x4,
                },
            "args" : {
                "destination":[12, LABEL],
            }
        },
        "sum" : {
            "values" : {
                "CMD" : 0x7,
                },
            "args" : {
                "rX": [4],
                "rY": [4],
            }
        },
        "sub" : {
            "values" : {
                "CMD" : 0x8,
                },
            "args" : {
                "rX": [4],
                "rY": [4],
            }
        },
        "shr" : {
            "values" : {
                "CMD" : 0x9,
                },
            "args" : {
                "rX": [4],
            }
        },
        "shl" : {
            "values" : {
                "CMD" : 0xa,
                },
            "args" : {
                "rX": [4],
            }
        },
        "dshr" : {
            "values" : {
                "CMD" : 0xb,
                },
            "args" : {
                "rX": [4],
                "rY": [4],
            }
        },
        "dshl" : {
            "values" : {
                "CMD" : 0xc,
                },
            "args" : {
                "rX": [4],
                "rY": [4],
            }
        },
        "and" : {
            "values" : {
                "CMD" : 0xd,
                },
            "args" : {
                "rX": [4],
                "rY": [4],
            }
        },
        "xor" : {
            "values" : {
                "CMD" : 0xe,
                },
            "args" : {
                "rX": [4],
                "rY": [4],
            }
        },
        "or" : {
            "values" : {
                "CMD" : 0xf,
                },
            "args" : {
                "rX": [4],
                "rY": [4],
            }
        },
        "not" : {
            "values" : {
                "CMD" : 0x10,
                },
            "args" : {
                "rX": [4],
            }
        },
        "inc" : {
            "values" : {
                "CMD" : 0x11,
                },
            "args" : {
                "rX": [4],
            }
        },
        "chkin" : {
            "values" : {
                "CMD" : 0x12,
                },
            "args" : {
            }
        },
        "ldin" : {
            "values" : {
                "CMD" : 0x13,
                },
            "args" : {
                "destination": [4],
            }
        },
        "input" : {
            "values" : {
                "CMD" : 0x14,
                },
            "args" : {
                "destination": [4],
            }
        },
        "ind0" : {
            "values" : {
                "CMD" : 0x15,
                },
            "args" : {
                "source": [4],
            }
        },
        "ind1" : {
            "values" : {
                "CMD" : 0x16,
                },
            "args" : {
                "source": [4],
            }
        },
        "ind2" : {
            "values" : {
                "CMD" : 0x17,
                },
            "args" : {
                "source": [4],
            }
        },
        "ind3" : {
            "values" : {
                "CMD" : 0x18,
                },
            "args" : {
                "source": [4],
            }
        },
        "indctrl" : {
            "values" : {
                "CMD" : 0x19,
                },
            "args" : {
                "source": [4],
            }
        },
    },
    
    "constants" : {
        "r0" : 0x0,
        "r1" : 0x1,
        "r2" : 0x2,
        "r3" : 0x3,
        "r4" : 0x4,
        "r5" : 0x5,
        "r6" : 0x6,
        "r7" : 0x7,
    },
}
asm = Assembler(ms, mncs)
lines = list()
with open(argv[1]) as ifile:
    for line in ifile:
        asm.process_line(line, collect_labels=True)
        lines.append(line)

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

roms = asm.assemble_roms()
from pathlib import Path
rom_files = { rom:open( Path(argv[2]) / (rom + ".bin"), "wb") for rom in asm.roms }
print("Writing rom files.")
for i in range(len(roms["cmdrom"])): # Hardcoding we trust (c)
    label = ""
    for lb,ln in asm.labels.items():
        if ln == i:
            label = lb + ':'
    print(f"{label:{lab_max_width}}{asm.compiled[i]:{line_max_width}} ->", end=" ")
    for rom_name, rom in roms.items():
        # ~ print(rom_name)
        rom_files[rom_name].write(rom[i].to_bytes())
        print(f"{rom[i]:b}".zfill(8), end=" ")
    print()
for rom_name, rom_file in rom_files.items():
    rom_file.close()

print(f"Assembled {asm.linenum} lines in total from {asm.ifile_line} lines of {argv[1]}")
