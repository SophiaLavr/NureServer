document.addEventListener('DOMContentLoaded', () => {
    const messagesDiv = document.getElementById('messages');
    const chatListDiv = document.getElementById('chat-list');
    let currentChat = null;

    const loadChatList = () => {
        fetch('/conversations')
        .then(response => response.json())
        .then(data => {
            chatListDiv.innerHTML = '';
            data.forEach((chat, index) => {
                const chatItem = document.createElement('div');
                chatItem.className = 'chat-item';
                chatItem.textContent = `${index + 1}. ${chat}`;
                chatItem.addEventListener('click', () => {
                    currentChat = chat.split(' <--> ');
                    loadMessages(currentChat);
                });
                chatListDiv.appendChild(chatItem);
            });
        });
    };

    const loadMessages = (chat) => {
        const [user1, user2] = chat;
        fetch(`/messages?user1=${user1}&user2=${user2}`)
        .then(response => response.json())
        .then(data => {
            messagesDiv.innerHTML = '';
            data.forEach(message => {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${message.from === user1 ? 'received' : 'sent'}`;
                messageDiv.textContent = `${message.from}: ${message.text}`;
                messagesDiv.appendChild(messageDiv);
            });
        });
    };

    loadChatList();
});
