import shutil
import warnings
from pathlib import Path
from typing import Iterator

import numpy as np

from h5py_like import GroupBase, FileMixin, AttributeManagerBase, Mode, mutation
from h5py_like.common import Name
from h5py_like.base import H5ObjectLike
from pyn5.attributes import AttributeManager
from pyn5.dataset import Dataset
from .pyn5 import create_dataset

N5_VERSION = "2.0.2"


class Group(GroupBase):
    def _create_child_group(self, name) -> GroupBase:
        dpath = self._path / name

        try:
            obj = self._get_child(name)
        except KeyError:
            pass
        else:
            if isinstance(obj, Dataset):
                raise TypeError(f"Dataset found at {dpath}")
            elif isinstance(obj, Group):
                raise FileExistsError(f"Group already exists at {dpath}")

        dpath.mkdir()
        return Group(name, self)

    def _create_child_dataset(
        self, name, shape=None, dtype=None, data=None, chunks=None, **kwds
    ):
        if chunks is None:
            raise ValueError("'chunks' must be given")

        for key in kwds:
            warnings.warn(
                f"pyn5 does not implement '{key}' argument for create_dataset; it will be ignored"
            )

        if data is not None:
            data = np.asarray(data, dtype=dtype)
            dtype = data.dtype
            shape = data.shape

        dtype = np.dtype(dtype)

        dpath = self._path / name

        try:
            obj = self._get_child(name)
        except KeyError:
            pass
        else:
            if isinstance(obj, Dataset):
                raise TypeError(f"Dataset already exists at {dpath}")
            elif isinstance(obj, Group):
                raise FileExistsError(f"Group found at {dpath}")

        file_path = str(self.file.filename)
        create_dataset(
            file_path,
            str(Name(self.name) / name)[1:],
            list(shape)[::-1],
            list(chunks)[::-1],
            dtype.name.upper(),
        )

        ds = Dataset(name, self)
        if data is not None:
            ds[...] = data
        return ds

    def __init__(self, name, parent):
        self._name = name
        self._parent = parent
        self._path = self.parent._path / name

        self._attrs = AttributeManager.from_parent(self)
        super().__init__(self.mode)

    def _get_child(self, name) -> H5ObjectLike:
        dpath = self._path / name
        if not dpath.is_dir():
            raise KeyError()
        attrs = AttributeManager(dpath)
        if attrs._is_dataset():
            return Dataset(name, self)
        else:
            return Group(name, self)

    @mutation
    def __setitem__(self, name, obj):
        raise NotImplementedError()

    def copy(
        self,
        source,
        dest,
        name=None,
        shallow=False,
        expand_soft=False,
        expand_external=False,
        expand_refs=False,
        without_attrs=False,
    ):
        raise NotImplementedError()

    @property
    def attrs(self) -> AttributeManagerBase:
        return self._attrs

    @property
    def name(self) -> str:
        return str(Name(self.parent.name) / self._name)

    @property
    def parent(self):
        return self._parent

    @mutation
    def __delitem__(self, v) -> None:
        shutil.rmtree(self[v]._path)

    def __len__(self) -> int:
        return len(list(self))

    def __iter__(self) -> Iterator:
        for path in self._path.iterdir():
            if path.is_dir():
                yield path.name


class File(FileMixin, Group):
    def __setitem__(self, name, obj):
        raise NotImplementedError()

    def copy(
        self,
        source,
        dest,
        name=None,
        shallow=False,
        expand_soft=False,
        expand_external=False,
        expand_refs=False,
        without_attrs=False,
    ):
        raise NotImplementedError()

    def __init__(self, name, mode=Mode.READ_WRITE_CREATE):
        super().__init__(name, mode)
        self._require_dir(self.filename)
        self._path = self.filename
        self._attrs = AttributeManager.from_parent(self)

    def _require_dir(self, dpath: Path):
        if dpath.is_file():
            raise FileExistsError("File found at desired location of directory")
        created = False
        if dpath.is_dir():
            if self.mode == Mode.CREATE:
                raise FileExistsError()
            elif self.mode == Mode.CREATE_TRUNCATE:
                shutil.rmtree(dpath)
                dpath.mkdir()
                created = True
        else:
            if self.mode in (Mode.READ_ONLY, Mode.READ_WRITE):
                raise FileNotFoundError()
            else:
                dpath.mkdir(parents=True)
                created = True

        attrs = AttributeManager(dpath, self.mode)
        if created:
            attrs["n5"] = N5_VERSION
        else:
            version = attrs.get("n5")
            if version != N5_VERSION:
                raise ValueError(f"Expected N5 version '{N5_VERSION}', got {version}")
        return created
