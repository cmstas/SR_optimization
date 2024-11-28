import numpy
import awkward as ak
import uproot
import sys

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--input", help = "input parquet file", type=str, default = "/ceph/cms/store/user/azecchin/ScoredParquet/fitted_pq_dnns.parquet")
parser.add_argument("--out_dir", help = "output directory", type=str, default = "/ceph/cms/store/user/azecchin/SRopt")
parser.add_argument("--out_name", help = "output filename, without extension", type=str, default = None)
parser.add_argument("--slim", help = "output file contains minimal branches", action="store_true", default = True)
args = parser.parse_args()

"""
Script to convert parquet files into TTrees so that it can be used with the SRs optimization script.
"""

def to_tensor(dataframe, columns = [], dtypes = {}):
    # Use all columns from data frame if none where listed when called
    if len(columns) <= 0:
        columns = dataframe.fields
    # Build list of dtypes to use, updating from any `dtypes` passed when called
    dtype_list = []
    for column in columns:
        if column not in dtypes.keys():
            if column == "proc" or column == "sample"or column =="run_era":
                dtype_list.append("S15")
            else: dtype_list.append(type(dataframe[column][0]))
                
        else:
            dtype_list.append(dtypes[column])
    # Build dictionary with lists of column names and formatting in the same order
    dtype_dict = {
        'names': columns,
        'formats': dtype_list
    }
    # Initialize _mostly_ empty numpy array with column names and formatting
    numpy_buffer = numpy.zeros(
        shape = len(dataframe),
        dtype = dtype_dict)
    # Insert values from dataframe columns into numpy labels
    for column in columns:
        print(f"column {column} input shape {numpy_buffer[column].shape} 
                                output shape {dataframe[column].to_numpy().shape}")
        numpy_buffer[column] = dataframe[column].to_numpy()
    # Return results of conversion
    return numpy_buffer


events = ak.from_parquet(args.input)

# For the time being, we have to match processes into integers. Will need to modify the SR opt FIXME  
proc_dict={
    "Data_EraE": 0, "Data_EraF": 0, "Data_EraG": 0, "Data": 0,
    "GluGluHToGG": 1, "ttHToGG": 2, "VBFHToGG": 3, "VHToGG": 4,
    "GGJets": 5, "DDQCDGJets": 6,"DDBKG": 6, 
    "GluGluToHH": 8  
}

if "proc" in events.fields(): #SnT style parquet
  events = ak.with_field(events, [ proc_dict.get(proc) for proc in events["proc"].to_list()] , "process_id")
  needed_fields=["mass","weight","score_GluGluToHH ","process_id"]

elif "sample" in events.fields(): #NW style parquet
  events = ak.with_field(events, [ proc_dict.get(proc) for proc in events["sample"].to_list()] , "process_id")
  needed_fields=["pt","mass","weight_tot","signleH_dnn_new","ddbkg_dnn","process_id"]
else:
    sys.exit("[Parquet2root] Parquet format not supported (no proc or sample field found)")
    
print ("[Parquet2root] Done with the id addition")

if args.slim: # Slimming by defaut. It's good for you + NW parquet conversion not fully working for literal fields FIXME
    events = events[[f for f in events.fields if f in needed_fields]]
    print("[Parquet2root] Done with the slimming")

events = to_tensor(events)

if args.out_name is None:
    output_root = args.out_dir + args.input.split("/")[-1].replace(".parquet", ".root")
else:
    output_root = args.out_dir + args.out_name + ".root"

with uproot.recreate(output_root) as f:
  f["t"] = events
