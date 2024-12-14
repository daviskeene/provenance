// Handle user interactions from the popup

document.getElementById("startButton").addEventListener("click", () => {
  chrome.runtime.sendMessage({ command: "start" }, (response) => {
    document.getElementById("status").textContent = response.message;
  });
});

document.getElementById("stopButton").addEventListener("click", () => {
  chrome.runtime.sendMessage({ command: "stop" }, (response) => {
    document.getElementById("status").textContent = response.message;
  });
});

// popup.js (on load)
chrome.storage.local.get(["sessionId"], (result) => {
  if (result.sessionId) {
    document.getElementById("status").textContent =
      `Session active: ${result.sessionId}`;
  }
});
