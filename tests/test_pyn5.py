#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `pyn5` package."""


import unittest
from pathlib import Path
import shutil
import numpy as np
import pytest

import pyn5

from .conftest import BLOCKSIZE


def dtype_info(dtype):
    if np.issubdtype(dtype, np.integer):
        info = np.iinfo(dtype)
    elif np.issubdtype(dtype, np.floating):
        info = np.finfo(dtype)
    else:
        raise ValueError(f"Unknown dtype {dtype}")

    return info


def valid_block(dtype):
    info = dtype_info(dtype)
    return np.linspace(info.min, info.max, np.product(BLOCKSIZE), dtype=dtype).tolist()


def overflow_block(dtype):
    info = dtype_info(dtype)
    length = np.product(BLOCKSIZE) // 2
    before = [info.min - i - 1 for i in range(length)]
    after = [info.max + i + 1 for i in range(length)]
    return before + after


def wrong_dtype_block(dtype):
    if np.issubdtype(dtype, np.integer):
        return np.linspace(0, 1, np.product(BLOCKSIZE)).tolist()
    else:
        return np.asarray(valid_block(dtype), dtype=np.dtype("int64")).tolist()


def ravel_block(block):
    return np.array(block).reshape(BLOCKSIZE, order="F")


def test_read_write_valid(ds_dtype):
    ds, dtype = ds_dtype
    block_idx = [0, 0, 0]

    expected = valid_block(dtype)
    ds.write_block(block_idx, expected)

    np.testing.assert_equal(
        ds.read_ndarray(block_idx, BLOCKSIZE), ravel_block(expected)
    )


def test_read_write_overflow(ds_dtype):
    ds, dtype = ds_dtype
    if np.issubdtype(dtype, np.floating):
        pytest.xfail(
            "Doesn't work properly for float types "
            "since floats that are too large get converted to inf"
        )

    block = overflow_block(dtype)

    with pytest.raises(OverflowError):
        ds.write_block([1, 1, 1], block)

    np.testing.assert_equal(ds.read_ndarray([2, 2, 2], BLOCKSIZE), np.zeros(BLOCKSIZE))


def test_read_write_wrong_dtype(ds_dtype):
    ds, dtype = ds_dtype
    if np.issubdtype(dtype, np.floating):
        pytest.xfail(
            "Doesn't work properly for float types "
            "since ints in lists don't hold their type"
        )

    block = wrong_dtype_block(dtype)

    with pytest.raises(TypeError):
        ds.write_block([2, 2, 2], block)

    np.testing.assert_equal(ds.read_ndarray([4, 4, 4], BLOCKSIZE), np.zeros(BLOCKSIZE))


class TestPythonReadWrite(unittest.TestCase):
    def setUp(self):
        self.root = "test.n5"
        self.dataset = "test"
        self.dtype = "UINT8"
        self.dataset_size = [10, 10, 10]
        self.block_size = [2, 2, 2]

        pyn5.create_dataset(
            self.root, self.dataset, self.dataset_size, self.block_size, self.dtype
        )
        self.n5 = pyn5.open(self.root, self.dataset, self.dtype, False)

    def tearDown(self):
        if Path(self.root).is_dir():
            shutil.rmtree(str(Path(self.root).absolute()))

    def test_read_write(self):
        # make sure n5 is initialized to all zeros
        self.assertTrue(
            np.array_equal(
                pyn5.read(self.n5, (np.array([0, 0, 0]), np.array(self.dataset_size))),
                np.zeros([10, 10, 10]),
            )
        )

        # write ones to whole dataset, and then
        # write on partial blocks to make sure data isn't overwritten
        pyn5.write(
            self.n5,
            (np.array([0, 0, 0]), np.array(self.dataset_size)),
            np.ones(self.dataset_size),
        )
        self.assertTrue(
            np.array_equal(
                pyn5.read(self.n5, (np.array([0, 0, 0]), np.array(self.dataset_size))),
                np.ones([10, 10, 10]),
            )
        )

        pyn5.write(
            self.n5, (np.array([1, 1, 1]), np.array([3, 3, 3])), np.ones([2, 2, 2]) * 2
        )
        self.assertTrue(
            np.array_equal(
                pyn5.read(self.n5, (np.array([1, 1, 1]), np.array([3, 3, 3]))),
                np.ones([2, 2, 2]) * 2,
            )
        )

        # test writting non-uniform block to make sure axis orderings are correct
        self.n5.write_ndarray(
            np.array([1, 1, 1]),
            np.array(range(64), dtype=np.uint8).reshape([4, 4, 4]),
            0,
        )
        self.assertTrue(
            np.array_equal(
                self.n5.read_ndarray(np.array([1, 1, 1]), np.array([4, 4, 4])),
                np.array(range(64), dtype=int).reshape([4, 4, 4]),
            )
        )

        # sanity check axis orderings
        data = np.zeros([5, 7, 1], dtype=np.uint8)
        data[0, :, 0] = 1
        data[1, :, 0] = 2
        data[2, :, 0] = 3
        self.n5.write_ndarray(np.array([0, 0, 0]), data, 0)
        self.assertTrue(
            np.all(self.n5.read_ndarray(np.array([1, 0, 0]), np.array([1, 7, 1])) == 2)
        )
        np.testing.assert_equal(
            self.n5.read_ndarray(np.array([0, 0, 0]), np.array([3, 1, 1])).flatten(),
            np.array([1, 2, 3]),
        )

        # test writing data in non block shapes
        data = np.array(range(6), dtype=np.uint8).reshape([1, 2, 3])
        self.n5.write_ndarray(np.array([0, 0, 0]), data, 0)

        self.assertTrue(
            np.array_equal(
                self.n5.read_ndarray(np.array([0, 0, 0]), np.array([1, 2, 3])), data
            )
        )
