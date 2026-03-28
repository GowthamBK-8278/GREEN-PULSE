// ============================================
// GREEN PULSE — Firebase Configuration
// ============================================
// IMPORTANT: Replace the values below with your
// Firebase project credentials from:
// https://console.firebase.google.com → Project Settings → Web App
// ============================================

const firebaseConfig = {
  apiKey: "AIzaSyDFPaIqYGTqELrIezSLjny-rp7b8WZYj_I",
  authDomain: "green-pulse-72e03.firebaseapp.com",
  projectId: "green-pulse-72e03",
  storageBucket: "green-pulse-72e03.firebasestorage.app",
  messagingSenderId: "380950203254",
  appId: "1:380950203254:web:11e3b9b4311ce30d9cc857",
  measurementId: "G-S8YR5K0R46"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

// ============ Auth Helper Functions ============

// Check if user is logged in (use on protected pages)
function requireAuth() {
    auth.onAuthStateChanged(user => {
        if (!user) {
            window.location.href = 'index.html';
        }
    });
}

// Get current user info
function getCurrentUser() {
    return auth.currentUser;
}

// Sign out
function signOut() {
    auth.signOut().then(() => {
        localStorage.clear();
        window.location.href = 'index.html';
    });
}
