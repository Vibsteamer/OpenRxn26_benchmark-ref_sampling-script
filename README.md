# OpenRxn26 benchmark data and sampling scripts

This repository provides benchmark reference data in manuscript [arXiv awaiting] and the sampling scripts used to produce the OpenRxn26 dataset.

The OpenRxn26 dataset is available through AIS Square: [https://www.aissquare.com/datasets/detail?pageType=datasets&name=OpenRxn26&id=425](https://www.aissquare.com/datasets/detail?pageType=datasets&name=OpenRxn26&id=425).
The DPA3_rxn model is available through AIS Square: public after manuscript on arXiv.

## benchmark_reference

Introduction please see [benchmark_reference/README.md](benchmark_reference/README.md).

Geometries are selected from

- [OMol25](https://doi.org/10.48550/arXiv.2505.08762). Levine *et al.*, *The Open Molecules 2025 (OMol25) Dataset, Evaluations, and Models*, arXiv:2505.08762 (2025).
- [Transition1x](https://doi.org/10.1038/s41597-022-01870-w). Schreiner *et al.*, *Scientific Data* **9**, 779 (2022).
- [RGD1](https://doi.org/10.1038/s41597-023-02043-z). Zhao *et al.*, *Scientific Data* **10**, 145 (2023).
- [BH9](https://doi.org/10.1021/acs.jctc.1c00694). Prasad *et al.*, *Journal of Chemical Theory and Computation* **18**, 151–166 (2022).
- [Textbook181](https://doi.org/10.31635/ccschem.026.202607339). Li *et al.*, *A Data-Efficient Reactive Machine Learning Potential to Accelerate Automated Exploration of Complex Reaction Networks*, *CCS Chemistry*.
- [cyclo[3+2]](https://doi.org/10.1038/s41597-023-01977-8). Stuyver, Jorner, and Coley, *Scientific Data* **10**, 66 (2023).

## sampling_scripts

Introduction please see [sampling_scripts/README.md](sampling_scripts/README.md).

The exploration workflow is orchestrated by [DPGEN2](https://github.com/deepmodeling/dpgen2), invoking [DeepMD-kit](https://github.com/deepmodeling/deepmd-kit), [LAMMPS](https://doi.org/10.1016/j.cpc.2021.108171), [PLUMED](https://doi.org/10.1016/j.cpc.2013.09.018), [ASE](https://wiki.fysik.dtu.dk/ase/) and [MDAnalysis](https://www.mdanalysis.org/). 
