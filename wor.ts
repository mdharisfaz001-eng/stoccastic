/// <reference lib="webworker" />
import { optimize, type Params } from "../lib/stochastic";
self.onmessage = (event: MessageEvent<Params>) => {
try { self.postMessage({ ok:true, result: optimize(event.data) }); }
catch (error) { self.postMessage({ ok:false, error: error instanceof Error ? error.message : "Simulation \
failed." }); }
};
