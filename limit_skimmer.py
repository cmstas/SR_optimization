import json

in_dir = './optimization_results/'
base = 'guided_optimizer_results_HH_ggHH_'
tags = [ 'test' ] #put here the SR optimization runs you want to compare

def limit_skimmer(in_dir,base,tag):
    with open(in_dir+base+tag+'.json', 'r') as f_in:
        results = json.load(f_in)

    best_lim = 999
    best_selection = ['0','0']
    best_yields = -999
    best_spread = -999

    for guess in results['1d']['2']['guided']['exp_lim']: # edit this to match the optimization results json
        if guess['disqualified'] == "True":
            continue
        if guess['exp_lim'][0] < best_lim:
            best_lim = guess['exp_lim'][0]
            best_spread = guess['exp_lim']
            best_selection = guess['selection']
            best_yields = guess['yields']

    print('For analysis: {}, the best limit was: {}, with selections, {}'.format(tag,best_lim,best_selection))
    print('Spread: ', best_spread)
    print('It\'s yields were: ', best_yields)

for tag in tags:
    limit_skimmer(in_dir,base,tag)
    print('-----------------------------------')
    print('')
