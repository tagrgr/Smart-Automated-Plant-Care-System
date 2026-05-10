const checkboxes = document.querySelectorAll(".file-checkbox");
const toolbar = document.getElementById("selectionToolbar");
const selectedCount = document.getElementById("selectedCount");

function updateSelectionToolbar() {
    const selected = document.querySelectorAll(".file-checkbox:checked");
    const count = selected.length;

    selectedCount.textContent = count + " selected";

    if (count > 0) {
        toolbar.classList.add("active");
    } else {
        toolbar.classList.remove("active");
    }
}

checkboxes.forEach(function(checkbox) {
    checkbox.addEventListener("change", updateSelectionToolbar);
});