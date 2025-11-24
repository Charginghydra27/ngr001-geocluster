import { cellToBoundary } from "h3-js";

export function hexToBox(h3: string){
    //Get the latitude and longitude of the cell
    const boundry = cellToBoundary(h3, true);
    const lons = boundry.map(p => p[0]);
    const lats = boundry.map(p => p[1]);

    return {
        minx: Math.min(...lons),
        miny: Math.min(...lats),
        maxx: Math.max(...lons),
        maxy: Math.max(...lats)
    };
}