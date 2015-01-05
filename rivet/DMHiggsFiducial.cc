// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/IdentifiedFinalState.hh"
#include "Rivet/Projections/MissingMomentum.hh"

namespace Rivet {

  bool inCrackRegion(double eta){
    return (1.37 < abs(eta) && abs(eta) < 1.56);
  }


  class DMHiggsFiducial : public Analysis {
  public:

    /// Constructor
    DMHiggsFiducial()
      : Analysis("DMHiggsFiducial")
    {    }


  public:

    /// @name Analysis methods
    //@{

    /// Book histograms and initialise projections before the run
    void init() {

      FinalState all;
      addProjection(all,"all");

      IdentifiedFinalState photons(all);
      photons.acceptIdPair(PID::PHOTON);
      addProjection(photons,"photons");


      MissingMomentum met;
      addProjection(met,"met");

      //histos  
      _h_MET  = bookHisto1D("MET",40,0,1000);
      _h_PhotonPt  = bookHisto1D("PhotonPt",40,0,1000);
      _h_PhotonEta  = bookHisto1D("PhotonEta",40,-3,3);

      int ncuts = 10;
      _h_Cutflow  = bookHisto1D("Cutflow",ncuts,-0.5,-0.5+ncuts);

    }


    /// Perform the per-event analysis
    void analyze(const Event& event) {
      const double weight = event.weight();

      int cutflowstep = 0;

      Particles photons = applyProjection<IdentifiedFinalState>(event,"photons").particlesByPt();
      MSG_DEBUG("Photon multiplicity         = " << photons.size());

      MissingMomentum metproj = applyProjection<MissingMomentum>(event,"met");
      double met = (-metproj.vectorEt()).mod();
      MSG_DEBUG("MET is: " << met/GeV << " GeV");
      _h_MET->fill(met/GeV,weight);

      _h_Cutflow->fill(cutflowstep++,weight);
      

      //invariant mass
      if(!(photons.size()==2)){
        MSG_WARNING("not a diphoton event, skip!");
        return;
      }
      _h_Cutflow->fill(cutflowstep++,weight);

      if(inCrackRegion(photons[0].momentum().eta()) || inCrackRegion(photons[1].momentum().eta())) return;
      _h_Cutflow->fill(cutflowstep++,weight);

      const double max_eta = 2.37;
      if(abs(photons[0].momentum().eta()) > max_eta || abs(photons[1].momentum().eta()) > max_eta) return;
      _h_Cutflow->fill(cutflowstep++,weight);
      

      foreach (const Particle& p, photons) _h_PhotonEta->fill(p.momentum().eta(),weight);

      
      FourMomentum diphotonMomentum = photons[0].momentum()+photons[1].momentum();
      double diphotonmass = diphotonMomentum.mass();

      MSG_DEBUG("diphoton mass: " << diphotonmass);

      if(diphotonmass < 105 || diphotonmass > 160) return;
      _h_Cutflow->fill(cutflowstep++,weight);

      double pt1 = photons[0].momentum().pt();
      double pt2 = photons[1].momentum().pt();

      if(pt1/GeV < 25 || pt2 < 25) return;
      _h_Cutflow->fill(cutflowstep++,weight);
      
      foreach (const Particle& p, photons) _h_PhotonPt->fill(p.momentum().pt()/GeV,weight);

      if(pt1/diphotonmass <= 0.35) return;
      _h_Cutflow->fill(cutflowstep++,weight);

      if(pt2/diphotonmass <= 0.25) return;
      _h_Cutflow->fill(cutflowstep++,weight);
      
      if(diphotonMomentum.pt() < 90*GeV) return;
      _h_Cutflow->fill(cutflowstep++,weight);

      if(met/GeV < 90) return;
      _h_Cutflow->fill(cutflowstep++,weight);
      
      MSG_DEBUG("good candidate event.");
    }


    /// Normalise histograms etc., after the run
    void finalize() {
    }

    //@}


  private:

    // Data members like post-cuts event weight counters go here


  private:

    /// @name Histograms
    //@{
    Histo1DPtr _h_MET;
    Histo1DPtr _h_PhotonPt;
    Histo1DPtr _h_PhotonEta;
    Histo1DPtr _h_Cutflow;
    //@}


  };



  // The hook for the plugin system
  DECLARE_RIVET_PLUGIN(DMHiggsFiducial);

}
