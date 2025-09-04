# Secure Finance Management Web Application

A secure, full-stack financial management application that allows users to register, log in, manage personal transactions, and gain insights through a conversational AI and interactive data visualizations.

<p align="center">
  <a href="https://finance-tracker-web-iwx8.onrender.com"> <img src="https://img.shields.io/badge/Live-Demo-brightgreen?style=for-the-badge&logo=render" alt="Live Demo"/>
  </a>
</p>

---

### Key Features ✨

* **Secure User Authentication:** Users can register and log in via a secure system using JWT (JSON Web Tokens). Passwords are fully hashed and salted.
* **Full CRUD for Transactions:** Logged-in users can create, read, and delete their individual financial transactions.
* **Data Visualization:** Generate a **Pie Chart** to see spending distribution by category or a **Line Chart** to track spending patterns over time.
* **AI-Powered Chatbot:** Interact with your financial data by asking questions in natural language. The system handles specific queries locally and forwards complex questions to an external AI service.
* **Secure Account Deletion:** Users have the option to permanently and securely delete their account and all associated data.
* **Responsive Design:** A clean, modern interface that works seamlessly on both desktop and mobile devices.

<p align="center">
  <img width="1195" height="782" alt="Live Website" src="https://github.com/user-attachments/assets/fa3ac87a-169d-4ff5-a497-53a4b226901b" />

</p>

---

## Tech Stack 🛠️

* **Backend:** Python, FastAPI, SQLAlchemy (ORM)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Database:** PostgreSQL
* **Authentication:** JWT (JSON Web Tokens), Passlib, python-jose
* **Deployment:** Render

---

## Architecture Overview 🏗️

This project is deployed on Render using a modern, decoupled architecture for scalability and security.

* **Backend API:** Hosted as a **Web Service** on Render, running a FastAPI server with Uvicorn.
* **Frontend Application:** Deployed as a **Static Site** on Render, which serves the content globally via a CDN for fast load times.
* **Database:** A managed **PostgreSQL** instance on Render, connected to the backend via a secure internal network connection.

---

## Environment Variables for Development 🔑

For developers looking to contribute or run this project locally, a `.env` file must be created in the root directory with the following variables:
.env file
<p>DATABASE_URL="postgresql://YOUR_LOCAL_DB_USER:YOUR_PASSWORD@localhost/YOUR_DB_NAME"</p>
<p>SECRET_KEY="YOUR_SUPER_SECRET_RANDOM_STRING"</p>
<p>API_KEY="YOUR_AI_SERVICE_API_KEY_HERE"</p>
> **Note:** The `API_KEY` can be obtained from services like [asi1.ai](https://asi1.ai/dashboard/api-keys).
## Contributing 🤝

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

You can also reach out to me via [LinkedIn](https://www.linkedin.com/in/lakshit-sachdeva-998936292/) if you'd like to collaborate on future projects!
