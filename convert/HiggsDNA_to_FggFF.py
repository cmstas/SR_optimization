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
    default = "Run3_env_test"
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
    default = [0.99,0.9]
)
parser.add_argument(
    "--unblind",
    help = "Unblind the signal region, 120-130 GeV",
    action = "store_true"
)
args = parser.parse_args()

"""
Script to convert parquet files into FlashggFinalFit flavor TTrees.
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
            else:
                dtype_list.append(type(dataframe[column][0]))
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
        dtype = dtype_dict
    )
    # Insert values from dataframe columns into numpy labels
    for col in columns:
        #print(f"column {col} input shape {numpy_buffer[col].shape} output shape {dataframe[col].to_numpy().shape}")
        numpy_buffer[col] = dataframe[col].to_numpy()
    return numpy_buffer

def save_to_root(filePath, TTreeName, df):
    if os.path.isfile(filePath):
        with uproot.update(filePath) as f_out:
            f_out[TTreeName] = df
    else:
        with uproot.recreate(filePath) as f_out:
            f_out[TTreeName] = df

needed_fields=['CMS_hgg_mass','weight_central','process_id','proc']
years = ['2017','2018']
procs = {'ttHH_ggbb':'ttHH_ggbb',
         'ttH_M125':'ttH'
        }

# Format output directories
out_dir = f'{args.FggFF}/files_systs/{args.tag}/'
if os.path.isdir(out_dir):
    print(f'Destination path {out_dir} already exits')
    print('Change tag or remove directory')
    quit()
# Purge old files at save destination, set output structure
os.system(f'rm -rf {out_dir}')

os.system(f'mkdir -p {out_dir}')
os.system(f'mkdir -p {out_dir}/Data')
for year in years:
    os.system(f'mkdir -p {out_dir}/{year}')
    
# Organize binning
nSRs = len(args.mvas)
args.mvas+=[99]
args.mvas.sort(reverse=True)

print('Started Processing Data')
df = ak.from_parquet(str(args.input)+'merged_nominal.parquet')
df = df[df.proc == "Data"]
print(f'File contains {len(df)} total Data events')
df['CMS_hgg_mass'] = df.Diphoton_mass

out_file = f'{out_dir}/Data/allData.root'
for sr in range(nSRs):
    sr_mask = (df[args.mva_name] < args.mvas[sr]) & (df[args.mva_name] >= args.mvas[sr+1])
    peak_mask = (df.Diphoton_mass < 120) | (df.Diphoton_mass > 130)
    if args.unblind:
        df_sr = df[sr_mask]
    else:
        df_sr = df[sr_mask & peak_mask]
    df_sr = to_tensor(df_sr, needed_fields)
    print(f'Adding {len(df_sr)} events to allData SR{sr+1}')
    save_to_root(out_file, f'Data_13TeV_SR{sr+1}', df_sr)
print('------------------------')

print("Started Processing MC")
# Second, open all the files and save a file per year per process with all the systematics
files = glob.glob(str(args.input)+'/*.parquet')
for f_in in files:
    print(f'Started Processing {f_in.split("/")[-1]}')
    df = ak.from_parquet(f_in)
    print(f'File contains {len(df)} total entries')
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

    # Renaming for Mr. flashggFinalFit
    df['CMS_hgg_mass'] = df['Diphoton_mass']
    # Train/test/validation splits
    df['weight'] = df['weight_central'] * 2
    df['weight_central'] = df['weight']

    yield_systematics = [field for field in df.fields if ("weight_" in field) and ("_up" in field or "_down" in field)]
    # A bit of gymnastics to get the inputs right for Mr. flashggFinalFit
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
    needed_fields+=rename_syst.values()

    for y in years:
        print('----------------------------')
        print(f'Started Processing year {y}')
        df_year = df[df.year == y]
        for sr in range(nSRs):
            # Test/Train/Validation split
            #TODO: Match one used in the Run3 SR optimizaiton
            sr_mask = (df_year[args.mva_name] < args.mvas[sr]) & (df_year[args.mva_name] >= args.mvas[sr+1]) & (df_year.event % 2 == 1) 
            peak_mask = (df_year.Diphoton_mass < 120) | (df_year.Diphoton_mass > 130)
            if args.unblind:
                df_sr = df_year[sr_mask]
            else:
                df_sr = df_year[sr_mask & peak_mask]

            for old, new in procs.items():
                df_out = df_sr[df_sr.proc==procs[old]] 
                df_out = to_tensor(df_out, needed_fields)
                print(f'Adding {len(df_out)} entires to {new} {y} SR{sr+1}')
                out_file = f'{out_dir}/{y}/{new}_125.38_13TeV.root'
                save_to_root(out_file, f'{new}_125.38_13TeV_SR{sr+1}{tag}', df_out)
    needed_fields = needed_fields[:-len(rename_syst.values())]
    print('----------------------------')
print('All files processed')
