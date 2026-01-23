import { useState } from "react";

type Props = {
zoom: number;
setZoom: (value: number | ((prev: number) => number)) => void;
}
export default function ZoomButtons({zoom,setZoom}:Props){


return(
    <div className="doc-viewer-toolbar">
        <button className="btn ghost" onClick={() => setZoom(z => Math.min(z + 0.1, 2))}>+</button>
        <button className="btn ghost" onClick={() => setZoom(z => Math.max(z - 0.1, 0.5))}>−</button>
        <button className="btn ghost" onClick={() => setZoom(1)}>Reset</button>
      </div>
)
}