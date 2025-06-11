import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../../components/DashboardLayout";
import styles from "./CreateProfile.module.css"; // Reuse your existing styles


function CreateProfile() {

    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        firstName: "",
        lastName: "",
        dob: "",
        gender: "",
        email: "",
        phone: "",
        address: "",
        city: "",
        state: "",
        country: "",
        postalCode: ""
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleCreateProfile = async () => {
        const token = localStorage.getItem("accessToken");
        const agentId = localStorage.getItem("agentId") || "placeholder-agent"; // Replace with real one
        const fullName = `${formData.firstName} ${formData.lastName}`;

        try {
            // 1. Create Client
            const clientRes = await fetch("http://ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/client/create", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json", 
                    "Accept": "application/json"  // <- Add this
                },
                body: JSON.stringify({
                    agent_id: agentId,
                    name: fullName,
                    date_of_birth: formData.dob,
                    gender: formData.gender,
                    email: formData.email,
                    phone_number: formData.phone,
                    address: formData.address,
                    city: formData.city,
                    state: formData.state,
                    country: formData.country,
                    postal_code: formData.postalCode
                })
            });

            const clientData = await clientRes.json();
            const clientId = clientData?.client?.client_id;

            if (!clientId) throw new Error("Client creation failed");

            // 2. Create Account
            const today = new Date().toISOString().split("T")[0];
            const accountRes = await fetch("http://ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/account/create", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    client_id: clientId,
                    agent_id: agentId,
                    account_type: "savings",
                    account_status: "active",
                    opening_date: today,
                    initial_deposit: 1000.00,
                    currency: "SGD",
                    branch_id: 1
                })
            });

            const accountData = await accountRes.json();
            if (!accountData.account?.account_id) throw new Error("Account creation failed");

            // 3. Log the action
            await fetch(
              "ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/log/create",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  operation: "CLIENT_CREATE",
                  agent_id: agentId,
                  client_id: clientId,
                  email: formData.email,
                }),
              }
            );

            alert("Client and account successfully created!");
            navigate("/agent");
        } catch (err) {
            console.error("Error creating profile:", err);
            alert("Failed to create profile. Check console.");
        }
    };


    return (
        <DashboardLayout title="Create new profile" subtitle="Create a new profile for your client" rightContentClassName={styles.customRightPanel}>
            <div className={styles.formWrapper}>
                <h2 className={styles.formHeader}>Enter new profile details:</h2>

                <div className={styles.columns}>
                    <div className={styles.column}>
                        <input name="firstName" placeholder="Enter First Name"
                            value={formData.firstName} onChange={handleChange}
                            className={styles.input}
                        />
                        <input name="lastName" placeholder="Enter Last Name"
                            value={formData.lastName} onChange={handleChange}
                            className={styles.input}
                        />
                        <input
                            name="dob"
                            type="date"
                            placeholder="Enter Date of Birth"
                            className={styles.input}
                            value={formData.dob}
                            onChange={handleChange}
                        />
                        <input name="gender" placeholder="Gender"
                            value={formData.gender} onChange={handleChange}
                            className={styles.input}
                        />
                        <input name="email" placeholder="Email"
                            value={formData.email} onChange={handleChange}
                            className={styles.input}
                        />
                        <input name="phone" placeholder="Phone"
                            value={formData.phone} onChange={handleChange}
                            className={styles.input}
                        />
                    </div>

                    <div className={styles.column}>
                        <input name="address" placeholder="Address"
                            value={formData.address} onChange={handleChange}
                            className={styles.input}
                        />
                        <input name="city" placeholder="City"
                            value={formData.city} onChange={handleChange}
                            className={styles.input}
                        />
                        <input name="state" placeholder="State"
                            value={formData.state} onChange={handleChange}
                            className={styles.input}
                        />
                        <input name="country" placeholder="Country"
                            value={formData.country} onChange={handleChange}
                            className={styles.input}
                        />
                        <input name="postalCode" placeholder="Postal Code"
                            value={formData.postalCode} onChange={handleChange}
                            className={styles.input}
                        />
                    </div>
                </div>

                <div className={styles.formActions}>
                    <button className={styles.saveButton} onClick={handleCreateProfile}>Save</button>
                    <button className={styles.backButton} onClick={() => navigate("/agent")}>
                        ← Back to Dashboard
                    </button>
                </div>
            </div>


        </DashboardLayout>
    );
}

export default CreateProfile;
