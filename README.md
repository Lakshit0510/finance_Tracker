# Finance Processing Agent & Chatbot

A web-based financial chatbot that allows users to manage and inquire about their personal financial transactions through a conversational interface. The application features data visualizations, dynamic transaction management, and a flexible backend capable of integrating with large language models for complex queries.



## ✨ Features

* **Conversational UI:** Interact with your financial data by asking questions in natural language.
* **Dynamic User Management:** Add new users and switch between existing user profiles on the fly.
* **Transaction Management:** Add new transactions (expenses) directly through a form in the interface.
* **Data Visualization:**
    * Generate a **Pie Chart** to see spending distribution by category.
    * Generate a **Line Chart** to track spending patterns over time.
* **Dual Query Processing:**
    * **Local Functions:** Handles common queries like "spending breakdown" or "largest expense category" instantly for fast results.
    * **AI Integration:** Forwards complex or undefined questions to an external AI service for intelligent responses (requires API key).
* **Responsive Design:** A clean and modern interface that works on various screen sizes.

---
<img width="200" height="250" alt="Screenshot 2025-07-23 184646" src="https://github.com/user-attachments/assets/74140042-4ca6-4b42-afeb-d0255ef5f6de" />

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, Pandas, Uvicorn
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Data Visualization:** Chart.js
* **API Interaction:** `requests` (Python), `fetch` (JavaScript)

---

## 🚀 Getting Started

Follow these instructions to set up and run the project on your local machine.

### Prerequisites

* [Python 3.7+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads/)
* A web browser

### Installation & Setup

1.  **Clone the repository:**
    
    ```bash
    git clone https://github.com/Lakshit0510/finance_Tracker.git
    cd finance_tracker
    ```

2.  **Set up the Backend:**
    * **Create and activate a virtual environment:**
        ```bash
        # For macOS/Linux
        python3 -m venv venv
        source venv/bin/activate

        # For Windows
        python -m venv venv
        venv\Scripts\activate
        ```
    * **Install the required dependencies:**
        ```bash
        pip install -r requirements.txt
        ```
    * **Create the environment file:** Create a file named `.env` in the root of the project directory. This is where you'll store your secret API key.
        ```
        API_KEY="YOUR_AI_SERVICE_API_KEY_HERE"
        ```
        > **Note:** The backend is configured to use a placeholder AI service URL.You can visit https://asi1.ai/dashboard/api-keys to get it for free to use.

3.  **Run the Application:**
    * **Start the backend server:**
        ```bash
        uvicorn Working:app --reload
        ```
        The server will be running at `http://127.0.0.1:8000`.

    * **Launch the frontend:** Open the `frontend/index.html` file in your web browser.

---

## 📖 How to Use

1.  **Select a User:** Use the dropdown at the top to select an existing user.
2.  **Add a New User:** If you are new, type a User ID in the "New User ID" field and click "Add User". You will be automatically selected.
3.  **Generate Visualizations:** Click the "Spending by Category" or "Spending Over Time" buttons to generate interactive plots for the selected user.
4.  **Add a Transaction:**
    * Click the "Add New Transaction" button to open the form.
    * Fill in the Amount, Category, and Date.
    * Click "Submit Transaction".
5.  **Ask a Question:** Type a query into the chat input at the bottom and press Enter or click "Send".

    **Example Queries:**
    * `What is my total spending?`
    * `Show me a spending breakdown`
    * `What is my largest expense category?`
    * `What was my most expensive shopping purchase?` (This will be sent to the AI)

---
