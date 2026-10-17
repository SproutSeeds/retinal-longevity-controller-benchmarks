import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';

// Run with the bundled presentation runtime. README documents environment paths.
const {SKILL_DIR,DECK_WORKSPACE,DATA_DIR,RUNTIME_PYTHON}=process.env;
for(const v of [SKILL_DIR,DECK_WORKSPACE,DATA_DIR,RUNTIME_PYTHON])if(!v||!path.isAbsolute(v))throw Error('Absolute runtime and workspace paths required');
const {resolvePresentationFont,applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')));
const font=resolvePresentationFont({fontFamily:'Liberation Sans'});
const out=path.join(DECK_WORKSPACE,'output'),stage=path.join(DECK_WORKSPACE,'.codex-finalizer');
await fs.mkdir(out,{recursive:true});await fs.mkdir(stage,{recursive:true});
const read=async name=>JSON.parse(await fs.readFile(path.join(DATA_DIR,name),'utf8'));
const g=await read('paired-guide-results.json'),m=await read('donor-model-results.json'),s=await read('clustered-sampling-results.json');
const repo='https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks';
const evidence=repo+'/tree/main/research/2026-10-public-data';
const C={ink:'#142E3A',teal:'#087F83',gray:'#536671',pale:'#EAF3F3',line:'#CFDDDF',white:'#FFFFFF',amber:'#9B5D22'};
const p=Presentation.create({slideSize:{width:1280,height:720}}),script=[];
let slideCount=0;
function txt(sl,text,x,y,w,h,size=27,bold=false,color=C.ink){
 const box=sl.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 box.text=text;box.text.style={typeface:font,fontSize:size,bold,color,autoFit:'none'};return box;
}
function rect(sl,x,y,w,h,fill){return sl.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});}
function slide(title,kicker='PUBLIC DATA · OCTOBER 2026'){
 const sl=p.slides.add();sl.background.fill=C.white;slideCount++;
 txt(sl,kicker,64,31,1080,28,16,true,C.teal);txt(sl,title,64,82,1152,102,42,true);
 rect(sl,64,654,1152,1,C.line);txt(sl,'FRG / SproutSeeds  ·  Computational findings; biological claims remain Heuristic',64,668,1070,27,14,false,C.gray);
 txt(sl,String(slideCount).padStart(2,'0'),1165,665,50,30,18,true,C.teal);return sl;
}
function notes(sl,title,body,urls=[]){sl.speakerNotes.textFrame.setText(body+'\n\nSources:\n'+urls.join('\n'));script.push({title,body,sources:urls});}
function chart(sl,categories,values,{x=64,y=205,w=720,h=380,max,format='0',inside=false}={}){
 const ch=sl.charts.add('bar',{position:{left:x,top:y,width:w,height:h},categories,
  series:[{name:'Computed result (rounded for display)',values:values.map(n=>Number(n.toFixed(3))),valuesFormatCode:format,fill:C.teal}],barOptions:{direction:'column',grouping:'clustered',gapWidth:100},hasLegend:false,
  xAxis:{textStyle:{fontSize:20,fill:C.gray}},yAxis:{min:0,max,numberFormatCode:format,textStyle:{fontSize:18,fill:C.gray}},
  dataLabels:{showValue:true,position:inside?'inEnd':'outEnd',numberFormatCode:format,textStyle:{fontSize:25,fill:inside?C.white:C.ink,bold:true}},chartFill:C.white,plotAreaFill:C.white});
 applyPresentationChartFont(ch,{fontFamily:font});return ch;
}

{
 const sl=slide('Retinal longevity\nand the recovery measurement','FRACTAL RESEARCH GROUP / SPROUTSEEDS');
 txt(sl,'What public data can answer now,\nand what a future experiment must add.',64,240,1080,110,35,false,C.gray);
 txt(sl,'Reproducible research + conditional funding package',64,405,1100,55,29,true,C.teal);
 txt(sl,'Cody Mitchell  ·  October 17, 2026',64,530,1050,42,24);
 notes(sl,'Retinal longevity and the recovery measurement','We want to understand whether a reprogramming response can preserve adult cell identity and recover after the factors are withdrawn. I have expanded the public-data analysis, corrected assumptions against the source methods, and packaged the remaining measurement gap. The current work supports a more precise research plan. It does not establish a retinal therapy.',[repo,evidence]);
}
{
 const sl=slide('Four questions still need a matched observation');
 const rows=[['Late identity','Which age-positive human cells retain adult identity?'],['Rare states','What unusual states occur, and can we detect them reliably?'],['Recovery','What remains after withdrawal and longer follow-up?'],['Continuity','Can a common measured trajectory connect the late windows?']];
 rows.forEach((r,i)=>{const y=205+i*94;txt(sl,String(i+1),64,y,48,42,30,true,C.teal);txt(sl,r[0],130,y,245,44,29,true);txt(sl,r[1],400,y,810,72,25);});
 txt(sl,'Current verdict for each: insufficient_signal',130,590,1080,38,24,true,C.amber);
 notes(sl,'Four questions','The benchmark separates late identity, unusual states, recovery and continuity. The inspected public sources give us pieces of those answers across different experiments. They do not yet provide the matched late human trajectory needed to resolve all four. Combining unrelated files cannot create that missing observation.',[evidence+'/source-resolution.json']);
}
{
 const sl=slide('Existing data reduce what we need to collect');
 const rows=[['Human perturbations','36,514 cells; guide assignments reconstructed and audited'],['Human recovery','Three-donor SRSF1 diagnostic; earlier bulk recovery comparators'],['Ocular measurements','Mouse RPE sensitivity analysis; exact clock replay still pending'],['Observed withdrawal','Mouse liver factor-off data; useful within its own biological scope']];
 rows.forEach((r,i)=>{const y=202+i*94;txt(sl,r[0],64,y,335,54,29,true,C.teal);txt(sl,r[1],425,y,775,78,26);});
 txt(sl,'Original experiments retain their authorship. Our work is reanalysis and evidence evaluation.',64,596,1135,43,21,false,C.gray);
 notes(sl,'Public-data foundation','The source teams have already generated valuable observations. Our contribution is to make those observations usable under explicit rules, test what the analyses actually show, and preserve the limits. Human fibroblasts, mouse liver and retinal pigment epithelium remain separate biological systems. The source audit includes ten priority resources and the specific missing inputs for each.',[evidence+'/SOURCE_AUDIT.md']);
}
{
 const sl=slide('The paired-guide design changes the analysis');
 chart(sl,['Earlier rule','Paired primary'],[97,g.variants[0].tested_perturbations]);
 txt(sl,'208',850,208,340,100,76,true,C.teal);txt(sl,'eligible comparisons',850,310,350,45,27,true);
 txt(sl,'Both targeting guides count.\n\nEZH2 moves toward zero.\nE2F3 fails the expected target-direction check.',850,382,350,195,25);
 txt(sl,'Comparisons require ≥20 target and ≥20 matched NT cells. Reconstructed assignments.',64,599,1145,45,21,false,C.gray);
 notes(sl,'Guide correction','Recovering the supplementary methods changed a key assumption. The vectors contain two targeting guides, so our earlier single-guide dominance rule discarded intended paired-guide cells. The revised primary rule produces 208 eligible comparisons, compared with 97 under our earlier rule. This increases usable comparisons, not independent donors. The EZH2 signal moves close to zero, and the E2F3 expression-direction check fails. Exact replication still needs the original assignment table and control-vector pair map.', ['https://doi.org/10.1073/pnas.2515183123','https://doi.org/10.6084/m9.figshare.30898748',evidence+'/paired-guide-results.json']);
}
{
 const sl=slide('The ocular endpoint needs to be named precisely');
 txt(sl,'+0.663 to +0.694',64,207,1130,100,66,true,C.teal);
 txt(sl,'Broad expression correlation across six fixed sensitivities',64,323,1130,56,29,true);
 txt(sl,'Our calculation: gene-wise age and OSK contrasts.\n\nSource study: a fitted transcriptomic clock with specific preprocessing.\n\nExact clock, imputation references and animal/cohort mapping remain prerequisites.',64,410,1110,192,27);
 notes(sl,'Ocular endpoint','The mouse RPE correlation stays positive across the declared sensitivities. The recovered full text clarifies that the authors used a fitted clock with different preprocessing. Our broad expression correlation is a different endpoint, so it cannot establish whether their clock result replicates. We need the historical fitted model, reference inputs and exact animal and cohort mapping. These expression matrices also do not independently reproduce vision outcomes.', ['https://doi.org/10.1101/2025.08.30.673239','https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE304044',evidence+'/ocular-sensitivity-results.json']);
}
{
 const sl=slide('A model recognizes treatment in held-out donors');
 chart(sl,['Expression','No cycle','Depth only'],['expression','expression_without_cycle','depth_only'].map(k=>m.variants[k].mean_donor_AUROC),{max:1,format:'0.00',inside:true});
 txt(sl,'3 donors',850,217,355,66,49,true,C.teal);txt(sl,'12 repeated libraries\nTwo donors train; one tests.',850,310,355,96,27);
 txt(sl,'Treatment recognition\n\nExperimental batch is missing.\nNo independent study test.',850,435,355,160,25);
 txt(sl,'Mean held-donor AUROC. Balanced label controls average 0.50. Benefit and safety remain unmeasured.',64,600,1150,45,20,false,C.gray);
 notes(sl,'Treatment-recognition model','The fixed-panel model separates SRSF1 from its control in each of three held-out donors. Its observed AUROC is one, while depth and detected genes alone reach about 0.83. There are only three donors and repeated libraries, with experimental batch unrecorded. The result is a treatment-recognition diagnostic. It does not quantify rejuvenation, and it does not justify scaling into a large intervention model without a compatible independent study.', ['https://www.nature.com/articles/s43587-026-01234-8',evidence+'/MODEL_CARD.md']);
}
{
 const sl=slide('More donors change rare-state detection');
 const rows=s.scenarios.filter(r=>r.prevalence===.01&&r.latent_donor_ICC===.05).sort((a,b)=>a.donors-b.donors);
 chart(sl,rows.map(r=>r.donors+' donor'+(r.donors>1?'s':'')),rows.map(r=>100*r.probability_at_least_one_detected),{max:100,format:'0'});
 txt(sl,'1,200 cells',850,211,355,62,44,true,C.teal);
 txt(sl,'Same total in each scenario\n\nAssumed prevalence: 1%\nSensitivity: 80%\nLatent donor correlation: 0.05',850,301,355,215,25);
 txt(sl,'Synthetic only',850,553,355,45,27,true,C.amber);
 txt(sl,'Chance of ≥1 true detection (%). Hypothetical assumptions; detector false positives also need calibration.',64,600,1150,45,20,false,C.gray);
 notes(sl,'Synthetic sampling','These are synthetic sampling scenarios, kept separate from biological data. At the same total of 1,200 cells, the chance of detecting at least one true state rises from about 53 percent with one donor to 81 percent with three and 92 percent with six under the displayed assumptions. The assumptions are hypothetical. The exercise shows why cell count alone is an incomplete sampling justification and why detector sensitivity and specificity both need calibration.',[evidence+'/clustered-sampling-results.json']);
}
{
 const sl=slide('Public withdrawal data exist — in another system');
 txt(sl,'Mouse liver: one day on, one day off',64,205,1120,65,36,true,C.teal);
 txt(sl,'16,042',64,320,345,100,66,true);txt(sl,'deposited barcodes',64,427,345,50,25);
 txt(sl,'2,288',452,320,345,100,66,true);txt(sl,'source-QC sensitivity',452,427,345,50,25);
 txt(sl,'2,284',840,320,345,100,66,true);txt(sl,'paper-reported cells',840,427,345,50,25);
 txt(sl,'Four-cell QC discrepancy remains. Early mouse liver data do not establish late human or retinal recovery.',64,550,1120,75,27,false,C.gray);
 notes(sl,'Observed withdrawal comparator','The mouse liver archive supplies an actual observed factor-off endpoint. The deposited files have 16,042 nonempty barcodes. Our post hoc interpretation of the paper’s count and mitochondrial filters retains 2,288, close to the reported 2,284. The exact four-cell discrepancy remains unresolved. This is a useful observed comparator and software fixture, with a different species, tissue and recovery duration from the human question.', ['https://doi.org/10.1016/j.celrep.2022.110730','https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE144600',evidence+'/liver-withdrawal-results.json']);
}
{
 const sl=slide('A focused pilot keeps the three comparisons');
 const values=[['Day','Reference','Induced / continued','Withdrawal'],['0','1 shared baseline','—','—'],['17','1','1 before branching','—'],['20','1','1','1'],['28','1','1','1'],['35','1','—','1']];
 const t=sl.tables.add({rows:6,columns:4,left:64,top:200,width:1150,height:305,columnWidths:[150,330,340,330],values});
 for(let r=0;r<6;r++)for(let c=0;c<4;c++){const cell=t.getCell(r,c);cell.fill=r===0?C.teal:(r%2===0?C.pale:C.white);cell.text.style={typeface:font,fontSize:23,bold:r===0,color:r===0?C.white:C.ink};}
 txt(sl,'11 libraries per donor × 3 donors = 33',64,542,1120,55,34,true,C.teal);
 txt(sl,'Proposed D17 branch. Feasibility and donor count require experimental partner review.',64,605,1130,35,20,false,C.gray);
 notes(sl,'Conditional pilot','The proposed focused pilot retains untreated references, continued exposure and withdrawal. A shared baseline and a common induced condition before a proposed day-17 branch give eleven biological collections per donor. With three donors that is 33 single-cell libraries. Three donors are a feasibility starting point, not a power calculation. The intervention, branch timing, assay calibration, culture replicates and donor requirements need review by a qualified experimental partner before execution.',[evidence+'/MEASUREMENT_PLAN.md',evidence+'/budget-quantities.json']);
}
{
 const sl=slide('Fund the missing observation in stages');
 const rows=[['First','Recover metadata and assess compatible banked material.'],['33 libraries','Focused feasibility pilot; estimate donor variance and assay performance.'],['57 libraries','Full nine-timepoint ladder, including four earlier reference/induced pairs.'],['Then','Longer recovery and a separate retinal/RPE functional bridge, if justified.']];
 rows.forEach((r,i)=>{const y=205+i*91;txt(sl,r[0],64,y,300,49,30,true,C.teal);txt(sl,r[1],395,y,810,76,26);});
 txt(sl,'Partner, calibrated endpoints and real quotes are pending. No wet-lab work has been purchased or arranged.',64,594,1140,48,21,false,C.gray);
 notes(sl,'Funding sequence','The first request is for reusable metadata and compatible existing material. If the joint measurement gap remains, the focused pilot would estimate feasibility and donor variation. Adding four earlier timepoints with reference and induced conditions brings the full ladder to 57 libraries. Longer follow-up is a separate extension. A retinal or RPE functional bridge is also a distinct study. The package contains budget quantities and deliverables; actual quotes, a named partner and appropriate review are still required. No wet-lab work has been purchased or arranged.',[evidence+'/MEASUREMENT_PLAN.md']);
}
{
 const sl=slide('A public result others can inspect and extend');
 txt(sl,'Code · source hashes · measured results · model card\nSynthetic assumptions · failed paths · funding design',64,212,1130,126,33,true,C.teal);
 txt(sl,'75 computational checks + 12 scientific failure-case tests\n\nAll four biological readouts remain open.\n\nThe most useful next contribution is the exact missing dataset or metadata.',64,388,1120,195,28);
 txt(sl,'github.com/SproutSeeds/retinal-longevity-controller-benchmarks',64,600,1150,40,22,true,C.teal);
 notes(sl,'Public review and next evidence','The public repository includes executable analysis, source hashes, numerical results, model limitations, synthetic assumptions and the conditional measurement plan. The 75 checks and twelve failure-case tests establish the stated computational properties. The four biological readouts remain open. A contributor can change that decision by supplying the exact missing observation, resolving source metadata or demonstrating a reproducible error. The next funding discussion can therefore focus on the measurement that would materially advance the project.',[repo,evidence+'/NEXT_STEPS.md']);
}

const candidatePath=path.join(stage,'candidate-v2.pptx');await (await PresentationFile.exportPptx(p)).save(candidatePath);
const finalPath=path.join(out,'retinal-public-data-v2.pptx');
const receipt=await finalizePresentation({workspaceDir:DECK_WORKSPACE,candidatePath,finalPath,pythonExecutable:RUNTIME_PYTHON,
 integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','9'],
 explicitTotalSlideCount:11,requiredNativeTableOwnerSlides:[9],requiredNativeChartOwnerSlides:[4,6,7],
 materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(stage,'validation-v2.json')});
await fs.writeFile(path.join(out,'spoken-notes.txt'),script.map((r,i)=>`${i+1}. ${r.title}\n\n${r.body}`).join('\n\n')+'\n');
await fs.writeFile(path.join(out,'spoken-notes.md'),script.map((r,i)=>`${i+1}. ${r.title}\n\n${r.body}`).join('\n\n')+'\n');
await fs.writeFile(path.join(out,'slide-sources.json'),JSON.stringify(script.map((r,i)=>({slide:i+1,title:r.title,sources:r.sources})),null,2)+'\n');
await fs.writeFile(path.join(stage,'content.json'),JSON.stringify(script,null,2)+'\n');
console.log(JSON.stringify({font,slideCount,finalPath,receipt},null,2));
