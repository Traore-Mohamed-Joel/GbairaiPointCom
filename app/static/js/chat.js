
const token = sessionStorage.getItem("access_token");

const chatContainer = document.querySelector(".chat-container");
const groupId = chatContainer.dataset.groupId;

const messagesList = document.getElementById("messages-list");
const messageForm = document.getElementById("message-form");
const imageForm = document.getElementById("image-form");
const chatMessage = document.getElementById("chat-message");

if (!token) {
    window.location.href = "/login";
}

// Communiquer avec FastAPI
async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            Authorization: `Bearer ${token}`,
        },
    });

    const result = await response.json();

    if (response.status === 401) {
        sessionStorage.removeItem("access_token");
        window.location.href = "/login";
        throw new Error("Session expirée.");
    }

    if (!response.ok) {
        throw new Error(result.detail || "Une erreur est survenue.");
    }

    return result;
}

// Afficher un message dans son propre bloc
function displayMessage(message) {
    const article = document.createElement("article");
    article.className = "message-item";

    // Auteur
    const author = document.createElement("strong");
    author.className = "message-author";
   author.textContent = message.username || "Utilisateur";

    article.appendChild(author);

    // Contenu texte
    if (message.content) {
        const content = document.createElement("p");
        content.className = "message-content";
        content.textContent = message.content;

        article.appendChild(content);
    }

    // Image
    if (message.message_type === "image" && message.image_path) {
        const image = document.createElement("img");
        image.className = "message-image";
        image.src = message.image_path;
        image.alt = "Image envoyée dans le groupe";

        article.appendChild(image);
    }

    // Date
    const date = document.createElement("small");
    date.className = "message-date";
    date.textContent = new Date(message.created_at).toLocaleString("fr-FR");

    article.appendChild(date);

    // Ajouter le bloc à la liste
    messagesList.appendChild(article);
}

// Charger les anciens messages
async function loadMessages() {
    messagesList.textContent = "Chargement des messages...";

    try {
        const messages = await apiRequest(
            `/groups/${groupId}/messages`
        );

        messagesList.replaceChildren();

        if (!Array.isArray(messages)) {
            throw new Error("Réponse incorrecte du serveur.");
        }

        if (messages.length === 0) {
            messagesList.textContent = "Aucun message pour le moment.";
            return;
        }

        messages.forEach((message) => {
            displayMessage(message);
        });

        messagesList.scrollTop = messagesList.scrollHeight;

    } catch (error) {
        messagesList.textContent = error.message;
        chatMessage.textContent = error.message;
        chatMessage.className = "error";

        console.error("Erreur de chargement :", error);
    }
}

// Envoyer un message texte
messageForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const input = document.getElementById("message-content");
    const content = input.value.trim();

    if (!content) return;

    try {
        const newMessage = await apiRequest(
            `/groups/${groupId}/messages`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ content }),
            }
        );

        if (!messagesList.querySelector(".message-item")) {
            messagesList.replaceChildren();
        }

        displayMessage(newMessage);

        messagesList.scrollTop = messagesList.scrollHeight;

        input.value = "";
        chatMessage.textContent = "";

    } catch (error) {
        chatMessage.textContent = error.message;
        chatMessage.className = "error";

        console.error("Erreur d'envoi du texte :", error);
    }
});

// Envoyer une image
imageForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const input = document.getElementById("image-file");
    const file = input.files[0];

    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
        chatMessage.textContent = "L'image ne doit pas dépasser 5 Mo.";
        chatMessage.className = "error";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
        const newMessage = await apiRequest(
            `/groups/${groupId}/images`,
            {
                method: "POST",
                body: formData,
            }
        );

        if (!messagesList.querySelector(".message-item")) {
            messagesList.replaceChildren();
        }

        displayMessage(newMessage);

        messagesList.scrollTop = messagesList.scrollHeight;

        imageForm.reset();
        chatMessage.textContent = "";

    } catch (error) {
        chatMessage.textContent = error.message;
        chatMessage.className = "error";

        console.error("Erreur d'envoi de l'image :", error);
    }
});

// Charger les messages au démarrage
loadMessages();
