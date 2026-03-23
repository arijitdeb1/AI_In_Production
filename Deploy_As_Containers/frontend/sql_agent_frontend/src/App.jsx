import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [query, setQuery] = useState('');
  const [threadId, setThreadId] = useState('');
  const [messages, setMessages] = useState([]); // Store conversation messages
  const [error, setError] = useState(null);

  // Generate a random thread ID on component mount
  useEffect(() => {
    const generateThreadId = () => {
      return Math.random().toString(36).substring(2, 10); // Random alphanumeric string
    };
    setThreadId(generateThreadId());
  }, []);

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Add user message to the conversation
    setMessages((prev) => [...prev, { sender: 'user', text: query }]);
    setQuery(''); // Clear input field immediately

    try {
      const res = await axios.post('https://y8hwmr9eiu.us-east-1.awsapprunner.com/query', {
        question: query,
        thread_id: threadId,
      });

      // Add bot response to the conversation
      setMessages((prev) => [...prev, { sender: 'bot', text: res.data.response }]);
    } catch (err) {
      setError(err.response ? err.response.data : 'An error occurred');
    }
  };

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', maxWidth: '600px', margin: '0 auto', padding: '20px', border: '1px solid #ccc', borderRadius: '10px', backgroundColor: '#f9f9f9' }}>
      <h1 style={{ textAlign: 'center', color: '#333' }}>DB Assistant</h1>
      <div style={{ marginBottom: '20px', textAlign: 'center', fontSize: '14px', color: '#555' }}>
        <strong>Thread ID:</strong> <span style={{ backgroundColor: '#e9e9e9', padding: '5px', borderRadius: '5px' }}>{threadId}</span>
      </div>
      <div style={{ height: '400px', overflowY: 'auto', border: '1px solid #ccc', borderRadius: '5px', padding: '10px', marginBottom: '20px', backgroundColor: '#fff' }}>
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              marginBottom: '10px',
            }}
          >
            <div
              style={{
                maxWidth: '70%',
                padding: '10px',
                borderRadius: '10px',
                backgroundColor: msg.sender === 'user' ? '#007BFF' : '#e9e9e9',
                color: msg.sender === 'user' ? '#fff' : '#000',
              }}
            >
              {msg.text}
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={handleQuerySubmit} style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your message..."
          style={{ flex: 1, padding: '10px', border: '1px solid #ccc', borderRadius: '5px' }}
        />
        <button type="submit" style={{ padding: '10px 20px', backgroundColor: '#007BFF', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
          Send
        </button>
      </form>
      {error && (
        <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #FF0000', borderRadius: '5px', backgroundColor: '#ffe9e9' }}>
          <h2 style={{ marginBottom: '10px', color: '#FF0000' }}>Error:</h2>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}

export default App;
