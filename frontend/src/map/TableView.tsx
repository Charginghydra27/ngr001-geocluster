import React from "react";

interface HexEventTableProperties{
    activeHex: string | null;
    hexEvents: any[] | null;
    onClose: any;
}

export default function HexEventTable({ activeHex, hexEvents, onClose }: HexEventTableProperties) {
    if (!activeHex) return null;

    return (   
        <div
        style={{
            position: "absolute",
            bottom: 30,
            left: 10,
            width: 1500,
            maxHeight: 250,
            overflow: "auto",
            background: "#222c",
            color: "#fff",
            padding: 10,
            borderRadius: 8
        }}
        >
        <button
        onClick={onClose}
        style={{
            position: "absolute",
            top: 5,
            right: 5,
            background: "transparent",
            color: "white",
            border: "none",
            fontSize: 18,
            cursor: "pointer",
        }}
    >
        X
    </button>
        <h4>Events in hex {activeHex}</h4>

        {!hexEvents && <div>Loading…</div>}

        {hexEvents && hexEvents.length === 0 && <div>No events</div>}

        {hexEvents && hexEvents.length > 0 && (
            <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse"}}>
            <thead>
                <tr>
                <th style={{ border: "1px solid white"}}>ID</th>
                <th style={{ border: "1px solid white"}}>Type</th>
                <th style={{ border: "1px solid white"}}>Date</th>
                </tr>
            </thead>
            <tbody>
                {hexEvents.map((ev: any) => (
                <tr key={ev.id}>
                    <td style={{ border: "1px solid white"}}>{ev.id}</td>
                    <td style={{ border: "1px solid white"}}>{ev.type}</td>
                    <td style={{ border: "1px solid white"}}>{ev.date}</td>
                </tr>
                ))}
            </tbody>
            </table>
        )}
        </div>
    );
}