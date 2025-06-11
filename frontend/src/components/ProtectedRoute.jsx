import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";


export default function PrivateRoute({ children, requiredRole }) {
    const token = localStorage.getItem("idToken");
    const userRole = localStorage.getItem("userRole"); // ✅ Grab stored role

    if (!token) {
        return <Navigate to="/login" replace />;
    }

    try {
        console.log("🔐 Decoded role from token:", userRole);

        if (requiredRole && userRole !== requiredRole) {
            console.warn("❌ Role mismatch:", { expected: requiredRole, got: userRole });
            return <Navigate to="/error" replace />;
        }

        return children;
    } catch (e) {
        return <Navigate to="/login" replace />;
    }
}


