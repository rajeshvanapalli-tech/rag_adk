import { useState } from 'react';
import axios from 'axios';
import { UploadCloud } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';


const UploadArea = ({ activeTab }) => {
    const [status, setStatus] = useState('');

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('files', file);
        formData.append('category', activeTab); // 'hr' or 'product'

        setStatus('Uploading...');

        try {
            await axios.post(`${API_BASE}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            setStatus(`Successfully uploaded for ${activeTab.toUpperCase()}!`);
        } catch (err) {
            console.error(err);
            setStatus('Upload failed. Please check the backend.');
        }
    };

    return (
        <div className="upload-container">
            <h3>Documents</h3>
            <p>Current Agent: <strong>{activeTab.toUpperCase()}</strong></p>

            <label className="drop-zone">
                <input
                    type="file"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                    accept=".txt,.pdf,.docx,.doc,.csv,.xlsx,.xls,.json"
                />
                <UploadCloud size={48} color="#94a3b8" />
                <p>Click to upload documents for {activeTab.toUpperCase()} agent</p>
            </label>

            {status && <p className="status-message">{status}</p>}
        </div>
    );
};

export default UploadArea;
