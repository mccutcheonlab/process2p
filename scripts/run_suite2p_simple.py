from sys import argv
from suite2p import default_ops, run_s2p

path_to_data = argv[1]
db = {'data_path': [path_to_data]}

ops = default_ops()
if len(argv) > 2:
    ops["tiff_list"] = [argv[2]]

run_s2p(ops=ops,db=db)