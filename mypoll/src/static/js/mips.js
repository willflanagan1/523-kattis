// fakeup a module like interface
var MIPS = (function () {
    var memPointer;
    var memory;
    var instr;
    var symbol;
    var unresolved;
    var breakpoint = [];
    var isAssembled;

    var useDOM = true; // set to false to enable running in node

    var opValue = {
        "j":2, "jal":3, "beq":4, "bne":5,
        "addi":8, "addiu":9, "slti":10, "sltiu":11,
        "andi":12, "ori":13, "xori":14, "lui":15,
        "lb":32, "lw":35, "sb":40, "sw":43,
        "sll":64, "srl":66, "sra":67, "sllv":68, "srlv":70, "srav":71,
        "jr":72, "jalr":73,
        "syscall":76,
        "mul":88, "div":90,
        "add":96, "addu":97, "sub":98, "subu":99,
        "and":100, "or":101, "xor":102, "nor":103,
        "slt":106, "sltu":107,
        ".word":-1, ".space":-2, ".asciiz":-3, ".text":-4, ".data":-5,
        ".globl":-6
    };

    var opDecode = [
        "ALU", "Inv", "j", "jal", "beq", "bne", "Inv", "Inv",
        "addi", "addiu", "slti", "sltiu", "andi", "ori", "xori", "lui",
        "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv",
        "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv",
        "lb",  "Inv", "Inv", "lw", "Inv", "Inv", "Inv", "Inv",
        "sb", "Inv", "Inv", "sw", "Inv", "Inv", "Inv", "Inv",
        "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv",
        "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv"
    ];

    var fnDecode = [
        "sll", "Inv", "srl", "sra", "sllv", "Inv", "srlv", "srav",
        "jr", "jalr", "Inv", "Inv", "syscall", "Inv", "Inv", "Inv",
        "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv",
        "mul", "Inv", "div", "Inv", "Inv", "Inv", "Inv", "Inv",
        "add", "addu", "sub", "subu", "and", "or", "xor", "nor",
        "Inv", "Inv", "slt", "sltu", "Inv", "Inv", "Inv", "Inv",
        "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv",
        "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv", "Inv"
    ];

    function toHex(val) {
        var hexval = '';
        for (var digit = 0; digit < 8; digit++) {
            hexval = "0123456789ABCDEF".charAt(val & 15) + hexval;
            val = val >> 4;
        }
        return "0x"+hexval;
    }

    function hexDump(valArray) {
        var hexString = new Array(valArray.length);
        for (var i = 0; i < valArray.length; i++) {
            hexString[i] = toHex(valArray[i]);
        }
        return hexString;
    }

    function trim(buffer, kruft) {
        kruft = (kruft == null) ? " \n\r\t" : kruft;
        var begin = 0;
        var end = buffer.length;
        while ((begin < end) && (kruft.indexOf(buffer.charAt(begin)) >= 0))
            begin += 1;
        while ((end > begin) && (kruft.indexOf(buffer.charAt(end-1)) >= 0))
            end -= 1;
        return buffer.substring(begin,end);
    }

    function stripComments(line) {
        var t = line.indexOf('#');
        var noComment = (t >= 0) ? line.substring(0,t) : line;
        return trim(noComment);
    }

    function addSymbol(label, value) {
        value = (typeof(value) == 'undefined') ? memPointer : value;
        symbol[label] = value;
        var backfill = unresolved[label];
        if (backfill != null) {
            // forward referenced labels are resolved here
            for (var i = 0; i < backfill.length; i++) {
                t = memory[backfill[i]];
                op = (t >> 26) & 63;
                if (op == 0) {          // .word
                    memory[backfill[i]] = 4*value;
                } else if (op < 4) {    // jumps
                    memory[backfill[i]] += (value & 0x3ffffff);
                } else if (op < 8) {    // branches
                    offset = (value - backfill[i]) & 0xffff;
                    memory[backfill[i]] = (t & 0xffff0000) + offset;
                } else if (op == 15) {   // lui
                    memory[backfill[i]] += ((4*value) >> 16) & 0xffff;
                } else if (op < 48) {   // load/store
                    memory[backfill[i]] += (4*value) & 0xffff;
                }
            }
            delete unresolved[label];
        }
    }

    function getSymbol(label) {
        var val;
        if (isNaN(label)) {
            val = symbol[label];
            if (val == null) {
                var backfill = unresolved[label];
                if (backfill == null) {
                    unresolved[label] = new Array();
                }
                unresolved[label].push(memPointer);
                val = 0;
            } else {
                val *= 4;
            }
        } else {
            val = parseInt(label);
        }
        return (val & 0x3ffffff);
    }

    function getRegister(arg) {
        var regName = {
                "zero":0, "at": 1, "v0":2, "v1":3,
                "a0":4, "a1":5, "a2":6, "a3":7,
                "t0":8, "t1":9, "t2":10, "t3":11,
                "t4":12, "t5":13, "t6":14, "t7":15,
                "s0":16, "s1":17, "s2":18, "s3":19,
                "s4":20, "s5":21, "s6":22, "s7":23,
                "t8":24, "t9":25, "k0":26, "k1":27,
                "gp":28, "sp":29, "fp":30, "ra":31
            };
        var t = arg.indexOf("$");
        if (t >= 0) {
            var reg = arg.substring(t+1,arg.length);
            if (isNaN(reg)) {
                t  = (reg in regName) ? regName[reg] : -1;
            } else {
                t = parseInt(reg);
            }
        }
        return t;
    }

    function getOffset(arg) {
        var t = arg.indexOf('(');
        var offset = (t > 0) ? arg.substring(0,t) : (t == 0) ? '0' : arg;
        return offset;
    }

    function getBase(arg) {
        var t1 = arg.indexOf('(');
        var t2 = arg.indexOf(')');
        var reg = ((t1 < 0) || (t2 < 0)) ? "$0" : arg.substring(t1+1,t2);
        return reg;
    }

    function appendRegOp(func, d, s, t) {
        if ((func < 4) || (func >= 48)) return -1;
        if ((d < 0) || (d >= 32)) return -2;
        if ((s < 0) || (s >= 32)) return -3;
        if ((t < 0) || (t >= 32)) return -4;
        var inst = s*(1<<21) + t*(1<<16) + d*(1<<11) + func;
        memory[memPointer] = inst;
        memPointer += 1;
        return 1;
    }

    function appendShift(shft, d, t, shamt) {
        if ((shft < 0) || (shft >= 4)) return -1;
        if ((d < 0) || (d >= 32)) return -2;
        if ((t < 0) || (t >= 32)) return -4;
        if ((shamt < 0) || (shamt >= 32)) return -5;
        var inst = t*(1<<16) + d*(1<<11) + shamt*(1<<6) + shft;
        memory[memPointer] = inst;
        memPointer += 1;
        return 1;
    }

    function appendImm16(op, t, s, imm16) {
        if ((op < 1) || (op >= 64)) return -1;
        if ((s < 0) || (s >= 32)) return -3;
        if ((t < 0) || (t >= 32)) return -4;
        imm16 = imm16 & 0xffff;
        var inst = op*(1<<26) + s*(1<<21) + t*(1<<16) + imm16;
        memory[memPointer] = inst;
        memPointer += 1;
        return 1;
    }

    function appendJump(op, imm26) {
        var inst = op*(1<<26) + imm26;
        memory[memPointer] = inst;
        memPointer += 1;
        return 1;
    }

    function appendWord(data) {
        memory[memPointer] = data & 0xffffffff;
        memPointer += 1;
        return 1;
    }

    function getChar(string, index) {
        return (index >= string.length) ? 0 : string.charCodeAt(index);
    }

    var pseudoOp = {
        "neg":0, "la":1, "not":2, "sgt":3, "b":4, "move":5, "nop":6, "negu":7,
        "subiu":8
    };

    function psTranslate(opcode, arg) {
        opIndex = pseudoOp[opcode];
        switch (opIndex) {
            case 0:                                // neg
                newop = opValue["sub"];
                arg.splice(1, 0, "$0");
                break;
            case 1:                                // la
                base = getBase(arg[1]);
                offset = getOffset(arg[1]);
                rt = getRegister(arg[0]);
                ival = parseInt(offset);
                fits16 = isNaN(ival) ? false : ((ival >= -32768) && (ival < 65336));
                if (fits16 == false) {
                    if (base == '$0') {
                        rval = isNaN(ival) ? getSymbol(offset) : ival;
                        t = appendImm16(opValue["lui"],rt,0,(rval>>16));  // lui
                        newop = opValue["ori"];
                        arg.splice(1, 1, arg[0], offset);
                    } else {
                        // Eventhough the two calls to getSymbol seem redundant
                        // they are necessary to assure that unresolved labels
                        // are backfilled in both the lui and ori instructions
                        rval = isNaN(ival) ? getSymbol(offset) : ival;
                        t = appendImm16(opValue["lui"],1,0,(rval>>16));  // lui
                        rval = isNaN(ival) ? getSymbol(offset) : ival;
                        t = appendImm16(opValue["ori"],1,1,rval);       // ori
                        newop = opValue["addu"];
                        arg.splice(1, 1, "$1", base);
                    }
                } else {
                    if (ival > 32767) {
                        if (base == '$0') {
                            newop = opValue["ori"];
                            arg.splice(1, 1, "$0", offset);
                        } else {
                            t = appendImm16(opValue["ori"],rt,0,ival);   // ori
                            newop = opValue["addu"];
                            arg.splice(1, 1, arg[0], base);
                        }
                    } else {
                        newop = opValue["addiu"];
                        arg.splice(1, 1, base, offset);
                    }
                }
                break;
            case 2:                                // not
                newop = opValue["nor"];
                arg.splice(1, 0, "$0");
                break;
            case 3:                                // sge
                newop = opValue["slt"];
                arg.splice(1, 2, arg[2], arg[1]);
                break;
            case 4:                                // b
                newop = opValue["beq"];
                arg.splice(0, 0, "$0", "$0");
                break;
            case 5:                                // move
                newop = opValue["addi"];
                arg.splice(2, 0, "0");
                break;
            case 6:                                // nop
                newop = opValue["sll"];
                arg.splice(0, 0, "$0", "$0", "0");
                break;
            case 7:                                // negu
                newop = opValue["subu"];
                arg.splice(1, 0, "$0");
                break;
            case 8:                                // subiu
                newop = opValue["addiu"];
                arg[2] = (arg[2].charAt(0) == '-') ? arg[2].substring(1) : '-' + arg[2];
                break;
        }
        return newop;
    }

    function asmToMemory(buffer) {
        var rd, rs, rt, shamt, imm16;
        var t = buffer.indexOf(" ");
        if (t < 0) t = buffer.indexOf("\t");
        if (t < 0) t = buffer.length;
        opcode = buffer.substring(0,t).toLowerCase();
        arg = buffer.substring(t+1,buffer.length).split(",");
        for (var i = 0; i < arg.length; i++)
            arg[i] = trim(arg[i]);
        if (opcode in pseudoOp) {
            t = psTranslate(opcode, arg);
        } else if (opcode in opValue) {
            t = opValue[opcode];
        } else {
            return -1;
        }
        var s = 0;
        var wordsGenerated = 0;
        if (t >= 64) {
            t = t & 63;
            if (t < 4) {                                // shift instruction format
                if (arg.length != 3) return -8;
                rd = getRegister(arg[0]);
                rt = getRegister(arg[1]);
                shamt = parseInt(arg[2]);
                wordsGenerated = appendShift(t,rd,rt,shamt);
            } else if (t < 8) {                         // variable shift instructions
                if (arg.length != 3) return -8;
                rd = getRegister(arg[0]);
                rt = getRegister(arg[1]);
                rs = getRegister(arg[2]);
                wordsGenerated = appendRegOp(t,rd,rs,rt);
            } else if (t == 8) {                        // jr instruction
                if (arg.length != 1) return -8;
                rs = getRegister(arg[0]);
                wordsGenerated = appendRegOp(t,0,rs,0);
            } else if (t == 9) {                        // jalr instruction
                if (arg.length != 2) return -8;
                rs = getRegister(arg[0]);
                rd = (arg.length > 1) ? getRegister(arg[1]) : 31;
                wordsGenerated = appendRegOp(t,rd,rs,0);
            } else if (t == 12) {                       // syscall
                if (arg.length != 1) return -8;
                wordsGenerated = appendRegOp(t,0,0,0);
            } else {                                    // 3-register format
                if (arg.length != 3) return -8;
                rd = getRegister(arg[0]);
                rs = getRegister(arg[1]);
                rt = getRegister(arg[2]);
                wordsGenerated = appendRegOp(t,rd,rs,rt);
            }
        } else if (t > 0) {
            if (t < 4) {                                // jumps
                if (arg.length != 1) return -8;
                s = getSymbol(arg[0])>>2;
                wordsGenerated = appendJump(t,s);
            } else if (t < 8) {                         // branches
                if (arg.length != 3) return -8;
                rs = getRegister(arg[0]);
                rt = getRegister(arg[1]);
                imm16 = (getSymbol(arg[2])>>2) - memPointer;
                wordsGenerated = appendImm16(t,rt,rs,imm16);
            } else if (t < 15) {                        // immediate format
                if (arg.length != 3) return -8;
                rt = getRegister(arg[0]);
                rs = getRegister(arg[1]);
                imm16 = (isNaN(arg[2])) ? getSymbol(arg[2]) : parseInt(arg[2]);
                wordsGenerated = appendImm16(t,rt,rs,imm16);
            } else if (t == 15) {                       // lui
                if (arg.length != 2) return -8;
                rt = getRegister(arg[0]);
                imm16 = (isNaN(arg[1])) ? (getSymbol(arg[1]) >> 16) : parseInt(arg[1]);
                wordsGenerated = appendImm16(t,rt,0,imm16);
            } else {                                    // load/store instructions
                if (arg.length != 2) return -8;
                rt = getRegister(arg[0]);
                rs = getRegister(getBase(arg[1]));
                imm16 = getOffset(arg[1]);
                if (isNaN(imm16))
                    imm16 = getSymbol(imm16);
                wordsGenerated = appendImm16(t,rt,rs,imm16);
            }
        } else {
            // assembler directives
            if (t == -1) {                              // .word
                for (var i = 0; i < arg.length; i++) {
                    s = (isNaN(arg[i])) ? getSymbol(arg[i]) : parseInt(arg[i]);
                    wordsGenerated += appendWord(s);
                }
            } else if (t == -2) {                       // .space
                var count = isNaN(arg[0]) ? -2 : parseInt(arg[0]);
                for (var i = 0; i < count; i+=4) {
                    wordsGenerated += appendWord(0);
                }
            } else if (t == -3) {                       // .asciiz
                for (var i = 0; i < arg.length; i++) {
                    strval = trim(arg[i], '"');
                    for (var j = 0; j <= strval.length; j += 4) {
                        s = getChar(strval,j);
                        s = s*256 + getChar(strval,j+1);
                        s = s*256 + getChar(strval,j+2);
                        s = s*256 + getChar(strval,j+3);
                        wordsGenerated += appendWord(s);
                    }
                }
            }
        }
        return wordsGenerated;
    }

    function assemble() {
        var textarea = document.getElementById('AssemblerInput');
        textarea.style.backgroundColor = 0xfff0f0;

        var text = textarea.value.replace(/\t/g, ' ');

        var errmsg = do_assemble(text);
        if (errmsg.length > 0) {
            noalert(errmsg);
            return false;
        }
        textarea.style.backgroundColor = 0xf0fff0;
        var status ="Assembly completed with no errors.\n" + memory.length + " locations initialized.";
        if (breakpoint.length > 0) {
            status += "\n\nBreakpoints at ["
            for (var i = 0; i < breakpoint.length; i++) {
                if (i > 0) status += ", ";
                status += toHex(breakpoint[i]);
            }
            status += "].\n"
        }
        textarea.style.backgroundColor = 0xffffff;
        resetSimulator();
        noalert(status);
        isAssembled = true;
        return true;
    }

    function do_assemble(text) {
        var buffer, label;
        memPointer = 0;
        memory = new Array();
        symbol = new Object();
        unresolved = new Object();
        instr = new Object();
        breakpoint = new Array();
        isAssembled = false;
        var line = text.split("\n");
        var count = 0;
        for (var i = 0; i < line.length; i++) {
            buffer = line[i].replace('\t', ' ');
            if (buffer.charAt(0) == '*') {
                breakpoint.push(4*memPointer);
                buffer = buffer.substring(1,buffer.length);
            }
            buffer = stripComments(buffer);
            label ="";
            var t = buffer.indexOf(":");
            if (t > 0) {
                label = trim(buffer.substring(0,t));
                addSymbol(label);
                buffer = trim(buffer.substring(t+1,buffer.length));
            }
            if (buffer.length == 0)
                continue;
            memBefore = memPointer;
            try {
                count = asmToMemory(buffer);
            } catch(e) {
                count = -100;
            }
            if (count < 0) {
                errmsg = "Error in line " + (i + 1);
                errmsg += ":\n    [" + buffer + "]\n";
                if (count == -1)
                    errmsg += "Unknown or Invalid opcode";
                else if (count == -2)
                    errmsg += "Invalid 1st operand";
                else if (count == -3)
                    errmsg += "Invalid 2nd operand";
                else if (count == -4)
                    errmsg += "Invalid 3rd operand";
                else if (count == -5)
                    errmsg += "Invalid shift amount";
                else if (count == -8)
                    errmsg += "Invalid number of operands";
                else if (count == -9)
                    errmsg += "Invalid immediate operand";
                return(errmsg);
            } else {
                for (var j = 0; j < count; j++) {
                    instr[toHex(4*(memBefore+j))] = (label.length > 0) ? label + ": " + buffer : buffer;
                }
            }
        }
        if (count >= 0) {
            expstr = ''
            for (label in symbol) {
                expstr += label + '=' + (4*symbol[label]) +";"
            }
            errmsg = '';
            for (key in unresolved) {
                // Evaluate Expressions
                expfun = expstr + "return " + key;
                try {
                    expval = Function(expfun).call();
                } catch(e) {
                    expval = undefined;
                }
                if (expval == undefined) {
                    addr = toHex(4*unresolved[key])
                    errmsg += 'Error unresolved symbol: "' + key
                    errmsg += '" at location ' + addr + '\n';
                    errmsg += "[ " + instr[addr] + " ]\n\n";
                } else {
                    addSymbol(key, expval/4);
                }
            }
            breakpoint.push(4*memPointer); // put a breakpoint at the end
            return errmsg;
        }
    }

    var register = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var programCounter;
    var instrCount;
    var refCount;
    var addrwin;
    var trace;

    function breakpointIndex(addr) {
        addr &= 0x1fffffff;
        for (var i = 0; i < breakpoint.length; i++) {
            if (breakpoint[i] > addr) break;
            if (breakpoint[i] == addr) return i;
        }
        return -1;
    }

    function readByte(ea) {
        return 0xff & (memory[ea>>>2] >>> (3-(ea&3))*8);
    }

    function writeByte(ea, b) {
        var shift = (3 - (ea & 3)) * 8,
            mask = ~(0xff << shift);
        memory[ea>>>2] = (memory[ea>>>2] & mask) | ((b & 0xff) << shift);
    }

    function extractString(addr) {
        var s = '', w;
        for(var i=addr; i<addr+100; i++) {
            s += String.fromCharCode(readByte(i));
        }
        return s;
    }

    function singleStep(doUpdate) {
        var op, rd, rs, rt, func, imm16, shamt;
        var idecode, ea, nextPC;
        if (isAssembled == false) {
            noalert("Program must assemble without errors\nbefore it can be simulated.");
            return false;
        }
        trace.push(programCounter);
        idecode = memory[(programCounter>>2) & 0x1fffffff];
        refCount += 1;
        instrCount += 1;
        nextPC = programCounter + 4;
        op = (idecode >> 26) & 63;
        if (op == 0) {
            func = idecode & 63;
            rd = (idecode >> 11) & 31;
            rt = (idecode >> 16) & 31;
            rs = (idecode >> 21) & 31;
            shamt = (idecode >> 6) & 31;
            switch (func) {
                case 0:         // sll rd, rt, shamt
                    register[rd] = register[rt] << shamt;
                    break;
                case 2:         // srl rd, rt, shamt
                    register[rd] = register[rt] >>> shamt;
                    break;
                case 3:         // sra rd, rt, shamt
                    register[rd] = register[rt] >> shamt;
                    break;
                case 4:         // sllv rd, rt, rs
                    register[rd] = register[rt] << (register[rs] & 31);
                    break;
                case 6:         // srlv rd, rt, rs
                    register[rd] = register[rt] >>> (register[rs] & 31);
                    break;
                case 7:         // srav rd, rt, rs
                    register[rd] = register[rt] >> (register[rs] & 31);
                    break;
                case 8:         // jr rs
                    nextPC = register[rs];
                    break;
                case 9:         // jalr rs, rd
                    register[rd] = nextPC;
                    nextPC = register[rs];
                    break;
                case 12:        // syscall
                    if (register[2] == 1) { // print integer
                        output('' +  register[4]);
                    } else if (register[2] == 4) { // print string
                        output(extractString(register[4]));
                    }
                    break;
                case 24:        // mul rd, rt, rs
                    register[rd] = (register[rs] * register[rt]) & 0xffffffff;
                    break;
                case 26:        // div rd, rt, rs
                    t = register[rt];
                    if (t == 0) {
                        noalert("Overflow: Divide by zero");
                        register[27] = programCounter;
                        nextPC = 0x80000400;
                        return false;
                    } else {
                        register[rd] = Math.floor(register[rs] / t);
                    }
                    break;
                case 32:        // add rd,rs,rt
                    s = register[rs];
                    t = register[rt];
                    d = (s + t) & 0xffffffff;
                    register[rd] = d;
                    if (((s >= 0) && (t >= 0) && (d < 0)) || ((s < 0) && (t < 0) && (d >= 0))) {
                        noalert("Integer overflow on ADD");
                        register[27] = programCounter;
                        nextPC = 0x80000400;
                        return false;
                    }
                    break;
                case 33:        // addu rd,rs,rt
                    register[rd] = register[rs] + register[rt];
                    break;
                case 34:        // sub rd,rs,rt
                    s = register[rs];
                    t = -register[rt];
                    d = (s + t) & 0xffffffff;
                    register[rd] = d;
                    if (((s >= 0) && (t >= 0) && (d < 0)) || ((s < 0) && (t < 0) && (d >= 0))) {
                        noalert("Integer overflow on SUB");
                        register[27] = programCounter;
                        nextPC = 0x80000400;
                        return false;
                    }
                    break;
                case 35:        // subu rd,rs,rt
                    register[rd] = register[rs] - register[rt];
                    break;
                case 36:        // and rd,rs,rt
                    register[rd] = register[rs] & register[rt];
                    break;
                case 37:        // or rd,rs,rt
                    register[rd] = register[rs] | register[rt];
                    break;
                case 38:        // xor rd,rs,rt
                    register[rd] = register[rs] ^ register[rt];
                    break;
                case 39:        // nor rd,rs,rt
                    register[rd] = ~(register[rs] | register[rt]);
                    break;
                case 42:        // slt rd,rs,rt
                    register[rd] =  (register[rs] < register[rt]) ? 1 : 0;
                    break;
                case 43:        // sltu rd,rs,rt
                    s = register[rs];
                    t = register[rt];
                    register[rd] = ((s^t) < 0) ? (imm16>>>31) : ((s < t) ? 1 : 0);
                    break;
                default:
                    error = "Invalid Instruction (" + toHex(idecode);
                    error += ") at pc = " + toHex(programCounter);
                    error += "\npc will be saved in $k1";
                    noalert(error);
                    register[27] = programCounter;
                    return false;
                    break;
            }
        } else {
            rt = (idecode >> 16) & 31;
            rs = (idecode >> 21) & 31;
            imm16 = idecode & 0xffff;
            if (((op & 60) != 12) && (imm16 >= 32768)) imm16 -= 65536;
            switch (op) {
                case 2:         // j target
                    nextPC = (nextPC & 0xf0000000) + 4*(idecode & 0x03ffffff);
                    break;
                case 3:         // jal target
                    register[31] = nextPC;
                    nextPC = (nextPC & 0xf0000000) + 4*(idecode & 0x03ffffff);
                    break;
                case 4:         // beq rs, rt, offset
                    if (register[rs] == register[rt])
                        nextPC = programCounter + 4*imm16;
                    break;
                case 5:         // bne rs, rt, offset
                    if (register[rs] != register[rt])
                        nextPC = programCounter + 4*imm16;
                    break;
                case 8:         // addi rt, rs, imm16
                    s = register[rs];
                    d = (s + imm16) & 0xffffffff;
                    register[rt] = d;
                    if (((s >= 0) && (imm16 >= 0) && (d < 0)) || ((s < 0) && (imm16 < 0) && (d >= 0))) {
                        noalert("Integer overflow on ADDI");
                        register[27] = programCounter;
                        nextPC = 0x80000400;
                        return false;
                    }
                    break;
                case 9:         // addiu rt, rs, imm16
                    register[rt] = register[rs] + imm16;
                    break;
                case 10:        // slti rt, rs, imm16
                    register[rt] = (register[rs] < imm16) ? 1 : 0;
                    break;
                case 11:        // sltiu rt, rs, imm16
                    s = register[rs];
                    register[rt] = ((s^imm16) < 0) ? (imm16>>>31) : ((s < imm16) ? 1 : 0);
                    break;
                case 12:        // andi rt, rs, imm16
                    register[rt] = register[rs] & imm16;
                    break;
                case 13:        // ori rt, rs, imm16
                    register[rt] = register[rs] | imm16;
                    break;
                case 14:        // xori rt, rs, imm16
                    register[rt] = register[rs] ^ imm16;
                    break;
                case 15:        // lui rt, imm16
                    register[rt] = imm16 << 16;
                    break;
                case 32:        // lb rt, imm16(rs)
                    ea = (register[rs] + imm16) & 0x7fffffff;
                    register[rt] = readByte(ea);
                    trace.push(ea);
                    refCount += 1;
                    break;

                case 35:        // lw rt, imm16(rs)
                    ea = (register[rs] + imm16) & 0x7fffffff;
                    // verify address is word aligned
                    if ((ea & 3) == 0) {
                        trace.push(ea);
                        register[rt] = memory[ea>>>2];
                        if (register[rt] === undefined) {
                            error = "Access exception: pc = " + toHex(programCounter);
                            error += "\nlw effective address =" + toHex(ea);
                            error += "\n$s = " + toHex(register[rs]);
                            error += ", imm16 =" + toHex(imm16);
                            noalert(error);
                            return false;
                        }
                        refCount += 1;
                    } else {
                        error = "Alignment exception: pc = " + toHex(programCounter);
                        error += "\nlw effective address =" + toHex(ea);
                        error += "\n$s = " + toHex(register[rs]);
                        error += ", imm16 =" + toHex(imm16);
                        error += "\npc will be saved in $k1";
                        noalert(error);
                        return false;
                    }
                    break;
                case 40:        // sb rt, imm16(rs)
                    ea = (register[rs] + imm16) & 0x7fffffff;
                    writeByte(ea, register[rt]);
                    trace.push(ea);
                    refCount += 1;
                    break;

                case 43:        // sw rt, imm16(rs)
                    ea = (register[rs] + imm16) & 0x7fffffff;
                    // verify address is word aligned
                    if ((ea & 3) == 0) {
                        trace.push(ea);
                        memory[ea>>>2] = register[rt];
                        refCount += 1;
                    } else {
                        error = "Alignment exception: pc = " + toHex(programCounter);
                        error += "\nsw effective address =" + toHex(ea);
                        error += "\n$s = " + toHex(register[rs]);
                        error += ", imm16 =" + toHex(imm16);
                        error += "\npc will be saved in $k1";
                        noalert(error);
                        return false;
                    }
                    break;
                default:
                    error = "Invalid instruction (" + toHex(idecode);
                    error += ") at pc = " + toHex(programCounter);
                    error += "\npc will be saved in $k1";
                    noalert(error);
                    return false;
                    break;
            }
        }
        register[0] = 0;
        prevPC = programCounter;
        programCounter = nextPC;
        if ((op == 43) && (breakpointIndex(ea) >= 0)) {
            mess = "Access breakpoint at location: " + toHex(ea);
            mess += "\n$pc = " + toHex(prevPC);
            contents = memory[ea>>2];
            mess += "\ncontents = " + toHex(contents);
            mess += " [" + contents + "]";
            noalert(mess);
            updateSimulator();
            return false;
        }
        if (breakpointIndex(programCounter) >= 0) {
            noalert("Reached breakpoint at " + toHex(programCounter));
            updateSimulator();
            return false;
        }
        if (doUpdate) updateSimulator();
        return true;
    }

    function multiStep() {
        var steps = document.getElementById("MultistepValue").value;
        for (var i = 0; i < steps; i++) {
            if (singleStep(0) == false)
                break;
        }
        updateSimulator();
    }

    function runToBreakpoint() {
        if ((breakpoint == null) || (breakpoint.length == 0)) {
            noalert("No breakpoints set.")
        } else {
            var step = 0,
                start = Date.now();
            while (singleStep(0)) {
                step += 1;
                if (step % 100000 == 0 &&  Date.now() - start > 2000) {
                    noalert('Looping?');
                    break;
                }
            }
        }
        updateSimulator();
    }

    function run() {
        var step = 0;
        while (singleStep(0)) {
            step += 1;
            if (step > 1000000) {
                return false;
            }
        }
        return true;
    }

    function reset() {
        programCounter = 1<<31;
        instrCount = 0;
        refCount = 0;
        trace = new Array();
        addrwin = new Array(-1,-1,-1,-1,-1,-1,-1);
        if (typeof window !== 'undefined') {
            for(let i=1; i<32; i++) {
                register[i] = 0xffffffff & Math.floor(Math.random() * (2**32 - 1));
            }
        }
    }

    function resetSimulator() {
        reset();
        var textarea = document.getElementById("OutputArea");
        textarea.value = "";
        if (document.getElementById("status")) {
            updateSimulator();
        }
    }

    function disassemble(addr) {
        var t = memory[addr];
        var op = (t >> 26) & 63;
        var opStr = opDecode[op]
        var rd, rs, rt, imm
        if (op == 0) {          // ALU ops
            fn = t & 63
            opStr = fnDecode[fn];
            if (opStr != 'Inv') {
                rd = (t >> 11) & 31;
                rt = (t >> 16) & 31;
                rs = (t >> 21) & 31;
                if (fn < 4) {           // shifts with immediate operands
                    var shamt = (t >> 6) & 31
                    opStr += " $" + rd + ",$" + rt + "," + shamt;
                } else if (fn < 8) {    // shifts with variable operands
                    opStr += " $" + rd + ",$" + rt + ",$" + rs;
                } else if (fn < 9) {    // jump register
                    opStr += " $" + rs + ",$" + rd;
                } else if (fn < 10) {   // jump and link register
                    opStr += " $" + rs;
                } else {
                    rs = (t >> 21) & 31;
                    opStr += " $" + rd + ",$" + rs + ",$" + rt;
                }
            } else {
                opStr = "Invalid ALU op = " + op;
            }
        } else if (opStr != 'Inv') {
            rt = (t >> 16) & 31;
            rs = (t >> 21) & 31;
            if (op < 4) {               // jumps
                imm = 4*(t & 0x03ffffff);
                opStr += "   " + imm;
            } else {
                imm = t & 0xffff;
                if ((op & 12 != 12) && (t & 0x8000)) {  // treat non-logic as signed
                    imm -= 65536;
                }
                if (op & 32) {          // loads and stores
                    opStr += " $" + rt + "," + imm + "($" + rs + ")";
                } else if (op == 15) {  // lui
                    opStr += " $" + rt + "," + imm;
                } else {
                    opStr += " $" + rt + ",$" + rs + "," + imm;
                }
            }
        } else {
            opStr = "Invalid op = " + op;
        }
        return opStr;
    }

    var standardRegisterName = [
        "zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
        "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
        "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
        "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra" ];

    function formatReg(i) {
        var regName, t;
        if (i == 'pc') {
            regName = "$pc";
            t = programCounter;
            if (t < 0) {
                regName = '[K]' + regName;
                t = t & 0xffffffff;
            }
        } else {
            t = register[i] & 0xffffffff;
            regName = "$" + standardRegisterName[i]; //((i >= 28) ? standardRegisterName[i] : i);
        }
        return regName + ': [<a href="javascript: void(0);" class="register" onmouseover="MIPS.regPopup(event);">'
                       + toHex(t) + "</a>]";
    }

    function regPopup(event) {
        var popup = document.getElementById("regPopup");
        if (event.target.nodeName == 'A') {
            var docX, docY;
            if (event.pageX == null) {
                // IE case
                var d = (document.documentElement &&
                        document.documentElement.scrollLeft != null) ?
                        document.documentElement : document.body;
                docX = event.clientX + d.scrollLeft;
                docY = event.clientY + d.scrollTop;
            } else {
                // all other browsers
                docX = event.pageX;
                docY = event.pageY;
            }
            popup.style.top = (docY + 20) + 'px';
            popup.style.left = (docX - 80) + 'px';

            var decimalValue = parseInt(event.target.innerHTML);
            var regName = event.target.offsetParent.id;
            if (regName.indexOf("reg") == 0) {
                regName = "$" + parseInt(regName.substr(3)) + " [$" + standardRegisterName[parseInt(regName.substr(3))] + "]";
            }
            signedValue = (decimalValue & 0x80000000) ? decimalValue - (2*0x80000000) : decimalValue;
            popup.innerHTML = "&nbsp;&nbsp;&nbsp;register: " + regName
                            + "<br>hexadecimal: " + event.target.innerHTML
                            + "<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;signed: " + signedValue
                            + "<br>&nbsp;&nbsp;&nbsp;unsigned: " + decimalValue;
            popup.style.display = "block";
        }
    }

    function removePopup(event) {
        document.getElementById("regPopup").style.display = "none";
    }

    function updateSimulator() {
        if (!useDOM) {
            return;
        }
        var status = "Registers";
        if (instrCount > 0) status += ",   Instruction Count = " + instrCount;
        if (refCount > 0) status += ",   Memory Refs = " + refCount;
        document.getElementById("status").innerHTML = status;

        // update register display
        document.getElementById("pc").innerHTML = formatReg('pc');
        for (n = 0; n < 32; n++)
            document.getElementById("reg"+n).innerHTML = formatReg(n);

        pc = programCounter >>> 2;
        addrwin[0] = addrwin[1];
        addrwin[1] = addrwin[2];
        addrwin[2] = addrwin[3];
        addrwin[3] = pc;
        addrwin[4] = pc+1;
        addrwin[5] = pc+2;
        addrwin[6] = pc+3;

        // <!-- update instruction display -->
        if (!memory) return;

        for (n = 0; n < 7; n++) {
            if (addrwin[n] >= 0) {
                memAddr = toHex(4*addrwin[n]);
                memIndex = addrwin[n] & 0x1fffffff;
                document.getElementById("addr"+n).innerHTML = (breakpointIndex(4*addrwin[n]) >= 0) ? '*'+memAddr+'*': memAddr;
                document.getElementById("cont"+n).innerHTML = toHex(memory[memIndex]);
                t = toHex(4*memIndex);
                if (t in instr) {
                    code = instr[t];
                    if ((code.indexOf('.word') >= 0) || (code.indexOf('.space') >= 0) || (code.indexOf('.asciiz') >= 0)) {
                        code += " # [" + disassemble(memIndex) + "]";
                    }
                } else {
                    code = "[" + disassemble(memIndex) + "]";
                }
                var maxlen = 30;
                code =  code.length > maxlen ? 
                        code.substring(0, maxlen-3) + '...' :
                        code;
                document.getElementById("inst"+n).innerHTML = code;
            } else {
                document.getElementById("addr"+n).innerHTML = "";
                document.getElementById("cont"+n).innerHTML = "";
                document.getElementById("inst"+n).innerHTML = "";
            }
        }
    }

    function createSimulator() {
        isAssembled = false;
        let ai = document.getElementById('AssemblerInput');
        ai.style.backgroundColor = 0xfff0f0;
        ai.addEventListener('keydown', (e) => {
          if (e.key === "Tab") {
            e.preventDefault();
            document.execCommand('insertText', false, '\t');
          }
        });

        popup = document.createElement('div');
        popup.id = "regPopup";
        popup.style.display = "none";
        popup.style.position = "absolute";
        popup.style.padding = "5px";
        popup.style.background = "#ffffcc";
        popup.style.fontFamily = "monospace";
        popup.style.fontSize = "80%";
        popup.style.border = "1px solid black";
        popup.style.zIndex = "200000";
        popup.onmouseover = removePopup;
        document.body.appendChild(popup);

        // <!-- generate register header -->
        var table = document.getElementById("SimulatorState");
        var tRow = table.insertRow(-1);
        tRow.bgColor = "#FFFFFF";
        tRow.onmouseout = removePopup;
        var cell = tRow.insertCell(-1);
        cell.id = "status";
        cell.align = "center";
        cell.colSpan =  "3";
        cell.height = "22px";
        cell.innerHTML = "Registers";

        cell = tRow.insertCell(-1);
        cell.id = "pc";
        cell.align = "right";
        cell.colSpan = "1";
        cell.height = "22px";
        cell.style.fontFamily = "monospace";
        cell.style.fontSize = "14px";
        cell.innerHTML = formatReg('pc');

        // <!-- generate register cells -->
        var n = 0;
        for (var j = 0; j < 8; j++) {
            tRow = table.insertRow(-1);
            tRow.onmouseout = removePopup;
            tRow.setAttribute("bgColor", "#FFFFFF");
            for (var i = 0; i < 4; i++) {
                cell = tRow.insertCell(-1);
                cell.id = "reg"+n;
                cell.align = "right";
                cell.height = "22px";
                cell.width = "25%";
                cell.style.fontFamily = "monospace";
                cell.style.fontSize = "14px";
                cell.innerHTML = formatReg(n);
                n += 1
            }
        }

        tRow = table.insertRow(-1);
        cell = tRow.insertCell(-1);
        cell.setAttribute("colSpan", "4");

        // <!-- generate code header -->
        tRow = table.insertRow(-1);
        tRow.setAttribute("bgColor", "#FFFFFF");

        cell = tRow.insertCell(-1);
        cell.setAttribute("align", "center");
        cell.setAttribute("height", "20px");
        cell.innerHTML = "Address";

        cell = tRow.insertCell(-1);
        cell.setAttribute("align", "center");
        cell.innerHTML = "Contents";

        cell = tRow.insertCell(-1);
        cell.setAttribute("align", "center");
        cell.setAttribute("colSpan", "2");
        cell.innerHTML = "Instruction";

        // <!-- generate code cells -->
        for (var j = 0; j < 7; j++) {
            tRow = table.insertRow(-1);
            tRow.setAttribute("bgColor", (j == 3) ? "#AAFFAA":"#FFFFFF");

            cell = tRow.insertCell(-1);
            cell.setAttribute("align", "center");
            cell.setAttribute("height", "20px");
            cell.setAttribute("style", "font-family: monospace; font-size: 14px");
            cell.setAttribute("id", "addr"+j);
            cell.innerHTML = " ";

            cell = tRow.insertCell(-1);
            cell.setAttribute("align", "center");
            cell.setAttribute("style", "font-family: monospace; font-size: 14px");
            cell.setAttribute("id","cont"+j);
            cell.innerHTML = " ";

            cell = tRow.insertCell(-1);
            cell.setAttribute("align", "left");
            cell.setAttribute("colSpan", "2");
            cell.setAttribute("style", "font-family: monospace; font-size: 14px");
            cell.setAttribute("id","inst"+j);
            cell.innerHTML = " ";
        }
        resetSimulator();
    }

    // when not using the dom accumulate the alerts
    var alerts = [];
    function noalert(txt) {
        if (!useDOM) {
            alerts.push(txt);
            return;
        }
        var outputarea = document.getElementById('OutputArea');
        if (!txt.endsWith('\n')) {
            txt += '\n';
        }
        var old = outputarea.value;
        if (old && !old.endsWith('\n')) {
            txt = '\n' + txt;
        }
        output(txt);
    }

    function output(txt) {
        var outputarea = document.getElementById('OutputArea');
        outputarea.value += txt;
        outputarea.scrollTop = outputarea.scrollHeight;
    }

    function outputTrace() {
        if (trace.length <= 0) {
            noalert("Error: Code must first run in order to output memory address trace")
            return;
        }
        var textarea = document.getElementById('OutputArea');
        response = '\nMemory trace\n';
        for (var i = 0; i < trace.length; i++) {
            response += toHex(trace[i]) + '\n'
        }
        response += '\n';
        textarea.value += response;
        //textarea.setAttribute("style", "display: block;");
    }

    function memDump() {
        if (isAssembled == false) {
            noalert("Error: Code must first be assembled in order to dump memory")
            return;
        }
        var dumpAddr = document.getElementById('MemDumpStart').value;
        var dumpCount = document.getElementById('MemDumpCount').value;
        var start = parseInt(dumpAddr);
        var count = parseInt(dumpCount);
        if (isNaN(start)) {
            start = symbol[dumpAddr];
            if (start == null) {
                expstr = ''
                for (label in symbol) {
                    if (dumpAddr.indexOf(label) < 0)
                        continue;
                    expstr += label + '$ =' + (4*symbol[label]) +";";
                    dumpAddr = dumpAddr.replace(label, label+'$')
                }
                // Evaluate Expressions
                expstr = expstr + "return " + dumpAddr;
                try {
                    start = Function(expstr).call();
                } catch (e) {
                    start = NaN
                }
            } else {
                start = 4*start;
            }
        }
        var response = "\t\tMemory Dump: " +  start;
        response += " = "+ start + "\n";
        start = 4*Math.floor(start/4);
        var end = start + count*4;
        response += "\n Address\t\t:\t Contents\t";
        while (start < end) {
            var contents = memory[start/4];
            if (contents == null) contents = 0;
            var signedValue = (contents & 0x80000000) ? (contents & 0x7fffffff) - 0x80000000 : contents;
            response += "\n" + toHex(start) + "\t:\t" + toHex(contents);
            response += "\t" + signedValue;
            start += 4;
        }
        noalert(response);
    }

    function asmChange() {
        var textarea = document.getElementById('AssemblerInput');
        textarea.style.backgroundColor = 0xfff0f0;
        isAssembled = false;
    }

    var tabstops = 8;

    function handleTabs(evt) {
        if (evt.keyCode == 9) {
            // Tab key - insert tab expansion
            evt.preventDefault();
            var t = evt.target;
            var ss = t.selectionStart;
            var se = t.selectionEnd;
            for (var i = ss - 1; i >= 0; i--) {
                if (t.value.charAt(i) == '\n')
                    break;
            }
            ns = tabstops - ((ss - i - 1) % tabstops);
            var tab = '';
            for (i = 0; i < ns; i++) {
                tab += ' ';
            }
            if (ss != se && t.value.slice(ss,se).indexOf("\n") != -1) {
                // Multi-line selection
                var pre = t.value.slice(0,ss);
                var sel = t.value.slice(ss,se).replace("\n","\n"+tab);
                var post = t.value.slice(se,t.value.length);
                t.value = pre.concat(tab).concat(sel).concat(post);
                t.selectionStart = ss + tab.length;
                t.selectionEnd = se + tab.length;
            } else {
                // "Typical" case (no selection or selection on one line only)
                t.value = t.value.slice(0,ss).concat(tab).concat(t.value.slice(ss,t.value.length));
                if (ss == se) {
                    t.selectionStart = t.selectionEnd = ss + tab.length;
                }
                else {
                    t.selectionStart = ss + tab.length;
                    t.selectionEnd = se + tab.length;
                }
            }
        }
    }

    function MIPSeval(code) {
        useDOM = false;
        alerts = [];
        try {
            // fix a tab bug in the parser
            code = code.replace(/\t/g, ' ');
            var errors = do_assemble(code);
            if (errors) {
                useDOM = true;
                return { errors };
            }
            isAssembled = true;
            reset();
            if (!run()) {
                useDOM = true;
                return { errors: "Program did not reach a breakpoint" };
            }
            var named = {};
            standardRegisterName.forEach((reg, i) =>
                named[reg] = register[i] || 0);
            named['pc'] = programCounter;
            useDOM = true;
            return { memory, register: named, symbol, alerts };
        } catch(e) {
            useDOM = true;
            console.log(e);
        }
    }

    return {
        assemble,
        createSimulator,
        memDump,
        MIPSeval,
        multiStep,
        outputTrace,
        resetSimulator,
        regPopup,
        runToBreakpoint,
        singleStep,
    };
})();
