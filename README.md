# SR Optimization

SR optimization code borrowed from ttH & ttHH analyses. Updated to get rid of python2, root_numpy and CMSSW based combine dependencies

## Installation

For the first time:

Requires conda `combine` installation


```
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit

conda install --name base mamba # faster conda
mamba env create -f conda_env.yml

conda activate combine
source set_conda_env_vars.sh
# Need to reactivate
conda deactivate
conda activate combine

make CONDA=1 -j 8
```

# Install combine

git clone git@github.com:cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit

# compile

```
cmsenv
scram b -j 20
```

After doing that once, you can set up the `combine` and `CMSSW` environments with
```
source setup.sh
```

## Running

After using `HggAnalysisDev/MVAs/zip_mva_scores.py` to zip your MVA score back into the dataframe of events, you can optimize signal regions with the following steps:

1. Use `HggAnalysisDev/MVAs/convert_dataframe_to_numpy.py` to convert `pkl` -> `npz` file.
2. Convert `npz` file to `TTree`: `python convert_numpy_to_root.py --input <path_to_npz>>`
3. Optimize signal regions:
```
python optimize_srs_hh.py
--file <root_file>
--tag <tag> # this is a string to identify this optimization
--coupling "HH"
--nCores <int> # how many cores to use in parallel (will automatically use niceness)
--bins <int> # number of signal regions
--metric "upper limit" # could also use "significance"
```

For example, I might do:
```
python optimize_srs_hh.py --file "HHggTauTau_1tau_24Mar2021.root" --tag "HHggTauTau_addggWW_24Mar2021" --coupling "HH" --nCores 18 --bins "2" --metric "upper limit"
```

This takes a `TTree` from "HHggTauTau_1tau_24Mar2021.root" and optimizes 2 signal regions, based on best expected upper limit, using 18 cores in parallel and tagging the output models/plots/datacards/results with "HHggTauTau_addggWW_24Mar2021".
