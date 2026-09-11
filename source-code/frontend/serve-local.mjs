import { startProdServer } from 'vinext/server/prod-server';
import { handler } from './local-server/api.mjs';
const port = Number(process.env.PORTAL_PORT || 5181);
const { server } = await startProdServer({
  host: '127.0.0.1',
  port,
  outDir: 'dist',
});
const frontend = server.listeners('request');
server.removeAllListeners('request');
server.on('request', (req, res) => {
  void handler(req, res, () => {
    for (const listener of frontend) listener.call(server, req, res);
  });
});
console.log(`AKURU local built preview: http://127.0.0.1:${port}`);
