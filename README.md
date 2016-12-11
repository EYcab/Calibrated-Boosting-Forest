# LightChem

LightChem provides high level machine-learning interface that served to used by researcher without deep machine-learning background. It aims to offer convenient exploration for researcher interested in machine-learning for drug discovery. LightChem is a package created by Haozhen Wu from [Small Molecule Screening Facility](http://www.uwhealth.org/uw-carbone-cancer-center/for-researchers/shared-resources/smsf/small-molecule-screening/27197)  
at University of Wisconsin-Madison.  

## Key features:  

* [XGBoost](https://github.com/dmlc/xgboost) backend
* Parallel computing    
* Supports tree based models and regression models  
* Interface to use ensemble(stacking) models  
* Support multiple evaluation metrics  
* Common featurization methods to transform molecules into fingerprint  
* Competitive benchmark results for well-known public datasets  

## Installation

We recommend you to use Anaconda for convenient installing packages. Right now, LightChem has been tested for Python 2.7 under OS X and linux Ubuntu Server 16.04.   

1. Download 64-bit Python 2.7 version of Anaconda for linux/OS X [here](https://www.continuum.io/downloads) and follow the instruction. After you installed Anaconda, you will have most of the dependencies ready.  

2. Install [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) if do not have:  
   Linux:    
   ```bash
   sudo yum install git-all
   ```

3. Install [rdkit](http://www.rdkit.org/docs/Install.html)  Note: `rdkit` is only used to transform SMILE string into fingerprint.  
   ```bash
   conda install -c omnia rdkit
   ```
   
3. Clone the `lightchem` github repository:  
   ```bash
   git clone https://github.com/haozhenWu/lightchem.git
   ```
