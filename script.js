// Biến lưu token, senderId và conversationId hiện tại
let idToken = null;
let senderId = null;
let currentConversationId = null;

// Biến lưu baseUrl để dễ sửa đổi
const baseUrl = "https://zarkchat-fvfgfuhactbbc2bv.southeastasia-01.azurewebsites.net";
const chatHubUrl = `${baseUrl}/chatHub`;
const loginApiUrl = `${baseUrl}/api/User/login`;
const conversationsApiUrl = `${baseUrl}/api/Conversation`;
const messagesApiUrl = `${baseUrl}/api/messages/conversation`;

// Khởi tạo SignalR connection
const connection = new signalR.HubConnectionBuilder()
    .withUrl(chatHubUrl, {
        accessTokenFactory: () => {
            console.log("Sending token:", idToken);
            if (!idToken) throw new Error("No token available");
            return idToken;
        }
    })
    .withAutomaticReconnect()
    .build();

// Hàm đăng nhập gọi API backend
async function login(email, password) {
    try {
        const response = await fetch(loginApiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });
        if (!response.ok) throw new Error("Login failed: " + response.statusText);
        const data = await response.json();
        idToken = data.token;
        senderId = data.userId;
        console.log("Login successful, token:", idToken, "senderId:", senderId);

        document.getElementById("senderId").textContent = senderId;
        document.getElementById("loginForm").style.display = "none";
        document.getElementById("chatUI").style.display = "block";
        initializeChat();
    } catch (error) {
        console.error("Login failed:", error.message);
        alert("Login failed: " + error.message);
    }
}

// Khởi động SignalR và tải danh sách hội thoại
async function initializeChat() {
    if (!idToken || !senderId) {
        console.error("No token or sender ID available. Please log in first.");
        return;
    }
    try {
        await connection.start();
        console.log("Connected to SignalR hub");
        await loadConversationList();
    } catch (error) {
        console.error("Connection failed:", error);
    }
}

// Tải danh sách hội thoại
async function loadConversationList() {
    try {
        const response = await fetch(conversationsApiUrl + "/conversations", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${idToken}`,
                "Content-Type": "application/json"
            }
        });
        if (!response.ok) throw new Error(`Failed to load conversations: ${response.status}`);
        const conversations = await response.json();
        displayConversationList(conversations);
    } catch (error) {
        console.error("Error loading conversation list:", error);
    }
}

// Hiển thị danh sách hội thoại
function displayConversationList(conversations) {
    const conversationList = document.getElementById("conversationList");
    conversationList.innerHTML = "";
    conversations.forEach(conv => {
        const convItem = document.createElement("div");
        convItem.className = "conversation-item";
        // Hiển thị tên nhóm hoặc tên người nhận (cho chat 1-1)
        const displayName = conv.name ||
            (conv.type === "Private"
                ? conv.participants.find(p => p.userId !== senderId)?.username || `Chat ${conv.conversationId}`
                : `Group ${conv.conversationId}`);
        convItem.textContent = displayName;
        convItem.onclick = () => {
            // Xóa class active khỏi item cũ
            document.querySelectorAll(".conversation-item").forEach(item => item.classList.remove("active"));
            // Thêm class active cho item được chọn
            convItem.classList.add("active");
            currentConversationId = conv.conversationId;
            document.getElementById("conversationTitle").textContent = displayName;
            loadChatHistory(currentConversationId);
        };
        conversationList.appendChild(convItem);
    });
}

// Tải lịch sử chat
async function loadChatHistory(conversationId) {
    if (!conversationId) {
        console.error("Conversation ID not set");
        return;
    }

    try {
        const response = await fetch(`${messagesApiUrl}/${conversationId}?page=1&pageSize=20`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${idToken}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to load chat history: ${response.status}`);
        }

        const messages = await response.json();
        const messagesContainer = document.getElementById("messagesContainer");
        messagesContainer.innerHTML = "";
        messages.forEach(message => {
            displayMessage(message.conversationId, message.userSendId, message.message, message.sendDate, message.type, message.mediaLink);
        });
    } catch (error) {
        console.error("Error loading chat history:", error);
    }
}

// Hiển thị tin nhắn
function displayMessage(conversationId, userSendId, content, sendDate, type, mediaLink) {
    if (conversationId !== currentConversationId) return;

    const messagesContainer = document.getElementById("messagesContainer");
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${userSendId === senderId ? "sent" : "received"}`;

    const contentDiv = document.createElement("div");
    if (type === "Text") {
        contentDiv.textContent = content;
    } else if (type === "Image" && mediaLink) {
        const img = document.createElement("img");
        img.src = mediaLink;
        img.style.maxWidth = "200px";
        contentDiv.appendChild(img);
    } else {
        contentDiv.textContent = `[${type}] ${content}`;
    }

    const timestampDiv = document.createElement("div");
    timestampDiv.className = "message-timestamp";
    timestampDiv.textContent = new Date(sendDate).toLocaleString();

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timestampDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Xử lý tin nhắn realtime
connection.on("ReceiveMessage", (conversationId, userSendId, content, messageType, sendDate) => {
    displayMessage(conversationId, userSendId, content, sendDate, messageType, null);
});

// Gửi tin nhắn
function sendMessage() {
    const messageInput = document.querySelector(".message-input");
    const content = messageInput.value.trim();

    if (!senderId) {
        alert("Please log in first!");
        return;
    }
    if (!currentConversationId) {
        alert("Please select a conversation!");
        return;
    }
    if (content) {
        connection.invoke("SendMessage", currentConversationId, senderId, content, "Text")
            .then(() => {
                messageInput.value = "";
            })
            .catch(error => {
                console.error("Error sending message:", error);
                alert("Failed to send message: " + error.message);
            });
    }
}

// Xử lý sự kiện khi trang load
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("loginButton").addEventListener("click", () => {
        const email = document.getElementById("emailInput").value;
        const password = document.getElementById("passwordInput").value;
        if (email && password) {
            login(email, password);
        } else {
            alert("Please enter both email and password!");
        }
    });

    document.querySelector(".message-input").addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });

    document.getElementById("sendButton").addEventListener("click", sendMessage);

    // Mở modal tạo hội thoại
    document.getElementById("newChatButton").addEventListener("click", showCreateConversationModal);

    // Xử lý modal
    document.getElementById("createConversationButton").addEventListener("click", createConversation);
    document.getElementById("cancelConversationButton").addEventListener("click", hideCreateConversationModal);

    // Ẩn/hiện group name dựa trên type
    document.getElementById("conversationType").addEventListener("change", (e) => {
        const isGroup = e.target.value === "Group";
        document.getElementById("groupNameLabel").style.display = isGroup ? "block" : "none";
        document.getElementById("groupName").style.display = isGroup ? "block" : "none";
    });
});

// Xử lý reconnect
connection.onclose(async () => {
    console.log("Connection closed. Attempting to reconnect...");
    await initializeChat();
});

// Hiển thị/ẩn modal tạo hội thoại
function showCreateConversationModal() {
    document.getElementById("createConversationModal").style.display = "flex";
    document.getElementById("conversationType").value = "Private";
    document.getElementById("participantIds").value = "";
    document.getElementById("groupName").value = "";
    document.getElementById("groupNameLabel").style.display = "none";
    document.getElementById("groupName").style.display = "none";
}

function hideCreateConversationModal() {
    document.getElementById("createConversationModal").style.display = "none";
}

// Tạo hội thoại mới
async function createConversation() {
    const type = document.getElementById("conversationType").value;
    const participantIdsInput = document.getElementById("participantIds").value.trim();
    const name = type === "Group" ? document.getElementById("groupName").value.trim() : null;

    if (!participantIdsInput) {
        alert("Please enter at least one participant ID");
        return;
    }

    const participantIds = participantIdsInput.split(",").map(id => parseInt(id.trim())).filter(id => !isNaN(id) && id !== senderId);
    if (participantIds.length === 0) {
        alert("Invalid participant IDs");
        return;
    }

    if (type === "Group" && !name) {
        alert("Please enter a group name");
        return;
    }

    try {
        const response = await fetch(conversationsApiUrl + "/create", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${idToken}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ creatorId: senderId, participantIds, type, name })
        });

        if (!response.ok) {
            throw new Error(`Failed to create conversation: ${response.status}`);
        }

        const data = await response.json();
        currentConversationId = data.conversationId;
        hideCreateConversationModal();
        await loadConversationList();
        // Tự động chọn hội thoại mới
        document.querySelectorAll(".conversation-item").forEach(item => {
            if (item.textContent.includes(data.conversationId)) {
                item.click();
            }
        });
    } catch (error) {
        console.error("Error creating conversation:", error);
        alert("Failed to create conversation: " + error.message);
    }
}