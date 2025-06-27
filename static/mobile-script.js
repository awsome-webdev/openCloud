let currentPath = "";
let pathStack = [];
setInterval(() => {
    updatepath();
}, 100);
async function getfiles(path = "") {
    const response = await fetch("/tree" + (path ? `?path=${encodeURIComponent(path)}` : ""));
    return await response.json();
}

function createExplorerElement(tree, path = "") {
    const container = document.createElement("ul");
    document.getElementById('folder-list').innerHTML = "";
    for (const key in tree) {
        const value = tree[key];
        const fullPath = path ? `${path}/${key}` : key;
        const li = document.createElement("li");
        if (value === null) {
            // File
            li.innerHTML = `📄 ${key}`;
            if (fullPath != key) {
                li.setAttribute('onclick', `open_file('${fullPath}')`);
                li.setAttribute('style', 'user-select: none;');
            }
            else {
                li.setAttribute('onclick', `open_file('${fullPath}')`);
                li.setAttribute('style', 'user-select: none;');
            }
            li.style.cursor = "pointer";
        } else {
            // Folder
            li.innerHTML = `<span class="folder-link" style="cursor:pointer;color:#2d7ff9;user-select: none;">📁 ${key}</span>`;
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
    showFileOptions();
    const file = await fetch(`/file?path=${path}`);
    console.log(file)
    const parent = document.getElementById('pre-parent');
    const pre = document.getElementById('preview')
    parent.style.display = "block";
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
        pre.innerHTML = `<div contenteditable="true" class="text-editor" style="white-space:pre-wrap;word-break:break-all;">${text}</div>`;
        document.getElementById('save-btn').style.display = 'block';
    } else if (contentType === "application/pdf") {
    const blob = await file.blob();
    const url = URL.createObjectURL(blob);
    pre.innerHTML = `<iframe src="${url}" style="width:100%;height:70vh;border:none;"></iframe>`;
    } else {
        // For other types, offer download
        pre.innerHTML = `<a href="/file?path=${encodeURIComponent(path)}" download>Download file (File type not supported)</a>`;
    }
    }
}
async function saveFile() {
    const pre = document.getElementById('pre-parent');
    const path = pre.getAttribute('path');
    const contentElement = pre.querySelector('.text-editor');
    const content = contentElement ? contentElement.innerText : null;
    const formData = new FormData();
    formData.append('content', content);

    const response = await fetch(`/save?path=${encodeURIComponent(path)}`, {
        method: 'POST',
        body: formData
    });

    if (response.ok) {
        alert('File saved!');
    } else {
        alert('Failed to save file.');
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
    const key = prompt("Enter encryption key (leave blank for no encryption):");
    if (key) {
        for (const file of fileInput.files) {
            const arrayBuffer = await file.arrayBuffer();
            const plaintextBytes = new Uint8Array(arrayBuffer);
            const encryptedBytes = encryptBinary(plaintextBytes, key);
            const blob = new Blob([encryptedBytes], { type: file.type });
            formData.append("file", blob, file.name + ".enc");
        }
    }
    else {
        for (const file of fileInput.files) {
            const arrayBuffer = await file.arrayBuffer();
            const plaintextBytes = new Uint8Array(arrayBuffer);
            const blob = new Blob([plaintextBytes], { type: file.type });
            formData.append("file", blob, file.name);
        }
    }

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
    fileInput.value = "";
});
function deleteFile(){
    const path = document.getElementById('preview').getAttribute('path');
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
async function downloadFile() {
    const path2 = document.getElementById('preview').getAttribute('path');
    if (!path2 || path2 === "" || path2 === "undefined") {
        alert("No file selected for download.");
        return;
    }

    // Check if the file is encrypted (e.g., ends with .enc)
    if (path2.endsWith('.enc')) {
        const key = prompt("Enter decryption key:");
        if (!key) return;

        // Fetch the encrypted file as ArrayBuffer
        const response = await fetch(`/download?path=${encodeURIComponent(path2)}`);
        if (!response.ok) {
            alert("Failed to download the file.");
            return;
        }
        const encryptedBuffer = await response.arrayBuffer();
        const encryptedBytes = new Uint8Array(encryptedBuffer);

        // Decrypt
        const decryptedBytes = decryptBinary(encryptedBytes, key);
        if (!decryptedBytes) return; // decryption failed

        // Guess original filename (remove .enc)
        const originalName = path2.replace(/\.enc$/, "");

        // Create a Blob and trigger download
        const blob = new Blob([decryptedBytes]);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = originalName;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
    } else {
        // Not encrypted, just download normally
        window.location.href = `/download?path=${encodeURIComponent(path2)}`;
    }
}
function downloadPath() {
    window.location.href = `/download?path=${currentPath}`;
}
function toggleFullScreen(){
    const pre = document.getElementById('pre-parent');
    if (!document.fullscreenElement) {
        pre.requestFullscreen().catch(err => {
            console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
            
        });
        document.getElementById('preview').style.height = "90vh";
        document.getElementById('preview').style.width = "100vw";
    } else {
        document.exitFullscreen();
        document.getElementById('preview').style.height = "90%";
        document.getElementById('preview').style.width = "100%";
    }
}
function renameFolder(){
    const path = currentPath
    if (!path || path === "" || path === "undefined") {
        alert("No folder selected for renaming.");
        return;
    }   
    else {
        const newName = prompt("Enter new name for the folder:");
        if (newName) {
            fetch(`/rename?path=${encodeURIComponent(path)}&new_name=${encodeURIComponent(newName)}`, {
                method: 'GET'
            }).then(response => {
                if (response.ok) {
                    alert("Folder renamed successfully!");
                    currentPath = `${pathStack.pop()}/${newName}` || "";
                    displayFiles();
                } else {
                    alert("Failed to rename the folder.");
                }
            });
        }
    }
}
function showFolderOptions(){
    const folder = document.getElementById('folder-options');
    const file = document.getElementById('file-options');
    folder.style.display = 'flex';
    file.style.display = 'none';
}
function showFileOptions(){
    const folder = document.getElementById('folder-options');
    const file = document.getElementById('file-options');
    folder.style.display = 'none';
    file.style.display = 'flex';
}
function updatepath(){
    if (currentPath === "") {
        document.getElementById('path-h3').innerText = "~/";
        return;
    }
    document.getElementById('path-h3').innerText = `~/${currentPath}`;
}
function renameFile(){
    const path = document.getElementById('preview').getAttribute('path');
    if (!path || path === "" || path === "undefined") {
        alert("No file selected for renaming.");
        return;
    }   
    else {
        const newName = prompt("Enter new name for the file:");
        if (newName) {
            fetch(`/rename?path=${encodeURIComponent(path)}&new_name=${encodeURIComponent(newName)}`, {
                method: 'GET'
            }).then(response => {
                if (response.ok) {
                    alert("File renamed successfully!");
                    displayFiles();
                } else {
                    alert("Failed to rename the file.");
                }
            });
        }
    }
}
function createFolder(){
    const newFolderName = prompt("Enter the name for the new folder:");
    if (newFolderName) {
        fetch(`/makefolder?path=${encodeURIComponent(currentPath)}&name=${encodeURIComponent(newFolderName)}`, {
            method: 'GET'
        }).then(response => {
            if (response.ok) {
                alert("Folder created successfully!");
                displayFiles();
            } else {
                alert("Failed to create the folder.");
            }
        });
    }
}
function decryptBinary(encryptedBytes, keyString) {
    while (keyString.length < 32) {
      keyString += "1";
    }
    const key = aesjs.utils.utf8.toBytes(keyString.slice(0, 32));
  
    const aesCtr = new aesjs.ModeOfOperation.ctr(key, new aesjs.Counter(5));
    const decryptedBytes = aesCtr.decrypt(encryptedBytes);
  
    // Verify the marker
    const marker = "VALID|";
    const markerBytes = aesjs.utils.utf8.toBytes(marker);
    for (let i = 0; i < markerBytes.length; i++) {
      if (decryptedBytes[i] !== markerBytes[i]) {
        alert("Decryption failed: Incorrect key.");
        return null;
      }
    }
    // Remove the marker and return the original file bytes
    return decryptedBytes.slice(markerBytes.length);
}
function encryptBinary(plaintextBytes, keyString) {
    // Ensure the key is at least 32 characters long (256 bits)
    while (keyString.length < 32) {
      keyString += "1"; // Append "1" until the key is long enough
    }
    const key = aesjs.utils.utf8.toBytes(keyString.slice(0, 32));
  
    // Prepend a marker to the plaintext so that you can check decryption later
    const marker = "VALID|";
    const markerBytes = aesjs.utils.utf8.toBytes(marker);
    const combined = new Uint8Array(markerBytes.length + plaintextBytes.length);
    combined.set(markerBytes, 0);
    combined.set(plaintextBytes, markerBytes.length);
  
    // Encrypt using AES-CTR mode (using a fixed counter for simplicity;
    const aesCtr = new aesjs.ModeOfOperation.ctr(key, new aesjs.Counter(5));
    const encryptedBytes = aesCtr.encrypt(combined);

    return encryptedBytes;
}