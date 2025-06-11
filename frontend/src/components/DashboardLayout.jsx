// src/components/DashboardLayout.jsx
import React, { useState } from "react";
import styles from "./DashboardLayout.module.css";
import profilepic from "../assets/profilepic.png";
import ProfileModal from "./ProfileModal";

function DashboardLayout({ title, subtitle, children, rightContentClassName = "" }) {
    const [isProfileOpen, setProfileOpen] = useState(false);

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
                    <h1 className={styles.pageTitle}>{title}</h1>
                    <p className={styles.prompt}>{subtitle}</p>
                </div>

                <div className={`${styles.rightPanel} ${rightContentClassName}`}>
                    <div className={styles.rightContent}>
                        {children}
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

export default DashboardLayout;
