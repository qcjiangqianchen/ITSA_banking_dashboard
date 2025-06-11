// AdminHistoryPage.jsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../../components/DashboardLayout";
import styles from "./ManageProfiles.module.css"; // Reuse your existing styles


function ManageProfile() {
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');
    const [clients, setClients] = useState([]);
    const [selectedClient, setSelectedClient] = useState(null);

    const fetchClients = async () => {
        try {
            const res = await fetch("http://ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/client/get/all");
            const data = await res.json();
            if (res.ok && Array.isArray(data)) {
                setClients(data);
            } else {
                console.warn("Unexpected client API response:", data);
            }
        } catch (err) {
            console.error("Failed to fetch clients:", err);
        }
    };

    useEffect(() => {
        fetchClients    ();
    }, []);


    const handleSearch = () => {
        const client = clients.find(
            c =>
                c.email === searchTerm ||
            c.name.toLowerCase().includes(searchTerm.toLowerCase())
        );
        if (client) setSelectedClient(client);
        else alert("Client not found");
    };

    const handleClientClick = (client) => {
        setSelectedClient(client);
    };

    const closeModal = () => {
        setSelectedClient(null);
    };

    const filteredClients = clients.filter(client =>
        client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        client.email.toLowerCase().includes(searchTerm.toLowerCase())
    );


    const handleDelete = async () => {
        if (!selectedClient) return;

        const agentId = selectedClient.agent_id;

        try {
            const res = await fetch(`http://ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/clients/delete/${selectedClient.client_id}`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ agent_id: agentId })
            });

            const result = await res.json();

            if (res.ok) {
                alert("Client deleted successfully.");
                setClients(clients.filter(c => c.client_id !== selectedClient.client_id));
                closeModal();
            } else {
                alert(result.error || "Failed to delete client.");
            }
        } catch (err) {
            console.error("Error deleting client:", err);
        }
    };


    return (
        <DashboardLayout title="Manage Client Profiles" subtitle="Overview of all client profiles and transactions" rightContentClassName={styles.customRightPanel}>
            <div className={styles.searchHeader}>
                <label className={styles.searchTitle}>Search by name or email:</label>
                <input
                    className={styles.input}
                    placeholder="Search..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
                <div className={styles.buttonRow}>
                    <button className={styles.searchButton} onClick={handleSearch}>Search</button>
                    <button className={styles.primaryButton} onClick={() => navigate("/agent/create-profile")}>
                        Create New Profile   
                    </button>
                </div>
            </div>

            <div className={styles.searchTitle}>
                <label className={styles.cardheader}>All client profiles:</label>
            </div>

            <div className={styles.userBox}>
                {filteredClients.map(client => (
                    <div
                        key={client.client_id}
                        className={styles.userCard}
                        onClick={() => handleClientClick(client)}
                    >
                        <p className={styles.userName}>{client.name}</p>
                        <p className={styles.userRole}>{client.client_id}</p>
                        <p className={styles.userRole}>Managed by: {client.agent_id}</p>
                    </div>
                ))}
            </div>
            <button onClick={() => navigate("/agent")} className={styles.backButton}>
                ← Back to Dashboard
            </button>

            
            {selectedClient && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modal}>
                        <button onClick={closeModal} className={styles.closeButton}>×</button>
                        <h3>Client Details</h3>
                        <p><strong>Name:</strong> {selectedClient.name}</p>
                        <p><strong>Email:</strong> {selectedClient.email}</p>
                        <p><strong>Client ID:</strong> {selectedClient.client_id}</p>
                        <p><strong>Managed By:</strong> {selectedClient.agent_id}</p>
                        <p><strong>Status:</strong> {selectedClient.account_status}</p>
                        <p><strong>Gender:</strong> {selectedClient.gender}</p>
                        <p><strong>DOB:</strong> {selectedClient.dob}</p>
                        <p><strong>Phone:</strong> {selectedClient.phone_number}</p>
                        <p><strong>Address:</strong> {selectedClient.address}, {selectedClient.city}, {selectedClient.state}, {selectedClient.country}, {selectedClient.postal_code}</p>
                        <div className={styles.modalActions}>
                            <button className={styles.editButton}>Edit</button>
                            <button className={styles.deleteButton} onClick={handleDelete}>Delete</button>
                        </div>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
}

export default ManageProfile;
