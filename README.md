[![pipeline status](https://gitlab.ebi.ac.uk/pdbe/ccdutils/badges/master/pipeline.svg)](https://gitlab.ebi.ac.uk/pdbe/ccdutils/commits/master)
[![coverage report](https://gitlab.ebi.ac.uk/pdbe/ccdutils/badges/master/coverage.svg)](https://gitlab.ebi.ac.uk/pdbe/ccdutils/commits/master)

# pdbeccdutils

* A set of python tools to deal with PDB chemical components definitions
  for small molecules, taken from the [wwPDB Chemical Component Dictionary](https://www.wwpdb.org/data/ccd)

* The tools use:
  * [RDKit](http://www.rdkit.org/) for chemistry
  * [PDBeCIF](https://gitlab.com/glenveegee/PDBeCIF.git) cif parser.
  * [scipy](https://www.scipy.org/) for depiction quality check.
  * [numpy](https://www.numpy.org/) for molecular scaling.

* Please note that the project is under active development.

## Installation instructions

You have the choice to install the code using the original installation instructions. A conda environment is also provided allowing easy installation of ccdutils and deployment elsewhere. 

### Standalone installation instructions

* `pdbeccdutils` requires RDKit to be installed.
  The official RDKit documentation has [installation instructions for a variety of platforms](http://www.rdkit.org/docs/Install.html).
  For linux/mac OS this is most easily done using the anaconda python with commands similar to:

  ```console
  conda create -c rdkit -n rdkit-env rdkit python=3.7
  conda activate rdkit-env
  ```

* Once you have installed RDKit, as described above then install pdbeccdutils using pip:

  ```console
  pip install git+https://gitlab.ebi.ac.uk/pdbe/ccdutils.git
  ```

### Installation using conda

You can also install a full conda environment for your development work on ccdutils using the following command:
```conda env create -f environment.yml```

Once this installation is done you can use the environment with: 
```conda activate ccdutils```

## Features

* mmCIF CCD read/write.
* Generation of 2D depictions (`No image available` generated if the flattening cannot be done) along with the quality check.
* Generation of 3D conformations.
* Fragment library search.
* Chemical scaffolds (Murcko scaffold, Murcko general, BRICS).
* Lightweight implementation of parity method by Jon Tyczak.
* RDKit molecular properties per component.
* UniChem mapping.


## TODO list

* Port rest of the important functionality implemented by Oliver
* Add more unit/regression tests to get at least 100% code coverage.
* Further improvement of the documentation.

## Notes

* Protein-ligand interaction has been extracted [here](https://gitlab.ebi.ac.uk/pdbe/release/interactions). This was because of the fact that at the end of the day it was not using any of the pdbeccdutils functionality and introduced additional dependencies on the package.

## Documentation

The documentation depends on the following packages:

* `sphinx`
* `sphinx_rtd_theme`
* `recommonmark`
* `sphinx-autodoc-typehints`

Note that `sphinx` needs to be a part of the virtual environment, if you want to generate documentation by yourself.
Otherwise it cannot pick `rdkit` module. `sphinx_rtd_theme` is a theme providing nice `ReadtheDocs` mobile friendly style.

* Generate *.rst* files to be included as a part of the documentation. Inside the directory `pdbeccdutils/doc` run the following commands to generate documentation.
* Alternatively, use the `recommonmark` package along with the proper configuration to get the Markdown working.
  
 Use the following to generate initial markup files to be used by sphinx.  This needs to be used when adding another sub-packages.

```console
sphinx-apidoc -f -o /path/to/output/dir ../pdbeccdutils/
```

Use this to re-generate the documentation from the doc/ directory:

```console
make html
```