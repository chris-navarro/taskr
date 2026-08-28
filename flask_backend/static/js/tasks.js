"use strict";

/***************************************************
 *
 * Taskr
 * Task Module
 *
 ***************************************************/


document.addEventListener("DOMContentLoaded", () => {

    initializeTaskForm();

    initializeDeleteButtons();

    initializeProgressBars();

    initializeProgressDate();

});


/***************************************************
 *
 * Create Task Validation
 *
 ***************************************************/

function initializeTaskForm() {

    const form = document.getElementById("taskForm");

    if (!form) return;

    form.addEventListener("submit", function (event) {

        const subject =
            form.subject.value.trim();

        const start =
            new Date(form.start_date.value);

        const due =
            new Date(form.due_date.value);

        if (subject.length === 0) {

            event.preventDefault();

            Swal.fire({

                icon: "warning",

                title: "Subject Required",

                text: "Please enter a task subject."

            });

            return;

        }

        if (subject.length > 150) {

            event.preventDefault();

            Swal.fire({

                icon: "error",

                title: "Subject Too Long",

                text: "Maximum is 150 characters."

            });

            return;

        }

        if (start > due) {

            event.preventDefault();

            Swal.fire({

                icon: "error",

                title: "Invalid Timeline",

                text: "Due Date must be after Start Date."

            });

            return;

        }

        Swal.fire({

            title: "Creating Task...",

            text: "Please wait.",

            allowOutsideClick: false,

            didOpen: () => {

                Swal.showLoading();

            }

        });

    });

}


/***************************************************
 *
 * Delete Confirmation
 *
 ***************************************************/

function initializeDeleteButtons() {

    const buttons = document.querySelectorAll(

        ".btn-delete"

    );

    buttons.forEach(button => {

        button.addEventListener("click", () => {

            const id =
                button.dataset.id;

            const subject =
                button.dataset.subject;

            Swal.fire({

                icon: "warning",

                title: "Delete Task?",

                html:

                    "<strong>" +

                    subject +

                    "</strong><br><br>This action can be restored because Taskr performs a soft delete.",

                showCancelButton: true,

                confirmButtonText: "Delete",

                confirmButtonColor: "#dc3545"

            })

            .then(result => {

                if (result.isConfirmed) {

                    createDeleteForm(id);

                }

            });

        });

    });

}


/***************************************************
 *
 * Dynamic Delete Form
 *
 ***************************************************/

function createDeleteForm(taskId) {

    const form =
        document.createElement("form");

    form.method = "POST";

    form.action =
        "/tasks/delete/" + taskId;

    document.body.appendChild(form);

    form.submit();

}


/***************************************************
 *
 * Progress Animation
 *
 ***************************************************/

function initializeProgressBars() {

    const progressBars =
        document.querySelectorAll(

            ".progress-bar"

        );

    progressBars.forEach(bar => {

        const width =
            bar.style.width || (bar.dataset.progress || "0") + "%";

        bar.style.width = "0%";

        setTimeout(() => {

            bar.style.transition =
                "width 0.8s ease";

            bar.style.width = width;

        }, 200);

    });

}

function initializeProgressDate() {
    const dateField = document.getElementById("dateWorked");
    const modal = document.getElementById("updateProgressModal");
    if (!dateField || !modal) return;

    modal.addEventListener("show.bs.modal", () => {
        if (dateField.value) return;
        const now = new Date();
        const localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
        dateField.value = localDate.toISOString().slice(0, 16);
    });
}


/***************************************************
 *
 * Reset Modal
 *
 ***************************************************/

const modal = document.getElementById(

    "createTaskModal"

);

if (modal) {

    modal.addEventListener(

        "hidden.bs.modal",

        () => {

            const form =
                document.getElementById(

                    "taskForm"

                );

            if (form) {

                form.reset();

            }

        }

    );

}


/***************************************************
 *
 * Character Counter
 *
 ***************************************************/

const subjectInput = document.querySelector(

    "input[name='subject']"

);

if (subjectInput) {

    const counter =
        document.createElement("small");

    counter.className =
        "text-muted";

    subjectInput.parentNode.appendChild(

        counter

    );

    subjectInput.addEventListener(

        "input",

        () => {

            counter.innerHTML =

                subjectInput.value.length +

                "/150 characters";

        }

    );

}


/***************************************************
 *
 * Estimated Hours Validation
 *
 ***************************************************/

const hours = document.querySelector(

    "input[name='estimated_hours']"

);

if (hours) {

    hours.addEventListener(

        "change",

        () => {

            if (hours.value < 0) {

                hours.value = 0;

            }

        }

    );

}