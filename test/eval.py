# MIT license: https://opensource.org/licenses/MIT
# See https://github.com/Isotel/mixedsim/blob/master/python/ngspice_read.py
# for a more complete library. Isotel's version is GPL licensed
from __future__ import division
import numpy as np
from numpy import ndarray
from pathlib import Path
from pprint import pprint

from math import isclose

BSIZE_SP = 512  # Max size of a line of data; we don't want to read the
# whole file to find a line, in case file does not have
# expected structure.
MDATA_LIST = [
    b"title",
    b"date",
    b"plotname",
    b"flags",
    b"no. variables",
    b"no. points",
    b"dimensions",
    b"command",
    b"option",
]


def rawread(fname: str) -> tuple[list[ndarray], list]:
    """Read ngspice binary raw files. Return tuple of the data, and the
    plot metadata. The dtype of the data contains field names. This is
    not very robust yet, and only supports ngspice.
    >>> darr, mdata = rawread('test.py')
    >>> darr.dtype.names
    >>> plot(np.real(darr['frequency']), np.abs(darr['v(out)']))
    """
    # Example header of raw file
    # Title: rc band pass example circuit
    # Date: Sun Feb 21 11:29:14  2016
    # Plotname: AC Analysis
    # Flags: complex
    # No. Variables: 3
    # No. Points: 41
    # Variables:
    #         0       frequency       frequency       grid=3
    #         1       v(out)  voltage
    #         2       v(in)   voltage
    # Binary:
    fp = open(fname, "rb")
    count = 0
    arrs = []
    plots = []
    plot = {}
    while True:
        try:
            mdata = fp.readline(BSIZE_SP).split(b":", maxsplit=1)
        except:
            raise
        if len(mdata) == 2:
            if mdata[0].lower() in MDATA_LIST:
                plot[mdata[0].lower()] = mdata[1].strip()
            if mdata[0].lower() == b"variables":
                nvars = int(plot[b"no. variables"])
                npoints = int(plot[b"no. points"])
                plot["varnames"] = []
                plot["varunits"] = []
                for varn in range(nvars):
                    varspec = fp.readline(BSIZE_SP).strip().decode("ascii").split()
                    assert varn == int(varspec[0])
                    plot["varnames"].append(varspec[1])
                    plot["varunits"].append(varspec[2])
            if mdata[0].lower() == b"binary":
                rowdtype = np.dtype(
                    {
                        "names": plot["varnames"],
                        "formats": [
                            np.complex_ if b"complex" in plot[b"flags"] else np.float_
                        ]
                        * nvars,
                    }
                )
                # We should have all the metadata by now
                arrs.append(np.fromfile(fp, dtype=rowdtype, count=npoints))
                plots.append(plot)
                plot = {}  # reset the plot dict
                fp.readline()  # Read to the end of line
        else:
            break
    return (arrs, plots)


def find_vector(arr: list[ndarray], label: str) -> ndarray:
    for vector in arr:
        if label == vector.dtype.names[0]:
            return vector


import sys


if len(sys.argv) != 2:
    print("Not enought arguments")

test_file = Path(sys.argv[-1])

print(f"Testing file: {test_file}")
arrs, plots = rawread(f"{test_file.with_suffix(".raw")}")

result = False
match test_file.stem:
    case "basic":
        vector = find_vector(arrs, "v(out)")
        result = isclose(vector[0][0], 2 / 3)

    case "testbench_dac_16nfet":
        print("IS WORKING HASTA AQUI")

        for data in arrs:
            time = find_vector(arrs, "time")
            # print(time)
            out = find_vector(arrs, "v(out)")
            # print(out)
            out_parax = find_vector(arrs, "v(out_parax)")
            print(out_parax)

            # print(out)
            # print(out_parax)
            break

    case _:
        raise RuntimeError("No valid test specified")

if not result:
    raise RuntimeError(f"Test {test_file} failed")
else:
    print(f"Test {test_file} ok")
