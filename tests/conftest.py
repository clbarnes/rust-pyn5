import pytest
import numpy as np

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
