#!/usr/bin/env python
# software from PDBe: Protein Data Bank in Europe; https://pdbe.org
#
# Copyright 2018 EMBL - European Bioinformatics Institute
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

import os
from collections import namedtuple

import numpy
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolTransforms
from rdkit.Geometry import Point2D
from scipy.spatial import KDTree

from pdbeccdutils.core import DepictionSource
from pdbeccdutils.utils import config

Mapping = namedtuple('Mapping', 'atom_mapping bond_mapping')
DepictionResult = namedtuple('DepictionResult', 'source template_name mol score')


class DepictionManager:
    """
    Toolkit for depicting ligand's structure using RDKit.
    One can supply either templates or 2D depictions by pubchem.
    PubCshem templates can be downloaded using PubChemDownloader class.
    """

    def __init__(self, pubchem_templates_path='', general_templates_path=config.general_templates):
        """
        Initialize component which does the ligand depiction.
        If Nones is provided as parameters just the defalt RDKit
        functionality is going to be used.

        Args:
            pubchem_templates_path (str, optional): Defaults to ''. 
                Path to the library with 2D structures downloaded from 
                PubChem. Use `setup_pubchem_library` for this task.                
            general_templates_path (str, optional): Defaults to 
                config.general_templates (supplied with the pdbeccdutils).
                Path to the library with general templates to be used
                for depicting ligand e.g. porphyring rings.

        """

        self.pubchem_templates = []
        self.substructures = []

        if os.path.isdir(general_templates_path):
            self.substructures = {k.split('.')[0]:
                                  self._load_template(os.path.join(general_templates_path, k))
                                  for k in os.listdir(general_templates_path)}

        if os.path.isdir(pubchem_templates_path):
            self.pubchem_templates = {k.split('.')[0]:
                                      os.path.join(pubchem_templates_path, k)
                                      for k in os.listdir(pubchem_templates_path)}

    def _load_template(self, path):
        """
        Loads a template molecule with 2D coordinates

        Args:
            path (str): path to the model molecule in *.sdf,
                or *.pdb format

        Raises:
            ValueError: if unsuported format is used: sdf|pdb

        Returns:
            rdkit.Chem.rdchem.Mol: RDKit representation of the template
        """
        mol = Chem.RWMol()
        extension = os.path.basename(path).split('.')[1]

        if extension == 'sdf':
            mol = Chem.MolFromMolFile(path, removeHs=True)
        elif extension == 'pdb':
            mol = Chem.MolFromPDBFile(path, removeHs=True)
        else:
            raise ValueError('Unsupported molecule type \'{}\''.format(extension))

        [x.SetAtomicNum(6) for x in mol.GetAtoms()]
        [x.SetBondType(Chem.BondType.UNSPECIFIED) for x in mol.GetBonds()]

        return mol

    def _anonymization(self, mol):
        """
        Converts all molecule atoms into carbons and all bonds into
        single ones. This is used for the substructure matching step.
        Original mapping of both is returned.

        Args:
            mol (rdkit.Chem.rdchem.Mol): molecule to be anonymized

        Returns:
            Mappings: original mapping between atoms and bonds
            of the molecule
        """
        molAtomMapping = {atom.GetIdx(): atom.GetAtomicNum() for atom in mol.GetAtoms()}
        molBondMapping = {bond.GetIdx(): bond.GetBondType() for bond in mol.GetBonds()}

        [x.SetAtomicNum(6) for x in mol.GetAtoms()]
        [x.SetBondType(Chem.BondType.SINGLE) for x in mol.GetBonds()]

        return Mapping(atom_mapping=molAtomMapping, bond_mapping=molBondMapping)

    def _deanonymization(self, mol, mappings):
        """
        Based on the original mapping restores atom elements and
        bond types.

        Args:
            mol (rdkit.Chem.rdchem.Mol): molecule to be restored
            mappings (Mapping): Original bond and atom info
        """

        [x.SetAtomicNum(mappings.atom_mapping[x.GetIdx()]) for x in mol.GetAtoms()]
        [x.SetBondType(mappings.bond_mapping[x.GetIdx()]) for x in mol.GetBonds()]

    def _rescale_molecule(self, mol, factor):
        """
        Rescale molecule coords to a given factor

        Args:
            mol (rdkit.Chem.rdchem.Mol) molecule to be rescaled
            factor (float): rescaling factor
        """
        matrix = numpy.zeros((4, 4), numpy.float)

        for i in range(3):
            matrix[i, i] = factor
        matrix[3, 3] = 1

        AllChem.TransformMol(mol, matrix)

    def depict_molecule(self, id, mol):
        """
        Given input molecule tries to generate its depictions.

        Presently 3 methods are used:
                Pubchem template - find 2d depiction in pubchem db
                User-provided templates - try to use general templates
                From 3D conformer - just apply default RDKit functionality

        Arguments:
            id (str): id of the ligand
            mol (Chem.rdchem.Mol): molecule to be depicted

        Returns:
            pdbeccdutils.utils.DepictionResult: Summary of the ligand
                depiction process.
        """
        temp_mol = Chem.RWMol(mol)
        mappings = self._anonymization(temp_mol)
        templateMol = Chem.RWMol(temp_mol).GetMol()
        pubchemMol = Chem.RWMol(temp_mol).GetMol()
        rdkitMol = Chem.RWMol(temp_mol).GetMol()
        results = []

        pubchem_res = self._get_2D_by_pubchem(id, pubchemMol) if not self.pubchem_templates else None
        template_res = self._get_2D_by_template(templateMol) if self.substructures else []
        rdkit_res = self._get_2D_by_rdkit(rdkitMol)

        if pubchem_res is not None:
            results.append(pubchem_res)
        if rdkit_res is not None:
            results.append(rdkit_res)

        results = results + template_res

        results.sort(key=lambda l: (l.score, l.source))

        if len(results) > 0:
            self._deanonymization(results[0].mol, mappings)
            return results[0]
        else:
            return DepictionResult(source=DepictionSource.Failed, template_name='', mol=None, score=1000)

    def _get_2D_by_rdkit(self, mol):
        """
        Get depiction done using solely the default RDKit functionality.

        Args:
            mol (rdkit.Chem.rdchem.Mol): Mol to be depicted

        Returns:
            DepictionResult: Depiction with some usefull metadata
        """
        try:
            AllChem.GenerateDepictionMatching3DStructure(mol, mol)
            flaws = DepictionValidator(mol).depiction_score()
            return DepictionResult(source=DepictionSource.RdKit, template_name=None, mol=mol, score=flaws)
        except Exception:
            return None

    def _get_2D_by_pubchem(self, id, mol):
        """
        Depict ligand using Pubchem templates.

        Args:
            id (str): of molecule to be processed
            mol (rdkit.Chem.rdchem.Mol): Mol to be depicted

        Returns:
            DepictionResult: Depiction with some usefull metadata
        """
        try:
            if id in self.pubchem_templates:
                template = self._load_template(self.pubchem_templates[id])
                self._rescale_molecule(template, 1.5)

                if mol.HasSubstructMatch(template):
                    AllChem.GenerateDepictionMatching2DStructure(mol, template)
                    flaws = DepictionValidator(mol).depiction_score()
                    return DepictionResult(source=DepictionSource.Pubchem, template_name=id, mol=mol, score=flaws)
        except Exception:
            pass

        return None

    def _get_2D_by_template(self, mol):
        """
        Depict ligand using user-provided templates

        Args:
            mol (rdkit.Chem.rdchem.Mol): Mol to be depicted

        Returns:
            list of pdbecccdutils.DepictionResult: Depictions with their
            quality and metadata.
        """
        results = list()
        try:
            for key, template in self.substructures.items():
                temp_mol = Chem.RWMol(mol)
                if temp_mol.HasSubstructMatch(template):
                    AllChem.GenerateDepictionMatching2DStructure(temp_mol, template)
                    flaws = DepictionValidator(temp_mol).depiction_score()
                    results.append(DepictionResult(source=DepictionSource.Template,
                                                   template_name=key, mol=temp_mol, score=flaws))
        except Exception:
            pass  # if it fails it fails, but genuinelly it wont

        return results


class DepictionValidator:
    """
    Toolkit for estimation of depiction quality
    """

    def __init__(self, mol):
        self.mol = mol
        self.conformer = mol.GetConformer()
        self.bonds = self.mol.GetBonds()

        atoms = [self.conformer.GetAtomPosition(i) for i in range(0, self.conformer.GetNumAtoms())]
        atom_centers = [[atom.x, atom.y, atom.z] for atom in atoms]

        self.kd_tree = KDTree(atom_centers)

    def _intersection(self, bondA, bondB):
        """
        True if two bonds collide, false otherwise. Note that false is
        retrieved even in case the bonds share common atom, as this is
        not a problem case. Cramer's rule is used for the linear
        equations system.

        Args:
            bondA (rdkit.Chem.rdchem.Bond): this bond
            bondB (rdkit.Chem.rdchem.Bond): other bond

        Returns:
            bool: true if bonds share collide, false otherwise.
        """
        atomA = self.conformer.GetAtomPosition(bondA.GetBeginAtomIdx())
        atomB = self.conformer.GetAtomPosition(bondA.GetEndAtomIdx())
        atomC = self.conformer.GetAtomPosition(bondB.GetBeginAtomIdx())
        atomD = self.conformer.GetAtomPosition(bondB.GetEndAtomIdx())

        vecA = Point2D(atomB.x - atomA.x, atomB.y - atomA.y)
        vecB = Point2D(atomD.x - atomC.x, atomD.y - atomC.y)

        # Cramer rule to identify intersection
        det = vecA.x * -vecB.y + vecA.y * vecB.x
        if round(det, 2) == 0.00:
            return False

        a = atomC.x - atomA.x
        b = atomC.y - atomA.y

        detP = (a * -vecB.y) - (b * -vecB.x)
        p = round(detP / det, 3)
        aa = detP / det

        if (p <= 0 or p >= 1):
            return False

        detR = (vecA.x * b) - (vecA.y * a)
        r = round(detR / det, 3)

        if 0 <= r <= 1:
            return True

        return False

    def has_degenerated_atom_positions(self, threshold):
        """
        Detects whether the structure has a pair or atoms closer to each
        other than threshold. This can detect structures which may need
        a template as they can be handled by RDKit correctly.

        Arguments:
            threshold (float): Bottom line to use for spatial search.

        Returns:
            (bool): if such atomic pair is found
        """

        for i in range(0, len(self.conformer.GetNumAtoms())):
            center = self.conformer.GetAtomPosition(i)
            point = [center.x, center.y, center.z]
            surrounding = self.kd_tree.query_ball_point(point, threshold)

            if len(surrounding) > 1:
                return True

        return False

    def count_suboptimal_atom_positions(self, lowerBound, upperBound):
        """
        Detects whether the structure has a pair or atoms in the range
        <lowerBound, upperBound> meaning that the depiction could
        be improved.

        Arguments:
            lowerBound (float): lower bound
            upperBound (float): upper bound

        Returns:
            bool: indication whether or not the atoms are not in
            optimal coordinates
        """
        counter = 0
        for i in range(self.conformer.GetNumAtoms()):
            center = self.conformer.GetAtomPosition(i)
            point = [center.x, center.y, center.z]
            surroundingLow = self.kd_tree.query_ball_point(point, lowerBound)
            surroundingHigh = self.kd_tree.query_ball_point(point, upperBound)

            if len(surroundingHigh) - len(surroundingLow) > 0:
                counter += 1

        return counter / 2

    def count_bond_collisions(self):
        """
        Counts number of collisions among all bonds. Can be used for estimations of how 'wrong'
        the depiction is.

        Returns:
            int: numer of bond collisions per molecule
        """

        errors = 0

        for i in range(0, len(self.bonds)):
            for a in range(i + 1, len(self.bonds)):
                result = self._intersection(self.bonds[i], self.bonds[a])

                if result:
                    errors += 1
        return errors

    def has_bond_crossing(self):
        """
        Tells if the structure contains collisions

        Returns:
            bool: Indication about bond collisions
        """
        return self.count_bond_collisions() > 0

    def depiction_score(self):
        """
        Calculate quality of the ligand depiction. The higher the worse.
        Ideally that should be 0.

        Returns:
            float: Penalty score
        """

        collision_penalty = 1
        degenerated_penalty = 0.4

        bond_collisions = self.count_bond_collisions()
        degenerated_atoms = self.count_suboptimal_atom_positions(0.0, 0.5)

        score = collision_penalty * bond_collisions + degenerated_penalty * degenerated_atoms

        return round(score, 1)