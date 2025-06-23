let currentPath = "";
let pathStack = [];

async function getfiles(path = "") {
    const response = await fetch("http://127.0.0.1:8080/tree" + (path ? `?path=${encodeURIComponent(path)}` : ""));
    return await response.json();
}

function createExplorerElement(tree, path = "") {
    const container = document.createElement("ul");
    for (const key in tree) {
        const value = tree[key];
        const fullPath = path ? `${path}/${key}` : key;
        const li = document.createElement("li");
        if (value === null) {
            // File
            li.innerHTML = `📄 ${key}`;
            if (fullPath != key) {
                li.setAttribute('onclick', `open_file('${fullPath}')`);
            }
            else {
                li.setAttribute('onclick', `open_file('${fullPath}')`);
            }
            li.style.cursor = "pointer";
        } else {
            // Folder
            li.innerHTML = `<span class="folder-link" style="cursor:pointer;color:#2d7ff9;">📁 ${key}</span>`;
            li.querySelector(".folder-link").onclick = () => {
                pathStack.push(currentPath);
                currentPath = fullPath;
                displayFiles();
            };
        }
        container.appendChild(li);
    }
    return container;
}
async function open_file(path) {
    const file = await fetch(`/file?path=${path}`);
    console.log(file)
    const pre = document.getElementById('pre-parent')
    pre.innerHTML = "Loading...";
    pre.innerHTML = "";
    pre.setAttribute('path', path)
    if (file.ok) {
        const contentType = file.headers.get("Content-Type");
        if (contentType.startsWith("image/")) {
            const blob = await file.blob();
            const url = URL.createObjectURL(blob);
            pre.innerHTML = `<img src="${url}" style="max-width:100%;max-height:60vh;">`;
        } else if (contentType.startsWith("video/")) {
            const blob = await file.blob();
            const url = URL.createObjectURL(blob);
            pre.innerHTML = `<video controls style="max-width:100%;max-height:60vh;"><source src="${url}" type="${contentType}"></video>`;
        } else if (contentType.startsWith("audio/")) {
            const blob = await file.blob();
            const url = URL.createObjectURL(blob);
            pre.innerHTML = `<audio controls><source src="${url}" type="${contentType}"></audio>`;
    } else if (contentType.startsWith("text/") || contentType === "application/json") {
        const text = await file.text();
        pre.innerHTML = `<pre style="white-space:pre-wrap;word-break:break-all;">${text}</pre>`;
    } else {
        // For other types, offer download
        pre.innerHTML = `<a href="/file?path=${encodeURIComponent(path)}" download>Download file (File type not supported)</a>`;
    }
    }
}
function displayFiles() {
    const parent = document.getElementById("folder-parent");
    parent.innerHTML = "Loading...";
    getfiles(currentPath).then(tree => {
        parent.innerHTML = "";
        if (currentPath) {
            const backBtn = document.createElement("button");
            backBtn.textContent = "⬅ Back";
            backBtn.className = "back-btn";
            backBtn.onclick = () => {
                currentPath = pathStack.pop() || "";
                displayFiles();
            };
            parent.appendChild(backBtn);
        }
        parent.appendChild(createExplorerElement(tree, currentPath));
    });
}

displayFiles();

// File upload
const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");

// Hide the file input
fileInput.style.display = "none";

// When upload button is clicked, trigger file input
uploadBtn.addEventListener("click", function(e) {
    e.preventDefault();
    fileInput.click();
});

// When a file is selected, upload it to the currentPath
fileInput.addEventListener("change", async function() {
    if (!fileInput.files.length) return;
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    const res = await fetch(`/upload?path=${encodeURIComponent(currentPath)}`, {
        method: "POST",
        body: formData
    });
    if (res.ok) {
        alert("Upload successful!");
        displayFiles();
    } else {
        alert("Upload failed.");
    }
    // Reset file input so the same file can be uploaded again if needed
    fileInput.value = "";
});
function deleteFile(){
    const path = document.getElementById('pre-parent').getAttribute('path');
    if (!path || path === "" || path === "undefined") {
        alert("No file selected for deletion.");
        return;
    }   
    else {
        fetch(`/delete?path=${path}`)
            .then(response => {
                if (response.ok) {
                    alert("File deleted successfully!");
                    displayFiles();
                } else {
                    alert("Failed to delete the file.");
                }
            });
    }
}
// Download file
function downloadFile(path) {
    const path2 = document.getElementById('pre-parent').getAttribute('path');
    if (!path2 || path2 === "" || path2 === "undefined") {
        alert("No file selected for download.");
        return;
    }   
    else {
        window.location.href = `/download?path=${path2}`;
    }
}
function downloadPath() {
    window.location.href = `/download?path=${currentPath}`;
}