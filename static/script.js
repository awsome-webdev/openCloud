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
uploadForm.addEventListener("submit", async function(e) {
    e.preventDefault();
    const fileInput = document.getElementById("file-input");
    if (!fileInput.files.length) return;
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    const res = await fetch("/upload", {
        method: "POST",
        body: formData
    });
    if (res.ok) {
        alert("Upload successful!");
        displayFiles();
    } else {
        alert("Upload failed.");
    }
});

// Download file
function downloadFile(path) {
    window.location.href = `/download?path=${path}`;
}
function downloadPath() {
    window.location.href = `/download?path=${currentPath}`;
}