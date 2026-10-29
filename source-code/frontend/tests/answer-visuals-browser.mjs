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
let role='student',failReview=true,failAudit=false;
attempt.assessmentId='assessment-test';
attempt.answerVisuals=[{assetId:'answer-image',partLabel:'c(ii)',pointCodes:['M1'],caption:'All bonds must be shown.',altText:'Displayed butane with every carbon hydrogen bond.',status:'approved'}];
const reviewBodies=[];
function state(){return {user:{id:role==='student'?child.id:role+'-test',name:'Test '+role,role,mustChangePassword:false},catalog:{courses:['iGCSE'],activeCourses:['iGCSE'],grades:['Grade 10'],terms:['Term2'],kinds:[],progressionPairs:[]},accounts:[],subjects:[{id:'maths',name:'Maths',color:'blue',icon:'∑',description:'Numbers'}],students:[child],drafts:{},questions:[{id:'q-test',subject:'maths',topic:'Numbers',title:'Multiply',prompt:'Calculate the product.',marks:1,type:'written',diagram:'triangle',source:'Test fixture',assessmentId:'assessment-test',equations:['\\frac{1}{2}x^2'],assetIds:['asset-test']}],attempts:[attempt],assignments:[],documents:[],exams:[{id:'assessment-test',studentId:child.id,status:'active',mode:'practice',questionIds:['q-test'],answers:{},files:{}}],assessmentBlueprints:[],officialPapers:[],reviews:[],plans:{},mastery:{[child.id]:[topic]},recommendations:{}};}

await page.route('**/api/v1/**', async route => {
 const path=new URL(route.request().url()).pathname;
 if(path.includes('/answer-visuals/')) return route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="120"><text x="10" y="40">H—C—C—C—C—H</text></svg>'});
 if(path.endsWith('/state')) return route.fulfill({json:state()});
 if(path.endsWith('/auth/me')) return route.fulfill({json:{user:state().user}});
 return route.fulfill({json:{}});
});
try {
 const base=process.env.AKURU_URL || 'http://127.0.0.1:5192';
 for (const width of [1360,390]) {
  await page.setViewportSize({width,height:900});
  await page.goto(base+'/student/progress');
  await page.getByRole('button',{name:/Question 1/}).click();
  await page.getByRole('heading',{name:'Approved model-answer diagrams'}).waitFor();
  const image=page.getByAltText('Displayed butane with every carbon hydrogen bond.').first();
  await image.waitFor();
  assert.ok(await image.evaluate(node => node.complete && node.naturalWidth > 0));
  await page.getByRole('button',{name:'Enlarge diagram',exact:true}).click();
  await page.getByRole('heading',{name:'Learning diagram',exact:true}).waitFor();
  await page.keyboard.press('Escape');
  await page.keyboard.press('Escape');
 }
 assert.deepEqual(errors,[]);
 console.log('PASS: model-answer images, enlargement and keyboard close at desktop/mobile widths.');
} finally { await browser.close(); }
