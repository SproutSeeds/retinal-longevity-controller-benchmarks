import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const {SKILL_DIR, DECK_WORKSPACE, DATA_DIR, RUNTIME_PYTHON} = process.env;
for (const v of [SKILL_DIR, DECK_WORKSPACE, DATA_DIR, RUNTIME_PYTHON]) {
  if (!v || !path.isAbsolute(v)) throw Error('Absolute runtime and task paths required');
}
const {resolvePresentationFont, applyPresentationChartFont, finalizePresentation} = await import(
  pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')));
const font=resolvePresentationFont({fontFamily:'Liberation Sans'});
const output=path.join(DECK_WORKSPACE,'output'), stage=path.join(DECK_WORKSPACE,'.codex-finalizer');
await fs.mkdir(output,{recursive:true}); await fs.mkdir(stage,{recursive:true});
const read=async f=>JSON.parse(await fs.readFile(path.join(DATA_DIR,f),'utf8'));
const bulk=await read('bulk/results.json'), human=await read('human/marker-audit.json');
const cross=await read('analysis/cross-cohort-results.json'), cell=await read('human/percell/results.json');
const decomp=await read('decomposition/results.json');
const base='https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/tree/main/research/2026-10-neural-validation';
const C={ink:'#142E3A',teal:'#087F83',gray:'#536671',amber:'#9B5D22',pale:'#EAF3F3',white:'#FFFFFF'};
const deck=Presentation.create({slideSize:{width:1280,height:720}}), narration=[];
function text(s,t,x,y,w,h,size=27,bold=false,color=C.ink){
  const b=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  b.text=t;b.text.style={typeface:font,fontSize:size,bold,color,autoFit:'none'};return b;
}
function slide(title){
  const s=deck.slides.add();s.background.fill=C.white;
  text(s,title,64,48,1152,110,42,true);
  text(s,'Cody Mitchell / FRG   October 18, 2026   Public-data reanalysis',64,672,1152,28,16,false,C.gray);
  return s;
}
function notes(s,title,body,sources){
  s.speakerNotes.textFrame.setText(body+'\n\nSources:\n'+sources.join('\n'));
  narration.push({title,body,sources});
}
function table(s,values,widths,y,height){
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:1152,height,values});
  t.columnWidths=widths;
  for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
    const z=t.getCell(r,c);z.fill=r===0?C.teal:(r%2?C.pale:C.white);
    z.text.style={typeface:font,fontSize:24,bold:r===0,color:r===0?C.white:C.ink};
  }return t;
}
function chart(s,categories,series,{y=208,height=350,min,max,grouping='clustered',format='0.00'}={}){
  series=series.map(row=>({...row,values:row.values.map(v=>Number(v.toFixed(8)))}));
  const ch=s.charts.add('bar',{position:{left:64,top:y,width:1152,height},categories,series,
    barOptions:{direction:'column',grouping,gapWidth:90},hasLegend:series.length>1,
    xAxis:{tickLabelPosition:'low',textStyle:{fontSize:21,fill:C.gray}},
    yAxis:{...(min===undefined?{}:{min}),...(max===undefined?{}:{max}),numberFormatCode:format,textStyle:{fontSize:20,fill:C.gray}},
    dataLabels:{showValue:true,position:grouping==='stacked'?'center':'outEnd',numberFormatCode:format,textStyle:{fontSize:20,fill:C.ink}},
    chartFill:C.white,plotAreaFill:C.white});
  applyPresentationChartFont(ch,{fontFamily:font});return ch;
}
const signed=(x,n=3)=>(x>=0?'+':'')+x.toFixed(n);
{
 const s=slide('Cell-cycle scores fall in all nine donor pairs');
 const r=bulk.panel_results.find(x=>x.method==='log2_cpm'&&x.panel==='cycle_panel');
 text(s,'Mouse neural cultures after 18 hours of Dox/OSKM exposure',64,165,1152,50,28,false,C.gray);
 chart(s,r.scores.map(x=>x.donor_id),[{name:'Paired cycle-panel difference',values:r.scores.map(x=>x.delta),fill:C.teal}],{y:225,height:310,min:-.4,max:0,format:'0.00'});
 text(s,'Every donor retains the negative direction under median-ratio and rank scoring.',64,555,1152,65,28,true,C.teal);
 text(s,'Mean log2(1 + CPM) score differences. The age contrast depends on the scoring method.',64,625,1152,34,23,false,C.gray);
 notes(s,'Nine paired neural donors','I compared treated and untreated cultures from nine independent mouse donors at the only timepoint with complete age and treatment groups. The cell-cycle panel decreased in every donor under all three scoring methods, and every single-gene omission retained that direction. The secondary sign-test Holm value is 0.015625. The primary CPM age contrasts pass the four-panel Holm rule, while rank scoring weakens them and reverses the stress contrast. These are acute transcriptional responses. They do not identify rejuvenation, functional arrest or a causal effect of age. The well layout differs across groups, and its relation to preparation order is unknown.',[base+'/bulk/results.json',base+'/bulk/RESULTS.md','https://doi.org/10.1038/s43587-024-00594-3','https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE245385']);
}
{
 const s=slide('Microglial cell-cycle means agree across cohorts');
 const r=cross.comparisons.find(x=>x.celltype==='Microglia'&&x.panel_name==='cycle_panel'&&x.support_tier==='primary_support');
 text(s,'Individual animal omissions expose the limit of that agreement',64,165,1152,60,29,true,C.amber);
 const rows=[['Mouse cohort','Full CPM mean','Omit one animal'],...['cohort2','cohort1'].map((k,i)=>{
   const a=r[k+'_direction_details'].log2_cpm;return [i===0?'Cohort 2':'Cohort 1',signed(a.mean_difference),a.animal_omission_range.map(x=>signed(x)).join(' to ')];})];
 table(s,rows,[400,300,452],260,226);
 text(s,'Cohort 1 can reverse direction when one animal is removed.',64,526,1152,56,30,true,C.amber);
 text(s,'Two treated and two control animals per primary comparison. Omission ranges are descriptive.',64,596,1152,58,24,false,C.gray);
 notes(s,'Animal sensitivity across cohorts','The mouse tissue analysis gives a negative mean microglial cell-cycle score in both cohorts. Cohort two retains a negative sign under animal omission, although one omission falls below the descriptive effect floor. Cohort one has a smaller mean and changes sign when either of two influential animals is omitted. Agreement between means therefore falls short of robust agreement across animals. The cohorts come from the same study and differ in age, sex composition and sequencing chemistry. The complete report retains every eligible cell type and all failed support checks. This comparison is separate from the nine-donor cultured neural result.',[base+'/analysis/ANALYSIS.md',base+'/analysis/cross-cohort-results.json','https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE224438']);
}
{
 const s=slide('CD24 supplies most of the human bulk score change');
 const rows=['OSK','O4YRSK'].map(c=>human.contrasts.find(x=>x.construct===c&&x.method==='log2_cpm'&&x.panel==='reprogramming_without_OSK_overlap'));
 const parts=rows.map(r=>r.gene_details.find(g=>g.gene==='CD24').additive_contribution);
 text(s,'Seven fixed markers after excluding POU5F1 and SOX2',64,165,1152,50,28,false,C.gray);
 chart(s,['OSK','O4YRSK'],[{name:'CD24 contribution',values:parts,fill:C.teal},{name:'Other six genes combined',values:rows.map((r,i)=>r.mean_difference-parts[i]),fill:'#B3C9CD'}],{y:228,height:320,min:0,max:.7,grouping:'stacked',format:'0.000'});
 text(s,'CD24 contributes 80–90% across the two original normalizations.',64,566,1152,52,30,true,C.teal);
 text(s,'One donor, eight libraries. This score does not establish a calibrated pluripotent state.',64,622,1152,37,24,false,C.gray);
 notes(s,'Human marker concentration','The original human bulk arithmetic reproduces. The interpretation needed a narrower description. CD24 contributes about eighty to ninety percent of the signed seven-gene panel difference, depending on construct and normalization. Removing CD24 preserves the group mean sign, but individual library comparisons can reverse. The raw matrix also distinguishes absent features from genes present with sparse or zero counts. Low RNA detection does not establish that a biological network is off. I preserved the earlier numerical files and added this correction with every gene contribution.',[base+'/human/ADDENDUM.md',base+'/human/gene-contributions.csv','https://doi.org/10.1016/j.cell.2025.07.031','https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297233']);
}
{
 const s=slide('Human co-detection fractions depend on UMI depth');
 text(s,'Day 7: at least two of five endogenous markers in the same barcode',64,164,1152,65,28,false,C.gray);
 const get=(d,v)=>cell.sample_variant_results.find(x=>x.donor===d&&x.day===7&&x.variant===v);
 const values=[['Detection definition','GM00731','GM23815']];
 for(const [label,variant] of [['At least 1 UMI per marker','primary'],['At least 2 UMIs per marker','endogenous_min2_umi'],['1,000-UMI thinning, seed 181026','thin1000_seed181026']]){
   values.push([label,...['GM00731','GM23815'].map(d=>{const r=get(d,variant);return `${r.coexpression_at_least_two_count}/${r.n_retained}\n${(100*r.coexpression_at_least_two_fraction).toFixed(2)}%`;})]);
 }
 table(s,values,[590,281,281],250,290);
 text(s,'57,317 observed barcodes across two donors and four collection times.',64,562,1152,49,28,true,C.teal);
 text(s,'All 22 sensitivity definitions are reported. These are marker observations without an age comparison.',64,616,1152,45,23,false,C.gray);
 notes(s,'Joint human marker observations','I separately measured endogenous-marker co-detection and fibroblast-marker expression in two donors over four timepoints. The primary joint identity-low and co-detection fractions at day seven are 11.74 percent and 22.01 percent. The table shows co-detection alone and its measurement sensitivity. Requiring two UMIs per marker reduces the observed fractions. Equalizing eligible cells to one thousand UMIs reduces them further and changes the retained denominator. Three seeded thinning repetitions and every predefined sensitivity remain in the report. These are different cells at each timepoint, with one donor at each age. They do not provide a true rare-state prevalence, an age-effect estimate or controlled withdrawal evidence.',[base+'/human/percell/REPORT.md',base+'/human/percell/results.json','https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297234']);
}
{
 const s=slide('Composition can oppose within-type changes');
 const r=decomp.results.find(x=>x.panel==='stress_panel'&&x.cell_floor===20&&x.scale===10000).equal_lane_mean;
 text(s,'Conditional stress-panel summary in the two admitted mouse cell types',64,166,1152,60,27,false,C.gray);
 chart(s,['Composition','Within type','Total'],[{name:'Mean per-cell log-expression difference',values:[r.composition,r.within_type,r.total],fill:C.teal}],{y:235,height:295,min:-.02,max:.015,format:'0.000'});
 text(s,`Symmetric partition (rounded): ${r.composition.toFixed(6)} + ${r.within_type.toFixed(6)} = ${r.total.toFixed(6)}.`,64,554,1152,62,28,true,C.teal);
 text(s,'Common support retains 58.8–68.1% of each animal’s recovered cells. Algebraic attribution is descriptive.',64,617,1152,44,22,false,C.gray);
 notes(s,'Conditional composition decomposition','I separated the conditional per-cell average into composition and within-type terms under a frozen symmetric formula. In the stress panel those terms oppose each other. The primary support includes Microglia and Oligodendrocyte and retains roughly fifty-nine to sixty-eight percent of each animal’s recovered cells. This exact identity concerns a different summary from pseudobulk. It does not identify causal tissue-composition changes. Named-type mixtures, detection depth and selection into support remain relevant. The public extension reports both one-sided conventions, gene contributions and a separate depth sensitivity.',[base+'/decomposition/README.md',base+'/decomposition/results.json',base+'/decomposition/EXTENSION.md']);
}
{
 const s=slide('Existing sequenced samples are the next data target');
 text(s,'Seven omitted mouse samples',64,182,1152,55,34,true,C.teal);
 text(s,'The published sample table lists them. The shared objects lack the complete cell-to-animal assignments. Five carry a withdrawal label whose exact endpoint timing still needs confirmation.',64,247,1152,133,29);
 text(s,'The decisive human measurement remains open',64,407,1152,56,34,true,C.amber);
 text(s,'Recover compatible existing data first. Then evaluate matched late identity and age, unusual-state detection and stability after factor withdrawal.',64,474,1152,101,29);
 text(s,'All four CX004 readouts remain insufficient_signal. The conditional funding plan specifies the remaining observations.',64,600,1152,60,24,false,C.gray);
 notes(s,'Existing-data recovery and the next decision','The most concrete recovery target is a complete barcode-to-animal map or the prefilter objects for seven already-sequenced samples. Five have a withdrawal label, but exact removal and harvest timing still need source confirmation. The current raw inventory does not provide verified assignments for them. Recovering those observations could improve the mouse comparison without commissioning another experiment. It would still leave the matched late human and ocular measurement to establish. The public funding plan already describes a conditional feasibility collection and the full timing design. Synthetic data can test software, detection assumptions and sampling choices. They cannot supply the missing biological outcome. No wet-lab operations were purchased or arranged.',[base+'/recovery/missing-inputs.json',base+'/NEXT_STEPS.md','https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/blob/main/research/2026-10-public-data/MEASUREMENT_PLAN.md']);
}
const candidatePath=path.join(stage,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidatePath);
const finalPath=path.join(output,'retinal-validation-results.pptx');
await finalizePresentation({workspaceDir:DECK_WORKSPACE,candidatePath,finalPath,pythonExecutable:RUNTIME_PYTHON,
 integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','2','--require-native-table-slide','4'],
 explicitTotalSlideCount:6,requiredNativeTableOwnerSlides:[2,4],requiredNativeChartOwnerSlides:[1,3,5],
 materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(stage,'validation.json')});
const spoken=narration.map((r,i)=>`${i+1}. ${r.title}\n\n${r.body}`).join('\n\n')+'\n';
await fs.writeFile(path.join(output,'spoken-notes.txt'),spoken);
await fs.writeFile(path.join(output,'spoken-notes.md'),spoken);
await fs.writeFile(path.join(output,'slide-sources.json'),JSON.stringify(narration.map((r,i)=>({slide:i+1,title:r.title,sources:r.sources})),null,2)+'\n');
console.log(JSON.stringify({finalPath,slides:narration.length,font}));
