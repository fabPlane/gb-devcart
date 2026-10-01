import {chromium} from 'playwright-core'; import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const root=process.cwd(); const types={'.html':'text/html','.js':'text/javascript','.glb':'model/gltf-binary'};
const srv=http.createServer((q,s)=>{const p=path.join(root,decodeURIComponent(q.url.split('?')[0])); if(!fs.existsSync(p)){s.writeHead(404);return s.end();} s.writeHead(200,{'content-type':types[path.extname(p)]||'application/octet-stream'}); fs.createReadStream(p).pipe(s);}).listen(8731);
const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const pg=await b.newPage({viewport:{width:1600,height:1200}}); pg.on('console',m=>console.log('console:',m.text())); pg.on('pageerror',e=>console.log('err:',e.message));
for(const v of process.argv.slice(2)){await pg.goto(`http://127.0.0.1:8731/index.html?view=${v}`); await pg.waitForFunction(()=>window.__done,null,{timeout:120000}); await pg.locator('canvas').screenshot({path:`out-${v}.png`}); console.log('wrote',v);}
await b.close(); srv.close();
