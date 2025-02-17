import ROOT
ROOT.gROOT.SetBatch(True)
from tdrStyle import *
setTDRStyle()

ROOT.gSystem.AddIncludePath("-I$COMBINE_BASE/ ")
ROOT.gSystem.Load("$COMBINE_BASE/build/lib/libHiggsAnalysisCombinedLimit.so")
ROOT.gSystem.AddIncludePath("-I$ROOFITSYS/include")
ROOT.gSystem.AddIncludePath("-Iinclude/")
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.DataHandling)
ROOT.RooMsgService.instance().getStream(1).removeTopic(ROOT.RooFit.ObjectHandling)

class makeModel():

    def __init__(self, config):

        self.debug = False

        self.tag = config["tag"]
        self.selection = config["selection"]
        self.plotpath = config["plotpath"]
        self.modelpath = config["modelpath"]
        self.savename = config["savename"]
        self.var = config["var"] #mass or masses
        # self.dim = config["dim"] #1D or 2D
        self.weightVar = config["weightVar"] #weight
        self.norm = -1
        self.filename = config["filename"]

        self.treename = "t"


    def getTree(self, t):

        self.tree = t


    def getTreeFromFile(self):

        self.file = ROOT.TFile.Open(self.filename)
        self.tree = self.file.Get(self.treename)


    def cleanDir(self): 
    #not used. One can decide to overwrite the output directories when using the same tag

        pathCmd =  "mkdir -p " + self.modelpath + ";"
        pathCmd += "rm " + self.modelpath+ "*;"
        pathCmd += "mkdir -p " + self.plotpath + ";"
        pathCmd += "rm " + self.plotpath+ "*;"
        pathCmd += "cp ./plotting/index.php " + self.plotpath

    def makeSignalModel(self, workspaceName, config):
        rooVar = "CMS_hgg_mass"

        replaceNorm = config["replaceNorm"]
        norm_in = config["norm_in"]
        fixParameters = config["fixParameters"]

        w = ROOT.RooWorkspace(workspaceName)
        w.factory(rooVar + "[100,180]")
        w.factory("MH[125]")

        h_mgg = ROOT.TH1F("h_mgg", "h_mgg", 320, 100, 180)
        h_mgg.Sumw2()

        #print("[makeModels.py] Info: h_mgg name: %s, var: %s, weightVar: %s, selection: %s" % (h_mgg.GetName(), self.var, self.weightVar, self.selection))

        self.tree.Project(h_mgg.GetName(), self.var[0], self.weightVar + "*(" + self.selection + ")")
        d_mgg = ROOT.RooDataHist("roohist_data_mass_" + self.tag, "", ROOT.RooArgList(w.var(rooVar)), h_mgg, 1)
        #print "bin dataset", h_mgg.Integral(), d_mgg.sumEntries(), d_mgg.numEntries()
       

        # normalization
        norm = d_mgg.sumEntries()
        if replaceNorm:
            norm = norm_in
        if norm <= 0:
            norm = 1e-09
        
        rv_norm = ROOT.RooRealVar(self.tag+"_norm", "", norm)

        self.norm = norm
        # pdf
        if config["simple"]:
          w.factory("Gaussian:gaus_"+self.tag+"(" + rooVar + ", mean_gaus_"+self.tag+"[125,120,130], width_gaus_"+
                    self.tag+"[2, 0.1, 10])")
        else:
          w.factory("DoubleCB:"+self.tag+"(" + rooVar + ", mean_"+self.tag+"[125,120,130], sigma_"+
                    self.tag+"[1,0.5,5], a1_"+self.tag+"[1,0.1,10], n1_"+self.tag+"[1,0.1,10], a2_"+
                    self.tag+"[1,0.1,10], n2_"+self.tag+"[1,0.1,10])")
       
        #w.factory("DoubleCB:dcb_"+self.tag+"(" + rooVar + ", mean_"+self.tag+"[125,120,130], sigma_"+self.tag+"[1,0,5], a1_"+self.tag+"[1,0,10], n1_"+self.tag+"[1,0,10], a2_"+self.tag+"[1,0,10], n2_"+self.tag+"[1,0,10])")
        #w.factory("SUM:" + self.tag + "(gaus_" + self.tag + ",dcb_" + self.tag + ")")
        #w.factory("SUM:"+self.tag + "(norm_gaus[1,0,999999]*gaus_" + self.tag + ",norm_dcb[1,0,999999]*dcb_" + self.tag + ")")
        exPdf = ROOT.RooExtendPdf("extend" + self.tag, "", w.pdf(self.tag), rv_norm)

        # fit
        w.pdf(self.tag).fitTo(d_mgg, ROOT.RooFit.SumW2Error(True) ,ROOT.RooFit.PrintLevel(-1))

        getattr(w,'import')(rv_norm)
        getattr(w,'import')(exPdf)

        # frame
        frame = w.var("CMS_hgg_mass").frame()
        d_mgg.plotOn(frame)
        w.pdf(self.tag).plotOn(frame)

        # plot
        if self.plotpath:
          c1 = ROOT.TCanvas("c1", "c1", 800, 800)
          dummy = ROOT.TH1D("dummy","dummy",1,100,180)
          dummy.SetMinimum(0)
          dummy.SetMaximum(h_mgg.GetMaximum()*1.2)
          dummy.SetLineColor(0)
          dummy.SetMarkerColor(0)
          dummy.SetLineWidth(0)
          dummy.SetMarkerSize(0)
          dummy.GetYaxis().SetTitle("Events")
          dummy.GetYaxis().SetTitleOffset(1.3)
          dummy.GetXaxis().SetTitle("m_{#gamma#gamma} (GeV)")
          dummy.Draw()

          latex = ROOT.TLatex()
          latex.SetNDC()
          latex.SetTextSize(0.6*c1.GetTopMargin())
          latex.SetTextFont(42)
          latex.SetTextAlign(11)
          latex.SetTextColor(1)

          latex.DrawLatex(0.5, 0.85, (self.tag.split("_"))[-2] + "_" + (self.tag.split("_"))[-1])
          latex.DrawLatex(0.5, 0.78, "mean = " + str(round(w.var("mean_"+self.tag).getVal(),3)) + 
                                                     " #pm " + str(round(w.var("mean_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.71, "sigma = " + str(round(w.var("sigma_"+self.tag).getVal(),3)) + 
                                                      " #pm " + str(round(w.var("sigma_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.64, "a1 = " + str(round(w.var("a1_"+self.tag).getVal(),3)) + 
                                                   " #pm " + str(round(w.var("a1_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.57, "a2 = " + str(round(w.var("a2_"+self.tag).getVal(),3)) + 
                                                   " #pm " + str(round(w.var("a2_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.50, "n1 = " + str(round(w.var("n1_"+self.tag).getVal(),3)) + 
                                                   " #pm " + str(round(w.var("n1_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.43, "n2 = " + str(round(w.var("n2_"+self.tag).getVal(),3)) + 
                                                   " #pm " + str(round(w.var("n2_"+self.tag).getError(),3)))

          frame.Draw("same")
          c1.SaveAs(self.plotpath + "/fit_sig_" + self.savename + ".png")
          c1.SaveAs(self.plotpath + "/fit_sig_" + self.savename + ".pdf")

        if fixParameters:
           w.var("mean_"+self.tag).setConstant()
           w.var("sigma_"+self.tag).setConstant()
           w.var("a1_"+self.tag).setConstant()
           w.var("a2_"+self.tag).setConstant()
           w.var("n1_"+self.tag).setConstant()
           w.var("n2_"+self.tag).setConstant()

        w.writeToFile(self.modelpath + "/" + self.savename + ".root")

        return norm
    
    def makeSignalModel2D(self, workspaceName, config):
        rooVar_gg = "CMS_hgg_mass"
        rooVar_jj = "CMS_hjj_mass"

        replaceNorm = config["replaceNorm"]
        norm_in = config["norm_in"]
        fixParameters = config["fixParameters"]

        w = ROOT.RooWorkspace(workspaceName)
        w.factory(rooVar_gg + "[100,180]")
        w.factory(rooVar_jj + "[70,190]")
        w.factory("MH[125]")
        # w.factory("MV[90]")
        # w.factory("Mtt[110,130]")

        tag_mjj = self.tag.replace("hgg", "hjj")
        h_mgg = ROOT.TH1F("h_mgg", "h_mgg", 320, 100, 180)
        h_mgg.Sumw2()

        h_mjj = ROOT.TH1F("h_mjj", "h_mjj", 120, 60, 190)
        h_mjj.Sumw2()
        print (self.var[0], " ", self.var[1], " ", self.weightVar, " ", self.selection)
        #print("[makeModels.py] Info: h_mgg name: %s, var: %s, weightVar: %s, selection: %s" % (h_mgg.GetName(), self.var, self.weightVar, self.selection))
        self.tree.Project(h_mgg.GetName(), self.var[0], self.weightVar + "*(" + self.selection + ")")
        self.tree.Project(h_mjj.GetName(), self.var[1], self.weightVar + "*(" + self.selection + ")")
        d_mgg = ROOT.RooDataHist("roohist_data_mass_" + self.tag, "", ROOT.RooArgList(w.var(rooVar_gg)), h_mgg, 1)
        d_mjj = ROOT.RooDataHist("roohist_data_mass_" + tag_mjj, "", ROOT.RooArgList(w.var(rooVar_jj)), h_mjj, 1)
        #print "bin dataset", h_mgg.Integral(), d_mgg.sumEntries(), d_mgg.numEntries()
       
        # normalization
        norm_mgg = d_mgg.sumEntries()
        norm_mjj = d_mjj.sumEntries()

        print("mgg norm ", norm_mgg, " mjj norm ", norm_mjj)

        if replaceNorm:
            norm_mgg = norm_mjj = norm_in
        
        norm_mgg = max(norm_mgg, 1e-09)
        norm_mjj = max(norm_mjj, 1e-09)
        
        rv_norm_mgg = ROOT.RooRealVar(self.tag+"_mgg_norm", "", norm_mgg)
        rv_norm_mjj = ROOT.RooRealVar(self.tag+"_mjj_norm", "", norm_mjj)
        

        self.norm = norm_mgg
        # pdf
        if "ggHH" in self.tag: #ggHH signal fitted with a double crystal ball in mgg and mjj
          w.factory("DoubleCB:"+self.tag+"(" + rooVar_gg + ", mean_"+self.tag+"[125,120,130], sigma_"+self.tag+
                    "[1,0.5,5], a1_"+self.tag+"[1,0.1,10], n1_"+self.tag+"[1,0.1,10], a2_"+self.tag+
                    "[1,0.1,10], n2_"+self.tag+"[1,0.1,10])")
          w.factory("DoubleCB:"+tag_mjj+"(" + rooVar_jj + ", mean_"+tag_mjj+"[120,100,140], sigma_"+tag_mjj+
                    "[10,5,30], a1_"+tag_mjj+"[1,0.1,10], n1_"+tag_mjj+"[1,0.1,10], a2_"+tag_mjj+"[1,0.1,10], n2_"+
                    tag_mjj+"[1,0.1,10])")
        
        elif "VH" in self.tag: #VH signal fitted with a double crystal ball in mgg and mjj
          w.factory("DoubleCB:"+self.tag+"(" + rooVar_gg + ", mean_"+self.tag+"[125,120,130], sigma_"+self.tag+
                    "[1,0.5,5], a1_"+self.tag+"[1,0.1,10], n1_"+self.tag+"[1,0.1,10], a2_"+self.tag+
                    "[1,0.1,10], n2_"+self.tag+"[1,0.1,10])")
          w.factory("DoubleCB:"+tag_mjj+"(" + rooVar_jj + ", mean_"+tag_mjj+"[90,80,100], sigma_"+tag_mjj+
                    "[10,5,20], a1_"+tag_mjj+"[1,0.1,10], n1_"+tag_mjj+"[1,0.1,10], a2_"+tag_mjj+"[1,0.1,10], n2_"+
                    tag_mjj+"[1,0.1,10])")
        
        elif "ttH" in self.tag: #ttH signal fitted with a double crystal ball in mgg and large gaussian mjj
          w.factory("DoubleCB:"+self.tag+"(" + rooVar_gg + ", mean_"+self.tag+"[125,120,130], sigma_"+self.tag+
                    "[1,0.5,5], a1_"+self.tag+"[1,0.1,10], n1_"+self.tag+"[1,0.1,10], a2_"+self.tag+
                    "[1,0.1,10], n2_"+self.tag+"[1,0.1,10])")
          w.factory("Gaussian:"+tag_mjj+"(" + rooVar_jj + ", mean_gaus_"+tag_mjj+
                    "[120,100,140], width_gaus_"+tag_mjj+"[30,20,40])")
  
        elif "ggFH" in self.tag or "VBFH" in self.tag: #ggH and VBFH fitted with a double crystal ball in mgg and falling distribution in mjj
          w.factory("DoubleCB:"+self.tag+"(" + rooVar_gg + ", mean_"+self.tag+"[125,120,130], sigma_"+self.tag+
                    "[1,0.5,5], a1_"+self.tag+"[1,0.1,10], n1_"+self.tag+"[1,0.1,10], a2_"+self.tag+
                    "[1,0.1,10], n2_"+self.tag+"[1,0.1,10])")
          w.factory("Exponential:"+tag_mjj+"(" + rooVar_jj + ", tau[-0.027,-0.5,-0.001])")
       
        if w.pdf(self.tag):
            extPdf_mgg = ROOT.RooExtendPdf("extend" + self.tag, "", w.pdf(self.tag), rv_norm_mgg)
        else:
            raise RuntimeError("PDFs for mgg  not found in the workspace")
        if w.pdf(tag_mjj):
            extPdf_mjj = ROOT.RooExtendPdf("extend" + tag_mjj, "", w.pdf(tag_mjj), rv_norm_mjj)
        else:
            raise RuntimeError("PDFs for mjj not found in the workspace")

        # fit mgg and mjj independently
        w.pdf(self.tag).fitTo(d_mgg, ROOT.RooFit.SumW2Error(True) ,ROOT.RooFit.PrintLevel(-1))
        w.pdf(tag_mjj).fitTo(d_mjj, ROOT.RooFit.SumW2Error(True) ,ROOT.RooFit.PrintLevel(-1))

        # Combine using RooProdPdf
        w.factory(f"PROD:{self.tag}_2D({self.tag}, {tag_mjj})")
        rv_norm_2d = ROOT.RooRealVar(f"{self.tag}_2D_norm", "", norm_mgg)
        if w.pdf(self.tag+"_2D"):
           extPdf_2d = ROOT.RooExtendPdf("extend" + self.tag+"_2D", "", w.pdf(self.tag+"_2D"), rv_norm_2d)

        getattr(w,'import')(rv_norm_mjj)
        getattr(w,'import')(rv_norm_mgg)
        getattr(w,'import')(extPdf_mgg)
        getattr(w,'import')(extPdf_mjj)
        getattr(w,'import')(extPdf_2d)
        getattr(w,'import')(rv_norm_2d)


        # plots
        if self.plotpath:
          
          # mgg plots
          frame = w.var("CMS_hgg_mass").frame()
          d_mgg.plotOn(frame)
          w.pdf(self.tag).plotOn(frame)

          c1 = ROOT.TCanvas("c1", "c1", 800, 800)
          dummy = ROOT.TH1D("dummy","dummy",1,100,180)
          dummy.SetMinimum(0)
          dummy.SetMaximum(h_mgg.GetMaximum()*1.2)
          dummy.SetLineColor(0)
          dummy.SetMarkerColor(0)
          dummy.SetLineWidth(0)
          dummy.SetMarkerSize(0)
          dummy.GetYaxis().SetTitle("Events")
          dummy.GetYaxis().SetTitleOffset(1.3)
          dummy.GetXaxis().SetTitle("m_{#gamma#gamma} (GeV)")
          dummy.Draw()

          latex = ROOT.TLatex()
          latex.SetNDC()
          latex.SetTextSize(0.6*c1.GetTopMargin())
          latex.SetTextFont(42)
          latex.SetTextAlign(11)
          latex.SetTextColor(1)

          latex.DrawLatex(0.5, 0.85, (self.tag.split("_"))[-2] + "_" + (self.tag.split("_"))[-1])
          latex.DrawLatex(0.5, 0.78, "mean = " + str(round(w.var("mean_"+self.tag).getVal(),3)) + 
                                                     " #pm " + str(round(w.var("mean_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.71, "sigma = " + str(round(w.var("sigma_"+self.tag).getVal(),3)) + 
                                                      " #pm " + str(round(w.var("sigma_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.64, "a1 = " + str(round(w.var("a1_"+self.tag).getVal(),3)) + 
                                                   " #pm " + str(round(w.var("a1_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.57, "a2 = " + str(round(w.var("a2_"+self.tag).getVal(),3)) + 
                                                   " #pm " + str(round(w.var("a2_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.50, "n1 = " + str(round(w.var("n1_"+self.tag).getVal(),3)) + 
                                                   " #pm " + str(round(w.var("n1_"+self.tag).getError(),3)))
          latex.DrawLatex(0.5, 0.43, "n2 = " + str(round(w.var("n2_"+self.tag).getVal(),3)) + 
                                                   " #pm " + str(round(w.var("n2_"+self.tag).getError(),3)))

          frame.Draw("same")
          c1.SaveAs(self.plotpath + "/fit_sig_" + self.savename + ".png")
          c1.SaveAs(self.plotpath + "/fit_sig_" + self.savename + ".pdf")

          # mjj plots
          frame2 = w.var("CMS_hjj_mass").frame()
          d_mjj.plotOn(frame2)
          w.pdf(tag_mjj).plotOn(frame2)

          c2 = ROOT.TCanvas("c2", "c2", 800, 800)
          dummy = ROOT.TH1D("dummy","dummy",1,60,190)
          dummy.SetMinimum(0)
          dummy.SetMaximum(h_mgg.GetMaximum()*1.2)
          dummy.SetLineColor(0)
          dummy.SetMarkerColor(0)
          dummy.SetLineWidth(0)
          dummy.SetMarkerSize(0)
          dummy.GetYaxis().SetTitle("Events")
          dummy.GetYaxis().SetTitleOffset(1.3)
          dummy.GetXaxis().SetTitle("m_{jj} (GeV)")
          dummy.Draw()

          latex = ROOT.TLatex()
          latex.SetNDC()
          latex.SetTextSize(0.6*c2.GetTopMargin())
          latex.SetTextFont(42)
          latex.SetTextAlign(11)
          latex.SetTextColor(1)
          latex.DrawLatex(0.5, 0.85, (tag_mjj.split("_"))[-2] + "_" + (tag_mjj.split("_"))[-1])

          if "ggHH" in self.tag or "VH" in self.tag:
            latex.DrawLatex(0.5, 0.78, "mean = " + str(round(w.var("mean_"+tag_mjj).getVal(),3)) + 
                                                       " #pm " + str(round(w.var("mean_"+tag_mjj).getError(),3)))
            latex.DrawLatex(0.5, 0.71, "sigma = " + str(round(w.var("sigma_"+tag_mjj).getVal(),3)) + 
                                                       " #pm " + str(round(w.var("sigma_"+tag_mjj).getError(),3)))
            latex.DrawLatex(0.5, 0.64, "a1 = " + str(round(w.var("a1_"+tag_mjj).getVal(),3)) + 
                                                       " #pm " + str(round(w.var("a1_"+tag_mjj).getError(),3)))
            latex.DrawLatex(0.5, 0.57, "a2 = " + str(round(w.var("a2_"+tag_mjj).getVal(),3)) + 
                                                       " #pm " + str(round(w.var("a2_"+tag_mjj).getError(),3)))
            latex.DrawLatex(0.5, 0.50, "n1 = " + str(round(w.var("n1_"+tag_mjj).getVal(),3)) + 
                                                       " #pm " + str(round(w.var("n1_"+tag_mjj).getError(),3)))
            latex.DrawLatex(0.5, 0.43, "n2 = " + str(round(w.var("n2_"+tag_mjj).getVal(),3)) + 
                                                       " #pm " + str(round(w.var("n2_"+tag_mjj).getError(),3)))
          elif "ttH" in self.tag:
            latex.DrawLatex(0.5, 0.78, "mean = " + str(round(w.var("mean_gaus_"+tag_mjj).getVal(),3)) + 
                                                       " #pm " + str(round(w.var("mean_gaus_"+tag_mjj).getError(),3)))
            latex.DrawLatex(0.5, 0.71, "sigma = " + str(round(w.var("width_gaus_"+tag_mjj).getVal(),3)) + 
                                                        " #pm " + str(round(w.var("width_gaus_"+tag_mjj).getError(),3)))
          elif "ggFH" in self.tag or "VBFH" in self.tag:  
            latex.DrawLatex(0.5, 0.78, "tau = " + str(round(w.var("tau").getVal(),3)) + 
                                                      " #pm " + str(round(w.var("tau").getError(),3)))

          frame2.Draw("same")
          c2.SaveAs(self.plotpath + "/fit_sig_" + self.savename.replace("HGG","HBB").replace("hgg","hjj") + ".png")
          c2.SaveAs(self.plotpath + "/fit_sig_" + self.savename.replace("HGG","HBB").replace("hgg","hjj") + ".pdf")

        if fixParameters:
           w.var("mean_"+self.tag).setConstant()
           w.var("sigma_"+self.tag).setConstant()
           w.var("a1_"+self.tag).setConstant()
           w.var("a2_"+self.tag).setConstant()
           w.var("n1_"+self.tag).setConstant()
           w.var("n2_"+self.tag).setConstant()
           if "ggHH" in self.tag or "VH" in self.tag:
            w.var("mean_"+tag_mjj).setConstant()
            w.var("sigma_"+tag_mjj).setConstant()
            w.var("a1_"+tag_mjj).setConstant()
            w.var("a2_"+tag_mjj).setConstant()
            w.var("n1_"+tag_mjj).setConstant()
            w.var("n2_"+tag_mjj).setConstant()
           elif "ttH" in self.tag:
            w.var("mean_gaus_"+tag_mjj).setConstant()
            w.var("width_gaus_"+tag_mjj).setConstant()
           elif "ggFH" in self.tag or "VBFH" in self.tag:
            w.var("tau").setConstant

        w.writeToFile(self.modelpath + "/" + self.savename + ".root")

        return norm_mgg
    

    def makeBackgroundModel(self, workspaceName, datasetTag):

        rooVar = "CMS_hgg_mass"

        w = ROOT.RooWorkspace(workspaceName)
        w.factory(rooVar + "[100,180]")
        w.factory("MH[125]")

        h_mgg = ROOT.TH1F("h_mgg", "h_mgg", 320, 100, 180)
        h_mgg.Sumw2()

        print("[makeModels.py] Info: h_mgg name: %s, var: %s, weightVar: %s, selection: %s" % (h_mgg.GetName(), 
                                                                                               self.var, 
                                                                                               self.weightVar, 
                                                                                               self.selection))

        self.tree.Project(h_mgg.GetName(), self.var[0], self.weightVar + "*(" + self.selection + ")") 
        d_mgg = ROOT.RooDataHist("roohist_data_mass_" + datasetTag, "", ROOT.RooArgList(w.var(rooVar)), h_mgg, 1)
        print ("bin dataset", h_mgg.Integral(), d_mgg.sumEntries(), d_mgg.numEntries())

        # normalization
        norm = d_mgg.sumEntries()

        # set variable range
        w.var(rooVar).setRange("SL", 100, 120)
        w.var(rooVar).setRange("SU", 130, 180)
        w.var(rooVar).setRange("full", 100, 180)
        w.var(rooVar).setRange("blind",120,130)
        w.var(rooVar).setRange("mass_window",122,128)

        # pdf 
        w.factory("Exponential:"+self.tag+"(" + rooVar + ", tau[-0.027,-0.5,-0.001])")
        w.factory("ExtendPdf:"+self.tag+"_ext("+self.tag+", nevt[100,0,10000000], 'full')")

        # fit
        w.pdf(self.tag+"_ext").fitTo(d_mgg, ROOT.RooFit.Range("SL,SU"), ROOT.RooFit.Extended(True), 
                                     ROOT.RooFit.PrintLevel(-1))

        integral_full = w.pdf(self.tag+"_ext").createIntegral(ROOT.RooArgSet(w.var(rooVar)), 
                                                              ROOT.RooFit.Range("full"))
        integral_blind = w.pdf(self.tag+"_ext").createIntegral(ROOT.RooArgSet(w.var(rooVar)), 
                                                               ROOT.RooFit.Range("mass_window"))

        #print("[makeModels.py] Normalization from pdf in full range: %.6f" % integral_full.getVal())
        #print("[makeModels.py] Normalization from pdf in blind range: %.6f" % integral_blind.getVal())
        #print("[makeModels.py] Raw normalization in full range from sum entries: %.6f" % norm)

        frame = w.var(rooVar).frame()
        d_mgg.plotOn(frame, ROOT.RooFit.Binning(80), ROOT.RooFit.CutRange("SL,SU"))
        w.pdf(self.tag+"_ext").plotOn(frame)

        #plot
        if self.plotpath:
          c1 = ROOT.TCanvas("c1", "c1", 800, 800)
          dummy = ROOT.TH1D("dummy","dummy",1,100,180)
          dummy.SetMinimum(0)
          dummy.SetMaximum(h_mgg.GetMaximum()*1.2*4)
          dummy.SetLineColor(0)
          dummy.SetMarkerColor(0)
          dummy.SetLineWidth(0)
          dummy.SetMarkerSize(0)
          dummy.GetYaxis().SetTitle("Events")
          dummy.GetYaxis().SetTitleOffset(1.3)
          dummy.GetXaxis().SetTitle("m_{#gamma#gamma} (GeV)")
          dummy.Draw()

          frame.Draw("same")

          latex = ROOT.TLatex()
          latex.SetNDC()
          latex.SetTextSize(0.6*c1.GetTopMargin())
          latex.SetTextFont(42)
          latex.SetTextAlign(11)
          latex.SetTextColor(1)

          latex.DrawLatex(0.4, 0.85, (self.tag.split("_"))[-2] + "_" + (self.tag.split("_"))[-1])
          latex.DrawLatex(0.4, 0.78, "nEvents = " + str(round(w.var("nevt").getVal(),3)) + 
                                                  " #pm " + str(round(w.var("nevt").getError(),3)))
          latex.DrawLatex(0.4, 0.71, "#tau = " + str(round(w.var("tau").getVal(),3)) + 
                                                  " #pm " + str(round(w.var("tau").getError(),3)))

          c1.SaveAs(self.plotpath + "/fit_bkg_" + self.savename + ".png")
          c1.SaveAs(self.plotpath + "/fit_bkg_" + self.savename + ".pdf")

        nEvt = w.var("nevt").getVal()

        # scale total yield by fraction of pdf in 122-128 range to get yield under mass window
        nEvt_mass_window = nEvt * (integral_blind.getVal() / integral_full.getVal()) 
      
        w.factory(self.tag+"_norm["+str(nEvt)+",0,"+str(3*nEvt)+"]")

        getattr(w,'import')(d_mgg, ROOT.RooCmdArg())
        w.writeToFile(self.modelpath + "/" + self.savename + ".root")

        from subprocess import call
        call("echo " + str(nEvt) + " > " + self.modelpath + "/" + self.savename + "_nbkg.txt" , shell=True)

        print("[makeModels.py] Normalization from sum entries: %.6f" % norm)
        print("[makeModels.py] Normalization from fit: %.6f" % nEvt)
        print("[makeModels.py] Normalization from fit (mass-window only): %.6f" % nEvt_mass_window)
        print("[makeModels.py] Normalization from fit (naive scaling to mass-window): %.6f" % (nEvt * (6./80.)))

        return nEvt_mass_window, nEvt, norm # nEvt under higgs mass window, total number, raw number

    def makeBackgroundModel2D(self, workspaceName, datasetTag):

        rooVar_gg = "CMS_hgg_mass"
        rooVar_jj = "CMS_hjj_mass"

        w = ROOT.RooWorkspace(workspaceName)
        w.factory(rooVar_gg + "[100,180]")
        w.factory(rooVar_jj + "[60,190]")
        w.factory("MH[125]")

        tag_mjj = self.tag.replace("hgg", "hjj")
        h_mgg = ROOT.TH1F("h_mgg", "h_mgg", 320, 100, 180)
        h_mgg.Sumw2()

        h_mjj = ROOT.TH1F("h_mjj", "h_mjj", 120, 60, 190)
        h_mjj.Sumw2()
        print("[makeModels.py] Info: h_mgg name: %s, var: %s, weightVar: %s, selection: %s" % (h_mgg.GetName(), 
                                                                              self.var, self.weightVar, self.selection))
        print("[makeModels.py] Info: h_mjj name: %s, var: %s, weightVar: %s, selection: %s" % (h_mjj.GetName(), 
                                                                              self.var, self.weightVar, self.selection))

        #print("[makeModels.py] Info: h_mgg name: %s, var: %s, weightVar: %s, selection: %s" % (h_mgg.GetName(), self.var, self.weightVar, self.selection))
        self.tree.Project(h_mgg.GetName(), self.var[0], self.weightVar + "*(" + self.selection + ")")
        self.tree.Project(h_mjj.GetName(), self.var[1], self.weightVar + "*(" + self.selection + ")")
        
        d_mgg = ROOT.RooDataHist("roohist_data_mass_" + datasetTag, "", ROOT.RooArgList(w.var(rooVar_gg)), h_mgg, 1)
        d_mjj = ROOT.RooDataHist("roohist_data_mass_jj_" + datasetTag, "", ROOT.RooArgList(w.var(rooVar_jj)), h_mjj, 1)
        d_mggmjj = ROOT.RooDataSet("roodataset_data_masses_"+ datasetTag, "",
         ROOT.RooArgSet(w.var(rooVar_gg),w.var(rooVar_jj)), "", self.weightVar + "*(" + self.selection + ")")
        
        print ("bin dataset mgg", h_mgg.Integral(), d_mgg.sumEntries(), d_mgg.numEntries())
        print ("bin dataset mjj", h_mjj.Integral(), d_mjj.sumEntries(), d_mjj.numEntries())

        # normalization
        norm_mgg = d_mgg.sumEntries()
        norm_mjj = d_mjj.sumEntries()

        # set mgg variable range
        w.var(rooVar_gg).setRange("SL", 100, 120)
        w.var(rooVar_gg).setRange("SU", 130, 180)
        w.var(rooVar_gg).setRange("full", 100, 180)
        w.var(rooVar_gg).setRange("blind",120,130)
        w.var(rooVar_gg).setRange("mass_window",122,128)

        # set mjj variable range
        w.var(rooVar_jj).setRange("SL_jj", 60, 90)
        w.var(rooVar_jj).setRange("SU_jj", 150, 190)
        w.var(rooVar_jj).setRange("full_jj", 60, 190)
        w.var(rooVar_jj).setRange("blind_jj",90,150)
        w.var(rooVar_jj).setRange("mass_window_jj",100,140)

        # pdf 
        w.factory("Exponential:"+self.tag+"(" + rooVar_gg + ", tau[-0.027,-0.5,-0.001])")
        w.factory("ExtendPdf:"+self.tag+"_ext("+self.tag+", nevt[100,0,10000000], 'full')")
        w.factory("Exponential:"+tag_mjj+"(" + rooVar_jj + ", tau_jj[-0.027,-0.5,-0.001])")
        w.factory("ExtendPdf:"+tag_mjj+"_ext("+tag_mjj+", nevt_jj[100,0,10000000], 'full')")

        # fit
        w.pdf(self.tag+"_ext").fitTo(d_mgg, ROOT.RooFit.Range("SL,SU"), ROOT.RooFit.Extended(True), 
                                     ROOT.RooFit.PrintLevel(-1))
        w.pdf(tag_mjj+"_ext").fitTo(d_mjj, ROOT.RooFit.Range("SL_jj,SU_jj"), ROOT.RooFit.Extended(True), 
                                    ROOT.RooFit.PrintLevel(-1))

        integral_mgg_full = w.pdf(self.tag+"_ext").createIntegral(ROOT.RooArgSet(w.var(rooVar_gg)), 
                                                                  ROOT.RooFit.Range("full"))
        integral_mgg_blind = w.pdf(self.tag+"_ext").createIntegral(ROOT.RooArgSet(w.var(rooVar_gg)), 
                                                                   ROOT.RooFit.Range("mass_window"))

        integral_mjj_full = w.pdf(tag_mjj+"_ext").createIntegral(ROOT.RooArgSet(w.var(rooVar_jj)), 
                                                                 ROOT.RooFit.Range("full_jj"))
        integral_mjj_blind = w.pdf(tag_mjj+"_ext").createIntegral(ROOT.RooArgSet(w.var(rooVar_jj)), 
                                                                  ROOT.RooFit.Range("mass_window_jj"))

        #print("[makeModels.py] Normalization from pdf in full range: %.6f" % integral_full.getVal())
        #print("[makeModels.py] Normalization from pdf in blind range: %.6f" % integral_blind.getVal())
        #print("[makeModels.py] Raw normalization in full range from sum entries: %.6f" % norm)

        nEvt = w.var("nevt").getVal()
        nEvt_jj = w.var("nevt_jj").getVal()

        # scale total yield by fraction of pdf in 122-128 (100-140) range to get yield under mass window
        nEvt_mass_window = nEvt * (integral_mgg_blind.getVal() / integral_mgg_full.getVal()) 
        nEvt_mass_window_jj = nEvt_jj * (integral_mjj_blind.getVal() / integral_mjj_full.getVal()) 
      
        w.factory(self.tag+"_norm["+str(nEvt)+",0,"+str(3*nEvt)+"]")
        w.factory(tag_mjj+"_norm["+str(nEvt_jj)+",0,"+str(3*nEvt_jj)+"]")

        # Combine using RooProdPdf
        w.factory(f"PROD:{self.tag}_2D({self.tag}, {tag_mjj})")
        rv_norm_2d = ROOT.RooRealVar(f"{self.tag}_2D_norm", "", norm_mgg)
      
        if w.pdf(self.tag+"_2D"):
           extPdf_2d = ROOT.RooExtendPdf("extend" + self.tag+"_2D", "", w.pdf(self.tag+"_2D"), rv_norm_2d)

        getattr(w,'import')(extPdf_2d)
        getattr(w,'import')(d_mgg, ROOT.RooCmdArg())
        getattr(w,'import')(d_mjj, ROOT.RooCmdArg())
        getattr(w,'import')(d_mggmjj, ROOT.RooCmdArg())

        #plot
        if self.plotpath:
          # mgg plots
          frame = w.var(rooVar_gg).frame()
          d_mgg.plotOn(frame, ROOT.RooFit.Binning(80), ROOT.RooFit.CutRange("SL,SU"))
          w.pdf(self.tag+"_ext").plotOn(frame)

          c1 = ROOT.TCanvas("c1", "c1", 800, 800)
          dummy = ROOT.TH1D("dummy","dummy",1,100,180)
          dummy.SetMinimum(0)
          dummy.SetMaximum(h_mgg.GetMaximum()*1.2*4)
          dummy.SetLineColor(0)
          dummy.SetMarkerColor(0)
          dummy.SetLineWidth(0)
          dummy.SetMarkerSize(0)
          dummy.GetYaxis().SetTitle("Events")
          dummy.GetYaxis().SetTitleOffset(1.3)
          dummy.GetXaxis().SetTitle("m_{#gamma#gamma} (GeV)")
          dummy.Draw()

          frame.Draw("same")

          latex = ROOT.TLatex()
          latex.SetNDC()
          latex.SetTextSize(0.6*c1.GetTopMargin())
          latex.SetTextFont(42)
          latex.SetTextAlign(11)
          latex.SetTextColor(1)

          latex.DrawLatex(0.4, 0.85, (self.tag.split("_"))[-2] + "_" + (self.tag.split("_"))[-1])
          latex.DrawLatex(0.4, 0.78, "nEvents = " + str(round(w.var("nevt").getVal(),3)) + 
                                                              " #pm " + str(round(w.var("nevt").getError(),3)))
          latex.DrawLatex(0.4, 0.71, "#tau = " + str(round(w.var("tau").getVal(),3)) + 
                                                           " #pm " + str(round(w.var("tau").getError(),3)))

          c1.SaveAs(self.plotpath + "/fit_bkg_" + self.savename + ".png")
          c1.SaveAs(self.plotpath + "/fit_bkg_" + self.savename + ".pdf")

          # mjj plots
          frame2 = w.var(rooVar_jj).frame()
          d_mjj.plotOn(frame2,ROOT.RooFit.Binning(75), ROOT.RooFit.CutRange("SL_jj,SU_jj"))
          w.pdf(tag_mjj+"_ext").plotOn(frame2)

          c2 = ROOT.TCanvas("c2", "c2", 800, 800)
          dummy = ROOT.TH1D("dummy","dummy",1,60,190)
          dummy.SetMinimum(0)
          dummy.SetMaximum(h_mjj.GetMaximum()*1.2)
          dummy.SetLineColor(0)
          dummy.SetMarkerColor(0)
          dummy.SetLineWidth(0)
          dummy.SetMarkerSize(0)
          dummy.GetYaxis().SetTitle("Events")
          dummy.GetYaxis().SetTitleOffset(1.3)
          dummy.GetXaxis().SetTitle("m_{jj} (GeV)")
          dummy.Draw()

          frame2.Draw("same")

          latex = ROOT.TLatex()
          latex.SetNDC()
          latex.SetTextSize(0.6*c2.GetTopMargin())
          latex.SetTextFont(42)
          latex.SetTextAlign(11)
          latex.SetTextColor(1)
          latex.DrawLatex(0.4, 0.85, (tag_mjj.split("_"))[-2] + "_" + (tag_mjj.split("_"))[-1])
          latex.DrawLatex(0.4, 0.78, "nEvents = " + str(round(w.var("nevt_jj").getVal(),3)) + 
                                                              " #pm " + str(round(w.var("nevt_jj").getError(),3)))
          latex.DrawLatex(0.4, 0.71, "#tau = " + str(round(w.var("tau_jj").getVal(),3)) + 
                                                           " #pm " + str(round(w.var("tau_jj").getError(),3)))

          c2.SaveAs(self.plotpath + "/fit_sig_" + self.savename.replace("HGG","HBB").replace("hgg","hjj") + ".png")
          c2.SaveAs(self.plotpath + "/fit_sig_" + self.savename.replace("HGG","HBB").replace("hgg","hjj") + ".pdf")
          

        w.writeToFile(self.modelpath + "/" + self.savename + ".root")

        from subprocess import call
        call("echo " + str(nEvt) + " > " + self.modelpath + "/" + self.savename + "_nbkg.txt" , shell=True)
        call("echo " + str(nEvt_jj) + " > " + self.modelpath + "/" + self.savename + "_nbkg_jj.txt" , shell=True)

        print("[makeModels.py] Normalization in mgg from sum entries: %.6f" % norm_mgg)
        print("[makeModels.py] Normalization in mgg from fit: %.6f" % nEvt)
        print("[makeModels.py] Normalization in mgg from fit (mass-window only): %.6f" % nEvt_mass_window)
        print("[makeModels.py] Normalization in mgg from fit (naive scaling to mass-window): %.6f" % (nEvt*(6./80.)))

        print("[makeModels.py] Normalization in mgg from sum entries: %.6f" % norm_mjj)
        print("[makeModels.py] Normalization in mgg from fit: %.6f" % nEvt_jj)
        print("[makeModels.py] Normalization in mgg from fit (mass-window only): %.6f" % nEvt_mass_window_jj)
        print("[makeModels.py] Normalization in mgg from fit (naive scaling to mass-window): %.6f" % (nEvt_jj*(4./13.)))

        return nEvt_mass_window, nEvt, norm_mgg # nEvt under higgs mass window, total number, raw number
