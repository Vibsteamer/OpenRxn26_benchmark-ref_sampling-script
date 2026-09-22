# Benchmark Reference Data

This directory contains geometries, DFT energies and forces, and metadata used
in the benchmark.

## Reference Data format

All data use the `deepmd/npy/mixed` format (can be loaded and converted with `dpdata`). 

For N frames and M atoms:

### common files


| file                  | contents                                                               | shape or example   |
| --------------------- | ---------------------------------------------------------------------- | ------------------ |
| `type.raw`            | mixed-type placeholder; all entries are `0`                            | text, `M` integers |
| `type_map.raw`        | ordered element map                                                    | `H C N O F P S Cl` |
| `nopbc`               | nonperiodic marker                                                     | empty file         |
| `box.npy`             | cell vectors in Å                                                      | `(N, 9)`           |
| `coord.npy`           | cartesian coordinates in Å                                             | `(N, 3M)`          |
| `energy.npy`          | total energy in eV                                                     | `(N,)` or `(N, 1)` |
| `force.npy`           | cartesian forces in eV/Å                                               | `(N, 3M)`          |
| `real_atom_types.npy` | frame-level indices into `type_map.raw` to recover element of the atom | `(N, M)`           |
| `fparam.npy`          | frame-level parameter, here for [charge, multiplicity]                 | `(N, 2)`           |


## `tSNE-ID-OOD_test`

`tSNE-ID-OOD_test/` contains OpenRxn26 and OMol25 reference subsets and
cross-labeled data.

### file structure

```text
tSNE-ID-OOD_test/
├── OpenRxn26_tSNE_random100K/
│   └── <number_of_atoms>/
│       ├── type.raw
│       ├── type_map.raw
│       ├── nopbc
│       └── set.000/
│           ├── box.npy
│           ├── coord.npy
│           ├── energy.npy
│           ├── force.npy
│           ├── fparam.npy
│           ├── real_atom_types.npy
│           └── center_atom_idx.npy
├── OMol25_tSNE_random100K/
├── OpenRxn26_tSNE-20x_random300/
├── OpenRxn26_tSNE-20x_random300_relabel-OMol25/
├── OMol25_tSNE-20x-NheavyLe30_random300/
├── OMol25_tSNE-20x-NheavyLe30_random300_relabel-OpenRxn26/
├── OMol25_tSNE-20x-NheavyGt30_random300/
└── OMol25_tSNE-20x-NheavyGt30_random300_relabel-OpenRxn26/
```

`OpenRxn26_tSNE_random100K`: 100,000 random frames from OpenRxn26 used as the
OpenRxn26 ID subset.
`OpenRxn26_tSNE-20x_random300`: 300 random frames from OpenRxn26-dominated
t-SNE regions, ID for OpenRxn26 and OOD for OMol25.
`OpenRxn26_tSNE-20x_random300_relabel-OMol25`: the same structure as `OpenRxn26_tSNE-20x_random300` but energy and force are recalculated using OMol25 DFT methods.
Structures in the three directories above have heavy atoms (atoms excluding hydrogen atoms) <= 30.

Other directories initialized with `OMol25_` are from OMol25 with similar selection or relabeling operations, where heavyLe30 denotes structures within having heavy atoms <= 30 and heavyGt30 is for > 30.

### custom metainfo file


| file                  | contents                                                  | shape or example |
| --------------------- | --------------------------------------------------------- | ---------------- |
| `center_atom_idx.npy` | zero-based index of the t-SNE analyzed atom in each frame | `(N, 1)`         |


## static_evaluation

`static_evaluation/` contains reactant, transition-state (`TS`), and product data for barrier and reaction-energy evaluation

### directory structure

```text
static_evaluation/
├── general_testsets/
│   └── label_OpenRxn26/
│       ├── Transition1x_1900/
│       │   ├── ID/
│       │   │   ├── reactant/
│       │   │   │   └── rxnkilo_000000/
│       │   │   │       └── <number_of_atoms>/
│       │   │   │           ├── type.raw
│       │   │   │           ├── type_map.raw
│       │   │   │           ├── nopbc
│       │   │   │           └── set.000000/
│       │   │   │               ├── box.npy
│       │   │   │               ├── coord.npy
│       │   │   │               ├── energy.npy
│       │   │   │               ├── force.npy
│       │   │   │               ├── fparam.npy
│       │   │   │               ├── real_atom_types.npy
│       │   │   │               └── rxn.npy
│       │   │   ├── ts/
│       │   │   └── product/
│       │   └── OOD_SMILES/
│       └── RGD1_1800/
│           ├── Nheavy3-7/
│           └── Nheavy8-10/
└── domain-specific_testsets/
    ├── label_OpenRxn26/
    │   ├── BH9_42/
    │   ├── Textbook181_100/
    │   └── cyclo3_2_350/
    ├── label_MDCD20/
    ├── label_OMol25/
    ├── label_transition1x/
    ├── label_ANI-1xBB/
    └── label_AIMNet2-rxn/
```

Geometries are selected from `Transition1x`, `RGD1`, `BH9`, `Textbook181`, and `cyclo[3+2]` datasets.
Single-point labels of `general_testsets` are re-calculated using the DFT labeling methods adopted by `OpenRxn26`.
Single-point labels of `domain-specific_testsets` are re-calculated using DFT labeling methods respectively adopted by `OpenRxn26`, `MDCD20`, `OMol25`, `AIMNet2-rxn`, `transition1x` and `ANI-1xBB`.

### custom metainfo file


| file      | contents                                                                                           | shape or example   |
| --------- | -------------------------------------------------------------------------------------------------- | ------------------ |
| `rxn.npy` | per-frame reaction identifier used to align `reactant`, `ts`, and `product` from the same reaction | `(N,)` or `(N, 1)` |


Except for `cyclo3_2_350`, reactant, TS, and product frames from the same reaction use the same identifier recorded in rxn.npy, such as `MR_149431_0` or `02_140`.
`cyclo3_2_350` uses the following matching rule in `rxn.npy`:

```text
two reactants:   <this_id>_0 and <this_id>_1
TS:              <this_id>
product:         <this_id>_0
```

## reactive_traj

`reactive_traj/` contains the reference data of `RXNPath_39` and two variants `RXNPath_39_sampled_by_MDCD-NN` and `RXNPath_39_sampled_by_MACE_OMol25`.
`RXNPath_39/` serves as the main benchmark data set in the manuscript, containing geometries sampled on the PES of `DPA3_rxn`. 
The other two supplementary variants are respectively sampled on the PES of `MDCD-NN` and the PES of `MACE_OMol25`.

Within each dataset, energies and forces of the same geometries are calculated using 6 DFT methods, respectively in line with `OpenRxn26`, `MDCD20`, `OMol25`, `transition1x`, `ANI-1xBB`, and `AIMNet2-rxn`.

### directory structure

```text
reactive_traj/
├── RXNPath_39/
│   ├── label_OpenRxn26/
│   │   └── <number_of_atoms>/
│   │       ├── type.raw
│   │       ├── type_map.raw
│   │       ├── nopbc
│   │       └── set.000/
│   │           ├── box.npy
│   │           ├── coord.npy
│   │           ├── energy.npy
│   │           ├── force.npy
│   │           ├── fparam.npy
│   │           ├── real_atom_types.npy
│   │           └── metainfo.npy
│   ├── label_MDCD20/
│   ├── label_OMol25/
│   ├── label_transition1x/
│   ├── label_ANI-1xBB/
│   └── label_AIMNet2-rxn/
├── RXNPath_39_sampled_by_MDCD-NN/
└── RXNPath_39_sampled_by_MACE_OMol25/
```

All three dataset directories use the same label structure.

### custom metainfo file


| file           | contents                                                                                                                                                                                                                                                                                                                                                                                                              | shape and example                                           |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `metainfo.npy` | provenance and position of each frame: `reaction_id`, `traj_idx` (0-2), `point_idx`: idx among the selected frames from the same traj (0-10), `target_progress_idx`: idx of the nearest equal-interval grid along the projected arc (0-10), `frame_progress`: progress value of the frame along the projected arc, `target_progress_value`: progress value of the nearest equal-interval grid along the projected arc | `(N,)`, `[('19__rxn060', 0, 4, 4, 2.44548423, 2.43919245)]` |


The projected arc is the trajectory projected into the space of bond-changing interatomic distances; the cumulative arc length along this arc defines the progress values.

`traj_idx` is local to one sampler directory. When matching the same frame
across DFT labels, use
`(reaction_id, traj_idx, target_progress_idx, point_idx)` from
`metainfo.npy`; row order can differ between label directories. Because these
are nonperiodic data marked by `nopbc`, `box.npy` is a nonphysical placeholder
and may differ between DFT-labeling pipelines.

## label_scripts_example

example input files for DFT single-point calculations used in relabeling

```text
label_scripts_example/
├── OpenRxn26_Gaussian.gjf
├── MDCD20_ORCA.inp
├── OMol25_ORCA.inp
├── transition1x_ORCA.inp
├── ANI-1xBB_ORCA.inp
└── AIMNet2-rxn_ORCA.inp
```

