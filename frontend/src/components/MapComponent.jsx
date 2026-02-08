// import React from "react";
// import { GoogleMap, useLoadScript, Marker } from "@react-google-maps/api";

// const containerStyle = {
//   width: "100%",
//   height: "400px",
// };

// const center = {
//   lat: 22.5744,
//   lng: 88.3629, // Kolkata
// };

// function MapComponent() {
//   const { isLoaded, loadError } = useLoadScript({
//     googleMapsApiKey: "AIzaSyBPrFX08yQZSIFj5T0UKCS2II9cQX18nlc",
//   });

//   const onLoad = React.useCallback((map) => {
//     console.log("Map loaded successfully");
//   }, []);

//   if (loadError) {
//     return (
//       <div style={{ padding: "20px", textAlign: "center" }}>
//         Error loading maps
//       </div>
//     );
//   }

//   if (!isLoaded) {
//     return (
//       <div style={{ padding: "20px", textAlign: "center" }}>Loading map...</div>
//     );
//   }

//   return (
//     <GoogleMap
//       mapContainerStyle={containerStyle}
//       center={center}
//       zoom={12}
//       onLoad={onLoad}
//     >
//       <Marker position={center} />
//     </GoogleMap>
//   );
// }

// export default MapComponent;
