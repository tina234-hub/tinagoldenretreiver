document.getElementById("uploadForm").addEventListener("submit", function (e) {
    e.preventDefault();
  
    const form = e.target;
    const formData = new FormData(form);
    const statusDiv = document.getElementById("status");
    statusDiv.textContent = "Uploading file...\n";
  
    fetch("/upload", {
      method: "POST",
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          statusDiv.textContent += "File uploaded. Starting data transfer...\n";
          const eventSource = new EventSource("/transfer-status");
  
          eventSource.onmessage = function (event) {
            if (event.data === "DONE") {
              statusDiv.textContent += "✅ Data transfer complete!\n";
              eventSource.close();
            } else {
              statusDiv.textContent += event.data + "\n";
            }
          };
  
          eventSource.onerror = function () {
            statusDiv.textContent += "❌ Error during transfer.\n";
            eventSource.close();
          };
        } else {
          statusDiv.textContent += "❌ Upload failed.\n";
        }
      })
      .catch(() => {
        statusDiv.textContent += "❌ Upload or transfer failed.\n";
      });
  });
  