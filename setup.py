from setuptools import setup

setup(name='pdbeccdutils',
      version='0.2',
      description='Toolkit to deal with wwPDB chemical components definitions for small molecules.',
      url='https://gitlab.com/pdbe/ccd_utils',
      author='Protein Data Bank in Europe',
      author_email='pdbehelp@ebi.ac.uk',
      license='Apache License 2.0.',
      packages=['pdbeccdutils'],
      scripts=['bin/setup_pubchem_library',
               'bin/process_components_cif'],
      zip_safe=False,
      include_package_data=True,
      install_requires=['Pillow', 'scipy', 'sphinx', 'sphinx_rtd_theme'],
      tests_require=['pytest']
      )
