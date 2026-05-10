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

if (searchInput) {
    searchInput.addEventListener("input", function () {
        const searchText = searchInput.value.toLowerCase();

        fileRows.forEach(function (row) {
            const filename = row.dataset.filename;

            if (filename.includes(searchText)) {
                row.style.display = "grid";
            } else {
                row.style.display = "none";
            }
        });
    });
}