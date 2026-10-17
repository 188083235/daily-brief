// Minimal local RSSHub: GET http://127.0.0.1:1200/<route>  -> JSON {title,item:[...]} (RSSHub's data object)
import http from 'node:http';
import { init, request } from 'rsshub';
await init({ UA: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', CACHE_TYPE: 'memory', CACHE_EXPIRE: 1800, LOGGER_LEVEL: 'warn', NO_LOGFILES: true, REQUEST_TIMEOUT: 20000 });
http.createServer(async (req, res) => {
  const route = decodeURIComponent(req.url);
  try {
    const data = await request(route);
    res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(data));
  } catch (e) {
    res.writeHead(502, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ error: String(e && e.message || e).slice(0, 500) }));
  }
}).listen(1200, '127.0.0.1', () => console.log('rsshub local on 127.0.0.1:1200'));
