import React, { useEffect, useState } from "react";
import { useNavigate } from 'react-router-dom';
import profilepic from "../assets/profilepic.png"
import ProfileModal from "../components/ProfileModal";
import { CognitoIdentityProviderClient, GetUserCommand } from "@aws-sdk/client-cognito-identity-provider";
import styles from './AdminDashboard.module.css';


// Sample activity logs


function AdminDashboard() {
    const [isProfileOpen, setProfileOpen] = useState(false);
    const [userInfo, setUserInfo] = useState({ name: "Admin", email: "" });
    const [recentActivities, setRecentActivities] = useState([]);
    const navigate = useNavigate();

    // const [userName, setUserName] = useState("");


    useEffect(() => {
        const fetchUserInfo = async () => {
            try {
                const token = localStorage.getItem("idToken"); // or sessionStorage
                if (!token) return;

                const res = await fetch(
                  "ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/user/get_by_email",
                  {
                    method: "GET",
                    headers: {
                      Authorization: `Bearer ${token}`,
                      "Content-Type": "application/json",
                    },
                  }
                );

                const result = await res.json();
                const user = result?.data;

                if (user) {
                    setUserInfo({
                        name: user.first_name,
                        email: user.email
                    });
                }

            } catch (error) {
                console.error("Failed to fetch user name:", error);
                setUserName("Admin");
            }
        };

        const fetchLogs = async () => {
            try {
                const res = await fetch(
                  "ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/admin/logs"
                );
                const data = await res.json();
        
                // Assuming your API returns the data in data.data (based on your Flask code)
                const logs = data.data || [];
        
                const formatted = logs.map(log => {
                    const actionVerb = {
                        'CREATE': 'created',
                        'UPDATE': 'updated',
                        'DELETE': 'deleted'
                    }[log.action_type] || 'performed action on';
        
                    const roleMapping = {
                        'client': 'Client',
                        'agent': 'Agent',
                        'admin': 'Admin'
                        // Add other role mappings as needed
                    };
        
                    const formattedRole = roleMapping[log.target_role.toLowerCase()] || log.target_role;
        
                    return `Admin ${log.admin_name} ${actionVerb} a ${formattedRole} Account ${log.target_name}`;
                });
        
                setRecentActivities(formatted.reverse().slice(0, 10)); // Show latest 10
            } catch (error) {
                console.error("Failed to fetch logs:", error);
            }
        };

        fetchUserInfo();
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
                    <h2 className={styles.greeting}>Welcome back,</h2>
                    <h1 className={styles.userName}>{userInfo.name || "Admin"}</h1>
                    <p className={styles.prompt}>What service would you like to engage today?</p>
                </div>

                <div className={styles.rightPanel}>
                    <div>
                        <h3 className={styles.sectionTitle}>Quick actions</h3>
                        <div className={styles.buttonGroup}>
                            <button className={styles.primaryButton} onClick={() => navigate("/admin/create-user")}>
                                Create new account
                            </button>
                            <button className={styles.primaryButton} onClick={() => navigate("/admin/manage-users")}>
                                Manage Accounts
                            </button>
                            <button className={styles.primaryButton} onClick={() => navigate("/admin/view-transactions")}>View history</button>
                        </div>
                    </div>

                    <div>
                        <h3 className={styles.sectionTitle}>Recent activities:</h3>
                        <div className={styles.activityWrapper}>
                            <ul>
                                {recentActivities.length > 0 ? (
                                    recentActivities.map((activity, index) => (
                                        <li key={index}>- {activity}</li>
                                    ))
                                ) : (
                                    <p>No recent activity.</p>
                                )}
                            </ul>
                        </div>
                        {/* <button onClick={() => navigate("/admin")} className={styles.backButton}>← Back to Dashboard</button> */}
                    </div>
                </div>
            </div>

            <ProfileModal
                isOpen={isProfileOpen}
                onClose={() => setProfileOpen(false)}
                user={{ name: userInfo.name, email: userInfo.email }}
            />
        </div>
    );
}

export default AdminDashboard;
