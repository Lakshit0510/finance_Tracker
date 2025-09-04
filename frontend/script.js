// At the very top of script.js, check for authentication
const token = localStorage.getItem("userToken");
if (!token) {
    window.location.href = "login.html"; // If no token, redirect to login
}

document.addEventListener("DOMContentLoaded", () => {
    // --- Element References ---
    const chatBox = document.getElementById("chat-box");
    const welcomeMessage = document.getElementById("welcome-message");
    const logoutBtn = document.getElementById("logout-btn");
    const queryInput = document.getElementById("query-input");
    const sendBtn = document.getElementById("send-btn");

    // Chart Elements
    const showCategoryChartBtn = document.getElementById("show-category-chart-btn");
    const showTimeChartBtn = document.getElementById("show-time-chart-btn");
    const chartCanvas = document.getElementById("myChart");
    let currentChart = null;

    // Transaction Form Elements
    const toggleFormBtn = document.getElementById("toggle-form-btn");
    const transactionForm = document.getElementById("add-transaction-form");
    const addTxBtn = document.getElementById("add-tx-btn");
    const txAmountInput = document.getElementById("tx-amount");
    const txClassInput = document.getElementById("tx-class");
    const txTimeInput = document.getElementById("tx-time");
    const transactionList = document.getElementById("transaction-list");
    const deleteAccountBtn = document.getElementById("delete-account-btn");

    const API_BASE_URL = "https://finance-tracker-lbql.onrender.com";

    // --- Initial Setup ---
    fetchCurrentUser();
    fetchAndDisplayTransactions();
    setDefaultDate();

    // --- Event Listeners ---
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("userToken");
        window.location.href = "login.html";
    });
    sendBtn.addEventListener("click", sendQuery);
    queryInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendQuery();
    });
    toggleFormBtn.addEventListener("click", () => transactionForm.classList.toggle("hidden"));
    addTxBtn.addEventListener("click", addTransaction);
    showCategoryChartBtn.addEventListener("click", () => renderChart('category'));
    showTimeChartBtn.addEventListener("click", () => renderChart('time'));
    deleteAccountBtn.addEventListener("click", handleDeleteAccount);
    transactionList.addEventListener("click", (e) => {
        if (e.target && e.target.classList.contains("delete-tx-btn")) {
            const txId = e.target.getAttribute("data-id");
            handleDeleteTransaction(txId);
        }
    });

    // --- Core Functions ---
    async function fetchCurrentUser() {
        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/users/me`);
            const user = await response.json();
            welcomeMessage.textContent = `Welcome, ${user.username}!`;
        } catch (error) {
            console.error("Failed to fetch user:", error);
            // If token is invalid, log out
            localStorage.removeItem("userToken");
            window.location.href = "login.html";
        }
    }

    async function sendQuery() {
        const query = queryInput.value.trim();
        if (!query) return;

        appendMessage(`You: ${query}`, "user-message");
        queryInput.value = "";

        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/query`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query }),
            });
            const data = await response.json();
            appendMessage(`Agent: ${data.response}`, "agent-message");
        } catch (error) {
            appendMessage(`Error: ${error.message}`, 'agent-message');
        }
    }

    async function addTransaction() {
        const amount = parseFloat(txAmountInput.value);
        const className = txClassInput.value.trim();
        const time = txTimeInput.value;

        if (isNaN(amount) || amount === 0 || !className || !time) {
            alert("Please fill out all transaction fields correctly.");
            return;
        }

        try {
            await fetchWithAuth(`${API_BASE_URL}/add_transaction`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ amount, class_name: className, time }),
            });
            appendMessage(`Successfully added transaction.`, "system-notification");
            fetchAndDisplayTransactions();
            txAmountInput.value = "";
            txClassInput.value = "";
            setDefaultDate();
            transactionForm.classList.add("hidden");
        } catch (error) {
            appendMessage(`Error: ${error.message}`, 'agent-message');
        }
    }

    async function renderChart(type) {
        const endpoint = type === 'category' ? `${API_BASE_URL}/plot/spending_by_category` : `${API_BASE_URL}/plot/spending_over_time`;
        const chartType = type === 'category' ? 'pie' : 'line';
        
        try {
            const response = await fetchWithAuth(endpoint);
            const plotData = await response.json();

            if (plotData.labels.length === 0) {
                if(currentChart) currentChart.destroy();
                alert(`No data available to plot.`);
                return;
            }

            const ctx = chartCanvas.getContext('2d');
            if (currentChart) currentChart.destroy();

            currentChart = new Chart(ctx, {
                type: chartType,
                data: {
                    labels: plotData.labels,
                    datasets: [{
                        label: `Spending by ${type}`,
                        data: plotData.data,
                        backgroundColor: ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2'],
                        borderColor: '#fff',
                        borderWidth: 1
                    }]
                },
                options: { responsive: true }
            });
        } catch (error) {
            console.error("Error rendering chart:", error);
        }
    }
    async function fetchAndDisplayTransactions() {
        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/transactions`);
            const transactions = await response.json();
            
            transactionList.innerHTML = ""; // Clear the list
            if (transactions.length === 0) {
                transactionList.innerHTML = "<li class='empty-state'>No transactions yet.</li>";
                return;
            }

            transactions.forEach(tx => {
                const isExpense = tx.amount > 0;
                const li = document.createElement("li");
                li.innerHTML = `
                    <div class="transaction-details">
                        <span class="transaction-class">${tx.class_name}</span>
                        <span class="transaction-info">${tx.time}</span>
                    </div>
                    <div class="transaction-amount ${isExpense ? 'expense' : 'income'}">
                        ${isExpense ? '-' : '+'}$${Math.abs(tx.amount).toFixed(2)}
                    </div>
                    <button class="delete-tx-btn" data-id="${tx.id}" title="Delete Transaction">&times;</button>
                `;
                transactionList.appendChild(li);
            });
        } catch (error) {
            console.error("Failed to fetch transactions:", error);
            transactionList.innerHTML = "<li class='empty-state'>Error loading transactions.</li>";
        }
    }

    async function handleDeleteTransaction(transactionId) {
        if (!confirm("Are you sure you want to delete this transaction?")) {
            return;
        }

        try {
            await fetchWithAuth(`${API_BASE_URL}/transactions/${transactionId}`, {
                method: "DELETE",
            });
            // Refresh the list after successful deletion
            fetchAndDisplayTransactions(); 
        } catch (error) {
            console.error("Failed to delete transaction:", error);
            alert(`Error: ${error.message}`);
        }
    }

    async function handleDeleteAccount() {
        const confirmation = prompt("This will permanently delete your account and all data. To confirm, please type 'DELETE' in the box below.");
        if (confirmation !== "DELETE") {
            alert("Deletion cancelled.");
            return;
        }

        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/users/me`, { method: "DELETE" });
            const result = await response.json();
            alert(result.message);
            
            localStorage.removeItem("userToken");
            window.location.href = "login.html";
        } catch (error) {
            console.error("Failed to delete account:", error);
            alert(`Error deleting account: ${error.message}`);
        }
    }

    // --- Helper Functions ---
    async function fetchWithAuth(url, options = {}) {
        const token = localStorage.getItem("userToken");
        const headers = { ...options.headers, "Authorization": `Bearer ${token}` };
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) { // Unauthorized
            localStorage.removeItem("userToken");
            window.location.href = "login.html";
            throw new Error("Session expired. Please log in again.");
        }
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "An API error occurred");
        }
        return response;
    }

    function appendMessage(text, className) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${className}`;
        messageElement.innerText = text; // Use innerText to preserve line breaks
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function setDefaultDate() {
        const now = new Date();
        txTimeInput.value = now.toISOString().split('T')[0];
    }
});