#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1", "h5py==3.16.0", "scikit-learn==1.9.1", "openpyxl==3.1.5", "matplotlib==3.11.2"]
# ///
"""Scientific failure cases, distinct from numerical output snapshot checks."""
import unittest
import numpy as np
from scipy.sparse import csr_matrix
from analyze import group_guides,old_guides,aggregate,detection

class ScientificFailureCases(unittest.TestCase):
 def setUp(self):
  self.names=['A_CRA1','A_CRA2','B_CRA1','B_CRA2','A_CRI1','A_CRI2','NT_1','NT_2']

 def test_intended_pair_is_not_a_doublet(self):
  x=np.array([[5,5,0,0,0,0,0,0]])
  labels,_=group_guides(x,self.names,['CRA'])
  self.assertEqual(labels.tolist(),['A_CRA'])
  self.assertEqual(old_guides(x,self.names,['CRA']).tolist(),['unassigned'])

 def test_dropout_is_only_admitted_in_named_sensitivity(self):
  x=np.array([[10,0,0,0,0,0,0,0]])
  self.assertEqual(group_guides(x,self.names,['CRA'])[0][0],'unassigned')
  self.assertEqual(group_guides(x,self.names,['CRA'],require_pair=False)[0][0],'A_CRA')

 def test_two_target_collision_is_rejected(self):
  x=np.array([[5,5,5,5,0,0,0,0]])
  self.assertEqual(group_guides(x,self.names,['CRA'])[0][0],'unassigned')

 def test_wrong_machinery_and_wt_are_rejected(self):
  x=np.array([[0,0,0,0,5,5,0,0],[5,5,0,0,0,0,0,0]])
  self.assertEqual(group_guides(x,self.names,['CRA','WT'])[0].tolist(),['unassigned','unassigned'])

 def test_nt_requires_two_channels(self):
  x=np.array([[0,0,0,0,0,0,3,2],[0,0,0,0,0,0,5,0]])
  self.assertEqual(group_guides(x,self.names,['CRI','CRI'])[0].tolist(),['CRI_NT','unassigned'])

 def test_zero_library_and_missing_pair(self):
  self.assertEqual(group_guides(np.zeros((1,8)),self.names,['CRA'])[0][0],'unassigned')
  self.assertEqual(group_guides(np.array([[12,0]]),['A_CRA1','NT_1'],['CRA'],require_pair=False)[0][0],'unassigned')

 def test_malformed_counts_cannot_enter_analysis(self):
  for value in [-1,np.nan,.5]:
   x=np.zeros((1,8));x[0,0]=value
   with self.assertRaises(ValueError):group_guides(x,self.names,['CRA'])

 def test_sparse_aggregation_preserves_all_groups(self):
  groups,pb,n=aggregate(csr_matrix([[1,0],[0,2],[3,4]]),np.array(['A','unassigned','A']))
  self.assertEqual(groups.tolist(),['A','unassigned'])
  np.testing.assert_array_equal(pb,[[4,4],[0,2]])
  self.assertEqual(n.tolist(),[2,1])

 def test_one_cell_has_same_marginal_detection_under_clustering(self):
  for rho in [0,.01,.05,.1]:self.assertAlmostEqual(detection(.01,.8,1,1,rho),.008,places=8)

 def test_independent_cells_do_not_care_about_donor_partition(self):
  self.assertAlmostEqual(detection(.01,.8,1,1200,0),detection(.01,.8,6,200,0),places=12)

 def test_donor_diversity_changes_clustered_detection(self):
  self.assertGreater(detection(.01,.8,6,200,.05),detection(.01,.8,1,1200,.05))

 def test_invalid_design_rejected(self):
  with self.assertRaises(ValueError):detection(.01,.8,0,1200,.05)
  with self.assertRaises(ValueError):detection(.01,.8,3,400,1)

if __name__=='__main__':unittest.main()
