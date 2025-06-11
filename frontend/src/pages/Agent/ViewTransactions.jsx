import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../../components/DashboardLayout";
import styles from "./ViewTransactions.module.css"; // Reuse your existing styles

function ViewTransactions() {
    const navigate = useNavigate();
    const [transactions, setTransactions] = useState([]);

    useEffect(() => {
        const fetchTransactions = async () => {
            try {
                const res = await fetch("http://ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/transaction/get");
                
                if (!res.ok) {
                    const errorText = await res.text(); // fallback if not JSON
                    console.error("Transaction fetch failed:", res.status, errorText);
                    return;
                }

                const data = await res.json();

                if (data.code === 200) {
                    const mapped = data.data.map((txn, index) => ({
                        id: txn.id || index,
                        type: txn.transaction_type === "D" ? "Deposit" : "Withdrawal",
                        amount: `$${txn.amount.toFixed(2)}`,
                        date: txn.date,
                        client_id: txn.client_id,
                    }));

                    // Optional: fetch all clients and match names
                    const clientsRes = await fetch("http://ecs-loadbalancer-team3-1853091125.ap-southeast-1.elb.amazonaws.com/api/client/get/all");
                    const clientsData = await clientsRes.json();

                    if (clientsData && Array.isArray(clientsData)) {
                        mapped.forEach(txn => {
                            const client = clientsData.find(c => c.client_id === txn.client_id);
                            if (client) txn.client_name = client.name;
                        });
                    }

                    setTransactions(mapped);
                }
            } catch (err) {
                console.error("Failed to fetch transactions:", err);
            }
        };

        fetchTransactions();
    }, []);

    return (
        <DashboardLayout title="View all transactions" subtitle="See the full client transaction history">
            <div className={styles.transactionBox}>
                {transactions.map((txn) => (
                    <div key={txn.id} className={styles.transactionItem}>
                        <p className={styles.txnType}>{txn.type}</p>
                        <p className={styles.txnAmount}>{txn.amount}</p>
                        <p className={styles.txnDate}>Client ID: {txn.client_id}</p>
                    </div>
                ))}
            </div>
            <button onClick={() => navigate("/agent")} className={styles.backButton}>
                ← Back to Dashboard
            </button>
        </DashboardLayout>
    );
}

export default ViewTransactions;
