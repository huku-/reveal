# -*- coding: utf-8 -*-

import os
import pickle
import sys

def main(argv: list[str]) -> int:
    mismatches = matches = 0
    with open(argv[1], "rb") as fp:
        try:
            while True:
                m = pickle.load(fp)
                _, lhs_name, _, rhs_name, _ = m
                if lhs_name != rhs_name:
                    mismatches += 1
                else:
                    matches += 1
                print(m)
        except EOFError:
            pass

    print(f"Matches {matches}")
    print(f"Mismatches {mismatches}")
    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
