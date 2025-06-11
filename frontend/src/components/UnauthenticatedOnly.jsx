import { Navigate } from "react-router-dom";

export default function UnauthenticatedOnly({ children }) {
    const token = localStorage.getItem("accessToken");

    if (token) {
        return <Navigate to="/" replace />; // or redirect based on decoded role
    }

    return children;
}   
