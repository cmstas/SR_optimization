# SR Optimization

SR optimization code borrowed from ttH & ttHH analyses. Updated to get rid of python2, root_numpy and CMSSW based combine dependencies.

It should work also elsewhere, but right now the scripts have been tested only on UAF machines!

## Installation

For the first time:

Requires conda `combine` installation, adding the combine conda env the awkward, uproot, xgboost and pyarrow packages

Here a re-arranged set of instructions taken from http://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/#standalone-compilation-with-conda
```
git clone https://github.com/cmstas/SR_optimization.git SR_optimization
cd SR_optimization

conda install --name base mamba # faster conda
mamba env create -f SRopt_env.yml

conda activate SRopt
pip install pyarrow==7.0.0 # For some reason I couldn't get mamba to install this version on the python 3.8 env that combine wants...

git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
source set_conda_env_vars.sh
# Need to reactivate
conda deactivate
conda activate SRopt

make CONDA=1 -j 12

cd -
source setup.sh # this creates the output folders if needed, and exports the COMBINE_BASE env variable
```

From then on, the env should be simply activated as :

```
conda activate SRopt
source setup.sh
```

## Running

If you have a parquet dataframe, with your MVA score(s) eveluated on the events, you can optimize signal regions with the following steps:

1. Convert `parquet` file to `TTree`:
```
python convert_parquet_to_root.py
  --input <path_to_parquet> # needed 
  --out_(dir/name) <output path and name>  #optional it would default to a SRopt folder on your ceph user area
  --slim # Output TTree contains only a small subset of branches (currently needed to use NW parquets) `
```
2. Optimize signal regions:
```
python optimize_srs_hh.py
--file <root_file>
--tag <tag> # this is a string to identify this optimization
--coupling "HH"  # Defines whic process is your signal
--nCores <int> # how many cores to use in parallel (will automatically use niceness so you can abuse it (hopefully :) )
--bins <int> # number of signal regions
--mvas #csv list of the scores you want to define the SR on
--weight #specify which branch contains the MC event weight (default "weight" but NW parquet uses "weight_tot") 
--minSB_events # minimum number of events in the mgg sidebands (defalut to 5)
--metric "upper limit" # could also use "significance"
--dry_run # do not optimize but estimate the limit on 1 cuts combo. You can specify it in the extSRs variable. If that's not defined random one is generated
```

For example, I might do:
```
python optimize_srs_hh.py --file "full2022_baseline.root" --tag "ful2022_baseline" --coupling "HH" --nCores 48 --bins "2" --mvas score_GluGluToHH --metric "upper limit"
```

This takes a `TTree` from "full2022_baseline.root" and optimizes 2 signal regions, based on best expected upper limit, using 48 cores in parallel and tagging the output models/plots/datacards/results with "ful2022_baseline".

Fit plots for each combination of cuts explored are automatically saved in your "~/public_html" folder under "SRs_scan/".

There is a WIP script (limit_skimmer.py that helps extracting best performing SRs across multiple optimization runs, based on the one Ian Reed wrote for the Run2 ttHH analysis. It is not yet updated to interplay with this repo, so I am not guaranteeing that it works right now.
