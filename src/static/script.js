// DOM ELEMENTS
const checkboxes = document.querySelectorAll(".file-checkbox");
const toolbar = document.getElementById("selectionToolbar");
const selectedCount = document.getElementById("selectedCount");
const downloadButton = document.getElementById("downloadButton");
const moveButton = document.getElementById("moveButton");
const infoButton = document.getElementById("infoButton");
const renameButton = document.getElementById("renameButton");

const searchInput = document.getElementById("searchInput");
const fileRows = document.querySelectorAll(".file-row");
const folderCards = document.querySelectorAll(".folder-card-wrapper");

const storageUsed = document.querySelector(".storage-used");

const profileModal = document.getElementById("profileModal");
const openProfileModal = document.getElementById("openProfileModal");
const closeProfileModal = document.getElementById("closeProfileModal");

const openProfileAfterReload = document.getElementById("openProfileAfterReload");

const sortSelect = document.getElementById("sortSelect");

const uploadDropZone = document.getElementById("uploadDropZone");
const uploadInput = document.querySelector('input[type="file"]');

const hiddenUploadInput = document.getElementById("hiddenUploadInput");

const uploadOverlay = document.getElementById("uploadOverlay");

const downloadOverlay = document.getElementById("downloadOverlay");

const rightSidebar = document.getElementById("rightSidebar");
const sidePanelContent = document.getElementById("sidePanelContent");
const appLayout = document.querySelector(".app-layout");

const renameModal = document.getElementById("renameModal");
const renameForm = document.getElementById("renameForm");
const renameInput = document.getElementById("renameInput");
const cancelRenameButton = document.getElementById("cancelRenameButton");

const deleteModal = document.getElementById("deleteModal");
const deleteForm = document.getElementById("deleteForm");
const deleteModalText = document.getElementById("deleteModalText");
const cancelDeleteButton = document.getElementById("cancelDeleteButton");
const bulkDeleteButton = document.getElementById("bulkDeleteButton");

const moveModal = document.getElementById("moveModal");
const moveForm = document.getElementById("moveForm");
const cancelMoveButton = document.getElementById("cancelMoveButton");

const contextMenu = document.getElementById("contextMenu");
const contextPreview = document.getElementById("contextPreview");
const contextDownload = document.getElementById("contextDownload");
const contextRename = document.getElementById("contextRename");
const contextDelete = document.getElementById("contextDelete");

// GLOBAL STATE
let lastSelectedIndex = null;
const fileRowList = Array.from(
    document.querySelectorAll(".file-row")
);
let draggedFilePaths = [];
let contextTargetRow = null;

// GENERAL HELPERS
function updateSelectionToolbar() {
    const selected = document.querySelectorAll(".file-checkbox:checked");
    const count = selected.length;

    selectedCount.textContent = count + " selected";

    if (count > 0) {
        toolbar.classList.add("active");
        downloadButton.disabled = false;
        moveButton.disabled = false;
    } else {
        toolbar.classList.remove("active");
        downloadButton.disabled = true;
        moveButton.disabled = true;
    }
    if (count === 1) {
        infoButton.disabled = false;
        renameButton.disabled = false;
    } else {
        infoButton.disabled = true;
        renameButton.disabled = true;
    }
}

function sortItems(items, selectedSort) {
    items.sort(function (a, b) {
        if (selectedSort === "newest") {
            return Number(b.dataset.modified) - Number(a.dataset.modified);
        }
        if (selectedSort === "oldest") {
            return Number(a.dataset.modified) - Number(b.dataset.modified);
        }
        if (selectedSort === "name-asc") {
            return a.dataset.name.localeCompare(b.dataset.name);
        }
        if (selectedSort === "name-desc") {
            return b.dataset.name.localeCompare(a.dataset.name);
        }
        if (selectedSort === "owner") {
            return a.dataset.owner.localeCompare(b.dataset.owner);
        }
        if (selectedSort === "modified") {
            return Number(b.dataset.modified) - Number(a.dataset.modified);
        }
        if (selectedSort === "type") {
            return a.dataset.extension.localeCompare(b.dataset.extension);
        }
        if (selectedSort === "size") {
            return Number(b.dataset.size) - Number(a.dataset.size);
        }
        return 0;
    });
}

function showUploadOverlay() {
    if (uploadOverlay) {
        uploadOverlay.classList.add("active");
    }
}

function showDownloadOverlay() {
    if (downloadOverlay) {
        downloadOverlay.classList.add("active");
    }
}

function openSidePanel(row, mode) {
    if (!rightSidebar || !sidePanelContent) {
        return;
    }

    const fileName = row.dataset.displayname;
    const fullPath = row.dataset.fullpath;
    const owner = row.dataset.owner;
    const location = row.dataset.location;
    const modifiedDate = row.dataset.modifieddate;
    const size = Number(row.dataset.size);
    const extension = row.dataset.extension || "folder";
    const sizeMb = (size / (1024 * 1024)).toFixed(2);
    const isImage = row.dataset.isimage.toLowerCase() === "true";
    const isVideo = row.dataset.isvideo.toLowerCase() === "true";
    const icon = row.dataset.icon || "📄";

    rightSidebar.classList.remove("info-mode", "preview-mode");
    appLayout.classList.remove("sidebar-info-open", "sidebar-preview-open");

    if (mode === "info") {
        rightSidebar.classList.add("info-mode");
        appLayout.classList.add("sidebar-info-open");
    } else {
        rightSidebar.classList.add("preview-mode");
        appLayout.classList.add("sidebar-preview-open");
    }

    let previewHtml = "";

    if (mode === "preview") {
        if (isImage) {
            previewHtml = `
                <img src="/view/${encodeURIComponent(fullPath)}" class="side-preview-image">
            `;
        } else if (isVideo) {
            previewHtml = `
                <video src="/view/${encodeURIComponent(fullPath)}" class="side-preview-video" controls></video>
            `;
        } else {
            previewHtml = `
                <div class="side-preview-file-icon">${icon}</div>
            `;
        }
    }

    sidePanelContent.innerHTML = `
        <div class="side-panel-header">
            <strong>${fileName}</strong>
            <button type="button" id="closeSidePanel">✕</button>
        </div>

        ${previewHtml}

        <div class="side-file-details">
            <div class="detail-row">
                <span class="detail-label">Name</span>
                <span class="detail-value">${fileName}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Owner</span>
                <span class="detail-value">${owner}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Type</span>
                <span class="detail-value">${extension}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Size</span>
                <span class="detail-value">${sizeMb} MB</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Modified</span>
                <span class="detail-value">${modifiedDate}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Location</span>
                <span class="detail-value">${location}</span>
            </div>
        </div>
    `;

    document.getElementById("closeSidePanel").addEventListener("click", function () {
        rightSidebar.classList.remove("info-mode", "preview-mode");
        appLayout.classList.remove("sidebar-info-open", "sidebar-preview-open");

        sidePanelContent.innerHTML = `
            <p>Select a file to preview details here.</p>
        `;
    });
}

// SELECTION TOOLBAR
checkboxes.forEach(function(checkbox) {
    checkbox.addEventListener("change", updateSelectionToolbar);
});

infoButton.addEventListener("click", function () {
    const selected = document.querySelector(".file-checkbox:checked");

    if (!selected) {
        return;
    }

    const row = selected.closest(".file-row");

    if (row) {
        openSidePanel(row, "info");
    }
});

renameButton.addEventListener("click", function () {
    const selected = document.querySelector(".file-checkbox:checked");

    if (!selected) {
        return;
    }

    const row = selected.closest(".file-row");

    if (row) {
        const filePath = selected.value;
        const fileName = row.dataset.displayname;
        renameForm.action = "/rename/" + filePath;
        renameInput.value = fileName;
        renameModal.classList.add("active");
        renameInput.focus();
    }
});

downloadButton.addEventListener("click", function () {
    showDownloadOverlay();

    const selected = document.querySelectorAll(".file-checkbox:checked");

    if (selected.length > 30) {
        alert("You can download a maximum of 30 files at a time.");
        return;
    }

    selected.forEach(function (checkbox) {
        const filename = checkbox.value;
        const downloadLink = document.createElement("a");
        downloadLink.href = "/download/" + filename;
        downloadLink.download = "";
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    });

    setTimeout(function () {
        downloadOverlay.classList.remove("active");
    }, 1200);
});

moveButton.addEventListener("click", function () {

    const selected = document.querySelectorAll(".file-checkbox:checked");

    if (selected.length === 0) {
        return;
    }
    moveModal.classList.add("active");
});

// SEARCH
if (searchInput) {
    searchInput.addEventListener("input", function () {
        const searchText = searchInput.value.toLowerCase();

        fileRows.forEach(function (row) {
            const filename = row.dataset.name;
            row.style.display = filename.includes(searchText) ? "grid" : "none";
        });

        folderCards.forEach(function (card) {
            const foldername = card.dataset.foldername;
            card.style.display = foldername.includes(searchText) ? "block" : "none";
        });
    });
}

// STORAGE BAR
if (storageUsed) {
    storageUsed.style.width = storageUsed.dataset.storage + "%";
}

// SORTING
if (sortSelect) {
    sortSelect.addEventListener("change", function () {
        localStorage.setItem("selectedSort", sortSelect.value);

        const selectedSort = sortSelect.value;
        const fileList = document.querySelector(".file-list");
        const folderGrid = document.querySelector(".folder-card-grid");
        const fileRows = Array.from(document.querySelectorAll(".file-row"));
        const folderCards = Array.from(document.querySelectorAll(".folder-card-wrapper"));

        sortItems(fileRows, selectedSort);
        sortItems(folderCards, selectedSort);

        fileRows.forEach(function (row) {
            fileList.appendChild(row);
        });

        folderCards.forEach(function (folder) {
            folderGrid.appendChild(folder);
        });
    });

    const savedSort = localStorage.getItem("selectedSort");

    if (savedSort) {
        sortSelect.value = savedSort;
        sortSelect.dispatchEvent(new Event("change"));
    }
}

// UPLOAD
if (uploadDropZone && uploadInput) {
    uploadDropZone.addEventListener("dragover", function (event) {
        event.preventDefault();
        uploadDropZone.classList.add("dragover");
    });

    uploadDropZone.addEventListener("dragleave", function () {
        uploadDropZone.classList.remove("dragover");
    });

    uploadDropZone.addEventListener("drop", function (event) {
        event.preventDefault();
        uploadDropZone.classList.remove("dragover");

        const droppedFiles = event.dataTransfer.files;

        if (droppedFiles.length > 30) {
            alert("You can upload a maximum of 30 files at a time.");
            return;
        }

        uploadInput.files = droppedFiles;
        const uploadForm = uploadInput.closest("form");
        showUploadOverlay();
        uploadForm.submit();
    });
} 

if (uploadDropZone && hiddenUploadInput) {
    uploadDropZone.addEventListener("click", function (event) {
        if (
            event.target.tagName !== "BUTTON" &&
            event.target.tagName !== "INPUT" &&
            event.target.tagName !== "LABEL"
        ) {
            hiddenUploadInput.click();
        }
    });
} 

if (hiddenUploadInput) {
    hiddenUploadInput.addEventListener("change", function () {
        if (hiddenUploadInput.files.length > 30) {
            alert("You can upload a maximum of 30 files at a time.");
            return;
        }
        if (hiddenUploadInput.files.length > 0) {
            const uploadForm = hiddenUploadInput.closest("form");
            showUploadOverlay();
            uploadForm.submit();
        }
    });
}

// PROFILE MODAL
if (openProfileModal && profileModal) {
    openProfileModal.addEventListener("click", function () {
        profileModal.classList.add("active");
    });
}

if (closeProfileModal && profileModal) {
    closeProfileModal.addEventListener("click", function () {
        profileModal.classList.remove("active");
    });
}

window.addEventListener("click", function (event) {
    if (event.target === profileModal) {
        profileModal.classList.remove("active");
    }
});

if (openProfileAfterReload && openProfileAfterReload.value === "True") {
    profileModal.classList.add("active");
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && profileModal) {
        profileModal.classList.remove("active");
    }
});

// FILE SELECTION
fileRowList.forEach(function (row, index) {
    row.addEventListener("click", function (event) {
        const checkbox = row.querySelector(".file-checkbox");

        if (
            event.target.tagName === "BUTTON" ||
            event.target.tagName === "A" ||
            event.target.closest(".dropdown-menu")
        ) {
            return;
        }
        if (event.target.tagName === "INPUT") {
            lastSelectedIndex = index;
            updateSelectionToolbar();
            return;
        }
        if (event.shiftKey && lastSelectedIndex !== null) {
            const start = Math.min(lastSelectedIndex, index);
            const end = Math.max(lastSelectedIndex, index);

            fileRowList.forEach(function (item, itemIndex) {
                const itemCheckbox = item.querySelector(".file-checkbox");
                itemCheckbox.checked = itemIndex >= start && itemIndex <= end;
            });
            updateSelectionToolbar();
            return;
        }
        if (event.ctrlKey || event.metaKey) {
            checkbox.checked = !checkbox.checked;
            lastSelectedIndex = index;
            updateSelectionToolbar();
            return;
        }
        document.querySelectorAll(".file-checkbox").forEach(function (box) {
            box.checked = false;
        });

        checkbox.checked = true;
        lastSelectedIndex = index;
        updateSelectionToolbar();
        openSidePanel(row, "preview");
    });
});

document.addEventListener("click", function (event) {
    if (
        event.target.closest(".file-row") ||
        event.target.closest(".selection-toolbar") ||
        event.target.closest(".dropdown-menu") ||
        event.target.closest(".right-sidebar")
    ) {
        return;
    }
    document.querySelectorAll(".file-checkbox").forEach(function (box) {
        box.checked = false;
    });
    updateSelectionToolbar();
});

// SIDE PANEL ACTIONS
document.querySelectorAll(".open-side-preview").forEach(function (link) {
    link.addEventListener("click", function (event) {
        event.preventDefault();

        const row = link.closest(".file-row");

        if (row) {
            openSidePanel(row, "preview");
        }
    });
});

document.querySelectorAll(".open-side-info").forEach(function (link) {
    link.addEventListener("click", function (event) {
        event.preventDefault();

        const row = link.closest(".file-row");

        if (row) {
            openSidePanel(row, "info");
        }
    });
});

// RENAME MODAL
document.querySelectorAll(".open-rename-modal").forEach(function (link) {
    link.addEventListener("click", function (event) {
        event.preventDefault();

        const filePath = link.dataset.file;
        const fileName = link.dataset.name;

        renameForm.action = "/rename/" + filePath;
        renameInput.value = fileName;
        renameModal.classList.add("active");
        renameInput.focus();
    });
});

if (cancelRenameButton && renameModal) {
    cancelRenameButton.addEventListener("click", function () {
        renameModal.classList.remove("active");
    });
}

window.addEventListener("click", function (event) {
    if (event.target === renameModal) {
        renameModal.classList.remove("active");
    }
});

// DELETE MODAL
document.querySelectorAll(".open-delete-modal").forEach(function (link) {
    link.addEventListener("click", function (event) {
        event.preventDefault();

        const filePath = link.dataset.file;
        const fileName = link.dataset.name;

        deleteForm.action = "/delete/" + filePath;
        deleteModalText.textContent =
            `Are you sure you want to move "${fileName}" to the Bin?`;
        deleteModal.classList.add("active");
    });
});

if (cancelDeleteButton) {
    cancelDeleteButton.addEventListener("click", function () {
        deleteModal.classList.remove("active");
    });
}

window.addEventListener("click", function (event) {
    if (event.target === deleteModal) {
        deleteModal.classList.remove("active");
    }
});

if (bulkDeleteButton) {
    bulkDeleteButton.addEventListener("click", function () {
        deleteForm.querySelectorAll('input[name="selected_files"]').forEach(function (input) {
            input.remove();
        });

        const selected = document.querySelectorAll(".file-checkbox:checked");

        if (selected.length === 0) {
            return;
        }
        deleteForm.action = "/bulk-bin";
        deleteModalText.textContent =
            `Are you sure you want to move ${selected.length} item(s) to the Bin?`;
        selected.forEach(function (checkbox) {
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = "selected_files";
            input.value = checkbox.value;
            deleteForm.appendChild(input);
        });
        deleteModal.classList.add("active");
    });
}

// MOVE MODAL
moveButton.addEventListener("click", function () {
    moveForm.querySelectorAll('input[name="selected_files"]').forEach(function (input) {
        input.remove();
    });

    const selected = document.querySelectorAll(".file-checkbox:checked");

    if (selected.length === 0) {
        return;
    }

    selected.forEach(function (checkbox) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "selected_files";
        input.value = checkbox.value;
        moveForm.appendChild(input);
    });
    moveModal.classList.add("active");
});

if (cancelMoveButton) {
    cancelMoveButton.addEventListener("click", function () {
        moveModal.classList.remove("active");
    });
}

window.addEventListener("click", function (event) {
    if (event.target === moveModal) {
        moveModal.classList.remove("active");
    }
});

document.querySelectorAll(".open-move-modal").forEach(function (link) {
    link.addEventListener("click", function (event) {
        event.preventDefault();

        moveForm.querySelectorAll('input[name="selected_files"]').forEach(function (input) {
            input.remove();
        });

        const input = document.createElement("input");

        input.type = "hidden";
        input.name = "selected_files";
        input.value = link.dataset.file;
        moveForm.appendChild(input);
        moveModal.classList.add("active");
    });
});

// FOLDER ACTIONS
document.querySelectorAll(".open-folder-info").forEach(function (link) {
    link.addEventListener("click", function (event) {
        event.preventDefault();

        rightSidebar.classList.remove("preview-mode");
        appLayout.classList.remove("sidebar-preview-open");
        rightSidebar.classList.add("info-mode");
        appLayout.classList.add("sidebar-info-open");

        sidePanelContent.innerHTML = `
            <div class="side-panel-header">
                <strong>${link.dataset.name}</strong>
                <button type="button" id="closeSidePanel">✕</button>
            </div>

            <div class="side-preview-file-icon">📁</div>

            <div class="side-file-details">
                <h3>Folder details</h3>
                <p><strong>Name:</strong> ${link.dataset.name}</p>
                <p><strong>Owner:</strong> ${link.dataset.owner}</p>
                <p><strong>Location:</strong> ${link.dataset.location}</p>
                <p><strong>Items:</strong> ${link.dataset.count}</p>
            </div>
        `;
        document.getElementById("closeSidePanel").addEventListener("click", function () {
            rightSidebar.classList.remove("info-mode", "preview-mode");
            appLayout.classList.remove("sidebar-info-open", "sidebar-preview-open");
            sidePanelContent.innerHTML = `<p>Select a file to preview details here.</p>`;
        });
    });
});

document.querySelectorAll(".folder-card-wrapper").forEach(function (folder) {
    folder.addEventListener("dblclick", function () {

        const folderPath = folder.dataset.folderpath;

        if (!folderPath) {
            return;
        }

        window.location.href = "/folder/" + encodeURIComponent(folderPath);
    });
});

// DRAG AND DROP
document.querySelectorAll(".file-row").forEach(function (row) {
    row.addEventListener("dragstart", function () {
        const rowCheckbox = row.querySelector(".file-checkbox");

        if (rowCheckbox.checked) {
            draggedFilePaths = Array.from(
                document.querySelectorAll(".file-checkbox:checked")
            ).map(function (checkbox) {
                return checkbox.value;
            });
        } else {
            draggedFilePaths = [row.dataset.fullpath];
        }
    });
});

document.querySelectorAll(".folder-card-wrapper").forEach(function (folder) {
    folder.addEventListener("dragenter", function () {
        folder.classList.add("drag-over");
    });

    folder.addEventListener("dragleave", function () {
        folder.classList.remove("drag-over");
    });

    folder.addEventListener("dragover", function (event) {
        event.preventDefault();
    });

    folder.addEventListener("drop", function (event) {
        event.preventDefault();
        folder.classList.remove("drag-over");

        const destination = folder.dataset.folderpath;

        if (draggedFilePaths.length === 0 || !destination) {
            return;
        }

        const formData = new FormData();

        draggedFilePaths.forEach(function (filePath) {
            formData.append("selected_files", filePath);
        });

        formData.append("destination", destination);
        formData.append("return_to", window.location.pathname);

        fetch("/bulk-move", {
            method: "POST",
            body: formData
        }).then(function () {

            document.querySelectorAll(".file-checkbox").forEach(function (box) {
                box.checked = false;
            });

            draggedFilePaths = [];
            lastSelectedIndex = null;
            updateSelectionToolbar();
            window.location.reload();
        });
    });
});

// CONTEXT MENU
document.addEventListener("contextmenu", function (event) {
    event.preventDefault();
});

document.querySelectorAll(".file-row").forEach(function (row) {
    row.addEventListener("contextmenu", function (event) {
        event.preventDefault();
        contextTargetRow = row;
        contextMenu.style.left = event.clientX + "px";
        contextMenu.style.top = event.clientY + "px";
        contextMenu.style.display = "block";
    });
});

document.addEventListener("click", function () {
    contextMenu.style.display = "none";
});

contextPreview.addEventListener("click", function () {
    if (contextTargetRow) {
        openSidePanel(contextTargetRow, "preview");
    }
});

contextDownload.addEventListener("click", function () {
    if (contextTargetRow) {
        window.location.href = "/download/" + contextTargetRow.dataset.fullpath;
    }
});

contextRename.addEventListener("click", function () {
    if (!contextTargetRow) {
        return;
    }

    const filePath = contextTargetRow.dataset.fullpath;
    const nameElement =
        contextTargetRow.querySelector(".file-name-text");
    const originalName = nameElement.textContent.trim();

    nameElement.contentEditable = true;
    nameElement.classList.add("editing");
    nameElement.focus();

    document.execCommand("selectAll", false, null);

    function finishRename() {
        nameElement.contentEditable = false;
        nameElement.classList.remove("editing");

        const newName = nameElement.textContent.trim();

        if (
            newName === "" ||
            newName === originalName
        ) {
            nameElement.textContent = originalName;
            return;
        }

        const formData = new FormData();

        formData.append("new_name", newName);

        fetch("/rename/" + filePath, {
            method: "POST",
            body: formData
        }).then(function () {
            window.location.reload();
        });
    }

    nameElement.addEventListener("keydown", function (event) {

        if (event.key === "Enter") {
            event.preventDefault();
            finishRename();
        }
    }, { once: true });

    nameElement.addEventListener("blur", finishRename, {
        once: true
    });
});

contextDelete.addEventListener("click", function () {
    if (contextTargetRow) {
        const filePath = contextTargetRow.dataset.fullpath;
        const fileName = contextTargetRow.dataset.displayname;

        deleteForm.action = "/delete/" + filePath;
        deleteModalText.textContent =
            `Are you sure you want to delete "${fileName}"?`;
        deleteModal.classList.add("active");
    }
});