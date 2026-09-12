import { startProdServer } from 'vinext/server/prod-server';
const port = Number(process.env.PORTAL_PORT || 5181);
await startProdServer({
  host: '127.0.0.1',
  port,
  outDir: 'dist',
});
console.log(`AKURU local built preview: http://127.0.0.1:${port}`);
