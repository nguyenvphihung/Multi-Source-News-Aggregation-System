import { initializeApp } from "https://www.gstatic.com/firebasejs/11.1.0/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/11.1.0/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyATa3PDtgT06iQow__oQkYZwbxzOSQWlLQ",
    authDomain: "newspapernaivebayes.firebaseapp.com",
    projectId: "newspapernaivebayes",
    storageBucket: "newspapernaivebayes.appspot.com",
    messagingSenderId: "375140229633",
    appId: "1:375140229633:web:bb3968c03ee4253b621600",
    measurementId: "G-N8EB8J1MMQ"
};

// Khởi tạo Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { auth, onAuthStateChanged, signOut };
