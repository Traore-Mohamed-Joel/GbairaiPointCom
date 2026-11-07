
const token = sessionStorage.getItem("access_token");

const message = document.getElementById("message");
const groupsList = document.getElementById("groups-list");

// Vérifier la connexion
if (!token) {
    window.location.replace("/login");
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
        window.location.replace("/login");
        throw new Error("Session expirée.");
    }

    if (!response.ok) {
        throw new Error(result.detail || "Une erreur est survenue.");
    }

    return result;
}

// Afficher un message
function showMessage(text, type = "success") {
    message.textContent = text;
    message.className = type;
}

// Charger les groupes
async function loadGroups() {
    try {
        const groups = await apiRequest("/groups/");

        groupsList.replaceChildren();

        if (groups.length === 0) {
            groupsList.textContent = "Tu n'as encore aucun groupe.";
            return;
        }

        groups.forEach((group) => {
    // Toute la carte devient un lien vers la discussion
    const card = document.createElement("a");
    card.href = `/groups/${group.id}/chat`;
    card.className = "dashboard-card group-card";

    const title = document.createElement("h3");
    title.textContent = group.name;

    const description = document.createElement("p");
    description.textContent =
        group.description || "Aucune description.";

    const id = document.createElement("small");
    id.textContent = `Identifiant : ${group.id}`;

    card.append(title, description, id);
    groupsList.appendChild(card);
});

    } catch (error) {
        showMessage(error.message, "error");
        groupsList.textContent = "Impossible de charger les groupes.";
    }
}

// Créer un groupe
document.getElementById("create-group-form")
    .addEventListener("submit", async (event) => {

        event.preventDefault();

        const name = document.getElementById("group-name").value.trim();

        const description =
            document.getElementById("group-description").value.trim();

        try {
            await apiRequest("/groups/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    name,
                    description: description || null,
                }),
            });

            showMessage("Groupe créé avec succès !");

            event.target.reset();

            await loadGroups();

        } catch (error) {
            showMessage(error.message, "error");
        }
    });

// Rejoindre un groupe
document.getElementById("join-group-form")
    .addEventListener("submit", async (event) => {

        event.preventDefault();

        const groupId = document.getElementById("group-id").value;

        try {
            const result = await apiRequest(
                `/groups/${groupId}/join`,
                { method: "POST" }
            );

            showMessage(result.message);

            event.target.reset();

            await loadGroups();

        } catch (error) {
            showMessage(error.message, "error");
        }
    });

// Déconnexion
document.getElementById("logout-button")
    .addEventListener("click", () => {

        sessionStorage.removeItem("access_token");
        window.location.replace("/login");
    });

// Charger les groupes au démarrage
loadGroups();
