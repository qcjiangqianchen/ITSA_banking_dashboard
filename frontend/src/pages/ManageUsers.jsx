import React, { useEffect, useState } from 'react';
import styles from './ManageUsers.module.css';
import profilepic from "../assets/profilepic.png";
import ProfileModal from "../components/ProfileModal";
import { useNavigate } from 'react-router-dom';


function ManageAccounts() {
    const navigate = useNavigate();
    const [isProfileOpen, setProfileOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedUser, setSelectedUser] = useState(null);
    const [users, setUsers] = useState([]);

    const fetchUsers = async () => {
        try {
            const token = localStorage.getItem("idToken");
            const res = await fetch("http://ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/user/get", {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            const result = await res.json();
            if (res.ok) setUsers(result.data.users);
        } catch (err) {
            console.error("Failed to fetch users:", err);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);


    const handleSearch = () => {
        const user = users.find(
            u =>
                u.email === searchTerm ||
                `${u.first_name} ${u.last_name}`.toLowerCase() === searchTerm.toLowerCase()
        );
        if (user) setSelectedUser(user);
        else alert("User not found");
    };

    const handleUserClick = (user) => {
        setSelectedUser(user);
    };

    const closeModal = () => {
        setSelectedUser(null);
    };

    const filteredUsers = users.filter(user =>
        (`${user.first_name} ${user.last_name}`.toLowerCase().includes(searchTerm.toLowerCase())) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
    );
    

    const handleDelete = async () => {
        try {
            const token = localStorage.getItem("idToken");
            const adminName = localStorage.getItem("adminName") || "Unknown Admin";
            if (!token) throw new Error("User not authenticated");
            const res = await fetch(
              `ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/user/delete/${selectedUser.user_id}`,
              {
                method: "DELETE",
                headers: {
                  Authorization: `Bearer ${token}`,
                },
              }
            );

            if (res.ok) {
                // Log action
                await fetch(
                  "ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/admin/log",
                  {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                      admin_name: adminName, // ideally pull from decoded token or profile state
                      target_name: selectedUser.name,
                      target_role: selectedUser.role,
                      action_type: "Delete",
                    }),
                  }
                );

                alert("User deleted.");
                fetchUsers(); // refresh list
                closeModal();
            } else {
                const result = await res.json();
                alert(result.message || "Error deleting user.");
            }
        } catch (err) {
            console.error("Error deleting user:", err);
        }
    };


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
                    <h1 className={styles.pageTitle}>Manage all accounts</h1>
                    <p className={styles.prompt}>Overview of all admin and agent accounts</p>
                </div>

                <div className={styles.rightPanel}>
                    <div className={styles.rightContent}>
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
                                <button className={styles.primaryButton} onClick={() => navigate("/admin/create-user")}>
                                    Create New Account
                                </button>
                            </div>
                        </div>

                        <div className={styles.searchTitle}>
                            <label className={styles.cardheader}>All accounts:</label>
                        </div>

                        <div className={styles.userBox}>
                            {filteredUsers.map(user => (
                                <div
                                    key={user.id}
                                    className={styles.userCard}
                                    onClick={() => handleUserClick(user)}
                                >
                                    <p className={styles.userName}>{user.first_name} {user.last_name}</p>
                                    <p className={styles.userRole}>{user.user_id}</p>
                                    <p className={styles.userRole}>{user.role}</p>
                                </div>
                            ))}
                        </div>

                        <button onClick={() => navigate("/admin")} className={styles.backButton}>← Back to Dashboard</button>
                    </div>
                </div>
            </div>

            {selectedUser && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modal}>
                        <button onClick={closeModal} className={styles.closeButton}>×</button>
                        <h3>User Details</h3>
                        <p><strong>Name:</strong> {selectedUser.first_name} {selectedUser.last_name}</p>
                        <p><strong>Email:</strong> {selectedUser.email}</p>
                        <p><strong>ID:</strong> {selectedUser.user_id}</p>
                        <p><strong>Role:</strong> {selectedUser.role}</p>
                        <div className={styles.modalActions}>
                            <button className={styles.editButton}>Edit</button>
                            <button className={styles.deleteButton} onClick={handleDelete}>Delete</button>
                        </div>
                    </div>
                </div>
            )}

            <ProfileModal
                isOpen={isProfileOpen}
                onClose={() => setProfileOpen(false)}
                user={{ name: "tom", email: "admin@example.com" }}
            />
        </div>
    );
}

export default ManageAccounts;
