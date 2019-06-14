from copy import deepcopy

from h5py_like.test_utils import FileTestBase, DatasetTestBase, GroupTestBase

ds_kwargs = deepcopy(DatasetTestBase.dataset_kwargs)
ds_kwargs["chunks"] = (5, 5, 5)


class TestFile(FileTestBase):
    dataset_kwargs = ds_kwargs
    pass


class TestGroup(GroupTestBase):
    dataset_kwargs = ds_kwargs
    pass


class TestDataset(DatasetTestBase):
    dataset_kwargs = ds_kwargs
    pass
