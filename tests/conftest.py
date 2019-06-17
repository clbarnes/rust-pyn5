import math
import warnings

from pathlib import Path

import pytest
import numpy as np
import tifffile

import pyn5

DS_SIZE = (10, 10, 10)
BLOCKSIZE = (2, 2, 2)

INT_DTYPES = ["UINT8", "UINT16", "UINT32", "UINT64", "INT8", "INT16", "INT32", "INT64"]
FLOAT_DTYPES = ["FLOAT32", "FLOAT64"]


@pytest.fixture(params=INT_DTYPES + FLOAT_DTYPES)
def ds_dtype(request, tmp_path):
    dtype = request.param
    n5_path = str(tmp_path / "test.n5")
    ds_name = "ds" + dtype

    pyn5.create_dataset(n5_path, ds_name, DS_SIZE, BLOCKSIZE, dtype)
    yield pyn5.open(n5_path, ds_name, dtype, False), np.dtype(dtype.lower())


@pytest.fixture
def file_(tmp_path):
    f = pyn5.File(tmp_path / "test.n5")
    yield f

# Benchmark fixtures


@pytest.fixture()
def data_dir():
    here = Path(__file__).resolve()
    test_dir = here.parent
    yield test_dir / "data"


@pytest.fixture
def t1_data(data_dir):
    fpath = data_dir / "JeffT1_le.tif"
    try:
        tiffdata = tifffile.imread(str(fpath))
    except FileNotFoundError:
        warnings.warn("Benchmark data not found - run `make data`")
        raise

    yield np.asarray(tiffdata, dtype="int16")


@pytest.fixture
def bench_data(t1_data):
    block_len = 64
    block_reps = 5

    desired_len = block_len * block_reps

    repeats = tuple(math.ceil(desired_len / d) for d in t1_data.shape)
    d = t1_data.astype(np.int16)
    for axis, reps in enumerate(repeats):
        d = np.concatenate([d] * reps, axis)

    arr = d[:desired_len, :desired_len, :desired_len]
    yield arr, (block_len,) * 3


@pytest.fixture
def bench_dataset(bench_data, tmp_path):
    arr, chunks = bench_data

    root_path = str(tmp_path / "bench.n5")
    path_name = "ds"

    pyn5.create_dataset(
        root_path,
        path_name,
        list(arr.shape),
        list(chunks),
        arr.dtype.name.upper()
    )

    return arr, pyn5.DatasetINT16(root_path, path_name, True)


@pytest.fixture
def bench_dataset_full(bench_dataset):
    arr, ds = bench_dataset
    ds.write_ndarray([0, 0, 0], arr, 0)

    yield arr, ds
