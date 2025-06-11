import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CognitoIdentityProviderClient, InitiateAuthCommand, RespondToAuthChallengeCommand } from "@aws-sdk/client-cognito-identity-provider";
import styles from './Login.module.css'; // Import the module
import { jwtDecode } from "jwt-decode";
const config = { region: "ap-southeast-1" }

const cognitoClient = new CognitoIdentityProviderClient(config);
const clientId = "5m07nmhkocfd7pabd5pp15flfa"

// console.log("Using Cognito Client Config:", config, clientId);


function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [view, setView] = useState("login");
    const [session, setSession] = useState("");
    const navigate = useNavigate();


    const handleLogin = async () => {
        try {
            localStorage.clear(); // 🔥 Clear any stale tokens BEFORE logging in fresh

            const input = {
                "AuthFlow": "USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "USERNAME": email,
                    "PASSWORD": password,   
                },
                "ClientId": clientId,
            };
            const command = new InitiateAuthCommand(input);
            const response = await cognitoClient.send(command);

            console.log(response)
            if (response.ChallengeName === "NEW_PASSWORD_REQUIRED") {
                setSession(response.Session)
                setView('otp')
            }
            else if (response['$metadata']['httpStatusCode'] === 200) {
                console.log("Login successful:", response);
                const idtoken = response.AuthenticationResult.IdToken;
                const accesstoken = response.AuthenticationResult.AccessToken;
                localStorage.setItem("idToken", idtoken);// Store the token in local storage or session storage
                localStorage.setItem("accessToken", accesstoken); // Store the refresh token

                const decoded = jwtDecode(idtoken);
                console.log("Decoded JWT:", decoded); // <--- ADD THIS
                const email = decoded.email;

                const res = await fetch("http://ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/user/get_by_email", {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${idtoken}`,
                        "Content-Type": "application/json",
                        // "Email": email  // Optional: if your backend uses this
                    },
                }
                );

                const result = await res.json();
                console.log("Backend role:", result);

                const role = result?.data?.role;
                localStorage.setItem("userRole", role); // ✅ Store manually

                const user = result?.data;
                const adminName = `${user.first_name} ${user.last_name}`;
                localStorage.setItem("adminName", adminName);

                console.log("Extracted role:", role); // <-- Add this
                //redirecting users to the correct dashboard based on their role
                if (role === "Admin") {
                    navigate("/admin");
                } else if (role === "Agent") {
                    navigate("/agent");
                } else {
                    alert("User role not recognized.");
                }
            }
        } catch (err) {
            console.error("Login error:", err);
            alert("Login failed. Please check your credentials.");
        }
    }

    const handleChallenge = async () => {
        const input = { // RespondToAuthChallengeRequest
            ClientId: clientId, // required
            ChallengeName: "NEW_PASSWORD_REQUIRED",
            Session: session,
            ChallengeResponses: {
                "NEW_PASSWORD": password, "USERNAME": email
            },
        };
        const command = new RespondToAuthChallengeCommand(input);
        const response = await cognitoClient.send(command);
        console.log(response)
        if (response['$metadata']['httpStatusCode'] === 200) { alert("Password Changed Successfully!"); setView('login') }
    }

    return (
        view === "login" ? (
            <div className={styles.container}>
                <div className={styles.logoWrapper}>
                    <h1 className={styles.logoText}>Scrooge</h1>
                    <label className={styles.logoText2}>bank</label>
                </div>
                <div className={styles.box}>
                    <div className={styles.leftPanel}>
                        <h1 className={styles.title}>Log In</h1>
                        <p className={styles.subtext}>Log into our CRM system, at your fingertips</p>

                        <label className={styles.inputLabel}>Email</label>
                        <input
                            type="text"
                            placeholder="Enter email"
                            className={styles.inputField}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />

                        <label className={styles.inputLabel}>Password</label>
                        <input
                            type="password"
                            placeholder="Enter password"
                            className={styles.inputField}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />

                        <button className={styles.signInButton} onClick={handleLogin}>Log in</button>
                    </div>
                </div>
            </div>
        ) : (
            <div className={styles.container}>
                <div className={styles.logoWrapper}>
                    <h1 className={styles.logoText}>Scrooge</h1>
                    <label className={styles.logoText2}>bank</label>
                </div>
                <div className={styles.box}>
                    <div className={styles.leftPanel}>
                        <h1 className={styles.title}>Reset password</h1>
                        <p className={styles.subtext}>You are required to rest your password on first login</p>

                        <input
                            className={styles.inputField}
                            placeholder='Enter new password'
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                        />
                        <button className={styles.signInButton} onClick={handleChallenge}>Save new password</button>
                    </div>
                </div>
            </div>
        )
    );
}

export default Login;
