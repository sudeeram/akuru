// Isolated component acceptance test with mocked APIs; no server or credentials required.
import { build } from '../node_modules/esbuild/lib/main.js';
import { fileURLToPath } from 'node:url';
import { mkdir } from 'node:fs/promises';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
import { readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../../', import.meta.url)).replace(/\/$/, '');
await mkdir(root+'/tmp', {recursive:true});
const entry=`import React from 'react'; import {createRoot} from 'react-dom/client'; import {PreparedTextbookImport} from './features/prepared-textbook-import'; createRoot(document.getElementById('root')).render(<PreparedTextbookImport bookRef="book_test" topicRef="topic_test" refreshBook={async()=>{}} notify={message=>{document.getElementById('notice').textContent=message}} navigate={path=>{document.getElementById('notice').textContent=path}}/>);`;
const output=await build({stdin:{contents:entry,resolveDir:root+'/source-code/frontend',loader:'tsx'},bundle:true,write:false,format:'iife',jsx:'automatic',tsconfig:root+'/source-code/frontend/tsconfig.json',define:{'process.env.NODE_ENV':'"production"'}});
const html=`<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font:16px system-ui;margin:24px;max-width:1000px}button,input,textarea{display:block;margin:12px 0;padding:8px;max-width:100%;box-sizing:border-box}textarea{width:100%}section,details{padding:16px;border:1px solid #ccc;margin:16px 0}label{display:block}output{display:block;color:#075}</style></head><body><div id="root"></div><output id="notice"></output><script>${output.outputFiles[0].text}</script></body></html>`;
let imported=false,confirmed=false,reviewCalls=0;
const issue={id:'SCI-01',title:'Solute / solvent wording',page:8,reason:'Verify the apparent source typo.',action:'Record the reviewed clarification.'};
const summary={sha256:'a'.repeat(64),title:'States of Matter',pageCount:12,blockCount:57,figureCount:19,exerciseCount:6,issues:[issue],documentId:'11111111-1111-1111-1111-111111111111'};
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('http://127.0.0.1:5199/**',async route=>{
 const req=route.request(),url=new URL(req.url());let data;
 if(url.pathname==='/'){return route.fulfill({contentType:'text/html',body:html})}
 if(url.pathname.endsWith('/sources'))data=imported?[{documentId:summary.documentId,filename:'prepared-textbook.zip',sequence:1,role:'supporting',reviewStatus:'needs_review'}]:[];
 else if(url.pathname.endsWith('/preview'))data=summary;
 else if(url.pathname.endsWith('/import')){imported=true;data=summary;}
 else if(url.pathname.endsWith('/review')){
   if(req.method()==='POST'){
     const body=req.postDataJSON();assert(body.confirmWholeDocument);assert(body.decisions['SCI-01']);reviewCalls++;confirmed=true;
   }
   data={documentId:summary.documentId,contentHash:'b'.repeat(64),issues:[issue],decisions:{},confirmed,immutable:false,reviewUrl:'/admin/textbooks/review/document_test'};
 }else return route.fulfill({status:404,body:'unmocked'});
 return route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
});
await page.goto('http://127.0.0.1:5199/');
await page.getByText('Import prepared screenshot textbook',{exact:true}).click();
await page.getByLabel('Prepared package (.zip)').setInputFiles({name:'topic.zip',mimeType:'application/zip',buffer:Buffer.from('mock; server validation covered by Python tests')});
await page.getByRole('button',{name:'Validate and preview package'}).click();
await page.getByRole('button',{name:'Import supporting draft'}).click();
await page.getByRole('button',{name:'Review prepared draft'}).click();
const confirm=page.getByRole('button',{name:'Confirm whole-document review'});
assert(await confirm.isDisabled());
await page.getByLabel('Reviewed teaching clarification or decision').fill('Read solvent in the apparent typo; preserve the source wording in provenance.');
assert(await confirm.isDisabled());
await page.getByRole('checkbox').check();assert(await confirm.isEnabled());
await confirm.click();await page.getByText('Whole-document review confirmed.',{exact:true}).waitFor();
assert.equal(reviewCalls,1);assert.equal(errors.length,0);
for(const width of [1280,390]){
 await page.setViewportSize({width,height:1000});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.screenshot({path:root+`/tmp/prepared-import-ui-${width}.png`,fullPage:true});
}
await browser.close();await writeFile(root+'/tmp/prepared-import-ui-results.json',JSON.stringify({passed:true,reviewCalls,errors,mockedApi:true,checks:['file preview','separate draft import','editable review link','notes and checkbox required','confirmation and notification','desktop/mobile overflow']},null,2));
console.log('Prepared import UI browser checks passed with mocked APIs.');
