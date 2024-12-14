let sessionId = null;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log("Background received message:", message);
  if (message.command === "start") {
    console.log("Received start command in background script.");
    // Call backend to start a session
    fetch("http://localhost:8000/sessions/start", { method: "POST" })
      .then((response) => response.json())
      .then((data) => {
        sessionId = data.session_id;
        // Notify the content script to start logging
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          chrome.tabs.sendMessage(tabs[0].id, {
            command: "start",
            sessionId: sessionId,
          });
        });
        sendResponse({ message: `Session started: ${sessionId}` });
        chrome.storage.local.set({ sessionId: data.session_id });
      })
      .catch((error) => {
        console.error(error);
        sendResponse({ message: "Failed to start session." });
      });
    return true; // Keeps the message channel open for async response
  }

  if (message.command === "stop") {
    // Notify the content script to stop logging
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { command: "stop" }, () => {
        // Finalize the session
        if (sessionId) {
          fetch(`http://localhost:8000/sessions/${sessionId}/finalize`, {
            method: "POST",
          })
            .then((response) => response.json())
            .then((data) => {
              sendResponse({ message: "Session finalized successfully." });
              sessionId = null;
            })
            .catch((error) => {
              console.error(error);
              sendResponse({ message: "Failed to finalize session." });
            });
        } else {
          sendResponse({ message: "No active session to finalize." });
        }
      });
    });
    return true;
  }
});
