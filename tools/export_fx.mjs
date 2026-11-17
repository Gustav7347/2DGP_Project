// Authoring only. Runtime needs exported PNG/JSON, never Node or PixelFX.
import { pathToFileURL } from 'node:url';
import { resolve, join } from 'node:path';
const root=resolve(process.argv[2] ?? '../vendor/pixelfx');
const {loadEffect,renderFrames,spriteSheet,save}=await import(pathToFileURL(join(root,'tools/lib/fxlib.mjs')));
for(const id of ['melee/sword-slash','melee/thrust','impacts/parry','impacts/hit-spark']) {
  const fx=await loadEffect(id);
  const options=id==='melee/sword-slash' ? {
    palette:['#252d37','#414b57','#6b7886','#95a7b6','#bdcbd2','#e6e8dd','#fff7dd'],
    sparks:['#fff5d1','#edca80','#c4834d','#775049']
  } : undefined;
  const r=renderFrames(fx,{actor:false,options,bg:'none'});
  const name=id.split('/')[1], sheet=spriteSheet(fx,r,name);
  save(resolve('assets/fx',name+'.png'),sheet.png);
  save(resolve('assets/fx',name+'.json'),JSON.stringify(sheet.json,null,1));
  console.log(id, r.n+' frames');
}
