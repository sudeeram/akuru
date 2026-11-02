// Local-only full TutorSessions fixture for visual/accessibility checks. No API credentials or paid calls.
import { build } from '../node_modules/esbuild/lib/main.js';
import { createServer } from 'node:http';
import { readFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const frontend = fileURLToPath(new URL('../', import.meta.url));
const imports = (
  await readFile(frontend + 'features/tutor-sessions.tsx', 'utf8')
).match(/import \{\s*addTutorAgentTurn,[\s\S]*?\} from '@\/api';/)[0];
const apiNames = imports
  .split('{')[1]
  .split('}')[0]
  .split(',')
  .map((s) => s.trim())
  .filter((s) => s && !s.startsWith('type '));
const fixture = `
const profile = {profileRef:'tutor_fixture',name:'AKURU Chemistry',avatarCode:'spark',version:1};
const topic = {topicRef:'topic_fixture',code:'1',title:'States of Matter',groupCode:'1',groupTitle:'Unit 1'};
const reply = {operationRef:'op_fixture',turnRef:'turn_8',content:'A **solid keeps its shape** because its particles stay in fixed positions. A liquid can flow because its particles move around each other.\\n\\n1. Particles in a solid vibrate about fixed positions.\\n2. Particles in a liquid move past one another.\\n\\nThe formula for water is **H₂O**. A volume can be written as 5cm³.\\n\\nWhich state can flow?',citations:[1,2,3].map(n=>({citationRef:'citation_'+n,textbookTitle:'Edexcel International GCSE Chemistry Student Book',pageReference:'Page '+n,assetUrl:'/fixture-source.svg'})),visuals:[],followUpChoices:['Do solid particles move?','Compare a liquid and a gas'],toolResults:[],proposedSignals:[],teachingMode:'explanation',provider:'openai',model:'fixture'};
if(location.search.includes('supplementary')) Object.assign(reply,{answerBasis:'mixed',content:'**Textbook-supported explanation**\\n\\nEvaporation occurs when particles escape from the surface of a liquid.\\n\\n**Additional explanation**\\n\\nThis extends beyond the retrieved textbook evidence; it is not an official Pearson answer.\\n\\n**Illustrative example:** wind carries humid air away from wet clothes, allowing evaporation to continue.'});
let session = {sessionRef:'session_fixture',subjectId:'chemistry',activeTopic:topic,currentTutor:profile,status:'active',turns:Array.from({length:8},(_,i)=>({turnRef:'turn_'+i,profileRef:profile.profileRef,profileVersion:1,createdAt:'2026-11-01T12:'+String(i+10).padStart(2,'0')+':00Z',role:i%2?'assistant':'student',modality:'text',content:i===7?reply.content:i%2?'Let us compare the particles and how they move.\\n\\n**Key idea:** particles in a solid vibrate about fixed positions.':'Can you explain the particle model?',structured:i===7?reply:{}}))};
const quota = {state:'available',enabled:true,requests:{remaining:98},textTokens:{remaining:190000},voiceMinutes:{remaining:60},fallbackMessage:'Your tutor allowance is available.',renewsAt:'2026-11-24T00:00:00Z'};
const api = {
 getTutorOptions:async()=>({avatars:[{code:'spark',imagePath:location.search.includes('missing-avatar')?'/akuru-bots/not-found.png':'/akuru-bots/akuru-bot-celebrate.png'}]}),
 getTutorSessionOptions:async()=>({pilotMode:true,subjects:[{id:'chemistry',name:'Chemistry',topics:[topic]}],profiles:[profile]}),
 getTutorSessions:async()=>({sessions:[structuredClone(session)]}),getTutorQuota:async()=>quota,getTutorPractice:async()=>null,
 errorMessage:e=>e.message,
 addTutorAgentTurn:async(ref,message)=>{await new Promise(r=>setTimeout(r,1000));const result={...reply,turnRef:'reply_'+Date.now()};session.turns.push({turnRef:'student_'+Date.now(),profileRef:profile.profileRef,profileVersion:1,createdAt:new Date().toISOString(),role:'student',modality:'text',content:message});session.turns.push({turnRef:result.turnRef,profileRef:profile.profileRef,profileVersion:1,createdAt:new Date().toISOString(),role:'assistant',modality:'text',content:result.content,structured:result});return result;}
};
${apiNames.map((name) => `export const ${name} = api.${name} || (async()=>{throw Error('Not part of this UI fixture')});`).join('\n')}
`;
const stubs = {
  api: fixture,
  image: `import React from 'react'; export default function Image({unoptimized,...props}) { return <img {...props}/>; }`,
  workspace: `import React from 'react';export function useFocusMode(){};export function AdvancedPanel({title,children}){return <details className="workspace-disclosure"><summary>{title}</summary>{children}</details>;}`,
  search: `export function useWorkspaceSearch(){return [{}];}`,
  signals: `export function TutorSignals(){return null;}`,
  voice: `export function TutorVoice(){return null;}`,
  answers: `export function ModelAnswerVisuals(){return null;}export function PracticeWorkedAnswer(){return null;}`,
  drawings: `export function DrawingSubmissions(){return null;}`,
  shared: `import React from 'react';export function Heading({eyebrow,title,children,action}){return <header className="page-header"><div><small>{eyebrow}</small><h1>{title}</h1><p>{children}</p></div>{action}</header>;}export function Empty({title,children}){return <div className="empty"><h3>{title}</h3><p>{children}</p></div>;}`,
};
const map = {
  '@/api': 'api',
  'next/image': 'image',
  '@/components/portal/workspace': 'workspace',
  '@/lib/use-workspace-search': 'search',
  '@/features/tutor-signals': 'signals',
  '@/features/tutor-voice': 'voice',
  './answer-visuals': 'answers',
  './drawing-submissions': 'drawings',
  '@/features/shared': 'shared',
};
const js = await build({
  stdin: {
    contents: `import React from 'react';import {createRoot} from 'react-dom/client';import {TutorSessions} from './features/tutor-sessions';createRoot(document.getElementById('root')).render(<TutorSessions notify={()=>{}}/>);`,
    resolveDir: frontend,
    loader: 'tsx',
  },
  bundle: true,
  write: false,
  format: 'iife',
  jsx: 'automatic',
  tsconfig: frontend + 'tsconfig.json',
  define: { 'process.env.NODE_ENV': '"production"' },
  plugins: [
    {
      name: 'fixture-only',
      setup(b) {
        b.onResolve({ filter: /.*/ }, (args) =>
          map[args.path]
            ? { path: map[args.path], namespace: 'fixture' }
            : null,
        );
        b.onLoad({ filter: /.*/, namespace: 'fixture' }, (args) => ({
          contents: stubs[args.path],
          loader: 'tsx',
          resolveDir: frontend,
        }));
      },
    },
  ],
});
const cssDir = frontend + 'dist/client/_next/static/css';
const css = (
  await Promise.all(
    (
      await readdir(cssDir)
    )
      .filter((n) => n.endsWith('.css'))
      .map((n) => readFile(path.join(cssDir, n), 'utf8')),
  )
).join('\n');
const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AKURU chat UI fixture</title><style>${css}body{background:#f5f6fb;padding:24px}.fixture-shell{max-width:1100px;margin:auto}.fixture-banner{font:12px system-ui;color:#665d78;margin:0 0 18px}.page-header{display:flex;justify-content:space-between;gap:12px}.page-header h1{font-size:1.5rem;font-weight:700}.page-header p{margin-top:6px;color:#667085;font-size:.85rem}@media(max-width:640px){body{padding:12px}}</style></head><body><main class="fixture-shell"><p class="fixture-banner">LOCAL UI FIXTURE · synthetic conversation · no live API or AI calls</p><div id="root"></div></main><script>${js.outputFiles[0].text}</script></body></html>`;
const server = createServer(async (req, res) => {
  try {
    const pathname = new URL(req.url, 'http://localhost').pathname;
    if (pathname === '/mobile') {
      res.setHeader('Content-Type', 'text/html; charset=utf-8');
      res.end(
        '<!doctype html><html><head><meta charset="utf-8"><title>Mobile Tutor fixture</title></head><body style="margin:0;background:#eceef7"><iframe title="Mobile Tutor chat" src="/' +
          new URL(req.url, 'http://localhost').search +
          '" style="width:390px;height:844px;border:0;background:white"></iframe></body></html>',
      );
      return;
    }
    if (pathname === '/') {
      res.setHeader('Content-Type', 'text/html; charset=utf-8');
      res.end(
        html.replace(
          '</head>',
          '<style>' +
            (await readFile(frontend + 'app/tutor-chat.css', 'utf8')) +
            '</style></head>',
        ),
      );
      return;
    }
    if (pathname === '/fixture-source.svg') {
      res.setHeader('Content-Type', 'image/svg+xml');
      res.end(
        '<svg xmlns="http://www.w3.org/2000/svg" width="500" height="300"><rect width="500" height="300" fill="#f0edff"/><text x="40" y="150" font-size="24">Synthetic textbook source</text></svg>',
      );
      return;
    }
    if (/^\/akuru-bots\/akuru-bot-[a-z-]+\.png$/.test(pathname)) {
      res.setHeader('Content-Type', 'image/png');
      res.end(await readFile(frontend + 'public' + pathname));
      return;
    }
    res.writeHead(404);
    res.end('Not found');
  } catch {
    res.writeHead(404);
    res.end('Not found');
  }
});
server.listen(0, '127.0.0.1', () =>
  console.log(
    'Local Tutor UI fixture: http://127.0.0.1:' + server.address().port,
  ),
);
