import os

import ROOT
ROOT.gROOT.SetBatch(True)

import numpy
import uproot
import subprocess

ROOT.gSystem.Load("$COMBINE_BASE/build/lib/libHiggsAnalysisCombinedLimit.so")
ROOT.gSystem.AddIncludePath("-I$ROOFITSYS/include")
ROOT.gSystem.AddIncludePath("-Iinclude/")
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.DataHandling)
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.ObjectHandling)

class scanClass():

    def __init__(self, config):

        self.debug = False

        self.tag = config["tag"]
        self.selection= config["selection"]
        self.modelpath = config["modelpath"]
        self.plotpath = config["plotpath"]
        self.var = config["var"]
        self.weightVar = config["weightVar"]
        self.filename = config["filename"]

        self.treename = "t"

        self.config = config

    def getTree(self):

        self.file = ROOT.TFile.Open(self.filename)
        self.tree = self.file.Get(self.treename)
        if not self.tree:
            print ("[scanClass.py] BAD TREE!")
        return self.tree

    def getEfficiency(self, cut_denominator, cut_numerator):

        h_denominator = ROOT.TH1F("h_denominator", "", 320, 100, 180)
        self.tree.Project(h_denominator.GetName(), self.var, self.weightVar + "*(" + cut_denominator + ")")
        h_numerator = ROOT.TH1F("h_numerator", "", 320, 100, 180)
        self.tree.Project(h_numerator.GetName(), self.var, self.weightVar + "*(" + cut_numerator + ")")
        n_denominator = h_denominator.Integral()
        n_numerator = h_numerator.Integral()

        efficiency = n_numerator/n_denominator
        print (efficiency)
        return efficiency

    def cleanDir(self):

        pathCmd =  "mkdir -p " + self.modelpath + ";"
        pathCmd += "rm " + self.modelpath+ "*;"
        pathCmd += "mkdir -p " + self.plotpath + ";"
        pathCmd += "rm " + self.plotpath+ "*;"
        pathCmd += "cp ./plotting/index.php " + self.plotpath

        subprocess.call(pathCmd, shell=True)

    def quantiles_to_mva_score(self, n_quantiles, mvaName, selection = ""):
        # for given selection, return mva_scores corresponding to each quantile in n_quantiles

        # get a numpy array from tree
        print("[SCANCLASS] Calculating quantile -> mva score function for %s with %d quantiles" % (mvaName, n_quantiles))
        print("[SCANCLASS]", self.selection + selection)
        print("[SCANCLASS]", [mvaName])
        
        tree = uproot.open(self.filename)[self.treename] 
        mva_scores = tree.arrays([mvaName], 
                                 cut=self.selection + selection,
                                 library="np")[mvaName]
        
        sorted_mva = numpy.flip(numpy.sort(mva_scores), 0)
        quantiles = []
        mva = []
        for i in range(n_quantiles):
            idx = int((float(i+1) / float(n_quantiles)) * len(sorted_mva)) - 1
            quantiles.append(float(i+1) / float(n_quantiles))
            mva.append(sorted_mva[idx])

        return mva, quantiles


    def runCombine(self, config):
        
        # perform global fit with combine
        combineOption = config["combineOption"]
        combineOutName = config["combineOutName"]
        cardName = config["cardName"]
        outtxtName = config["outtxtName"]

        cmdCombine = "#!/bin/sh\n\n"
        cmdCombine += "cd " + self.modelpath + ";"
        cmdCombine += "combine -M " + combineOption + " -n " + combineOutName + " " + cardName + " -t -1 > " + self.modelpath + outtxtName + ";"

        print (cmdCombine)
        
        combineCmdFileName = self.modelpath + "combineCmd_" + combineOutName + ".sh"
        combineCmdFile = open(combineCmdFileName,"w")
        combineCmdFile.write(cmdCombine)
        combineCmdFile.close() #to change file access modes

        os.system("chmod u+x %s" % combineCmdFileName)
        os.chdir(self.modelpath)
        subprocess.call(["./%s" % combineCmdFileName.split("/")[-1]])

        if "Significance" in combineOption:
            significance = os.popen('grep "Significance:" %s | awk "{print $2}"' % (self.modelpath + outtxtName)).read().split(" ")[-1]
            sig_up1sigma = 0
            sig_down1sigma = 0
            sig_up2sigma = 0
            sig_down2sigma = 0

        elif "MultiDimFit" in combineOption:
            cl = os.popen('grep "r :" %s | awk "{print $2}"' % (self.modelpath + outtxtName)).read().split(" ")[-2]
            cl = cl.split("/")
            cl_up = cl[1][1:]
            cl_down = cl[0][1:]
            significance = max(float(cl_up),float(cl_down))
            sig_up1sigma = cl_up
            sig_down1sigma = cl_down
            sig_up2sigma = 0
            sig_down2sigma = 0

        elif "AsymptoticLimits" in combineOption:
            significance = os.popen('grep "Expected 50.0" %s | awk "{print $2}"' % (self.modelpath + outtxtName)).read().split(" ")[-1]
            sig_up1sigma = os.popen('grep "Expected 84.0" %s | awk "{print $2}"' % (self.modelpath + outtxtName)).read().split(" ")[-1]
            sig_down1sigma = os.popen('grep "Expected 16.0" %s | awk "{print $2}"' % (self.modelpath + outtxtName)).read().split(" ")[-1]
            sig_up2sigma = os.popen('grep "Expected 97.5" %s | awk "{print $2}"' % (self.modelpath + outtxtName)).read().split(" ")[-1]
            sig_down2sigma = os.popen('grep "Expected  2.5" %s | awk "{print $2}"' % (self.modelpath + outtxtName)).read().split(" ")[-1]

        return float(significance), float(sig_up1sigma), float(sig_down1sigma), float(sig_up2sigma), float(sig_down2sigma)

