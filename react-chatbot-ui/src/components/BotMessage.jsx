import React, { useState, useEffect } from "react";

export default function BotMessage({ fetchMessage }) {
  const [isLoading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadMessage() {
      const msg = await fetchMessage();
      setLoading(false);
      setMessage(msg);
    }
    loadMessage();
  }, [fetchMessage]);

  return (

    <div className="message-container">
      <div className="bot-message"
           dangerouslySetInnerHTML={{ __html: isLoading ? "..." : message }}
           style={{ whiteSpace: 'pre-line',textAlign:"start" }}
      >
      </div>
    </div>
  );
}
