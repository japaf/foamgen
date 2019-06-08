# Foamgen: create foam morphology

Foamgen can create spatially three-dimensional virtual representations of foam morphology with desired foam density, cell size distribution and strut content. Can be used to create both closed-cell and open-cell foams. Capable of generation of both structured (uniform grid) and unstructured meshes.

## Installation

### Dependencies

Make sure you have the following dependencies installed:

- [packing-generation](https://github.com/VasiliBaranov/packing-generation.git)
- [Neper](http://neper.sourceforge.net/index.html)
- [Voro++](http://math.lbl.gov/voro++/about.html)
- [meshconv](http://www.patrickmin.com/meshconv)
- [binvox](http://www.patrickmin.com/binvox/)
- [GSL](http://www.gnu.org/software/gsl/)

On Ubuntu, all of these can be installed using:

```bash
sudo ./install_dependencies.sh
```

### Module

Install using pip:

```bash
pip install .
```

## Files

The folder `FoamConstruction` contains following files:

- `packing.py` - sphere packing
- `tessellation.py` - tessellation, creation of RVE
- `periodicBox.py` - creation of the box with periodic boundary conditions
- `vtkconv.py` - conversion from binary vtk to ascii vtk
- `geo_tools.py` - manipulation of GMSH geometry files, creation of unstructured mesh
- `run.py` - main executable script
- `simulation.py` - experimental script for FEM simulations using FEniCS (conductivity or diffusivity)

All files must be in one directory.

## Inputs

The code is controlled by the `input.json` file, which must be located in the
root of `FoamConstruction` folder. Default input file can be found
in `example_inputs` directory. Following inputs can be adjusted:

- `filename`: base name of created files
- `packing`: create sphere packing [true, false],
- `packing_options`:
    - `shape`: shape of log-normal distribution,
    - `domain_size`: domain size (1 is recommended),
    - `number_of_cells`: number of cells,
    - `scale`: scale of log-normal distribution,
    - `algorithm`: type of sphere packing algorithm [`simple`, `-ls`, `-fba`, `-lsgd`, `-lsebc`, `-ojt`, `-kjt`], `simple` algorithm is included, others are enabled by packing-generation (see <https://github.com/VasiliBaranov/packing-generation),> `-fba` is recommended
- `tessellation`: create tessellated foam [true, false],
- `tessellation_options`:
    - `visualize_tessellation`: visualize tessellation [true, false], false is recommended
- `structured_grid`: create structured (voxel) mesh [true, false],
- `structured_grid_options`:
    - `render_box`: visualize foam [true, false], false is recommended
    - `strut_content`: strut content,
    - `porosity`: foam porosity,
    - `strut_size_guess`: strut size in voxels, guess usually 4-8
    - `binarize_box`: run part of the script, which creates voxel mesh, [true, false], true is recommended
    - `move_to_periodic_box`: run part of the script, which moves foam to periodic box, [true, false], true is recommended
- `unstructured_grid`: create unstructured (tetrahedral) mesh [true, false],
- `unstructured_grid_options`:
    - `create_geometry`: run part of the script, which creates foam, [true, false], true is recommended,
    - `convert_mesh`: run part of the script, which converts mesh to .xml, [true, false], true is recommended,
    - `wall_thickness`: wall thickness parameter, 0.02 is good guess
    - `mesh_domain`: run part of the script, which creates mesh, [true, false], true is recommended

## Execution

Prepare `input.json`, then:

```bash
./run.py
```

Optimizing porosity and strut content of voxelized foam is relatively time
consuming. You can switch to `Bounded` method if you approximately know the
size of the box in voxels (usually from experience with the program). In that
case you need to edit the `run.py` script.

## Outputs

Several output files are created. Structured mesh is in `{filename}_str.vtk`, unstructured mesh is in `{filename}_uns.msh`.

Generally, `.geo`, and `.msh` files can be viewed with `gmsh`. `.stl`, `.ply` and `.vtk`
files can be viewed with `paraview`.
