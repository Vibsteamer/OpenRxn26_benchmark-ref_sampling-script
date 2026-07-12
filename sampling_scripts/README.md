# Scripts for the sampling strategy

## overview

The data-generation workflow is organized by the concurrent-learning platform DPGEN2; during `exploration`, DP-GEN2 invokes LAMMPS and PLUMED to implement the sampling.  
The DPGEN2 control file `dpgen2_example.json` specifies the custom LAMMPS and PLUMED input templates and exposes key sampling parameters through its `revisions` block. Advanced full-parameter controls are configured inside `lammps_Rxn_template.in`.

Custom Python functions in `lammps_Rxn_template.in` (by in-line Python interface of LAMMPS) implement the metadynamics + TS-optimization strategy. 
The metadynamics simulation runs in a loop of several restart segments; each segment deposits one bias hill; PLUMED intermediate files are modified between segments according to the CV design.
The downstream TS optimization uses the dimer method in ASE, involving selection of near-reactive geometry seeds from metadynamics, and post-downsampling of outcome dimer trajectories.

## Files


| file                                          | role                                                                                                                                                                         |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dpgen2_example.json`                         | DP-GEN2 configuration; in exploration, invoking LAMMPS and PLUMED, substituting `V_*` variables in template files                                                            |
| `train_iters_dpa3.json`                       | training template of DPA-3 fine-tuning model ensemble, referenced by the DP-GEN2 configuration                                                                                |
| `lammps_Rxn_template.in`                      | LAMMPS input template; referenced by the DP-GEN2 configuration; containing custom Python functions to implement the sampling strategy                                        |
| `input.plumed`                                | PLUMED input template; referenced by the DP-GEN2 configuration; attached to LAMMPS through `fix plumed` and modified by functions in `lammps_Rxn_template.in` during the run |
| `deepmd_server_client/deepmd_multi_server.py` | launches independent local DeepMD servers for batch ASE dimer calculations                                                                                                   |
| `deepmd_server_client/deepmd_client.py`       | provides the ASE calculator client for batch ASE dimer calculations                                                                                                          |


## Key parameters exposed in `dpgen2_example.json`


| parameter key                     | explanation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | example                       |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| `V_LOCAL_RCUT`                    | cutoff (Å) for local partition of molecules, controlling the size of local domains thus spatial-resolution of CV                                                                                                                                                                                                                                                                                                                                                                                                              | `[2.1, 4.5, 10.0]`            |
| `V_Nrepeats`                      | number of snapshots (steps) to be averaged per reference geometry, enabling the temporal filtering of high-frequency fluctuations; string initialized with 'random' and entries separated by comma selects one random entry per task;                                                                                                                                                                                                                                                                                         | `["random:500,500,300,100"]`  |
| `V_HILL_HEIGHT`                   | height (eV) of each Gaussian hill as bias; `random:` string selects one entry per task                                                                                                                                                                                                                                                                                                                                                                                                                                        | `["random:2.0,3.0,4.0"]`      |
| `V_HILL_SIGMA`                    | sigma (std) value controlling width of each Gaussian hill in CV space (Å); `random:` selects one listed value per task                                                                                                                                                                                                                                                                                                                                                                                                        | `["random:0.2,0.3,0.35,0.5"]` |
| `V_EXPECT_NUMB_REACT_INSTANCE`    | number of expected reactive events in simulation, used to self-adaptively set the number of restarting segments in the `LOOP = ceil[(4.6 × 0.8 / HILL_HEIGHT) × V_EXPECT_NUMB_REACT_INSTANCE] + 2`. Here `4.6 × 0.8` eV approximately equal to 80 kcal /mol is the reference bond energy of a C-C single bond. It estimates how many ideal biases (each in one segment) are needed to break the expected number of reference bonds. +2 is for two unbiased segments ahead each task. Apparently, the value is overly optimistic | `[4.5]`                       |
| `V_HARMONIC_THICKNESS`            | thickness of the spherical harmonic wall in Å, used to confine the molecule                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `[6]`                         |
| `V_HARMONIC_FACTOR`               | force constant of the spherical harmonic nanoreactor wall in eV Å⁻²                                                                                                                                                                                                                                                                                                                                                                                                                                                           | `[10]`                        |
| `V_SECURE_SINGLE_ATOM_RCUT`       | maximum distance in Å for merging an isolated single-atom domain (after the local partition operation) into its nearest domain                                                                                                                                                                                                                                                                                                                                                                                                | `[3.5]`                       |
| `V_DROP_HYDROGEN_RCUT_LARGERTHAN` | threshold of local-partition cutoff in Å, at or above which H atoms are excluded from the domain CV metric                                                                                                                                                                                                                                                                                                                                                                                                                    | `[2.0]`                       |
| `V_TEMP`                          | thermostat temperature in K                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `[300]`                       |
| `V_TIME_STEP`                     | simulation time step in ps                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | `[0.001]`                     |
| `V_MASS_HYDROGEN`                 | hydrogen mass in amu                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `[8.0]`                       |
| `V_PACE`                          | simulation steps per segment in the loop                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | `[500]`                       |
| `V_OUTFREQ_PLUMED`                | stride for PLUMED output, also adopted here by LAMMPS thermo and dump output, needed to be consistent with another general DPGEN2 parameter 'trj_freq'                                                                                                                                                                                                                                                                                                                                                                         | `[5]`                         |


`lammps_Rxn_template.in` and `input.plumed` support standalone execution after all key parameters (`V_*` placeholders) have been properly replaced.

## Technique details

### Flowchart

```text
                                                 DP-GEN2
                                           dpgen2_example.json
                              orchestrates exploration; set key parameters
                                                    |
                                                    v                                Sampling strategy
   +-------------------------------------------------------------------------------------------------+
   |                                                |                                                |
   |                                  LAMMPS; custom functions                                       |
   |                                  lammps_Rxn_template.in                                         |
   |                                  organizing the sampling strategy                               |
   |                                                |                                                |
   |                                                |                          metaD loop            |
   |              +----------------------+----------+-----------+----------------------+             |
   |              |                      |                      |                      |             |
   |    custom functions              PLUMED                 LAMMPS                   DeepMD-kit     |
   |    lammps_Rxn_template.in        input.plumed           lammps_Rxn_template.in   MLIP file      |
   |    modify PLUMED files   ---->   applies bias           run simulation           PES            |
   |              |                      |                      |                      |             |
   |              +----------------------+----------+-----------+----------------------+             |
   |                                                |                                                |
   |                                custom functions                                                 |
   |                                lammps_Rxn_template.in                                           |
   |                                select near-reactive configuration seeds                         |
   |                                                |                                                |
   |                                                |              batch TS optimization             |
   |              +---------------------------------+----------------------------------+             |
   |              |                                                                    |             |
   |    ASE                                                        DeepMD local server; DeepMD-kit   |
   |    lammps_Rxn_template.in                                     server/client.py; MLIP file       |
   |    run dimer TS optimization from metaD seeds                 enable batch run; PES             |
   |              |                                                                    |             |
   |              +---------------------------------+----------------------------------+             |
   |                                                |                                                |
   |                                                |                                                |
   |                                custom functions                                                 |
   |                                lammps_Rxn_template.in                                           |
   |                                select sparsified samples from dimer trajectories                |
   |                                                |                                                |
   |                                                |                                                |
   |                                custom functions; DeepMD-kit                                     |
   |                                lammps_Rxn_template.in                                           |
   |                                arrange files and calculate model deviation of samples           |
   |                                                |                                                |
   +-------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
                                                 DP-GEN2
                                           dpgen2_example.json
                                select candidates from samples for labeling
```

### Custom functions in lammps_Rxn_template.in

Custom Python functions in lammps_Rxn_template.in are defined in the `source` block, parameterized in `registration` block, and called through `invoke`. 
All parameters can be set in `registration` block. Details please see the script and annotations within.

The tree below shows operations (letters), LAMMPS-invoked functions (numbers), internal helper functions (unlabeled), and outputs/revised files (square brackets).

```text
initialization
├── a. construct local and time-averaged references for the RMSD metric
│   ├── 1. convert_lmpdata_to_pdb [ave_pre.pdb]
│   ├── 2. make_local_division [divisions.json]
│   │   ├── load_coordinates
│   │   ├── calculate_center
│   │   ├── distance
│   │   ├── create_division
│   │   ├── merge_single_atom_divisions
│   │   └── make_division_plus_one_dropHydrogen
│   ├── 3. distinguish_local_global 
│   ├── 4. split_avepdb_local_pdbs [ave_local_*.pdb]
│   ├── 5. merge_sep_ref_pdb_integrated_pdb [ave.pdb]
│   └── 6. revise_multirmsd_avepdb [ave_multiRMSD.pdb]
└── b. initialize averaging and restart controls
    ├── 7. touch_hills [HILLS]
    ├── 8. add_command_lmpptr [input.plumed, ave_local_*.dump, LOOP]
    │   └── revise_plumed_if_random
    └── 9. delete_avepdb_back_from_dpgen_workaround

simulation loop
├── c. adapt PLUMED inputs and the formats of related files
│   ├── 10. revise_plumed_in_single_to_multi [input.plumed]
│   ├── 11. revise_columnames [HILLS, COLVAR]
│   └── 12. combine_bck_file [bck_combined.output.plumed]
└── d. remap HILLS records and update reference-geometry PDB files between MetaD segments
    ├── 13. convert_lmpdump_to_pdb [ave_local_*.pdb]
    ├── 14. merge_sep_ref_pdb_integrated_pdb [ave.pdb]
    ├── 15. revise_cv_HILLS [HILLS]
    │   └── update_CV
    └── 16. revise_multirmsd_avepdb [ave_multiRMSD.pdb]

TS optimization
├── e. select near-reactive frames from the MetaD trajectory
│   └── 17. snapshots_from_traj [opt_startpoint_*.lmp, bond_changes_mapping.json, reaction_event_groups.json]
│       ├── load_cv_data
│       ├── load_log_data
│       ├── find_extended_points
│       ├── analyze_potential_energy
│       ├── detect_bonds
│       │   └── get_bond_radii
│       ├── analyze_equilibrium_bonds
│       └── check_bond_changes
│           └── get_bond_radii
├── f. prepare DeepMD servers for TS-optimization client tasks
│   └── 18. boost_deepmd_multi_server [deepmd_server_client_config.json, local DeepMD server processes]
└── g. batch-run ASE dimer optimizations from selected MetaD seeds
    └── 19. run_dimer_batch_for_lammps [opt_startpoint_*_dp_ts.xyz/.dump/.log]
        ├── get_deepmd_model
        └── run_single_dimer_parallel
            ├── read_lammps_data
            ├── generate_initial_displacement
            │   └── generate_random_displacement
            └── run_dimer_for_structure
                ├── DimerLogFile
                ├── trajectory_observer
                ├── AdaptiveOptimizer
                │   └── check_phase_switch
                │       └── print_dimer_info
                └── custom_converged_wrapper

post-processing
├── h. sparsify dimer optimization trajectories to collect samples
│   └── 20. convert_xyz_lmpdump_deepmdnpymixed [traj_dp_ts.dump, data_dp_ts/, arc_sampling_info_*.json, global_reaction_coordinate_info.json]
│       ├── parse_gauxyz_and_get_atom_types_list
│       ├── get_coords_from_frame
│       ├── detect_initial_bonds
│       ├── analyze_equilibrium_bonds
│       └── calculate_normalized_reaction_coordinate
└── i. organize sample files and calculate model_deviation for DP-GEN2
    ├── 21. get_model_devi [model_devi_dp_ts.out]
    ├── 22. merge_model_devi [model_devi.out, model_devi.out.md_backup]
    └── 23. merge_traj [traj.dump, traj.dump.md_backup]
```

### Environment dependencies

The versions below were used in the production.


| package                | version                 | details                                                      |
| ---------------------- | ----------------------- | ------------------------------------------------------------ |
| DeepMD-kit             | 3.1.1                   |                                                              |
| LAMMPS                 | 29 Aug 2024             | requires `PYTHON`, `PLUMED`, and `USER-DEEPMD` User-packages |
| PLUMED                 | 2.9.2                   |                                                              |
| ASE                    | 3.22.1                  |                                                              |
| MDAnalysis             | 1.9.0                   |                                                              |
| dpdata                 | 0.2.24                  |                                                              |
| requests / Flask       | 2.32.4 / 3.1.2          | required by DeePMD local server-client                       |
| NumPy / pandas / SciPy | 1.26.4 / 2.3.0 / 1.15.2 |                                                              |


