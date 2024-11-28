import guided_optimizer_hh as guided_optimizer

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--tag", help = "tag to distinguish this optimization", type=str, default = "test")
parser.add_argument("--file", help = "path to final fit tree", type=str)
parser.add_argument("--coupling", help = "which signal you want", type=str)
parser.add_argument("--mvas", help = "csv list of mvas for SR optimization",type=str, default = "mva_score")
parser.add_argument("--weight", help = "name of the weight field to be used",type=str, default = "weight")
parser.add_argument("--sm_higgs_unc", help = "value of unc on sm higgs processes", type=float, default = 0.1)
parser.add_argument("--nCores", help = "number of cores to use", type=int, default = 18)
parser.add_argument("--minSB_events", help = "minimum number of events in mgg sideband", type=float, default = 5.)
parser.add_argument("--bins", help = "csv list of number of bins", type=str, default = "1,2,3,4,5")
parser.add_argument("--metric", help = "What are you optimizing for? Possible metrics are: \n \
                    limit \n \
                    upper limit \n \
                    significance \n \
                    cl", type=str, default = "limit")
parser.add_argument("--pt_selection", help = "cut on dipho_pt", type=str, default="")
parser.add_argument("--dry_run", help = "Don't optimize SRs, but run all the rest using fixed SR", action='store_true')

args = parser.parse_args()

mvas = args.mvas.split(",")
dim = len(mvas)
mva_dict = { str(dim) + "d" : mvas }

bins = [int(a) for a in args.bins.split(",")]

if args.metric == "limit":
    combineOption = 'AsymptoticLimits -m 125 --expectSignal=0'
elif args.metric == "upper limit":
    combineOption = 'AsymptoticLimits -m 125 --expectSignal=1'
elif args.metric == "significance":
    combineOption = 'Significance --expectSignal=1 '
elif args.metric == "cl":
    combineOption = 'MultiDimFit --algo=singles --expectSignal=1'

optimizer = guided_optimizer.Guided_Optimizer(
                input = args.file,
                tag = args.tag,
                coupling = args.coupling,
                nCores = args.nCores,

                sm_higgs_unc = args.sm_higgs_unc,
                combineOption = combineOption,
                pt_selection = args.pt_selection,

                n_bins = bins,
                mvas = mva_dict,
                weight_var = args.weight,
                strategies = ['guided'],
                minSBevents = args.minSB_events,
                diagnostic_mode=args.dry_run,
                # when providing ext SRS in 2d boundaries are:
                # mva1_bin0,mva1_bin1,mva2_bin0,mva2_bin1 
                extSRs = [0.9,0.8,0.9,0.9],
               
                initial_points = 36,
                points_per_epoch = 36,
                n_epochs = 5,
                verbose = True
)

optimizer.optimize()
