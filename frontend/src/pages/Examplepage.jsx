// AdminHistoryPage.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import styles from "../components/DashboardLayout"; // Reuse your existing styles

const transactions = [
    { id: 1, type: "Payment Received", amount: "$150.00", date: "2025-04-09" },
    { id: 2, type: "Refund Issued", amount: "-$40.00", date: "2025-04-08" },
    { id: 3, type: "Subscription Renewal", amount: "$25.00", date: "2025-04-07" },
    { id: 4, type: "Account Credit", amount: "$10.00", date: "2025-04-05" },
];

function Examplepage() {
    const navigate = useNavigate();

    return (
        <DashboardLayout title="View all history" subtitle="See the full admin history">
            <div className={styles.transactionBox}>
                {transactions.map((txn) => (
                    <div key={txn.id} className={styles.transactionItem}>
                        <p className={styles.txnType}>{txn.type}</p>
                        <p className={styles.txnAmount}>{txn.amount}</p>
                        <p className={styles.txnDate}>{txn.date}</p>
                    </div>
                ))}
            </div>
            <button onClick={() => navigate("/admin")} className={styles.backButton}>
                ← Back to Dashboard
            </button>
        </DashboardLayout>
    );
}

export default Examplepage;
