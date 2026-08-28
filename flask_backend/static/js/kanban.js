document.addEventListener("DOMContentLoaded", function () {
    let draggedTask;
    const modal = document.getElementById("kanbanUpdateModal");
    const dateField = document.getElementById("kanbanWorkedAt");
    modal.addEventListener("show.bs.modal", function () {
        if (!dateField.value) {
            const now = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
            dateField.value = now.toISOString().slice(0, 16);
        }
    });
    document.querySelectorAll(".kanban-card").forEach(function (card) {
        card.addEventListener("dragstart", function () {
            draggedTask = card;
            card.classList.add("is-dragging");
        });
        card.addEventListener("dragend", function () {
            card.classList.remove("is-dragging");
        });
    });
    document.querySelectorAll(".kanban-dropzone").forEach(function (zone) {
        zone.addEventListener("dragover", function (event) {
            event.preventDefault();
            zone.classList.add("is-over");
        });
        zone.addEventListener("dragleave", function () {
            zone.classList.remove("is-over");
        });
        zone.addEventListener("drop", async function (event) {
            event.preventDefault();
            zone.classList.remove("is-over");
            if (!draggedTask) return;
            const status = zone.closest(".kanban-column").dataset.status;
            const taskId = draggedTask.dataset.taskId;
            const form = modal.querySelector("form");
            form.action = "/tasks/" + encodeURIComponent(taskId) + "/updates";
            modal.querySelector("[name='status']").value = status;
            modal.querySelector("[name='progress']").value = draggedTask.dataset.progress || "0";
            modal.querySelector("[name='update_start_date']").value = draggedTask.dataset.start;
            modal.querySelector("[name='update_due_date']").value = draggedTask.dataset.due;
            modal.querySelector("[name='estimated_hours']").value = draggedTask.dataset.estimated || "0";
            bootstrap.Modal.getOrCreateInstance(modal).show();
        });
    });
});
