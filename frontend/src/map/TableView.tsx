import React, {useState} from "react";

interface HexEventTableProperties{
    activeHex: string | null;
    hexEvents: any[] | null;
    onClose: any;
    onUpdate: any;
}

export default function HexEventTable({ activeHex, hexEvents, onClose, onUpdate }: HexEventTableProperties) {
    if (!activeHex) return null;

    //allow edit local copy of events
    const [localEvents, setLocalEvents] = useState<any[]>([]);
    const [dirty, setDirty] = useState<Record<number, boolean>>({});
    const [saving, setSaving] = useState(false);

    // Sync the local state when a hex event changes
    React.useEffect(() => {
        if (hexEvents){       
            setLocalEvents(hexEvents);
            setDirty({});
        }
    }, [hexEvents]);

    const handleChange = (id: number, field: string, value:string) => {
        setLocalEvents(events => events.map(e => (e.id === id ? { ...e, [field]: value} : e)));
        setDirty(prev => ({ ...prev, [id]: true}))
    };

    const handleSave = async () => {
        const changes = localEvents.filter(ev => dirty[ev.id]);
        if (changes.length === 0) return;

        setSaving(true);
        try{
            await onUpdate(changes);
            setDirty({});
        } catch (e) {
            alert("Error saving changes.");
        } finally {
            setSaving(false);
        }
    };

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
        onClick={handleSave}
        style={{
            position: "absolute",
            top: 5,
            left: 5,
            background: "transparent",
            color: "white",
            border: "1px solid white",
            fontSize: 18,
            cursor: "pointer",
        }}
        >
            {saving ? "Saving..." : "Save"}
        </button>
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
                <th style={{ border: "1px solid white"}}>Severity</th>
                <th style={{ border: "1px solid white"}}>Date</th>
                </tr>
            </thead>
            <tbody>
                {localEvents.map((ev: any) => (
                <tr key={ev.id}>
                    <td style={{ border: "1px solid white"}}>{ev.id}</td>
                    <td style={{ border: "1px solid white"}}>
                        <input value={ev.type} onChange={(e) => handleChange(ev.id, "type", e.target.value)} style={{width:"100%", background: "transparent", color: "white"}}/>
                    </td>
                    <td style={{ border: "1px solid white"}}>
                        <input value={ev.severity} onChange={(e) => handleChange(ev.id, "severity", e.target.value)} style={{width:"100%", background: "transparent", color: "white"}}/>
                    </td>
                    <td style={{ border: "1px solid white"}}>
                        <input value={ev.occurred_at} onChange={(e) => handleChange(ev.id, "occurred_at", e.target.value)} style={{width:"100%", background: "transparent", color: "white"}}/>
                    </td>
                </tr>
                ))}
            </tbody>
            </table>
        )}
        </div>
    );
}