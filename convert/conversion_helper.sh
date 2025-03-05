#! /usr/bin/bash

input=/home/users/iareed/HiggsDNA/pre_app_all_local/
fggff=/home/users/iareed/CMSSW_10_2_13/src/flashggFinalFit/
tag="Run3_env_test_again"
mva_name="SM_mva_score"
sr1=0.99
sr2=0.96
python HiggsDNA_to_FggFF.py --input "$input" --FggFF "$fggff" --tag "$tag" --mvas $sr1 $sr2 --mva_name "$mva_name" #--unblind

# Example for processing interpreations with multiple trainings/mass points
#declare -A sr1_edges=(
#[250]=0.9869
#[275]=0.9874
#)
#declare -A sr2_edges=(
#[250]=0.869321
#[275]=0.743894
#)
#for mass in 250 275
#do
#    tag="2HDM_M${mass}_pre_app_1108_unblind"
#    mva_name="2HDM_M${mass}_mva_score"
#    sr1=${sr1_edges[$mass]}
#    sr2=${sr2_edges[$mass]}
#    # Use a conversion file with dummy values for the given point to avoid multiple files per interpratation
#    sed -i "38,40 s/dummy/${mass}/g" convert_HiggsDNA_to_FggFF.py
#    python convert_HiggsDNA_to_FggFF.py --input "$input" --FggFF "$fggff" --tag "$tag" --mvas $sr1 $sr2 --mva_name "$mva_name" #--unblind
#    sed -i "38,40 s/${mass}/dummy/g" convert_HiggsDNA_to_FggFF.py
#done
