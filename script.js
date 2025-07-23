document.addEventListener("DOMContentLoaded", () => {
    // --- Element References ---
    const queryInput = document.getElementById("query-input");
    const sendBtn = document.getElementById("send-btn");
    const chatBox = document.getElementById("chat-box");
    const loadingIndicator = document.getElementById("loading-indicator");
    const userSelect = document.getElementById("user-select");
    const addUserBtn = document.getElementById("add-user-btn");
    const newUserInput = document.getElementById("new-user-input");
    const toggleFormBtn = document.getElementById("toggle-form-btn");
    const transactionForm = document.getElementById("add-transaction-form");
    const addTxBtn = document.getElementById("add-tx-btn");
    const txAmountInput = document.getElementById("tx-amount");
    const txClassInput = document.getElementById("tx-class");
    const txTimeInput = document.getElementById("tx-time");

    // Chart Elements
    const showCategoryChartBtn = document.getElementById("show-category-chart-btn");
    const showTimeChartBtn = document.getElementById("show-time-chart-btn");
    const chartCanvas = document.getElementById("myChart");
    let currentChart = null; 

    const API_BASE_URL = "http://127.0.0.1:8000";

    // --- Initial Setup ---
    populateUserDropdown();
    setDefaultDate(); 

    // --- Event Listeners ---
    sendBtn.addEventListener("click", sendQuery);
    queryInput.addEventListener("keypress", (event) => { if (event.key === "Enter") sendQuery(); });
    addUserBtn.addEventListener("click", addNewUser);
    newUserInput.addEventListener("keypress", (event) => { if (event.key === "Enter") addNewUser(); });
    toggleFormBtn.addEventListener("click", () => transactionForm.classList.toggle("hidden"));
    addTxBtn.addEventListener("click", addTransaction);
    showCategoryChartBtn.addEventListener("click", () => renderChart('category'));
    showTimeChartBtn.addEventListener("click", () => renderChart('time'));

    // --- Charting Function ---
    async function renderChart(type) {
        const userId = userSelect.value;
        if (!userId) {
            alert("Please select a user first.");
            return;
        }

        let endpoint = '';
        let chartType = '';
        let chartLabel = '';

        if (type === 'category') {
            endpoint = `${API_BASE_URL}/plot/spending_by_category?userid=${userId}`;
            chartType = 'pie';
            chartLabel = 'Spending by Category';
        } else {
            endpoint = `${API_BASE_URL}/plot/spending_over_time?userid=${userId}`;
            chartType = 'line';
            chartLabel = 'Spending Over Time';
        }

        try {
            const response = await fetch(endpoint);
            const plotData = await response.json();

            if (plotData.labels.length === 0) {
                alert(`No data available to plot for user '${userId}'.`);
                if(currentChart) currentChart.destroy(); // Clear old chart if new data is empty
                return;
            }

            const ctx = chartCanvas.getContext('2d');
            if (currentChart) {
                currentChart.destroy();
            }

            currentChart = new Chart(ctx, {
                type: chartType,
                data: {
                    labels: plotData.labels,
                    datasets: [{
                        label: chartLabel,
                        data: plotData.data,
                        backgroundColor: ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2', '#fd7e14', '#e83e8c'],
                        borderColor: chartType === 'line' ? '#007bff' : '#fff',
                        borderWidth: chartType === 'line' ? 2 : 1,
                        fill: chartType === 'line' ? false : true,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        title: { display: true, text: `${chartLabel} for ${userId}` }
                    }
                }
            });

        } catch (error) {
            console.error("Error rendering chart:", error);
            alert("Could not load chart data.");
        }
    }

    // --- Core Functions ---
    async function populateUserDropdown() {
        try {
            const response = await fetch(`${API_BASE_URL}/get_users`);
            const data = await response.json();
            userSelect.innerHTML = "";
            if (data.users && data.users.length > 0) {
                data.users.forEach(user => {
                    const option = document.createElement("option");
                    option.value = user;
                    option.textContent = user;
                    userSelect.appendChild(option);
                });
            } else {
                appendMessage("No users found. Add a new user to begin.", "system-notification");
            }
        } catch (error) {
            console.error("Error fetching users:", error);
            appendMessage("Could not fetch user list from the server.", "system-notification");
        }
    }

    function addNewUser() {
        const newUserId = newUserInput.value.trim();
        if (!newUserId) { alert("Please enter a User ID."); return; }
        const userExists = [...userSelect.options].some(option => option.value === newUserId);
        if (userExists) { alert(`User '${newUserId}' already exists.`); return; }

        const option = document.createElement("option");
        option.value = newUserId;
        option.textContent = newUserId;
        userSelect.appendChild(option);
        userSelect.value = newUserId;
        newUserInput.value = "";
        appendMessage(`User '${newUserId}' has been added and selected.`, "system-notification");
    }

    async function sendQuery() {
        const query = queryInput.value.trim();
        const userId = userSelect.value;
        if (!query) return;
        if (!userId) { appendMessage("Please select or add a user first.", "system-notification"); return; }
        
        appendMessage(query, 'user-message');
        queryInput.value = "";
        showLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/query`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userid: userId, query: query })
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const data = await response.json();
            appendMessage(data.response, 'agent-message');
        } catch (error) {
            console.error("Error fetching response:", error);
            appendMessage("Sorry, something went wrong. Please check the console.", 'agent-message');
        } finally {
            showLoading(false);
        }
    }

    async function addTransaction() {
        const userId = userSelect.value;
        const amount = parseFloat(txAmountInput.value);
        const className = txClassInput.value.trim();
        const time = txTimeInput.value;

        if (!userId || isNaN(amount) || amount <= 0 || !className || !time) {
            alert("Please fill out all transaction fields correctly.");
            return;
        }

        const transactionData = { userid: userId, amount: amount, class_name: className, time: time };

        try {
            const response = await fetch(`${API_BASE_URL}/add_transaction`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(transactionData)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || "Failed to add transaction");
            
            appendMessage(`Successfully added transaction for ${userId}.`, "system-notification");
            txAmountInput.value = "";
            txClassInput.value = "";
            setDefaultDate();
            transactionForm.classList.add("hidden");
        } catch (error) {
            console.error("Error adding transaction:", error);
            appendMessage(`Error: ${error.message}`, 'agent-message');
        }
    }

    // --- Helper Functions ---
    function appendMessage(text, className) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${className}`;
        messageElement.textContent = text;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function showLoading(isLoading) {
        loadingIndicator.classList.toggle("hidden", !isLoading);
        queryInput.disabled = isLoading;
        sendBtn.disabled = isLoading;
        if (!isLoading) queryInput.focus();
    }
    
    function setDefaultDate() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        txTimeInput.value = `${year}-${month}-${day}`;
    }
});
