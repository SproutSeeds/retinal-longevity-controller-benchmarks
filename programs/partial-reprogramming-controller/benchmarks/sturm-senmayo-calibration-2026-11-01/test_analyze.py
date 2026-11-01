import csv
import gzip
from pathlib import Path
import tempfile
import unittest

import analyze as a


class AnalysisChecks(unittest.TestCase):
    def test_known_tied_rank_result(self):
        self.assertEqual(a.ranks([4,1,1,3]),[4,1.5,1.5,3])
        self.assertAlmostEqual(a.spearman([1,1,3,4],[4,3,2,1]),-0.9486832980505138)

    def test_linear_time_confounding_reversal(self):
        t = list(range(12))
        z = [(-1.0)**i for i in t]
        x,y = [v+w for v,w in zip(t,z)],[v-2*w for v,w in zip(t,z)]
        self.assertGreater(a.spearman(x,y),0.5)
        self.assertAlmostEqual(a.adjusted(x,y,t),-1.0)

    def test_constant_and_linear_residuals_are_unavailable(self):
        self.assertIsNone(a.spearman([1]*5,list(range(5))))
        self.assertIsNone(a.adjusted([0,2,4,6,8],[1,4,2,5,3],list(range(5))))
        self.assertIsNone(a.residuals([0,2,4,6,8+1e-14],list(range(5))))

    def test_nonfinite_statistics_rejected(self):
        with self.assertRaises(ValueError): a.spearman([1,2,float('nan')],[1,2,3])

    def test_missing_function_interval_is_never_bridged(self):
        records=[{'donor':'HC1','days':i,'study_sample_id':str(i),'score':i*i,'function':None if i==1 else 10-i} for i in range(4)]
        rows=a.interval_rows(records)
        included=[(r['from_study_sample_id'],r['to_study_sample_id']) for r in rows if r['status']=='included']
        self.assertEqual(included,[('2','3')])
        self.assertEqual(len(rows),3)

    def test_duplicate_time_rejected(self):
        rows=[{'donor':'HC1','days':0,'study_sample_id':str(i),'score':1,'function':2} for i in range(2)]
        with self.assertRaises(ValueError): a.interval_rows(rows)

    def test_frozen_coverage_boundary_and_exact_case(self):
        genes=['G'+str(i) for i in range(125)]
        self.assertEqual(a.panel_coverage(genes,dict.fromkeys(genes[:99]))['status'],'INCONCLUSIVE')
        self.assertEqual(a.panel_coverage(genes,dict.fromkeys(genes[:100]))['status'],'PASS')
        self.assertEqual(a.panel_coverage(genes,dict.fromkeys(g.lower() for g in genes))['available_genes'],0)

    def matrix(self, folder, rows, header=None):
        p=Path(folder)/'fixture.csv.gz'
        with gzip.open(p,'wt',newline='') as stream:
            w=csv.writer(stream);w.writerow(header or ['']+['Sample_'+str(i) for i in range(1,346)]);w.writerows(rows)
        return p

    def test_exact_column_reordering_preserves_values(self):
        header=['']+['Sample_'+str(i) for i in range(345,0,-1)]
        with tempfile.TemporaryDirectory() as d:
            p=self.matrix(d,[['GENE']+list(range(345,0,-1))],header)
            result,count=a.extract_matrix(p,{'GENE'},[{'rna_column':'Sample_1'},{'rna_column':'Sample_345'}])
            self.assertEqual(result,{'GENE':{'Sample_1':'1','Sample_345':'345'}})
            self.assertEqual(count,1)

    def test_duplicate_blank_gene_and_nonfinite_matrix_reject(self):
        with tempfile.TemporaryDirectory() as d:
            for rows in [[['A']+['1']*345,['A']+['2']*345],[['']+['1']*345],[['A']+['NaN']*345]]:
                with self.subTest(rows=len(rows)):
                    with self.assertRaises(ValueError): a.extract_matrix(self.matrix(d,rows),{'A'},[{'rna_column':'Sample_1'}])

    def test_missing_or_duplicate_RNA_labels_reject(self):
        with tempfile.TemporaryDirectory() as d:
            header=['']+['Sample_2']*345
            with self.assertRaises(ValueError): a.extract_matrix(self.matrix(d,[['A']+['1']*345],header),{'A'},[{'rna_column':'Sample_1'}])
            with self.assertRaises(ValueError): a.extract_matrix(self.matrix(d,[['A']+['1']*345]),{'A'},[{'rna_column':'Sample_999'}])

    def test_wrong_sample_identity_rejects(self):
        records=a.table(a.UPSTREAM/'eligible-untreated-records.tsv')
        paired=a.table(a.UPSTREAM/'matched-records.tsv')
        a.validate_records(records,paired)
        records[0]['rna_column']='Wrong_RNA'
        with self.assertRaises(ValueError): a.validate_records(records,paired)

    def test_donor_permutation_and_leave_out_completeness(self):
        records=[{'donor':donor,'days':i,'study_sample_id':donor+str(i),'score':i*i+(-1)**i,'function':i+2*((-1)**i),'passage_number':i+1} for donor in ['HC1','HC2'] for i in range(7)]
        stats,intervals,loo=a.summarize(records)
        stats2,intervals2,loo2=a.summarize(list(reversed(records)))
        self.assertEqual(stats,stats2)
        self.assertEqual(intervals,intervals2)
        self.assertEqual(loo,loo2)
        self.assertEqual(len(loo),14)
        self.assertEqual({r['excluded_study_sample_id'] for r in loo},{r['study_sample_id'] for r in records})


if __name__=='__main__':
    unittest.main()
