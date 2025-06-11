import React, { useEffect, useRef } from "react";
import logoutIcon from "../assets/logout_icon.png"
import profilepic from "../assets/profilepic.png"
import { useNavigate } from 'react-router-dom';


function ProfileModal({ isOpen, onClose, user }) {
    const navigate = useNavigate(); // ⬅️ Initialize navigation
    const modalRef = useRef(null); // ⬅️ Ref to detect clicks outside
    
     // Close modal if user clicks outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (modalRef.current && !modalRef.current.contains(event.target)) {
                onClose(); // ⬅️ Close modal
            }
        }

        // Attach event listener when modal is open
        if (isOpen) {
            document.addEventListener("mousedown", handleClickOutside);
        }

        // Cleanup event listener on unmount
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [isOpen, onClose]);


    if (!isOpen) return null;

    const handleLogout = () => {
        localStorage.removeItem("accessToken");
        navigate("/login");
    };

    return (
        <div className="absolute right-20 top-22 mt-2 w-80 bg-white shadow-lg rounded-lg p-4 z-50">
            {/* Modal Box */}
            <div>
                {/* Profile Header */}
                <div className="flex flex-col items-center">
                    <img
                        src={profilepic}
                        alt="Profile"
                        className="w-16 h-16 rounded-full"
                    />
                    <h3 className="mt-2 text-lg font-semibold">{user.name}</h3>
                    <p className="text-gray-500 text-sm">{user.email}</p>
                </div>

                {/* Logout Button */}
                <button
                    className="w-full flex items-center justify-between mt-4 p-3 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                    onClick={handleLogout} // Replace with logout function
                >
                    <span className="flex items-center space-x-2">
                        <img src={logoutIcon} alt="logout" className="w-6 h-6 inline-block mr-2"/>
                        <span>Logout</span>
                    </span>
                    <span>➡️</span>
                </button>
            </div>
        </div>
    );
}

export default ProfileModal;
