import React, { useEffect, useState } from "react";
import { useNavigate } from 'react-router-dom';
import styles from './ViewHistory.module.css';
import profilepic from "../assets/profilepic.png";
import ProfileModal from "../components/ProfileModal";

function ViewTransactions() {
    const navigate = useNavigate();
    const [isProfileOpen, setProfileOpen] = useState(false);
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await fetch(
                  "ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/admin/logs"
                );
                const data = await res.json();
                if (data.code === 200) {
                    setLogs(data.data);
                }
            } catch (err) {
                console.error("Failed to fetch logs:", err);
            }
        };

        fetchLogs();
    }, []);

    return (
        <div className={styles.container}>
            <div className={styles.logoFixed}>
                <h1 className={styles.logoText}>Scrooge</h1>
                <label className={styles.logoText2}>bank</label>
            </div>

            <div className={styles.profileFixed}>
                <button onClick={() => setProfileOpen(true)}>
                    <img src={profilepic} alt="Profile" className={styles.avatar} />
                </button>
            </div>


            <div className={styles.dashboardBox}>
                <div className={styles.leftPanel}>
                    <h1 className={styles.userName}>View all history</h1>
                    <p className={styles.prompt}>See the full admin history</p>
                </div>

                <div className={styles.rightPanel}>
                    <div className={styles.rightContent}>
                        <div className={styles.transactionBox}>
                            {logs.length > 0 ? (
                                logs.map((log) => (
                                    <div key={log.id} className={styles.transactionItem}>
                                        <p className={styles.txnType}>
                                            Account {log.target_name} {log.action_type.charAt(0) + log.action_type.slice(1).toLowerCase()}
                                        </p>
                                        <p className={styles.txnAmount}>performed by {log.admin_name}</p>
                                        <p className={styles.txnDate}>{log.timestamp.slice(0, 10)}</p>
                                    </div>
                                ))
                            ) : (
                                <p>No history found.</p>
                            )}
                        </div>
                        <button onClick={() => navigate("/admin")} className={styles.backButton}>← Back to Dashboard</button>
                    </div>
                </div>
            </div>
            
            <ProfileModal
                isOpen={isProfileOpen}
                onClose={() => setProfileOpen(false)}
                user={{ name: "tom", email: "admin@example.com" }}
            />
        </div>
    );
}

export default ViewTransactions;
