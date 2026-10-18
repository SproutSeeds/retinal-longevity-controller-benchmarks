#!/usr/bin/env python3
"""Synthetic/adversarial tests; never read biological count rows."""
import copy
import csv
import gzip
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import hashlib
import json
import numpy as np
import analyze
from admit_metadata import parse_identifier, join_header, donor_pairs
from analyze import (average_ranks, normalizations, exact_age_permutation,
                     exact_sign_test, holm, canonical_gene, read_counts, run_analysis, coverage)


class ExactTestTests(unittest.TestCase):
    def test_asymmetric_partition_can_have_one_over_126(self):
        result = exact_age_permutation([0,1,2,3,10,11,12,13,14], [True]*4+[False]*5)
        self.assertEqual((result['numerator'],result['denominator']), (1,126))
        self.assertAlmostEqual(result['signed_effect'], -10.5)

    def test_all_ties_are_included(self):
        result = exact_age_permutation([0]*9, [True]*4+[False]*5)
        self.assertEqual((result['numerator'],result['denominator']), (126,126))

    def test_permutation_is_invariant_to_joint_order(self):
        x = np.array([0,1,2,3,10,11,12,13,14.])
        old = np.array([True]*4+[False]*5)
        order = [5,1,7,3,0,8,4,2,6]
        a,b = exact_age_permutation(x,old),exact_age_permutation(x[order],old[order])
        self.assertEqual(a['numerator'],b['numerator'])
        self.assertEqual(a['signed_effect'],b['signed_effect'])

    def test_all_nine_positive_signs(self):
        result = exact_sign_test(np.arange(1,10))
        self.assertEqual((result['positive'],result['negative'],result['zero']), (9,0,0))
        self.assertEqual((result['numerator'],result['denominator']), (2,512))

    def test_zero_signs_excluded_without_imputation(self):
        result = exact_sign_test([0,0,1,2,3,-1])
        self.assertEqual((result['nonzero_n'],result['zero']), (4,2))
        self.assertEqual(result['p'], 0.625)
        self.assertEqual(exact_sign_test([0]*9)['p'], 1)

    def test_holm_preserves_four_test_family_with_missing(self):
        result = holm([0.01, 0.02, None, 0.5])
        self.assertEqual(result,[0.04,0.06,None,1.0])

    def test_invalid_statistics_rejected(self):
        for x,old in [([1,float('nan')],[True,False]), ([1,2],[True,True]), ([1,2],[True])]:
            with self.subTest(x=x), self.assertRaises(ValueError):
                exact_age_permutation(x,old)
        with self.assertRaises(ValueError):
            exact_sign_test([float('inf')])
        with self.assertRaises(ValueError):
            holm([1.01])


class MetadataTests(unittest.TestCase):
    def test_time_alias_is_exact(self):
        self.assertEqual(parse_identifier('A1_940_A6h_Dox_chim'), parse_identifier('A1_940_A06h_Dox_chim'))
        self.assertEqual(parse_identifier('H8_966_D6h_Dox_chim')['well'],'H8')
        for name in ['A1_940_A18h_Dox_chim_extra','I1_940_A18h_Dox_chim','A1_940_A12h_Dox_chim']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                parse_identifier(name)

    def test_header_collision_and_treatment_conflict_rejected(self):
        rows = [{'description':'A1_940_A06h_Dox_chim'}]
        good = ['Geneid','Length','A1_940_A6h_Dox_chim']
        self.assertEqual(join_header(copy.deepcopy(rows),good)[0]['count_column'],good[2])
        for header in [good+[good[2]],good+['A1_940_A06h_Dox_chim'],['Geneid','Length','A1_940_A6h_untr_chim']]:
            with self.subTest(header=header), self.assertRaises(ValueError):
                join_header(copy.deepcopy(rows),header)

    def test_donor_pair_rejects_duplicate_and_sex_conflict(self):
        base = {'donor_id':'940','age_group':'old','sex':'F','species':'Mus musculus',
                'genotype':'iOSKM','replicate_label':1,'timepoint':'A18h','geo_accession':'GSM1','well':'A1'}
        rows = [{**base,'treatment':'untr','count_column':'c'},
                {**base,'treatment':'Dox','count_column':'t','well':'A2','geo_accession':'GSM2'}]
        self.assertEqual(len(donor_pairs(rows)),1)
        for bad in [rows+[rows[1]], [rows[0],{**rows[1],'sex':'M'}], [rows[0]]]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                donor_pairs(bad)


class NormalizationTests(unittest.TestCase):
    def test_average_rank_ties_include_zeros(self):
        np.testing.assert_array_equal(average_ranks([0,0,2,5]), [1.5,1.5,3,4])

    def test_normalizers_invariant_to_library_scaling(self):
        x = np.tile(np.arange(1,121)[:,None], (1,4)).astype(float)
        x[:10,1] *= 2
        a,_ = normalizations(x)
        b,_ = normalizations(x*np.array([2,3,4,5]))
        for method in a:
            with self.subTest(method=method):
                np.testing.assert_allclose(a[method],b[method],rtol=1e-12,atol=1e-12)

    def test_median_ratio_failure_is_explicit(self):
        values,audit = normalizations(np.ones((99,4)))
        self.assertNotIn('log2_median_ratio',values)
        self.assertEqual(audit['all_positive_genes'],99)

    def test_missing_gene_differs_from_present_zero(self):
        panel = {'source_human_genes':['a','b','c','d'], 'genes':[
            {'human_symbol':x,'status':'mapped','mouse_symbol':x,'mouse_ensembl_gene':x} for x in 'abcd']}
        self.assertEqual(coverage(panel,list('abcd'))[0]['failures'],[])
        self.assertIn('source_human_coverage_below_0.8',coverage(panel,list('abc'))[0]['failures'])


class CountReaderTests(unittest.TestCase):
    def read_synthetic(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'counts.csv.gz'
            with gzip.open(path,'wt') as stream:
                stream.write(text)
            return read_counts(path,['Geneid','Length','c','t'])

    def test_rejects_invalid_counts_and_version_collisions(self):
        valid='Geneid,Length,c,t\nENSMUSG00000000001,10,1,2\nENSMUSG00000000002,5,3,4\n'
        self.assertEqual(self.read_synthetic(valid)[1].shape,(2,2))
        for wrong in [valid.replace(',1,2',',-1,2'),valid.replace(',1,2',',0.5,2'),
                      valid.replace(',1,2',',nan,2'),valid.replace(',10,',',0,'),
                      valid.replace('ENSMUSG00000000002','ENSMUSG00000000001.2')]:
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                self.read_synthetic(wrong)

    def test_only_numeric_ensembl_suffix_is_removed(self):
        self.assertEqual(canonical_gene('ENSMUSG00000000001.2'),'ENSMUSG00000000001')
        self.assertEqual(canonical_gene('rtTA.2'),'rtTA.2')


class EndToEndSyntheticTests(unittest.TestCase):
    def make_input(self):
        genes=[f'ENSMUSG{i:011d}' for i in range(1,501)]
        columns=[f'{i}_{arm}' for i in range(9) for arm in ['c','t']]
        pairs=[{'donor_id':str(i),'age_group':'old' if i<4 else 'young','sex':'F',
                'control_count_column':f'{i}_c','treated_count_column':f'{i}_t'} for i in range(9)]
        x=np.tile(np.arange(1,501)[:,None],(1,18))
        for i in range(9):
            x[:3,2*i+1] += i+1
        panel={'source_human_genes':['x','y','z'],'genes':[
            {'human_symbol':h,'status':'mapped','mouse_symbol':h,'mouse_ensembl_gene':g}
            for h,g in zip(['x','y','z'],genes[:3])]}
        panels={name:copy.deepcopy(panel) for name in ['cycle_panel','stress_panel','reprogramming_state','reprogramming_without_OSKM_overlap']}
        return genes,x,columns,{'pairs':pairs},panels

    def test_all_panels_methods_donors_and_contributions_survive(self):
        result,genes=run_analysis(*self.make_input())
        self.assertEqual(len(result['panel_results']),12)
        self.assertEqual(len(result['library_qc']),18)
        for row in result['panel_results']:
            self.assertEqual(row['status'],'available')
            self.assertEqual(len(row['scores']),9)
            self.assertEqual(row['age_test']['denominator'],126)
            self.assertAlmostEqual(sum(r['age_difference_contribution'] for r in row['gene_contributions']),
                                   row['age_test']['signed_effect'])
            self.assertEqual(len(row['gene_omissions']),3)
            if row['method']=='log2_cpm':
                self.assertEqual(len(row['donor_omissions']),9)
        self.assertEqual(len(genes),12*3*9)

    def test_qc_failure_cannot_drop_one_donor(self):
        args=list(self.make_input())
        args[1][100:,0]=0
        result,genes=run_analysis(*args)
        self.assertEqual(result['status'],'primary_unavailable_library_qc')
        self.assertEqual(len(result['panel_results']),12)
        self.assertTrue(all(r['status']=='unavailable' and r['age_test'] is None for r in result['panel_results']))
        self.assertEqual(len({(r['method'],r['panel']) for r in result['panel_results']}),12)
        self.assertEqual(genes,[])


class PortabilityTests(unittest.TestCase):
    def test_archived_replay_checks_hashes_without_git(self):
        with tempfile.TemporaryDirectory() as directory:
            here=Path(directory)
            receipt={'commit':'historical-commit','expression_execution_authorized':True}
            for name,key in [('contract.json','contract_sha256'),('admission.json','admission_sha256'),
                             ('panels.json','panels_sha256'),('analyze.py','analysis_sha256')]:
                data=name.encode()
                (here/name).write_bytes(data)
                receipt[key]=hashlib.sha256(data).hexdigest()
            (here/'FREEZE.json').write_text(json.JSONEncoder().encode(receipt))
            with patch.object(analyze,'HERE',here), patch.object(analyze.subprocess,'check_output',side_effect=AssertionError('git must not run')):
                _,validation=analyze.validate_freeze(True)
                self.assertFalse(validation['historical_git_proof_reexecuted'])
                (here/'panels.json').write_text('changed')
                with self.assertRaisesRegex(ValueError,'Current bytes differ'):
                    analyze.validate_freeze(True)

    def test_portable_cached_receipt_preserves_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            here,cache,out=(root/p for p in ['archive','cache','output'])
            here.mkdir(); cache.mkdir()
            data=gzip.compress(b'Geneid,Length,c,t\na,1,1,1\nb,1,2,2\n')
            path=cache/'GSE245385_countTable.csv.gz';path.write_bytes(data)
            receipt={'sha256':hashlib.sha256(data).hexdigest(),'cache_path':'historical-location'}
            raw=json.JSONEncoder().encode(receipt)
            (here/'count-source-receipt.json').write_text(raw)
            contract={'input':{'expected_compressed_bytes':len(data)}}
            with patch.object(analyze,'HERE',here):
                got,record=analyze.acquire_counts(contract,cache,out)
            self.assertEqual(got,path)
            self.assertEqual(record['cache_path'],str(path))
            self.assertEqual((here/'count-source-receipt.json').read_text(),raw)
            self.assertTrue((out/'count-source-receipt.json').exists())


if __name__=='__main__':
    unittest.main()
