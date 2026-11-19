// Core model: kept separate from the UI so each step can be explained in a viva.
export type Distribution = "Normal" | "Uniform" | "Triangular";
export type Params = { c:number; p:number; v:number; b:number; mu:number; sigma:number; capacity:number; \
scenarios:number; seed:number; distribution:Distribution };
export type Point = { x:number; profit:number };
export type Result = {
optimalX:number; expectedProfit:number; profitStd:number; percentile5:number;
probabilityLoss:number; serviceLevel:number; curve:Point[]; histogram:{bin:string;count:number}[];
demandPlot:{demand:number;count:number}[]; convergence:{scenarios:number;optimalX:number}[];
deterministicX:number; deterministicProfit:number; stochasticProfit:number; vss:number; evpi:number;
};
export function seededRandom(seed:number) {
let state = seed >>> 0;
return () => { state = (state * 1664525 + 1013904223) >>> 0; return state / 4294967296; };
}
function normal(r:()=>number) {
const u=Math.max(r(),1e-12), v=r();
return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);
}
export function sampleDemand(p:Params, r:()=>number):number {
let d=0;
if(p.distribution==="Normal") { do { d=p.mu+p.sigma*normal(r); } while(d<0); }
else if(p.distribution==="Uniform") { const width=Math.sqrt(12)*p.sigma; d=p.mu-width/2+r()*width; }
else { // Symmetric triangular distribution calibrated to the requested mean and standard deviation.
const halfWidth=Math.sqrt(6)*p.sigma, u=r();
d=u<.5 ? p.mu-halfWidth+halfWidth*Math.sqrt(2*u) : p.mu+halfWidth-halfWidth*Math.sqrt(2*(1-u));
}
return Math.max(0,d);
}
export function profit(x:number,d:number,p:Params) {
return p.p*Math.min(x,d)+p.v*Math.max(x-d,0)-p.c*x-p.b*Math.max(d-x,0);
}
const mean=(a:number[])=>a.reduce((s,v)=>s+v,0)/Math.max(1,a.length);
const quantile=(a:number[],q:number)=>{const b=[...a].sort((x,y)=>x-y);return \
b[Math.min(b.length-1,Math.floor(q*(b.length-1))) ]??0;};
export function optimize(p:Params):Result {
const rng=seededRandom(p.seed), demand=Array.from({length:p.scenarios},()=>sampleDemand(p,rng));
const step=Math.max(1,Math.ceil(p.capacity/150)), xs:number[]=[];
for(let x=0;x<=p.capacity;x+=step) xs.push(x);
if(xs[xs.length-1]!==p.capacity) xs.push(p.capacity);
const curve=xs.map(x=>({x,profit:mean(demand.map(d=>profit(x,d,p)))}));
const best=curve.reduce((a,b)=>b.profit>a.profit?b:a,curve[0]);
const profits=demand.map(d=>profit(best.x,d,p));
const deterministicX=Math.min(p.capacity,Math.max(0,p.mu));
const deterministicProfit=mean(demand.map(d=>profit(deterministicX,d,p)));
// Perfect information chooses production after demand is known (bounded by capacity).
const perfect=mean(demand.map(d=>Math.max(...[0,Math.min(d,p.capacity)].map(x=>profit(x,d,p)))));
const histN=18, min=Math.min(...profits), max=Math.max(...profits), span=Math.max(1,(max-min)/histN);
const histogram=Array.from({length:histN},(_,i)=>({bin:`${Math.round(min+i*span)}`,count:0}));
profits.forEach(v=>{const i=Math.min(histN-1,Math.floor((v-min)/span));histogram[i].count++;});
const demandBins=20, maxD=Math.max(...demand), \
demandPlot=Array.from({length:demandBins},(_,i)=>({demand:Math.round(i*maxD/demandBins),count:0}));
demand.forEach(d=>{const i=Math.min(demandBins-1,Math.floor(d/maxD*demandBins));demandPlot[i].count++;});
const convergence:number[]=[100,250,500,1000,2000,5000,10000,20000,50000].filter(n=>n<=p.scenarios);
if(!convergence.includes(p.scenarios)) convergence.push(p.scenarios);
const convergenceData=convergence.map(n=>{
const sub=demand.slice(0,n);
const bestSub=curve.reduce((a,b)=>mean(sub.map(d=>profit(b.x,d,p)))>mean(sub.map(d=>profit(a.x,d,p)))?b:a,cu \
rve[0]);
return {scenarios:n,optimalX:bestSub.x};
});
const losses=profits.filter(v=>v<0).length;
return {optimalX:best.x,expectedProfit:best.profit,profitStd:Math.sqrt(mean(profits.map(v=>(v-mean(profits))** \
2))),
percentile5:quantile(profits,.05),probabilityLoss:losses/profits.length,
serviceLevel:demand.filter(d=>d<=best.x).length/demand.length,curve,histogram,demandPlot,convergence:converg \
enceData,
deterministicX,deterministicProfit,stochasticProfit:best.profit,vss:best.profit-deterministicProfit,evpi:per \
fect-best.profit};
}
