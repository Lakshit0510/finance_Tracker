async function sendQuery() {
    let query = document.getElementById("query").value;
    let chatBox = document.getElementById("chat-box");
    chatBox.innerHTML += `<p><strong>You:</strong> ${query}</p>`;
    document.getElementById("query").value = "";

    let response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userid: "user123", query: query })
    });

    let data = await response.json();
    chatBox.innerHTML += `<p><strong>Agent:</strong> ${data.response}</p>`;
}