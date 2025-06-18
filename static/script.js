async function getfiles() {
    return fetch("http://127.0.0.1:8080/tree")
        .then(response => response.json());
}
function displayFiles() {
    getfiles().then(files => {
        Object.keys(files).forEach(key => {
                const folder = document.createElement("div");
                folder.classList.add("folder");
                folder.innerHTML = `<h1>${key}</h1><label><a href="" onclick="expandFolder(this)">Expand</a></label>`;
                document.getElementById("folder-parent").appendChild(folder);
                if (files[key] === null) {
                    const file = document.createElement("div");
                    file.classList.add("file");
                    file.innerHTML = `<h1>${key}</h1>`;
                    document.getElementById("folder-parent").appendChild(file);
            }
        });
    });
}
displayFiles();