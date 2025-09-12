import MapView from "./map/MapView";
export default function App() {
  return (
    <div style={{ height: "100vh", width: "100vw" }}>
      <MapView />
      <div style={{position:"absolute", bottom:10, left:10, background:"#fff"}}>hello</div>
    </div>
  );
}
