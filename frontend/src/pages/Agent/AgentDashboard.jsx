import React, { useEffect, useState } from "react";
import { useNavigate } from 'react-router-dom';
import profilepic from "../../assets/profilepic.png"
import ProfileModal from "../../components/ProfileModal";
import { CognitoIdentityProviderClient, GetUserCommand } from "@aws-sdk/client-cognito-identity-provider";
import styles from './AgentDashboard.module.css';

// Sample activity logs
const userData = {
    name: "Admin User",
    email: "admin@example.com",
    avatar: "https://via.placeholder.com/80",
};

//retrieve user details from user.py

const userName = "User57486"; // Placeholder for logged-in user
const recentActivities = [
    "User1 created an account",
    "User2 updated profile details",
    "User3 deleted an account",
    "User1 created an account",
];

function AgentDashboard() {
    const [isProfileOpen, setProfileOpen] = useState(false);
    const [userInfo, setUserInfo] = useState({ name: "Admin", email: "" });
    const [recentActivities, setRecentActivities] = useState([]);
    const navigate = useNavigate();

    const [userName, setUserName] = useState("");

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
                setUserName("Agent");
            }
        };


        const fetchLogs = async () => {
            try {
                const res = await fetch("http://ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/log/get");
                const data = await res.json();

                const logs = data.logs || [];

                // Only show logs related to admins/agents
                const userLogs = logs.filter(log => log.agent_id || log.client_id);

                const formatted = userLogs.map(log => {
                    const agent = log.agent_id || "Unknown";
                    const client = log.client_id || "user";

                    if (log.operation === "CREATE") {
                        return `${agent} created account for ${client}`;
                    } else if (log.operation === "UPDATE") {
                        return `${agent} updated ${log.attribute} from "${log.before_value}" to "${log.after_value}" for ${client}`;
                    } else if (log.operation === "DELETE") {
                        return `${agent} deleted ${client}'s account`;
                    } else {
                        return `${agent} performed ${log.operation} on ${client}`;
                    }
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
                    <h1 className={styles.userName}>{userInfo.name || "Agent"}</h1>
                    <p className={styles.prompt}>What service would you like to engage today?</p>
                </div>

                <div className={styles.rightPanel}>
                    <div>
                        <h3 className={styles.sectionTitle}>Quick actions</h3>
                        <div className={styles.buttonGroup}>
                            <button className={styles.primaryButton} onClick={() => navigate("/agent/create-profile")}>
                                Create New Client Profile
                            </button>
                            <button className={styles.primaryButton} onClick={() => navigate("/agent/manage-profiles")}>
                                Manage Profiles
                            </button>
                            <button className={styles.primaryButton} onClick={() => navigate("/agent/view-transactions")}>View Transactions</button>
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
                user={{ name: userName, email: "admin@example.com" }}
            />
        </div>
    );
}

export default AgentDashboard;
