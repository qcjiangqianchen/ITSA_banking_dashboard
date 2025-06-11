import React, { useState } from "react";
import { useNavigate } from 'react-router-dom';
import { CognitoIdentityProviderClient, AdminCreateUserCommand } from "@aws-sdk/client-cognito-identity-provider";
import styles from './CreateUser.module.css';
import profilepic from "../assets/profilepic.png"
import ProfileModal from "../components/ProfileModal";

function CreateUser() {
    const navigate = useNavigate();
    const [isProfileOpen, setProfileOpen] = useState(false);

    const [formData, setFormData] = useState({
        id: "",
        firstName: "",
        lastName: "",
        email: "",
        role: "",
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    }; 

    const handleCreateAccount = async () => {
        try {
            const token = localStorage.getItem("accessToken");
            if (!token) throw new Error("User not authenticated");

            // 1. logic to upload details of the user to Cognito is now in the backend

            // 2. Create in Flask backend
            const backendRes = await fetch(
              "ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/user/create",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                  first_name: formData.firstName,
                  last_name: formData.lastName,
                  email: formData.email,
                  role: formData.role,
                }),
              }
            );

            const result = await backendRes.json();

            if (backendRes.ok) {
                alert("User successfully created in Cognito and backend.");
                navigate("/admin");
            } else {
                alert(`Error: ${result?.message || "Failed to create user."}`);
            }
            
        } catch (error) {
            console.error("Error creating user:", error);
            alert("Error creating user. Check console for details.");
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
                    <h1 className={styles.userName}>Create an account</h1>
                    <p className={styles.prompt}>Create a new admin or agent account</p>
                </div>

                <div className={styles.rightPanel}>
                    <div className={styles.rightContent}>
                        <label className={styles.cardheader}>Enter details:</label>
                        <div className={styles.card}>
                            <input
                                className={styles.input}
                                name="firstName"
                                value={formData.firstName}
                                onChange={handleChange}
                                placeholder="Enter first name"
                            />

                            <input
                                className={styles.input}
                                name="lastName"
                                value={formData.lastName}
                                onChange={handleChange}
                                placeholder="Enter last name"
                            />
                            <input
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                className={styles.input}
                                placeholder={`Enter email`}
                            />


                            <select
                                name="role"
                                value={formData.role}
                                onChange={handleChange}
                                className={styles.select}
                                placeholder={`Select role`}
                            >
                                <option value="" disabled hidden>Select role</option>
                                <option value="Admin">Admin</option>
                                <option value="Agent">Agent</option>
                            </select>
                        </div>

                        <button onClick={handleCreateAccount} className={styles.button}>Create Account</button>
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

export default CreateUser;
