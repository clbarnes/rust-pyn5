
def test_write_block(bench_dataset, benchmark):
    arr, ds = bench_dataset
    slicing = tuple(slice(None, c) for c in ds.block_shape)
    chunk_arr = arr[slicing].flatten().tolist()

    benchmark(ds.write_block, [0, 0, 0], chunk_arr)


# def test_write_whole(bench_dataset, benchmark):
#     arr, ds = bench_dataset
#
#     benchmark(ds.write_ndarray, [0, 0, 0], arr, 0)
#
#
# def test_read_whole(bench_dataset_full, benchmark):
#     arr, ds = bench_dataset_full
#
#     benchmark(ds.read_ndarray, [0, 0, 0], arr.shape)
