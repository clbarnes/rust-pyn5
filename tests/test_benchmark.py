
def test_write(bench_dataset, benchmark):
    arr, ds = bench_dataset

    def fn():
        return ds.write_ndarray([0, 0, 0], arr, 0)

    benchmark(fn)


def test_read(bench_dataset_full, benchmark):
    arr, ds = bench_dataset_full

    def fn():
        return ds.read_ndarray([0, 0, 0], arr.shape)

    benchmark(fn)
