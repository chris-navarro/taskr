(function () {
    "use strict";

    const form = document.getElementById("taskForm");
    if (!form) {
        return;
    }

    const descriptionField = document.getElementById("descriptionEditor");
    const remarksField = document.getElementById("remarksEditor");
    const editors = {};

    function makeEditor(field, placeholder) {
        if (!field) {
            return null;
        }
        if (typeof Quill === "undefined") {
            field.name = field.id === "descriptionEditor" ? "description" : "remarks";
            return null;
        }
        const editor = document.createElement("div");
        editor.className = "form-control p-0";
        editor.setAttribute("aria-label", field.getAttribute("aria-label") || "Rich text editor");
        field.hidden = true;
        field.parentNode.insertBefore(editor, field);
        return new Quill(editor, {
            theme: "snow",
            placeholder: placeholder,
            modules: {
                toolbar: [
                    ["bold", "italic", "underline"],
                    [{ list: "bullet" }, { list: "ordered" }],
                    ["link"]
                ]
            }
        });
    }

    editors.description = makeEditor(descriptionField, "Describe the task...");
    editors.remarks = makeEditor(remarksField, "Add remarks...");

    document.querySelectorAll(".task-date").forEach(function (field) {
        if (typeof flatpickr !== "undefined") {
            flatpickr(field, {
                enableTime: true,
                dateFormat: "Y-m-d H:i",
                time_24hr: true,
                allowInput: true
            });
        }
    });

    if (typeof TomSelect !== "undefined") {
        new TomSelect("#tagsInput", {
            plugins: ["remove_button"],
            delimiter: ",",
            persist: false,
            create: true,
            createOnBlur: true
        });
        new TomSelect("#parentTask", { create: false });
    }

    function showError(message) {
        let alert = form.querySelector(".task-form-error");
        if (!alert) {
            alert = document.createElement("div");
            alert.className = "alert alert-danger task-form-error";
            form.querySelector(".modal-body").prepend(alert);
        }
        alert.textContent = message;
        alert.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function syncEditors() {
        const descriptionValue = document.getElementById("descriptionValue");
        const remarksValue = document.getElementById("remarksValue");
        if (descriptionValue && editors.description) {
            descriptionValue.value = editors.description.root.innerHTML;
        }
        if (remarksValue && editors.remarks) {
            remarksValue.value = editors.remarks.root.innerHTML;
        }
    }

    form.addEventListener("submit", function (event) {
        syncEditors();
        const subject = form.elements.subject.value.trim();
        const start = form.elements.start_date.value;
        const due = form.elements.due_date.value;
        const hours = Number(form.elements.estimated_hours.value);

        if (!subject) {
            event.preventDefault();
            showError("Subject is required.");
            form.elements.subject.focus();
            return;
        }
        if (!start || !due || new Date(due) < new Date(start)) {
            event.preventDefault();
            showError("Due date must be on or after the start date.");
            return;
        }
        if (!Number.isFinite(hours) || hours < 0) {
            event.preventDefault();
            showError("Estimated hours must be zero or greater.");
            return;
        }

        event.preventDefault();
        const submitButton = form.querySelector("[type=submit]");
        submitButton.disabled = true;
        fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            headers: { "X-Requested-With": "XMLHttpRequest", Accept: "application/json" }
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    if (!response.ok) {
                        throw new Error(data.error || "Unable to create task.");
                    }
                    return data;
                });
            })
            .then(function (data) {
                if (typeof Swal !== "undefined") {
                    Swal.close();
                }
                if (window.location.hash === "#createTaskModal") {
                    window.history.replaceState(null, "", window.location.pathname + window.location.search);
                }
                window.location.reload();
            })
            .catch(function (error) {
                if (typeof Swal !== "undefined") {
                    Swal.close();
                }
                showError(error.message);
            })
            .finally(function () {
                submitButton.disabled = false;
            });
    });

    window.addEventListener("task:created", function (event) {
        const task = event.detail;
        const body = document.getElementById("taskTableBody");
        if (!body || !task) {
            return;
        }
        const emptyRow = body.querySelector("td[colspan]");
        if (emptyRow) {
            body.innerHTML = "";
        }
        const row = document.createElement("tr");
        row.innerHTML = "<td><strong></strong></td>" +
            "<td></td><td><span class=\"badge bg-secondary\"></span></td>" +
            "<td><span class=\"badge bg-primary\"></span></td>" +
            "<td><div class=\"progress\"><div class=\"progress-bar\" role=\"progressbar\" style=\"width: 0%\">0%</div></div></td>" +
            "<td></td><td><a class=\"btn btn-sm btn-primary\"><i class=\"bi bi-eye\"></i></a></td>";
        row.querySelector("strong").textContent = task.subject;
        row.children[1].textContent = task.project_id || "";
        row.children[2].querySelector("span").textContent = task.status;
        row.children[3].querySelector("span").textContent = task.priority;
        row.children[5].textContent = task.due_date;
        row.children[6].querySelector("a").href = "/tasks/" + encodeURIComponent(task._id);
        body.prepend(row);
    });

    if (window.location.hash === "#createTaskModal" && typeof bootstrap !== "undefined") {
        bootstrap.Modal.getOrCreateInstance(document.getElementById("createTaskModal")).show();
    }
})();
