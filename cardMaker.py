import ROOT

ROOT.gROOT.SetBatch(True)

ROOT.gSystem.AddIncludePath("-I$COMBINE_BASE/ ")
ROOT.gSystem.Load("$COMBINE_BASE/build/lib/libHiggsAnalysisCombinedLimit.so")
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.DataHandling)
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.ObjectHandling)

class makeCards():

    def __init__(self, savepath, cardname, config={}):

        self.cardname = savepath + "/" + cardname #"CMS-HGG_mva_13p6TeV_datacard.txt"
        print (self.cardname)
        self.txtfile =  open(self.cardname, "w")

        #some lists
        self.processNames = []
        self.tagNames = []
        self.inputRootNames = []
        self.wsNames = []
        self.modelNames = []

        self.path = savepath

        if "sm_higgs_unc" in config.keys():
            self.sm_higgs_unc = config["sm_higgs_unc"]
        else:
            self.sm_higgs_unc = 0.0001

    def WriteBasicNum(self, nChannel, nSig, nBkg, nNuisance=0):

        if nChannel == -1:
            self.txtfile.write("imax *\n" )
        else:
            self.txtfile.write("imax {0}\n".format(nChannel) )

        if nSig == -1 and nBkg == -1:
            self.txtfile.write("jmax *\n" )
        else:
            self.txtfile.write("jmax {0}\n".format(nSig + nBkg - 1) )

        if nNuisance > 0:
            self.txtfile.write("kmax {0}\n".format(nNuisance) )
        else:
            self.txtfile.write("kmax *\n")

        self.txtfile.write("------------\n")

    def PrepareNames(self, sigList, bkgList, tagList, postFix):

        processes = sigList + bkgList
        processes.append("data_obs")

        for process in processes:
            for i in range(len(tagList)):
                self.processNames.append(process)
                self.tagNames.append(tagList[i])

                if process == "data_obs":
                    self.inputRootNames.append("CMS-HGG_bkg_" + tagList[i] + postFix + ".root")
                    self.wsNames.append("wbkg_13p6TeV")
                    self.modelNames.append("roohist_data_mass_" + tagList[i] + postFix)

                if ("hgg" in process) :
                    self.inputRootNames.append("CMS-HGG_sigfit_mva_" + process + "_" + tagList[i] + postFix + ".root")
                    self.wsNames.append("wsig_13p6TeV")
                    self.modelNames.append("hggpdfsmrel_" + process + "_" + tagList[i] + postFix)

                if "bkg" in process:
                    self.inputRootNames.append("CMS-HGG_bkg_" + tagList[i] + postFix + ".root")
                    self.wsNames.append("wbkg_13p6TeV")
                    self.modelNames.append("CMS_hgg_bkgshape_" + tagList[i] + postFix)


    def WriteShapes(self):

        if len(self.processNames) != len(self.tagNames) or len(self.processNames) != len(self.inputRootNames) or len(self.processNames) != len(self.wsNames) or len(self.processNames) != len(self.modelNames):
            print (len(self.processNames), len(self.tagNames), len(self.inputRootNames), len(self.wsNames), len(self.modelNames))
            print (self.processNames)
            print (self.inputRootNames)
            raise Exception('check n_quantiles and useNCores')

        for i in range(len(self.processNames)):
            self.txtfile.write("shapes " + self.processNames[i] + " " + self.tagNames[i] + " " + self.inputRootNames[i] + " " + self.wsNames[i] + ":" + self.modelNames[i] + "\n" )
        self.txtfile.write("------------\n")


    def WriteObs(self, tagList, obsEvents):

        self.txtfile.write("bin " + " ".join(tagList) + " \n" )
        self.txtfile.write("observation " + " ".join(obsEvents) +  "  \n")
        self.txtfile.write("------------\n")


    def WriteExpect(self, sigList, bkgList, tagList):

        processes = sigList + bkgList

        bin_l1 = ""
        process_l2 = ""
        process_l3 = ""
        rate_l4 = ""

        lumi_l5 = ""
        sm_higgs_l6 = ""

        sm_higgs_unc = self.sm_higgs_unc


        for tag in tagList:
            for i in range(len(processes)):

                bin_l1 += tag + " "
                process_l2 += processes[i] + " "
                process_l3 += str( i+1-len(sigList) ) + " "
                rate_l4 += "1.0 "
                if processes[i] == "bkg_mass":
                    lumi_l5 += "- "
                else:
                    lumi_l5 += "1.025 "

                if processes[i] == "sm_higgs":
                    sm_higgs_l6 += "%.3f/%.3f " % (1 - sm_higgs_unc, 1 + sm_higgs_unc)
                else:
                    sm_higgs_l6 += "- "


        bin_l1 = "bin " + bin_l1 + "\n"
        process_l2 = "process " + process_l2 + "\n"
        process_l3 = "process " + process_l3 + "\n"
        rate_l4 = "rate " + rate_l4 + "\n"

        lumi_l5 = "lumi_13p6TeV lnN " + lumi_l5 + "\n"
        sm_higgs_l6 = "sm_higgs_xs lnN " + sm_higgs_l6 + "\n"

        self.txtfile.write(bin_l1)
        self.txtfile.write(process_l2)
        self.txtfile.write(process_l3)
        self.txtfile.write(rate_l4)
        self.txtfile.write("------------\n")
        self.txtfile.write(lumi_l5)
        self.txtfile.write(sm_higgs_l6)

    def WriteCard(self, sigList, bkgList, tagList, postFix):

        self.WriteBasicNum(-1,-1,-1)

        self.PrepareNames(sigList, bkgList, tagList, postFix)
        self.WriteShapes()

        self.WriteObs(tagList, ["-1"]*len(tagList))

        self.WriteExpect(sigList, bkgList, tagList)
        self.txtfile.close()
