
const token = sessionStorage.getItem("access_token");

const message = document.getElementById("message");
const groupsList = document.getElementById("groups-list");

let currentUser = null;

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

// Charger le profil connecté
async function loadCurrentUser() {
    currentUser = await apiRequest("/me");
}

// Afficher les membres d'un groupe
async function showMembers(groupId, membersContainer) {
    try {
        const members = await apiRequest(
            `/groups/${groupId}/members`
        );

        membersContainer.replaceChildren();

        const title = document.createElement("h4");
        title.textContent = "Membres du groupe";
        membersContainer.appendChild(title);

        if (members.length === 0) {
            membersContainer.textContent = "Aucun membre.";
            return;
        }

        members.forEach((member) => {
            const item = document.createElement("p");

            item.textContent =
                `${member.username} — ${member.role}`;

            membersContainer.appendChild(item);
        });

    } catch (error) {
        showMessage(error.message, "error");
    }
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
            const card = document.createElement("div");
            card.className = "dashboard-card group-card";

            // Lien vers la discussion
            const link = document.createElement("a");
            link.href = `/groups/${group.id}/chat`;
            link.className = "group-link";

            const title = document.createElement("h3");
            title.textContent = group.name;

            const description = document.createElement("p");
            description.textContent =
                group.description || "Aucune description.";

            const id = document.createElement("small");
            id.textContent = `Identifiant : ${group.id}`;

            link.append(title, description, id);

            // Zone des actions
            const actions = document.createElement("div");
            actions.className = "group-actions-buttons";

            // Bouton Voir les membres
            const membersButton = document.createElement("button");
            membersButton.type = "button";
            membersButton.textContent = "Voir les membres";

            const membersContainer = document.createElement("div");
            membersContainer.className = "group-members";
            membersContainer.hidden = true;

            membersButton.addEventListener("click", async () => {
                if (membersContainer.hidden) {
                    membersContainer.hidden = false;
                    await showMembers(group.id, membersContainer);
                } else {
                    membersContainer.hidden = true;
                }
            });

            actions.appendChild(membersButton);

            // Vérifier si l'utilisateur est le créateur
            const isCreator = group.created_by === currentUser.id;

            if (isCreator) {
                // Bouton Supprimer le groupe
                const deleteButton = document.createElement("button");
                deleteButton.type = "button";
                deleteButton.textContent = "Supprimer le groupe";

                deleteButton.addEventListener("click", async () => {
                    const confirmed = window.confirm(
                        `Veux-tu vraiment supprimer le groupe "${group.name}" ?`
                    );

                    if (!confirmed) return;

                    try {
                        const result = await apiRequest(
                            `/groups/${group.id}`,
                            { method: "DELETE" }
                        );

                        showMessage(result.message);
                        await loadGroups();

                    } catch (error) {
                        showMessage(error.message, "error");
                    }
                });

                actions.appendChild(deleteButton);

            } else {
                // Bouton Quitter le groupe
                const leaveButton = document.createElement("button");
                leaveButton.type = "button";
                leaveButton.textContent = "Quitter le groupe";

                leaveButton.addEventListener("click", async () => {
                    const confirmed = window.confirm(
                        `Veux-tu vraiment quitter le groupe "${group.name}" ?`
                    );

                    if (!confirmed) return;

                    try {
                        const result = await apiRequest(
                            `/groups/${group.id}/leave`,
                            { method: "POST" }
                        );

                        showMessage(result.message);
                        await loadGroups();

                    } catch (error) {
                        showMessage(error.message, "error");
                    }
                });

                actions.appendChild(leaveButton);
            }

            card.append(link, actions, membersContainer);
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

// Initialisation du tableau de bord
async function initializeDashboard() {
    try {
        await loadCurrentUser();
        await loadGroups();
    } catch (error) {
        showMessage(error.message, "error");
    }
}

initializeDashboard();
