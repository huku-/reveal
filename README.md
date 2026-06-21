# REveal

![AUTh](images/auth.png?raw=true "AUTh")


## Introduction

REveal is a function matching engine for divide-and-conquer binary diffing,
developed as part of my PhD research.

It is framework-agnostic via [RElib](https://github.com/huku-/relib), which
currently supports only IDA Pro.


## Installation

To install REveal, run the following commands in a Python virtual environment
accessible to your reverse engineering framework:

    git clone https://github.com/huku-/reveal.git
    pip install .


## Using REveal

1.  Open the first executable (e.g., **/tmp/example1**) in IDA Pro and run **bin/export.py.**
    This creates **/tmp/example1.export/** containing exported data.

2.  Open the second executable (e.g., **/tmp/example2**) in IDA Pro and run **bin/export.py**.
    This creates **/tmp/example2.export/**.

    If you plan to use compile-unit recovery as the divide-and-conquer strategy,
    deploy [REcover](https://github.com/huku-/recover) and follow the related
    instructions.

3.  Run `reveal` to perform the diffing. Select the divide-and-conquer strategy
    with `--match-hierarchical`. For example:

        reveal -d --match-hierarchical recover-apsnse \
            /tmp/example1.export /tmp/example2.export /tmp/results

    The positional arguments specify the two export directories and the output
    directory for the diffing results.

4.  Inspect the recovered matches:

        python bin/parse_matches.py /tmp/results/matched.pcl


## Things to know

*   REveal can match functions by name. This is particularly useful for imported
    and exported symbols, which can often be identified by their names and
    ordinals. By default, only imported symbols are matched by name (`reveal -h`
    for details).

*   REveal builds on prior research in binary diffing published by various
    talented researchers. Notable predecessors include BinDiff, Diaphora, YaDiff
    and DarunGrim.

*   **REveal was developed without funding from any organization or government.**


## Cite

    @inproceedings{Karamitas2018,
        title = {Efficient features for function matching between binary executables},
        author = {Karamitas, Chariton and Kehagias, Athanasios},
        year = {2018},
        booktitle = {2018 IEEE 25th International Conference on Software Analysis, Evolution and Reengineering (SANER)},
        pages = {335--345},
        organization = {IEEE}
    }

    @article{Karamitas2019,
        title = {Function matching between binary executables: efficient algorithms and features},
        author = {Karamitas, Chariton and Kehagias, Athanasios},
        year = {2019},
        journal = {Journal of Computer Virology and Hacking Techniques},
        publisher = {Springer},
        volume = {15},
        number = {4},
        pages = {307--323}
    }

    @article{Karamitas2023,
        title = {Improving binary diffing speed and accuracy using community detection and locality-sensitive hashing: an empirical study},
        author = {Karamitas, Chariton and Kehagias, Athanasios},
        year = {2023},
        journal = {Journal of Computer Virology and Hacking Techniques},
        publisher = {Springer},
        volume = {19(2)},
        pages = {319--337}
    }

    @article{karamitas2025,
        title={REcover: towards recovering object files from stripped binary executables},
        author={Karamitas, Chariton and Kehagias, Athanasios},
        journal={Journal of Computer Virology and Hacking Techniques},
        volume={21},
        number={1},
        pages={29},
        year={2025},
        publisher={Springer}
    }


## License

Copyright © 2018-2026, Chariton Karamitas, Athanasios Kehagias, All rights reserved
