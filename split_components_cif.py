# software from PDBe: Protein Data Bank in Europe; http://pdbe.org
#
# Copyright 2017 EMBL - European Bioinformatics Institute
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
#
import mmCif.mmcifIO as mmcifIO
from pdb_chemical_components_rdkit import PdbChemicalComponentsRDKit


class SplitComponentsCif(object):
    """deals with splitting the wwPDB Chemical Component Dictionary into individual PdbChemicalComponentsRDKit
    objects for each chem_comp definition.
    """
    def __init__(self, file_name):
        cif_parser = mmcifIO.CifFileReader(input='data', preserve_order=True)
        self.cif_dictionary = cif_parser.read(file_name, output='cif_dictionary')

    def individual_pdb_ccd_rdkit(self):
        for data_block_id, data_block in self.cif_dictionary.items():
            individual_cif_dictionary = {}
            individual_cif_dictionary[data_block_id] = data_block
            pdb_ccd = PdbChemicalComponentsRDKit(cif_dictionary=individual_cif_dictionary)
            yield pdb_ccd



