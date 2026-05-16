const checkboxes = document.querySelectorAll(".file-checkbox");

const toolbar = document.getElementById("selectionToolbar");
const selectedCount = document.getElementById("selectedCount");

const downloadButton = document.getElementById("downloadButton");
const moveButton = document.getElementById("moveButton");
const infoButton = document.getElementById("infoButton");
const renameButton = document.getElementById("renameButton");

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

checkboxes.forEach(function(checkbox) {
    checkbox.addEventListener("change", updateSelectionToolbar);
});

infoButton.addEventListener("click", function () {

    const selected = document.querySelector(".file-checkbox:checked");

    if (!selected) {
        return;
    }

    const filename = selected.value;

    window.location.href = "/info/" + filename;
});

renameButton.addEventListener("click", function () {
    const selected = document.querySelector(".file-checkbox:checked");

    if (!selected) {
        return;
    }

    const filename = selected.value;

    window.location.href = "/rename-page/" + filename;
});

downloadButton.addEventListener("click", function () {
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
});

moveButton.addEventListener("click", function () {
    const selected = document.querySelectorAll(".file-checkbox:checked");

    if (selected.length === 0) {
        return;
    }

    const form = document.createElement("form");
    form.method = "post";
    form.action = "/bulk-move-page";

    const returnInput = document.createElement("input");
    returnInput.type = "hidden";
    returnInput.name = "return_to";
    returnInput.value = window.location.pathname;

    form.appendChild(returnInput);

    selected.forEach(function (checkbox) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "selected_files";
        input.value = checkbox.value;
        form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
});

const searchInput = document.getElementById("searchInput");
const fileRows = document.querySelectorAll(".file-row");
const folderCards = document.querySelectorAll(".folder-card-wrapper");

if (searchInput) {
    searchInput.addEventListener("input", function () {
        const searchText = searchInput.value.toLowerCase();

        fileRows.forEach(function (row) {
            const filename = row.dataset.filename;

            row.style.display = filename.includes(searchText) ? "grid" : "none";
        });

        folderCards.forEach(function (card) {
            const foldername = card.dataset.foldername;

            card.style.display = foldername.includes(searchText) ? "block" : "none";
        });
    });
}

const storageUsed = document.querySelector(".storage-used");

if (storageUsed) {
    storageUsed.style.width = storageUsed.dataset.storage + "%";
}

const profileModal = document.getElementById("profileModal");
const openProfileModal = document.getElementById("openProfileModal");
const closeProfileModal = document.getElementById("closeProfileModal");

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

const openProfileAfterReload = document.getElementById("openProfileAfterReload");

if (openProfileAfterReload && openProfileAfterReload.value === "True") {
    profileModal.classList.add("active");
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && profileModal) {
        profileModal.classList.remove("active");
    }
});

const sortSelect = document.getElementById("sortSelect");

if (sortSelect) {

    sortSelect.addEventListener("change", function () {

        localStorage.setItem("selectedSort", sortSelect.value);

        const fileList = document.querySelector(".file-list");
        const rows = Array.from(document.querySelectorAll(".file-row"));

        const selectedSort = sortSelect.value;

        rows.sort(function (a, b) {
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

            if (selectedSort === "location") {
                return a.dataset.location.localeCompare(b.dataset.location);
            }

            return 0;
        });

        rows.forEach(function (row) {
            fileList.appendChild(row);
        });

    });

    const savedSort = localStorage.getItem("selectedSort");

    if (savedSort && sortSelect) {
        sortSelect.value = savedSort;
        sortSelect.dispatchEvent(new Event("change"));
    }

}

const uploadDropZone = document.getElementById("uploadDropZone");
const uploadInput = document.querySelector('input[type="file"]');

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
        uploadForm.submit();
    });

}

const hiddenUploadInput = document.getElementById("hiddenUploadInput");

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
            uploadForm.submit();
        }
    });
}