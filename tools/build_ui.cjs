/* Authoring only: npm package playwright + installed Chrome; no game dependency. */
const fs=require('fs/promises'),path=require('path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../assets/ui');
const defs=`<defs><linearGradient id="iron" x2="0" y2="1"><stop stop-color="#424651"/><stop offset=".15" stop-color="#222833"/><stop offset=".65" stop-color="#161b24"/><stop offset="1" stop-color="#10141a"/></linearGradient><linearGradient id="edge" x2="0" y2="1"><stop stop-color="#c2b28e"/><stop offset=".4" stop-color="#68645a"/><stop offset="1" stop-color="#3f4148"/></linearGradient><filter id="grain"><feTurbulence baseFrequency=".68" numOctaves="2" seed="7"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope=".055"/></feComponentTransfer><feBlend in="SourceGraphic" mode="soft-light"/></filter></defs>`;
function panel(w,h,medal=false){
 const d=`M20 3 H${w-28} L${w-4} 23 V${h-25} L${w-24} ${h-4} H22 L4 ${h-22} V20 Z`;
 return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${defs}<path d="${d}" fill="#06080b" stroke="#06080b" stroke-width="6"/><path d="${d}" fill="url(#iron)" stroke="url(#edge)" stroke-width="2" filter="url(#grain)"/><path d="M24 10 H${w-31} L${w-11} 28 M11 ${h-27} L27 ${h-11} H${w-29}" fill="none" stroke="#7f796b" stroke-opacity=".5"/><path d="M${w-37} 17 l15 15 m-15 -10 l10 10 M17 ${h-38} l15 15 m-10 -15 l10 10" stroke="#b3a17d" opacity=".55"/>${medal?`<circle cx="64" cy="${h/2}" r="46" fill="#14191f" stroke="#8c816a" stroke-width="3"/><circle cx="64" cy="${h/2}" r="40" fill="#20252e" stroke="#484e59"/><path d="M27 ${h/2+28} Q64 ${h/2+45} 96 ${h/2+22}" fill="none" stroke="#883d40" stroke-width="6"/>`:''}<path d="M28 4 l7 5 h17 l8 -5 M${w-57} ${h-4} l8 -5 h17 l7 5" stroke="#b3a17d" fill="none" opacity=".7"/></svg>`;
}
function seal(){return `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">${defs}<path d="M64 2 L78 12 L102 13 L115 35 L125 64 L115 93 L94 115 L64 126 L35 115 L13 94 L2 64 L13 35 L35 13 Z" fill="url(#iron)" stroke="#67665f" stroke-width="2"/><circle cx="64" cy="64" r="49" fill="#141a23" stroke="#b5a17b" stroke-width="2"/><circle cx="64" cy="64" r="43" fill="none" stroke="#454c57"/><path d="M64 6v10 M64 112v10 M6 64h10 M112 64h10" stroke="#d5c6a3" stroke-width="2"/></svg>`;}
async function main(){
 await fs.mkdir(root,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
  const page=await browser.newPage({deviceScaleFactor:1});
  const vignette='<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs><linearGradient id="shade"><stop stop-color="#080d14" stop-opacity=".83"/><stop offset=".58" stop-color="#080d14" stop-opacity=".27"/><stop offset="1" stop-color="#080d14" stop-opacity=".06"/></linearGradient></defs><path d="M0 0h1280v720H0z" fill="url(#shade)"/></svg>';
  const wanderer='<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><path d="M64 14 12 49Q17 59 39 62l-2 22 14 23 26 1 15-32-2-15q22-1 28-12L64 14Z" fill="#d7cfb4"/><path d="m64 24-35 25 14 4 20-25 22 26 15-5zM38 65l43 5-7 14-25-6zM44 91l31 4-8 6-17-3z" fill="#202630"/></svg>';
  const sources={health:panel(500,124,true),panel:panel(440,106),card:panel(340,300),button:panel(490,50),band:panel(700,92),seal:seal(),vignette,wanderer};
  for(const name of await fs.readdir(path.join(root,'source-icons'))){
   if(!name.endsWith('.svg'))continue;
   let svg=await fs.readFile(path.join(root,'source-icons',name),'utf8');
   svg=svg.replace(/<path d="M0 0h512v512H0z"\s*\/>/,'').replace(/fill="[^"]*"/g,'fill="#ffffff"').replace('<svg ','<svg style="width:128px;height:128px;fill:white" ');
   sources[name.slice(0,-4)]=svg;
  }
  for(const [name,svg] of Object.entries(sources)){
   await fs.writeFile(path.join(root,name+'.svg'),svg);
   await page.setContent('<style>*{margin:0;padding:0}html,body{background:transparent}svg{display:block}</style>'+svg);
   await page.locator('svg').screenshot({path:path.join(root,name+'.png'),omitBackground:true});
  }
  console.log(`${Object.keys(sources).length} native game UI textures exported`);
 }finally{await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1});
