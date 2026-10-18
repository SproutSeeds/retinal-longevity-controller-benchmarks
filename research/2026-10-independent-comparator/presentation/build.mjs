import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const {SKILL_DIR, DECK_WORKSPACE, DATA_DIR, RUNTIME_PYTHON} = process.env;
for (const value of [SKILL_DIR, DECK_WORKSPACE, DATA_DIR, RUNTIME_PYTHON]) {
  if (!value || !path.isAbsolute(value)) throw Error('Absolute runtime and task paths required');
}
const {resolvePresentationFont, applyPresentationChartFont, finalizePresentation} = await import(pathToFileURL(path.join(SKILL_DIR, 'container_tools/artifact_tool_utils.mjs')));
const font = resolvePresentationFont({fontFamily:'Liberation Sans'});
const output = path.join(DECK_WORKSPACE,'output'), stage = path.join(DECK_WORKSPACE,'.codex-finalizer');
await fs.mkdir(output,{recursive:true}); await fs.mkdir(stage,{recursive:true});
const read = async name => JSON.parse(await fs.readFile(path.join(DATA_DIR,name),'utf8'));
const h = await read('human-results.json'), n = await read('neural-admission.json'), s = await read('synthetic-results.json');
const base = 'https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/tree/main/research/2026-10-independent-comparator';
const C = {ink:'#142E3A',teal:'#087F83',gray:'#536671',line:'#CFDDDF',white:'#FFFFFF',amber:'#9B5D22',pale:'#EAF3F3'};
const deck = Presentation.create({slideSize:{width:1280,height:720}}), script=[];
let count=0;
function text(sl,content,x,y,w,ht,size=26,bold=false,color=C.ink) {
  const box=sl.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:ht},fill:'none',line:{fill:'none',width:0}});
  box.text=content;box.text.style={typeface:font,fontSize:size,bold,color,autoFit:'none'};return box;
}
function slide(title) {
  const sl=deck.slides.add();sl.background.fill=C.white;count++;
  text(sl,title,64,54,1152,113,42,true);
  sl.shapes.add({geometry:'rect',position:{left:64,top:654,width:1152,height:1},fill:C.line,line:{fill:'none',width:0}});
  text(sl,'Cody Mitchell / FRG · October 18, 2026 · Public-data analysis',64,670,1080,27,15,false,C.gray);
  text(sl,String(count),1174,667,40,30,18,true,C.teal);return sl;
}
function notes(sl,title,body,sources) {sl.speakerNotes.textFrame.setText(body+'\n\nSources:\n'+sources.join('\n'));script.push({title,body,sources});}
function table(sl,values,widths,y=220,hgt=290) {
  const t=sl.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:1152,height:hgt,values});
  t.columnWidths=widths;
  for(let r=0;r<values.length;r++) for(let c=0;c<values[0].length;c++) {
    const cell=t.getCell(r,c);cell.fill=r===0?C.teal:(r%2?C.pale:C.white);
    cell.text.style={typeface:font,fontSize:r===0?23:25,bold:r===0,color:r===0?C.white:C.ink};
  }
  return t;
}
{
 const sl=slide('Human expression changes depend on the endpoint');
 text(sl,'Eight libraries from one donor · four-day treatment comparison',64,171,1152,44,25,false,C.gray);
 const keys=['fibroblast_identity','cycle_panel','stress_panel','reprogramming_without_OSK_overlap'];
 const labels=['Fibroblast markers','Cell cycle','Stress','Reprogramming*'];
 const values=[['Panel','OSK\nCPM','OSK\nmedian ratio','O4YRSK\nCPM','O4YRSK\nmedian ratio']];
 keys.forEach((key,i)=>{const vals=[];for(const c of ['OSK','O4YRSK'])for(const method of ['log2_cpm','log2_median_ratio_cpm_equivalent']) {
   const v=h.contrasts.find(r=>r.construct===c&&r.panel===key).methods[method].mean_difference;vals.push((v>0?'+':'')+v.toFixed(3));
 }values.push([labels[i],...vals]);});
 table(sl,values,[360,180,216,180,216],227,305);
 text(sl,'OSK stress reverses direction under the normalization sensitivity.',64,553,1140,43,27,true,C.amber);
 text(sl,'Mean log-expression differences. *POU5F1 and SOX2 excluded. No young or recovery arm.',64,605,1140,37,21,false,C.gray);
 notes(sl,'Human expression comparison','I analyzed the eight human libraries under a fixed contract. All 46 predefined marker genes were present. Fibroblast markers decreased, while cycle and reprogramming markers increased under both normalization methods. The OSK stress score changed direction between methods. That makes a simple stress-benefit interpretation unreliable. The reprogramming row excludes POU5F1 and SOX2 because the treatment introduces those factors. These are descriptive expression changes from one donor. They do not establish rejuvenation, identity preservation or safety. The public report includes the full panel and every sensitivity.',[base+'/human-results.json','https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297233','https://doi.org/10.1016/j.cell.2025.07.031']);
}
{
 const sl=slide('A mouse neural dataset retains seven animal identities');
 text(sl,'3,857 cells · 31,057 RNA genes · three multiplexed libraries',64,175,1152,48,29,true,C.teal);
 const groups=[['old','2Dox0','Old treated'],['old','untr','Old untreated'],['young','untr','Young untreated']];
 const values=[['Cohort-2 group','Animals','Cells'],...groups.map(([age,treatment,label])=>{const r=n.group_counts.find(r=>r.age===age&&r.treatment===treatment);return [label,String(r.animals),r.cells.toLocaleString('en-US')];})];
 table(sl,values,[680,236,236],246,236);
 text(sl,'The deposited subset contains no withdrawal samples.\nBoth young animals occur in lane 3; 70 cells have unresolved cluster labels.',64,512,1152,82,27);
 text(sl,'Admission complete. Animal-level expression testing is the next step.',64,607,1152,35,23,true,C.teal);
 notes(sl,'Neural data admission','I verified the deposited mouse neural object against its repository checksum, raw count columns and the authors’ animal map. The seven animals include two old treated, three old untreated and two young untreated mice. The deposited subset omits all withdrawal samples. Both young animals occur in lane three, which limits age comparisons. Four numeric clusters totaling seventy cells still lack biological labels. This pass verifies that an animal-level analysis is possible. I have not yet run neural expression contrasts. The next contract will keep expression within a cell type separate from changes in the mix of recovered cells.',[base+'/neural-admission.json',base+'/NEURAL_NEXT.md','https://doi.org/10.1038/s43587-024-00594-3','https://doi.org/10.5281/zenodo.10626910']);
}
{
 const sl=slide('Balanced donors improve repeat detection in the simulation');
 const rows=s.scenarios.filter(r=>r.prevalence===.01&&r.latent_donor_correlation===.05&&r.specificity===1);
 const ch=sl.charts.add('bar',{position:{left:64,top:187,width:800,height:350},categories:['3 balanced','3 imbalanced','6 balanced','6 imbalanced'],
  series:[{name:'At least one donor',values:rows.map(r=>Number((100*r.any_donor_flagged).toFixed(3))),fill:C.teal},{name:'At least two donors',values:rows.map(r=>Number((100*r.two_or_more_donors_flagged).toFixed(3))),fill:'#647B38'}],
  barOptions:{direction:'column',grouping:'clustered',gapWidth:85},hasLegend:true,
  xAxis:{textStyle:{fontSize:18,fill:C.gray}},yAxis:{min:0,max:100,numberFormatCode:'0',textStyle:{fontSize:18,fill:C.gray}},
  dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0',textStyle:{fontSize:19,fill:C.ink}},chartFill:C.white,plotAreaFill:C.white});
 applyPresentationChartFont(ch,{fontFamily:font});
 text(sl,'1,200 cells\n\nAssumed prevalence: 1%\nSensitivity: 80%\nSpecificity: 100%\nDonor correlation: 0.05',902,198,310,280,24);
 text(sl,'Synthetic only',902,520,310,45,28,true,C.amber);
 text(sl,'Probability of flags (%). With no true states and 99.9% specificity, six balanced donors\nstill produce a 29.9% chance of flags in two donors under independent errors.',64,579,1150,65,23,false,C.gray);
 notes(sl,'Synthetic donor balance','The simulation keeps the total at twelve hundred cells. Under the displayed hypothetical assumptions, balanced sampling across six donors yields about a sixty-eight percent chance of flags in at least two donors. An imbalanced six-donor allocation yields about forty-two percent. Requiring two donors reduces false alarms, but it also loses sensitivity. With no true unusual states and ninety-nine point nine percent specificity, the balanced design still has about a thirty percent chance of two flagged donors when errors are independent. The detector needs empirical calibration. These simulations guide analysis design; they do not create biological observations or establish a sample size.',[base+'/synthetic-results.json',base+'/METHODS.md']);
}
{
 const sl=slide('The next analysis and the remaining measurement');
 const rows=[['Next computation','Animal-level neural expression and composition, with lane sensitivity and a cohort-1 replication audit.'],
             ['Pending source inputs','Reconcile clock, sample and guide metadata when the requested artifacts arrive.'],
             ['Biological gap','Matched late human identity, calibrated unusual-state detection, withdrawal stability and trajectory continuity.']];
 rows.forEach((row,i)=>{const y=204+i*116;text(sl,row[0],64,y,330,52,28,true,C.teal);text(sl,row[1],415,y,795,90,27);});
 text(sl,'All four readouts remain insufficient_signal. Experiment replacement: INCONCLUSIVE.',64,566,1150,64,25,true,C.amber);
 notes(sl,'Next analysis and remaining measurement','There is useful computational work to do while the metadata requests are pending. The next task is an animal-level neural comparison with a separate frozen contract, followed by an audit of the independent cohort. The larger gap remains a matched late human measurement that connects identity, unusual states and recovery after withdrawal. Public data may still reduce that collection. The existing thirty-three-library feasibility proposal and fifty-seven-library full design remain conditional funding plans, not validated sample-size recommendations. No paid compute or wet-lab work was purchased or arranged in this pass.',[base+'/NEXT_STEPS.md',base+'/CLAIM.md','https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/blob/main/research/2026-10-public-data/MEASUREMENT_PLAN.md']);
}
const candidatePath=path.join(stage,'candidate.pptx');await (await PresentationFile.exportPptx(deck)).save(candidatePath);
const finalPath=path.join(output,'retinal-comparator-update.pptx');
await finalizePresentation({workspaceDir:DECK_WORKSPACE,candidatePath,finalPath,pythonExecutable:RUNTIME_PYTHON,
 integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','1','--require-native-table-slide','2'],
 explicitTotalSlideCount:4,requiredNativeTableOwnerSlides:[1,2],requiredNativeChartOwnerSlides:[3],
 materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(stage,'validation.json')});
const narration=script.map((r,i)=>`${i+1}. ${r.title}\n\n${r.body}`).join('\n\n')+'\n';
await fs.writeFile(path.join(output,'spoken-notes.txt'),narration);
await fs.writeFile(path.join(output,'spoken-notes.md'),narration);
await fs.writeFile(path.join(output,'slide-sources.json'),JSON.stringify(script.map((r,i)=>({slide:i+1,title:r.title,sources:r.sources})),null,2)+'\n');
console.log(JSON.stringify({finalPath,slides:count,font}));
