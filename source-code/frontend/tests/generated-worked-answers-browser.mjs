// Run against an already running local frontend. Fixtures stay in the browser context;
// no accounts, answers, or AI calls are created in the real backend.
import assert from 'node:assert/strict';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({viewport:{width:1360,height:1000}});
const errors=[]; page.on('pageerror', error => errors.push(error.message));
const decision={pointId:'M1',criterion:'Use the correct method',awarded:true,marksAwarded:1,maxMarks:1,studentEvidence:'2 × 3 = 6',rationale:'Correct multiplication',confidence:.95};
const child={id:'student-test',parentId:'parent-test',username:'learner',name:'Test Learner',initial:'T',grade:'Grade 10',term:'Term2',level:'iGCSE',subjects:['maths'],courses:{maths:{level:'iGCSE'}},progression:[{grade:'Grade 10',term:'Term2'}]};
const attempt={id:'result-test',studentId:child.id,subject:'maths',questionId:'q-test',title:'Question 1',answer:'2 × 3 = 6',fileId:'',hints:0,mark:null,maxMarks:1,status:'needs-review',feedback:'Correct method',explanation:'Multiply the two values.',improvedAnswer:'2 × 3 = 6',points:[],createdAt:'2026-09-14T10:00:00Z',markingDecisions:[decision],strengths:['Correct multiplication'],smallMistakes:[],conceptualMistakes:[],confidence:.95,resultVersion:1,reviewReasons:['Verify the working.']};
const topic={topicRef:'topic_test',topicCode:'T1',topicTitle:'Numbers',groupLabel:'Unit',groupCode:'M1',groupTitle:'Number',subjectId:'maths',score:7,preciseScore:7,confidence:'medium',provisional:false,evidenceCount:3,evidenceWeight:2,varietyCount:3,trend:1,lastEvidenceAt:'2026-09-14',dimensions:[{dimension:'method',score:7,evidenceWeight:2}],recentEvents:[{id:'e-test',previousScore:6,newScore:7,newConfidence:'medium',explanation:'More correct method marks',createdAt:'2026-09-14T10:00:00Z'}]};
const audit={resultId:attempt.id,assessmentId:'assessment-test',questionId:'q-test',studentId:child.id,studentName:child.name,subjectId:'maths',assessmentTitle:'Term mock',questionNumber:'1',questionPrompt:'Multiply 2 by 3.',version:1,status:'needs_review',awardedMarks:1,maxMarks:1,confidence:.95,provider:'test',model:'test',promptName:'assessment',promptVersion:'1',subjectEngine:'maths',subjectEngineVersion:'1',reviewReasons:['Verify working'],markingDecisions:[decision],strengths:[],smallMistakes:[],conceptualMistakes:[],improvedAnswer:'2 × 3 = 6',teachingExplanation:'Multiply the numbers.',deterministicChecks:{},sourceManifest:[{type:'frozen_rubric'}],createdAt:'2026-09-14T10:00:00Z'};
let role='admin';
attempt.assessmentId='assessment-test';
attempt.answerVisuals=[{assetId:'answer-image',partLabel:'c(ii)',pointCodes:['M1'],caption:'All bonds must be shown.',altText:'Displayed butane with every carbon hydrogen bond.',status:'approved'}];

function state(){return {user:{id:role==='student'?child.id:role+'-test',name:'Test '+role,role,mustChangePassword:false},catalog:{courses:['iGCSE'],activeCourses:['iGCSE'],grades:['Grade 10'],terms:['Term2'],kinds:[],progressionPairs:[]},accounts:[],subjects:[{id:'maths',name:'Maths',color:'blue',icon:'∑',description:'Numbers'}],students:[child],drafts:{},questions:[{id:'q-test',subject:'maths',topic:'Numbers',title:'Multiply',prompt:'Calculate the product.',marks:1,type:'written',diagram:'triangle',source:'Test fixture',assessmentId:'assessment-test',equations:['\\frac{1}{2}x^2'],assetIds:['asset-test'],generatedWorkedAnswerAvailable:true}],attempts:[attempt],assignments:[],documents:[{id:"11111111-1111-4111-8111-111111111111",kind:"Past paper",name:"Synthetic paper",subject:"maths"},{id:"scheme-test",kind:"Mark scheme",name:"Synthetic scheme",subject:"maths",paperId:"11111111-1111-4111-8111-111111111111"}],exams:[{id:'assessment-test',studentId:child.id,status:'active',mode:'practice',questionIds:['q-test'],answers:{},files:{}}],assessmentBlueprints:[],officialPapers:[],reviews:[],plans:{},mastery:{[child.id]:[topic]},recommendations:{}};}

await page.route('**/api/v1/**', async route => {
 const path=new URL(route.request().url()).pathname;
 if(path.includes('/documents/') && path.includes('/assets/')) {
  if(path.includes('/assets/answer-image/')) assert.ok(path.includes('/documents/scheme-test/'), 'Preview must use the saved workspace scheme, not an empty companion selector');
  return route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120"><text x="10" y="30">Model answer</text></svg>'});
 }
 if(path.endsWith('/official-paper-reviews/11111111-1111-4111-8111-111111111111')) return route.fulfill({json:{paperDocumentId:'11111111-1111-4111-8111-111111111111',paperVersionId:'v1',schemeDocumentId:'scheme-test',reportDocumentId:null,expectedQuestionCount:1,questionCount:1,approvedCount:0,wholePaperReady:false,blockers:[],questions:[{number:'5',revision:1,status:'needs_correction',data:{marks:1,prompt:'Draw a molecule.',sharedStem:'',paperSources:[],visualAssetIds:[],candidateVisualAssetIds:[],visualAltText:'',parts:[{label:'c(ii)',marks:1,prompt:'Draw.',visualAssetIds:[],markingPoints:[{code:'M1',text:'All bonds',kind:'other'}],alternatives:[],examinerAdvice:'',paperSources:[],schemeSources:[],reportSources:[],topicRefs:[],coverage:'unreviewed',coverageReason:'',status:'unreviewed',responseType:'drawing',answerVisualRequired:true,answerVisuals:attempt.answerVisuals}],exclusionReason:''}}]}});
 if(path.endsWith('/topics') || path.endsWith('/visual-crops')) return route.fulfill({json:[]});
 if(path.endsWith('/extraction')) return route.fulfill({json:{status:'completed',pages:[{id:'page1',pageNumber:1,widthPoints:600,heightPoints:800,renderAssetId:'render',blocks:[]}]}});
 if(path.includes('/answer-visuals/')) return route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="120"><text x="10" y="40">H—C—C—C—C—H</text></svg>'});
 if(path.endsWith('/state')) return route.fulfill({json:state()});
 if(path.endsWith('/auth/me')) return route.fulfill({json:{user:state().user}});
 return route.fulfill({json:{}});
});

const generatedVisual={assetId:'generated-image',partLabel:'c(ii)',pointCodes:['M1'],caption:'Verified synthetic plot',altText:'Synthetic verified plotted points and labelled axes.',status:'approved',origin:'ai_generated',workedAnswerId:'generated-test',explanation:'Plot the source values at their verified coordinates.',limitations:'Illustrative worked solution; valid student graphs may differ.',dataText:'0, 21; 5, 22.3'};
attempt.answerVisuals=[generatedVisual];
let row=null,revealCount=0,attachCount=0;
const graph={schemaVersion:'graph-v1',title:'Synthetic experiment',xAxis:{label:'Volume / cm³',minimum:0,maximum:40,tick:10},yAxis:{label:'Temperature / °C',minimum:20,maximum:30,tick:2},points:[{x:0,y:21},{x:5,y:22.3}],steps:[{partLabel:'c(ii)',explanation:generatedVisual.explanation,showPoints:true,circleIndexes:[],fits:[]}],limitations:generatedVisual.limitations};
await page.route('**/api/v1/**',async route=>{
 const path=new URL(route.request().url()).pathname;
 if(path.endsWith('/worked-answer-capabilities'))return route.fulfill({json:{enabled:true,providerConfigured:true,ready:true}});
 if(path.endsWith('/worked-answer')){revealCount++;return route.fulfill({json:{visuals:[generatedVisual],message:'This question is now assisted practice and will not increase independent mastery.'}});}
 if(path.includes('/worked-answers')){
  if(path.endsWith('/attach')){attachCount++;assert.equal(route.request().postDataJSON().expectedQuestionRevision,1);return route.fulfill({json:{questionRevision:2,assetIds:['generated-image']}});}
  if(path.endsWith('/image'))return route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400"><text x="10" y="30">AI-generated synthetic graph</text></svg>'});
  if(path.endsWith('/review')){
   const body=route.request().postDataJSON();assert.equal(body.expectedRevision,row.revision);
   row={...row,revision:row.revision+1,status:body.action==='approve'?'approved':body.action==='reject'?'rejected':'awaiting_review',solution:body.solution||row.solution};return route.fulfill({json:row});
  }
  if(route.request().method()==='POST'){
   const body=route.request().postDataJSON();assert.equal(body.expectedQuestionRevision,1);assert.deepEqual(body.graph.partLabels,['c(ii)']);
   row={id:'generated-test',revision:3,status:'awaiting_review',solution:graph,label:'AI-generated worked answer — not an official Pearson answer',provenance:{model:'synthetic-test',checks:['verified points unchanged']},sourceManifest:{versions:[]},sourceHash:'1234567890abcdef',graphInput:{verificationNote:body.graph.verificationNote}};
   return route.fulfill({json:row,status:202});
  }
  return route.fulfill({json:row?[row]:[]});
 }
 return route.fallback();
});
try {
 const base=process.env.AKURU_URL || 'http://127.0.0.1:5192';
 await page.goto(base+'/admin/exam-documents/review/11111111-1111-4111-8111-111111111111');
 const panel=page.locator('section,article,div').filter({has:page.getByRole('heading',{name:'AI-generated worked answers',exact:true})}).last();
 await page.getByText('Generate a graph solution',{exact:true}).click();
 await page.getByLabel('Label including units').nth(0).fill('Volume / cm³');
 await page.getByLabel('Label including units').nth(1).fill('Temperature / °C');
 await page.getByLabel('Verified data: x, y — one pair per line').fill('0,21\n5,22.3');
 await page.getByRole('group',{name:'Subparts to explain'}).getByLabel('c(ii)',{exact:true}).check();
 await page.getByLabel('Source verification note (at least 20 characters)').fill('Verified synthetic data against both original sources.');
 await page.getByRole('button',{name:'Generate draft',exact:true}).click();
 await page.getByText('Part c(ii) — preview worked answer',{exact:true}).click();
 const preview=page.getByAltText(generatedVisual.explanation).last();await preview.scrollIntoViewIfNeeded();
 await preview.evaluate(el=>el.complete?Promise.resolve():new Promise(resolve=>{el.onload=resolve;el.onerror=resolve}));assert.ok(await preview.evaluate(el=>el.naturalWidth>0));
 await page.getByLabel('Review note (at least 20 characters)').fill('Checked the synthetic plot and explanation against the source.');
 await page.getByRole('button',{name:'Edit explanation and plotting instructions',exact:true}).click();
 await page.getByRole('textbox',{name:/^Explanation/}).fill('Corrected explanation: plot every verified source value precisely.',{timeout:5000});
 await page.getByRole('button',{name:'Save edited draft',exact:true}).click();
 await page.getByRole('button',{name:'Save edited draft',exact:true}).waitFor({state:'hidden'});
 assert.equal(row.solution.steps[0].explanation,'Corrected explanation: plot every verified source value precisely.');
 await page.getByRole('button',{name:'Approve worked answer',exact:true}).click();
 await page.getByRole('button',{name:'Attach approved answer to question',exact:true}).waitFor();
 assert.equal(row.status,'approved');
 await page.getByRole('button',{name:'Attach approved answer to question',exact:true}).click();
 await page.getByText('Question refreshed with generated answer.',{exact:true}).waitFor();assert.equal(attachCount,1);
 role='student';
 for(const width of [1360,390]){
  await page.setViewportSize({width,height:900});
  await page.goto(base+'/student/progress');
  await page.getByRole('button',{name:/Question 1/}).click();
  await page.getByText('Show worked step for part c(ii)',{exact:true}).click();
  await page.getByText(/not an official Pearson answer/).waitFor();
  await page.getByText('Graph values (horizontal, vertical)',{exact:true}).click();
  await page.getByText('0, 21; 5, 22.3',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Enlarge diagram',exact:true}).click();
  await page.getByRole('heading',{name:'Learning diagram',exact:true}).waitFor();await page.keyboard.press('Escape');await page.keyboard.press('Escape');
 }
 await page.goto(base+'/student/practice');
 await page.getByRole('button',{name:'Show worked answer',exact:true}).click();
 await page.getByText(/This question is now assisted practice/).waitFor();assert.equal(revealCount,1);
 assert.deepEqual(errors,[]);
 console.log('PASS: generated-answer Admin generation/preview/edit/re-approval/attachment, labelled Student feedback and practice reveal on desktop/mobile; browser fixtures only.');
} catch(error) {console.log('PAGE ERRORS',errors);console.log((await page.locator('body').innerText()).slice(-15000));throw error;} finally {await browser.close();}
