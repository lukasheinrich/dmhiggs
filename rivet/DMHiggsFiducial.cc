// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/IdentifiedFinalState.hh"
#include "Rivet/Projections/MissingMomentum.hh"

namespace Rivet {


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
      _h_Cutflow  = bookHisto1D("Cutflow",6,-0.5,5.5);

    }


    /// Perform the per-event analysis
    void analyze(const Event& event) {
      const double weight = event.weight();

      auto photons = applyProjection<IdentifiedFinalState>(event,"photons");
      MSG_INFO("Photon multiplicity         = " << photons.particles().size());

      foreach (const Particle& p, photons.particles()) {
        MSG_INFO("photon pid = " << p.pid());
        _h_PhotonPt->fill(p.momentum().pt(),weight);
      }

      auto met = applyProjection<MissingMomentum>(event,"met");
      double metInGeV = (-met.vectorEt()).mod()/GeV;
      MSG_INFO("MET is: " << metInGeV);
      _h_MET->fill(metInGeV,weight);

      _h_Cutflow->fill(0,weight);
      

      //invariant mass
      if(!photons.particles().size()==2){
        MSG_WARNING("not a diphoton event, skip!");
        return;
      }

      _h_Cutflow->fill(1,weight);
      
      auto diphotonMomentum = photons.particles()[0].momentum()+photons.particles()[1].momentum();
      auto diphotonmass = diphotonMomentum.mass();

      MSG_INFO("diphoton mass: " << diphotonmass);

      if(diphotonmass < 105 || diphotonmass > 160) return;
      _h_Cutflow->fill(2,weight);

      auto pt1 = photons.particles()[0].momentum().pt();
      auto pt2 = photons.particles()[1].momentum().pt();

      if(pt1/diphotonmass <= 0.35) return;
      _h_Cutflow->fill(3,weight);

      if(pt1/diphotonmass <= 0.25) return;
      _h_Cutflow->fill(4,weight);

      if(diphotonMomentum.pt()/GeV < 90) return;
      _h_Cutflow->fill(5,weight);

      if(metInGeV < 90) return;
      _h_Cutflow->fill(6,weight);
      
      MSG_INFO("good candidate event.");
    }


    /// Normalise histograms etc., after the run
    void finalize() {

      /// @todo Normalise, scale and otherwise manipulate histograms here

      // scale(_h_YYYY, crossSection()/sumOfWeights()); // norm to cross section
      // normalize(_h_YYYY); // normalize to unity

    }

    //@}


  private:

    // Data members like post-cuts event weight counters go here


  private:

    /// @name Histograms
    //@{
    Histo1DPtr _h_MET;
    Histo1DPtr _h_PhotonPt;
    Histo1DPtr _h_Cutflow;
    //@}


  };



  // The hook for the plugin system
  DECLARE_RIVET_PLUGIN(DMHiggsFiducial);

}
