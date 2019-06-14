import errno
import json
from contextlib import contextmanager
from typing import Iterator, Any, Dict

from h5py_like import AttributeManagerBase, mutation, Mode


class AttributeManager(AttributeManagerBase):
    _dataset_keys = {"dimensions", "blockSize", "dataType", "compression"}

    def __init__(self, fpath, mode=Mode.READ_ONLY):
        self._path = fpath / "attributes.json"
        super().__init__(mode)

    @classmethod
    def from_parent(cls, parent):
        return cls(parent._path, parent.mode)

    @mutation
    def __setitem__(self, k, v) -> None:
        with self._open_attributes(True) as attrs:
            attrs[k] = v

    @mutation
    def __delitem__(self, v) -> None:
        with self._open_attributes(True) as attrs:
            del attrs[v]

    def __getitem__(self, k):
        with self._open_attributes(True) as attrs:
            return attrs[k]

    def __len__(self) -> int:
        with self._open_attributes(True) as attrs:
            return len(attrs)

    def __iter__(self) -> Iterator:
        yield from self.keys()

    def keys(self):
        with self._open_attributes() as attrs:
            return attrs.keys()

    def values(self):
        with self._open_attributes() as attrs:
            return attrs.values()

    def items(self):
        with self._open_attributes() as attrs:
            return attrs.items()

    def __contains__(self, item):
        with self._open_attributes() as attrs:
            return item in attrs

    def _is_dataset(self):
        with self._open_attributes() as attrs:
            return self._dataset_keys.issubset(attrs)

    @contextmanager
    def _open_attributes(self, write=False) -> Dict[str, Any]:
        attributes = self._read_attributes()
        yield attributes
        if write:
            self._write_attributes(attributes)

    def _read_attributes(self):
        try:
            with open(self._path, "r") as f:
                attributes = json.load(f)
        except ValueError:
            attributes = {}
        except IOError as e:
            if e.errno == errno.ENOENT:
                attributes = {}
            else:
                raise

        return attributes

    def _write_attributes(self, attrs):
        with open(self._path, "w") as f:
            json.dump(attrs, f)
