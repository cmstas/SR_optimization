export COMBINE_BASE="${PWD}/HiggsAnalysis/CombinedLimit/"

mkdir -p optimization_results
mkdir -p models
if [[ ${hostname} == *"uaf"* ]]; then
  mkdir -p ~/public_html/SRs_scan/
else
  echo " Your site has no public_html folder, cannot create default directory for fitting plots, \ 
  make sure you create one and specify it running the SR optimization scripts" 
fi