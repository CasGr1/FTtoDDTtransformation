import os
from .FTParser import *
import numpy as np


def FTpartialparser(filename, extension):
    with open(filename, "r") as file:
        gates = []
        bes = []

        for line in file:
            line = line.strip().replace('"', '').replace(';', '')
            if not line:
                continue

            linelist = line.split()
            updated_line = []

            for token in linelist:
                token_lower = token.lower()

                # Preserve logic operators
                if token_lower in {"and", "or"}:
                    updated_line.append(token)

                # Preserve probability and cost exactly as written
                elif token_lower.startswith("prob="):
                    updated_line.append(token)

                elif token_lower.startswith("cost="):
                    updated_line.append(token)

                # Everything else is a name → apply extension if needed
                else:
                    if extension is not None:
                        updated_line.append(f"{token}_{extension}")
                    else:
                        updated_line.append(token)

            # Classify line type safely
            if len(updated_line) > 1:
                if updated_line[1].lower() in {"and", "or"}:
                    gates.append(updated_line)

                elif updated_line[1].lower().startswith("prob="):
                    bes.append(updated_line)

        return gates, bes

def FTsave(FTgates, FTbes, output):
    with open(output, "w") as f:
        f.write(f'toplevel "{FTgates[0][0]}";\n')
        for sublist in FTgates:
            first = f'"{sublist[0]}"'
            connector = sublist[1]
            rest = " ".join(f'"{x}"' for x in sublist[2:])
            f.write(f"{first} {connector} {rest};\n")
        for sublist in FTbes:
            first = f'"{sublist[0]}"'
            prob = sublist[1]
            cost = sublist[2]
            # cost = sublist[2]
            f.write(f"{first} {prob} {cost};\n")
            # f.write(f"{first} {prob} {cost};\n")


def random_BE(FT1gates, FT1bes, FT2gates, FT2bes):
    gate = np.random.randint(len(FT1bes))
    be = FT1bes[gate][0]
    for i in FT1gates:
        if be in i:
            index1 = FT1gates.index(i)
            index2 = FT1gates[index1].index(be)
            if FT2gates[0][0] == "System":
                FT2gates[0][0] = "Sys2"
            FT1gates[index1][index2] = FT2gates[0][0]
    return FT1gates + FT2gates, FT1bes + FT2bes

def random_shared_be(FT1gates, FT1bes, FT2gates, FT2bes, GATETYPE):
    new_gate = ["TOPGATE", GATETYPE, FT1gates[0][0], FT2gates[0][0]]
    gate1 = np.random.randint(len(FT1bes))
    be1 = FT1bes[gate1][0]
    gate2 = np.random.randint(len(FT2bes))
    be2 = FT2bes[gate2][0]
    for i in FT2gates:
        if be2 in i:
            index1 = FT2gates.index(i)
            index2 = FT2gates[index1].index(be2)
            FT2gates[index1][index2] = be1
    return [new_gate] + FT1gates + FT2gates, FT1bes + FT2bes

def new_TOP(FT1gates, FT1bes, FT2gates, FT2bes, GATETYPE):
    new_gate = ["TOPGATE", GATETYPE, FT1gates[0][0], FT2gates[0][0]]
    return [new_gate] + FT1gates + FT2gates, FT1bes + FT2bes

def random_gen(folder, min_size, temp_path):
    FTfile = np.random.choice(os.listdir(folder))
    new_ft = FTpartialparser(os.path.join(folder, FTfile), "A")
    extension = 1
    height = 0
    while height < min_size:
        ext_ftfile = np.random.choice(os.listdir(folder))
        ext_ft = FTpartialparser(os.path.join(folder, ext_ftfile), str(extension))
        choice = np.random.randint(1, 4)
        if choice == 1:
            new_ft = random_BE(new_ft[0], new_ft[1], ext_ft[0], ext_ft[1])
        elif choice == 2:
            new_ft = random_shared_be(new_ft[0], new_ft[1], ext_ft[0], ext_ft[1], np.random.choice(["and", "or"]))
        elif choice == 3:
            new_ft = new_TOP(new_ft[0], new_ft[1], ext_ft[0], ext_ft[1], np.random.choice(["and", "or"]))
        FTsave(new_ft[0], new_ft[1], temp_path)
        FTparsed = FTParse(temp_path)
        height = FTparsed.max_height()
        print(height)
        extension += 1
    return new_ft


if __name__ == "__main__":
    folder = "FTs/FFORT"

    for i in range(0, 50):
        new = random_gen(folder, 7)
        FTsave(new[0], new[1], "FTs/FFORTcombined/MinHeight7/FT" + str(i) + ".dft")