(function () {
    "use strict";

    document.querySelectorAll(".milestone-card").forEach(function (card, index) {
        card.style.setProperty("--milestone-order", index);
        card.addEventListener("click", function () {
            document.querySelectorAll(".milestone-card.is-selected").forEach(function (selected) {
                selected.classList.remove("is-selected");
            });
            card.classList.add("is-selected");
        });
    });

    document.querySelectorAll(".gantt-fill").forEach(function (bar) {
        bar.style.width = (bar.dataset.progress || "0") + "%";
    });

    const hourBars = document.querySelectorAll(".analytics-bar span");
    const maxHours = Math.max.apply(null, Array.from(hourBars).map(function (bar) {
        return Number(bar.dataset.width) || 0;
    }).concat([1]));
    hourBars.forEach(function (bar) {
        bar.style.width = ((Number(bar.dataset.width) || 0) / maxHours * 100) + "%";
    });
    const plannedActualBars = document.querySelectorAll(".planned-actual-bar span");
    const maxPlannedActual = Math.max.apply(null, Array.from(plannedActualBars).map(function (bar) {
        return Number(bar.dataset.width) || 0;
    }).concat([1]));
    plannedActualBars.forEach(function (bar) {
        bar.style.width = ((Number(bar.dataset.width) || 0) / maxPlannedActual * 100) + "%";
    });
    document.querySelectorAll(".gantt-marker").forEach(function (marker) {
        const schedule = marker.closest(".gantt-schedule");
        marker.style.left = (((Number(marker.dataset.left) || 0) - Number(schedule.dataset.left || 0)) / (Number(schedule.dataset.width) || 1) * 100) + "%";
    });
    document.querySelectorAll(".gantt-schedule").forEach(function (schedule) {
        schedule.style.left = (schedule.dataset.left || 0) + "%";
        schedule.style.width = (schedule.dataset.width || 1) + "%";
    });
})();
