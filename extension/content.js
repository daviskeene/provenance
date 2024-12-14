let isRecording = false;
let currentSessionId = null;
let eventBuffer = [];
const BUFFER_THRESHOLD = 10; // Number of events before sending
const SEND_DELAY_MS = 2000; // Minimum delay between sends

let lastSendTime = 0; // Track the last time events were sent
let iframeKeyListenerAttached = false; // Prevent redundant listeners

// Find the iframe and attach the keydown listener
// TODO: This is a hack to get the iframe. We need to find a better way to do this.
const iframe = document.querySelector("iframe.docs-texteventtarget-iframe"); // Adjust selector if needed
attachKeydownListenerToIframe(iframe);

// Attach keydown listener to iframe's document
function attachKeydownListenerToIframe(iframe) {
  try {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

    if (!iframeDoc) {
      console.warn("Unable to access iframe document.");
      return;
    }

    // Ensure only one listener is attached
    if (iframeKeyListenerAttached) {
      console.log("Keydown listener already attached to iframe.");
      return;
    }

    console.log("Attaching keydown listener to iframe...");
    iframeDoc.addEventListener("keydown", handleKeydownEvent);
    iframeKeyListenerAttached = true; // Mark as attached
  } catch (error) {
    console.error("Failed to attach keydown listener to iframe:", error);
  }
}

// Keydown event handler
function handleKeydownEvent(event) {
  if (isRecording && currentSessionId) {
    // Prevent redundant events
    eventBuffer.push({
      character: event.key,
      timestamp: new Date().toISOString(),
    });

    console.log(`Event captured: ${event.key}`);
    console.log(eventBuffer);

    // Check if buffer threshold is met or delay has passed
    const now = Date.now();
    if (
      eventBuffer.length >= BUFFER_THRESHOLD ||
      now - lastSendTime >= SEND_DELAY_MS
    ) {
      sendEvents();
    }
  }
}

// Send buffered events to the backend
async function sendEvents() {
  if (!currentSessionId || eventBuffer.length === 0) return;

  const eventsToSend = [...eventBuffer];
  eventBuffer = [];
  lastSendTime = Date.now(); // Update the last send timestamp

  try {
    console.log(`Sending ${eventsToSend.length} events to the server...`);
    await fetch(`http://localhost:8000/sessions/${currentSessionId}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(eventsToSend),
    });
    console.log("Events sent successfully.");
  } catch (error) {
    console.error("Failed to send events:", error);
    eventBuffer = eventsToSend.concat(eventBuffer); // Re-queue unsent events
  }
}

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.command === "start") {
    isRecording = true;
    currentSessionId = message.sessionId;
    console.log(`Recording started: session ${currentSessionId}`);
    sendResponse({ status: "started" });
  } else if (message.command === "stop") {
    isRecording = false;
    console.log(`Recording stopped: session ${currentSessionId}`);
    sendEvents().then(() => sendResponse({ status: "stopped" }));
    currentSessionId = null;
    return true; // Keeps message channel open for async sendEvents
  }
});

// Utility function to flush remaining events (e.g., on window unload)
function flushRemainingEvents() {
  if (isRecording && eventBuffer.length > 0) {
    console.log("Flushing remaining events before unload...");
    sendEvents();
  }
}

// Add a listener to handle page unload (optional but useful for cleanup)
window.addEventListener("beforeunload", flushRemainingEvents);

console.log("Content script initialized.");
