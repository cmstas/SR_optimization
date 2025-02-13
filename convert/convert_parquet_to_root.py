import os
import glob
import numpy
import awkward as ak
import uproot
import argparse
import getpass

import json

parser = argparse.ArgumentParser()
usr=getpass.getuser()
parser.add_argument(
    "--input",
    help = "path to input parquet directory",
    type = str,
    default = '/home/users/iareed/HiggsDNA/Full_Samples_with_tH_with_systematics/'
)
parser.add_argument(
    "--FggFF",
    help = "path to FggFF",
    type = str,
    default = '/home/users/iareed/CMSSW_10_2_13/src/flashggFinalFit/'
)
parser.add_argument(
    "--tag",
    help = "unique tag to identify batch of processed samples",
    type = str,
    default = "SM_22Sep23_with_tH"
)
parser.add_argument(
    "--mva_name",
    help = "title of mva score to use",
    type = str,
    default = "mva_score"
)
parser.add_argument(
    "--mvas",
    nargs="*",
    help = "mva limits to SRs",
    type = float,
    default = [0.969541,0.9899]
)
parser.add_argument(
    "--unblind",
    help = "Unblind the signal region, 120-130 GeV",
    action = "store_true"
)
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
    for col in columns:
        #print(f"column {col} input shape {numpy_buffer[col].shape} output shape {dataframe[col].to_numpy().shape}")
        numpy_buffer[col] = dataframe[col].to_numpy()
    # Return results of conversion
    return numpy_buffer



# Format output directories
out_dir = str(args.FggFF) + 'files_systs/' + str(args.tag) + '/'
# Purge old files at save destination, set output structure
os.system("rm -rf %s"%(out_dir))

os.system("mkdir -p %s"%(out_dir))
os.system("mkdir -p %s/Data"%(out_dir))
os.system("mkdir -p %s/2016"%(out_dir))
os.system("mkdir -p %s/2017"%(out_dir))
os.system("mkdir -p %s/2018"%(out_dir))

# Organize binning
nSRs = len(args.mvas)
print(nSRs)
args.mvas+=[99]
args.mvas.sort(reverse=True)

#TODO: Alter now that process names are in the parquet
with open(str(args.input)+'/summary.json',"r") as f_in:
    procs_id_map = json.load(f_in)
procs_id_map = procs_id_map["sample_id_map"]

needed_fields=['CMS_hgg_mass','weight_central','process_id']
years = ['2017','2018']
procs = ['ttHH_ggbb','ttH_M125']

df = ak.from_parquet(str(args.input)+'merged_nominal.parquet')
df = df[df.process_id == procs_id_map["Data"]]
df['CMS_hgg_mass'] = df.Diphoton_mass

for sr in range(nSRs):
    print(f'Processing SR {sr}')
    sr_mask = (df[args.mva_name] < args.mvas[sr]) & (df[args.mva_name] >= args.mvas[sr+1])
    peak_mask = (df.Diphoton_mass < 120) | (df.Diphoton_mass > 130)
    if args.unblind:
        dfs = df[sr_mask]
    else:
        dfs = df[sr_mask & peak_mask]
    dfs = dfs[[f for f in dfs.fields if f in needed_fields]]
    print(dfs.fields)
    dfs = to_tensor(dfs)
    print(f'Adding {len(dfs)} events to allData')
    if not sr:
        with uproot.recreate(out_dir+'/Data/allData.root') as f_out:
            f_out['Data_13TeV_SR'+str(sr+1)] = dfs
    else:
        with uproot.update(out_dir+'/Data/allData.root') as f_out:
            f_out['Data_13TeV_SR'+str(sr+1)] = dfs
 
# Second, open all the files and save a file per year per process with all the systematics
files = glob.glob(str(args.input)+'/*.parquet')
firstRound = True
for f_in in files:
    df = ak.from_parquet(f_in)
    print(f'{len(df)} total entries')
    # Build unique TTree names
    tag = ''
    if 'nominal' not in f_in.split("/")[-1]:
        if 'up' in f_in.split("/")[-1]:
            tag  = f_in.split("merged")[-1]
            tag  = tag.split("_up")[0]
            tag  += 'Up01sigma'
        if 'down' in f_in.split("/")[-1]:
            tag  = f_in.split("merged")[-1]
            tag  = tag.split("_down")[0]
            tag  += 'Down01sigma'
    if 'scale' in f_in.split("/")[-1]:
        tag = '_MCScale' + tag
    if 'smear' in f_in.split("/")[-1]:
        tag = '_MCSmear' + tag
        df['CMS_hgg_mass'] = df['Diphoton_mass']
        df['weight'] = df['weight_central'] * 2
        df['weight_central'] = df['weight']

    yield_systematics = [ field for field in df.fields if ( "weight_" in field ) and ( "_up" in field or "_down" in field )]
    # A bit of gymnastics to get the inputs right for Mr. flashggFinalFit
    #TODO: Maybe consider renaming during the preselection/skimming?
    rename_syst = {}
    for syst in yield_systematics:
        if "_up" in syst:
            syst_central = syst.replace("_up","_central")
        elif "_down" in syst:
            syst_central = syst.replace("_down","_central")
        rename_syst[syst] = syst
        if 'btag' in syst_central:
            syst_central = 'weight_btag_deepjet_sf_SelectedJet_central'
        df[syst] = df[syst] / df[syst_central]
        if syst.endswith("_lf"):
            rename_syst[syst] = rename_syst[syst].replace("_lf","_LF")
        elif syst.endswith("_hf"):
            rename_syst[syst] = rename_syst[syst].replace("_hf","_HF")
        if "_up" in syst:
            if 'btag' in syst:
                rename_syst[syst] = rename_syst[syst].replace("_up","")
                rename_syst[syst] += "Up01sigma"
                continue
            rename_syst[syst] = syst.replace("_up","Up01sigma")
        if "_down" in syst:
            if 'btag' in syst:
                rename_syst[syst] = rename_syst[syst].replace("_down","")
                rename_syst[syst] += "Down01sigma"
                continue
            rename_syst[syst] = syst.replace("_down","Down01sigma")
        df[rename_syst[syst]] = df[syst]

    #for sr in range(nSRs):
    #    dfs = df.loc[ ( df[args.mva_name] < args.mvas[sr] ) & ( df[args.mva_name] >= args.mvas[sr+1] ) & (df.event % 2 == 1) ]
    #    print("Adding {} events to {}".format(len(dfs),year_str+"_"+proc_tag))
    #    dfs.to_root(out_dir+year_str+'/'+proc_tag+'_125.38_13TeV.root',''+proc_tag+'_125.38_13TeV_SR'+str(sr+1)+tag, mode='a')
    for y in years:
        dfy = df[df.year == y]
        for sr in range(nSRs):
            print(f'Processing SR {sr}')
            # Test/Train/Validation split
            #TODO: Match one used in the Run3 SR optimizaiton
            sr_mask = (dfy[args.mva_name] < args.mvas[sr]) & (dfy[args.mva_name] >= args.mvas[sr+1]) & (dfy.event % 2 == 1) 
            peak_mask = (dfy.Diphoton_mass < 120) | (dfy.Diphoton_mass > 130)
            if args.unblind:
                dfs = dfy[sr_mask]
            else:
                dfs = dfy[sr_mask & peak_mask]
            dfs = dfs[[f for f in dfs.fields if f in needed_fields]]

            for p in procs:
                dfo = dfs[dfs.process_id==procs_id_map[p]] 
                dfo = to_tensor(dfo)
                print(f'Adding {len(dfo)} entires to {p} {y}')
                if firstRound:
                    with uproot.recreate(out_dir+f'/{y}/{p}_125.38_13TeV.root') as f_out:
                        f_out[f'{p}_125.38_13TeV_SR'+str(sr+1)+tag] = dfo
                else:
                    with uproot.update(out_dir+f'/{y}/{p}_125.38_13TeV.root') as f_out:
                        f_out[f'{p}_125.38_13TeV_SR'+str(sr+1)+tag] = dfo
    firstRound = False
 

#
#
#
#
#events = ak.from_parquet(args.input)
#
## For the time being, we have to match processes into integers. Will need to modify the SR opt FIXME  
#proc_dict={
#    "Data_EraE": 0, "Data_EraF": 0, "Data_EraG": 0, "Data": 0,
#    "GluGluHToGG": 1, "ttHToGG": 2, "VBFHToGG": 3, "VHToGG": 4,
#    "GGJets": 5, "DDQCDGJets": 6,"DDBKG": 6, 
#    "GluGluToHH": 8  
#}
#
#if "proc" in events.fields: #SnT style parquet
#  events = ak.with_field(events, [ proc_dict.get(proc) for proc in events["proc"].to_list()] , "process_id")
#  needed_fields=["mass","weight","score_GluGluToHH","process_id"]
#
#elif "sample" in events.fields: #NW style parquet
#  events = ak.with_field(events, [ proc_dict.get(proc) for proc in events["sample"].to_list()] , "process_id")
#  needed_fields=["pt","mass","weight_tot","signleH_dnn_new","ddbkg_dnn","process_id"]
#else:
#    sys.exit("[Parquet2root] Parquet format not supported (no proc or sample field found)")
#    
#print ("[Parquet2root] Done with the id addition")
#
#if args.slim: # Slimming by defaut. It's good for you + NW parquet conversion not fully working for literal fields FIXME
#    events = events[[f for f in events.fields if f in needed_fields]]
#    print("[Parquet2root] Done with the slimming")
#
##square down parquet dataframes before exporting to root
#events = to_tensor(events)
#
#if args.out_name is None:
#    output_root = args.out_dir + args.input.split("/")[-1].replace(".parquet", ".root")
#else:
#    output_root = args.out_dir + args.out_name + ".root"
#
#with uproot.recreate(output_root) as f:
#  f["t"] = events
#  
#print("[Parquet2root] All good")
