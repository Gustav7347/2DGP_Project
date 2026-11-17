// Original compact clash, authored against PixelFX's pure-effect drawing API.
export const meta={name:'Blade contact',size:[112,96],origin:[56,48],
  duration:.28,loop:false,fps:60,bg:'none',options:{}};
// PixelFX's painter takes packed ABGR integers, not CSS color strings.
const WHITE=0xffffffff,IVORY=0xffdff6ff,WARM=0xffc4f0ff,AMBER=0xff6ba9d3,SILVER=0xffd2ccc6;
export function draw(p,t){
  if(t>=.28)return;
  const core=Math.max(0,1-t/.05);
  if(core>0)for(let d=-8;d<=8;d++){
    const a=core*(1-Math.abs(d)/10);
    p.dot(d,0,IVORY,a);p.dot(0,d*.6,WHITE,a);
  }
  for(let i=0;i<9;i++){
    const angle=-1.3+i*.31,speed=70+(i%3)*27;
    const x=Math.cos(angle)*speed*t,y=Math.sin(angle)*speed*t+45*t*t;
    const fade=Math.max(0,1-t/(.18+(i%3)*.04));
    for(let j=0;j<4;j++)p.dot(x-Math.cos(angle)*j,y-Math.sin(angle)*j,
      j===0?WARM:i%2?AMBER:SILVER,fade*(1-j*.18));
  }
}
