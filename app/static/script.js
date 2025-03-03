document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatBox = document.getElementById('chatBox');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const favoriteIngredients = document.getElementById('favoriteIngredients');
    const favoriteCocktails = document.getElementById('favoriteCocktails');
    const clearPreferencesButton = document.getElementById('clearPreferencesButton');
    
    // Generate a unique session ID for this user
    const sessionId = generateSessionId();
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    clearPreferencesButton.addEventListener('click', clearPreferences);
    
    // Load user preferences on startup
    loadUserPreferences();
    
    // Function to send user message
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        userInput.value = '';
        
        // Show loading indicator
        showLoading();
        
        // Send message to API
        fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove loading indicator
            removeLoading();
            
            // Add bot response to chat
            addMessage(data.response, 'bot');
            
            // If preferences were detected, update the preferences panel
            if (data.detected_preferences && data.detected_preferences.length > 0) {
                loadUserPreferences();
            }
        })
        .catch(error => {
            // Remove loading indicator
            removeLoading();
            
            // Show error message
            addMessage('Sorry, there was an error processing your request. Please try again.', 'system');
            console.error('Error:', error);
        });
    }
    
    // Function to add a message to the chat
    function addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        
        if (sender === 'user') {
            messageDiv.classList.add('user-message');
        } else if (sender === 'bot') {
            messageDiv.classList.add('bot-message');
        } else {
            messageDiv.classList.add('system-message');
        }
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        // Format the message content with proper paragraphs
        const formattedContent = formatMessageContent(content);
        messageContent.innerHTML = formattedContent;
        
        messageDiv.appendChild(messageContent);
        chatBox.appendChild(messageDiv);
        
        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    // Function to format message content
    function formatMessageContent(content) {
        // Split by line breaks and create paragraphs
        const paragraphs = content.split('\n').filter(p => p.trim() !== '');
        let formatted = '';
        
        paragraphs.forEach(paragraph => {
            // Check if this is a list item
            if (paragraph.trim().match(/^\d+\.\s/)) {
                // This is likely a list item, but make sure we're handling lists properly
                if (!formatted.endsWith('</ul>') && !formatted.endsWith('</ol>')) {
                    formatted += '<ol>';
                }
                formatted += `<li>${paragraph.replace(/^\d+\.\s/, '')}</li>`;
            } else if (paragraph.trim().match(/^[\*\-]\s/)) {
                // Bullet list item
                if (!formatted.endsWith('</ul>')) {
                    formatted += '<ul>';
                }
                formatted += `<li>${paragraph.replace(/^[\*\-]\s/, '')}</li>`;
            } else {
                // Close any open lists
                if (formatted.endsWith('</li>')) {
                    if (formatted.includes('<ol>') && !formatted.includes('</ol>')) {
                        formatted += '</ol>';
                    }
                    if (formatted.includes('<ul>') && !formatted.includes('</ul>')) {
                        formatted += '</ul>';
                    }
                }
                // Regular paragraph
                formatted += `<p>${paragraph}</p>`;
            }
        });
        
        // Close any open lists
        if (formatted.endsWith('</li>')) {
            if (formatted.includes('<ol>') && !formatted.includes('</ol>')) {
                formatted += '</ol>';
            }
            if (formatted.includes('<ul>') && !formatted.includes('</ul>')) {
                formatted += '</ul>';
            }
        }
        
        return formatted;
    }
    
    // Function to show loading indicator
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'bot-message', 'loading');
        
        const loadingContent = document.createElement('div');
        loadingContent.classList.add('message-content');
        loadingContent.innerHTML = 'Thinking...';
        
        loadingDiv.appendChild(loadingContent);
        chatBox.appendChild(loadingDiv);
        
        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    // Function to remove loading indicator
    function removeLoading() {
        const loadingElement = document.querySelector('.loading');
        if (loadingElement) {
            loadingElement.remove();
        }
    }
    
    // Function to load user preferences
    function loadUserPreferences() {
        fetch(`/api/memory/${sessionId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update preferences panel
            if (data.favorite_ingredients && data.favorite_ingredients.length > 0) {
                favoriteIngredients.textContent = data.favorite_ingredients.join(', ');
            } else {
                favoriteIngredients.textContent = 'None yet';
            }
            
            if (data.favorite_cocktails && data.favorite_cocktails.length > 0) {
                favoriteCocktails.textContent = data.favorite_cocktails.join(', ');
            } else {
                favoriteCocktails.textContent = 'None yet';
            }
        })
        .catch(error => {
            console.error('Error loading preferences:', error);
        });
    }
    
    // Function to clear preferences
    function clearPreferences() {
        fetch(`/api/memory/${sessionId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(() => {
            // Update preferences panel
            favoriteIngredients.textContent = 'None yet';
            favoriteCocktails.textContent = 'None yet';
            
            // Add system message
            addMessage('Your preferences have been cleared.', 'system');
        })
        .catch(error => {
            console.error('Error clearing preferences:', error);
        });
    }
    
    // Function to generate a session ID
    function generateSessionId() {
        // Check if we already have a session ID in localStorage
        let id = localStorage.getItem('cocktailAdvisorSessionId');
        
        if (!id) {
            // Generate a random ID
            id = 'session_' + Math.random().toString(36).substring(2, 15);
            localStorage.setItem('cocktailAdvisorSessionId', id);
        }
        
        return id;
    }
});