
// ==================== MAIN SCRIPT ====================
document.addEventListener("DOMContentLoaded", () => {

  // Grab key DOM elements
  const addBtn = document.getElementById("add-task");
  const viewBox = document.getElementById("task-view-box");
  const emptyView = document.getElementById("empty-view");
  const taskDetails = document.getElementById("task-details");
  const taskForm = document.getElementById("task-form");
  const taskBox = document.getElementById("task-box");

  // guard clause: stop if any critical element is missing
  if (!addBtn || !viewBox || !emptyView || !taskDetails || !taskForm || !taskBox) return;

  // helper: escape text inserted into innerHTML
  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  //==================== COMPLETION STATE (localStorage) ====================
  function loadCompletionState() {
    const saved = JSON.parse(localStorage.getItem("completedTasks") || "{}");
    return saved;
  }

  function saveCompletionState(state) {
    localStorage.setItem("completedTasks", JSON.stringify(state));
  }

  // Restore task completion state to DOM
  function restoreCompletionState() {
    const completedTasks = loadCompletionState();
    taskBox.querySelectorAll(".task").forEach((li) => {
      const id = li.dataset.id;
      const check = li.querySelector(".task-check");
      if (id && completedTasks[id]) {
        li.classList.add("completed");
        if (check) check.checked = true;
      } else {
        li.classList.remove("completed");
        if (check) check.checked = false;
      }
    });
  }

  // Save changes when checkbox toggled
  taskBox.addEventListener("change", (ev) => {
    if (ev.target.classList.contains("task-check")) {
      const li = ev.target.closest(".task");
      if (!li) return;

      const id = li.dataset.id;
      const completedTasks = loadCompletionState();

      if (ev.target.checked) {
        li.classList.add("completed");
        if (id) completedTasks[id] = true; // save
      } else {
        li.classList.remove("completed");
        if (id) delete completedTasks[id]; // remove
      }

      saveCompletionState(completedTasks); // persist
    }
  });

  // --- restore state on load
  restoreCompletionState();

  // ==================== TOAST NOTIFICATION ====================
  function showToast(message, undoUrl) {
    const toast = document.getElementById("toast");
    const toastMsg = document.getElementById("toast-message");
    const undoBtn = document.getElementById("undo-btn");

    if (!toast || !toastMsg || !undoBtn) return;

    toastMsg.textContent = message;
    toast.classList.remove("hidden");
    toast.classList.add("show");

    if (undoUrl && undoUrl !== "#") {
      undoBtn.style.display = "inline-block";
      undoBtn.onclick = () => {
        toast.classList.remove("show");
        toast.classList.add("hidden");
        window.location.href = undoUrl;
      };
    } else {
      undoBtn.style.display = "none"; // hide undo for updates
    }

    // Auto-hide after 5s
    setTimeout(() => {
      toast.classList.remove("show");
      toast.classList.add("hidden");
    }, 5000);
  }

  // ==================== ADD FORM TOGGLE ====================
  addBtn.addEventListener("click", (ev) => {
    ev.stopPropagation();

    const formVisible = !taskForm.classList.contains("hidden");
    if (!formVisible) {
      // Show form
      taskForm.classList.remove("hidden");
      taskDetails.classList.add("hidden");
      emptyView.classList.add("hidden");
      viewBox.classList.add("dim");
      const first = taskForm.querySelector("input, textarea, select");
      if (first) first.focus();
    } else {
      // Hide form
      taskForm.classList.add("hidden");
      viewBox.classList.remove("dim");
      if (taskDetails.classList.contains("hidden")) {
        emptyView.classList.remove("hidden");
      }
    }
  });

  // Prevent clicks inside right panel from closing form/details
  viewBox.addEventListener("click", (e) => e.stopPropagation());

  // ==================== TASK CLICK HANDLER ====================
  taskBox.addEventListener("click", (ev) => {
    const li = ev.target.closest(".task");
    if (!li) return;
    ev.stopPropagation();

    // remove 'selected' from others
    [...taskBox.querySelectorAll(".task")].forEach((t) => t.classList.remove("selected"));
    li.classList.add("selected");

    // hide form & placeholder
    taskForm.classList.add("hidden");
    emptyView.classList.add("hidden");
    viewBox.classList.remove("dim");
    taskDetails.classList.remove("hidden");

    // read data attributes
    const priority = li.dataset.priority || li.dataset.prio || "";

    viewBox.classList.remove("high", "medium", "low");

    // apply color based on priority
    if (priority === "1") {
      viewBox.classList.add("high");
    } else if (priority === "2") {
      viewBox.classList.add("medium");
    } else if (priority === "3") {
      viewBox.classList.add("low");
    }

    const label = li.dataset.label || "";
    const taskName = li.dataset.task || "";
    const date = li.dataset.date || "";
    const time = li.dataset.time || "";
    const desc = li.dataset.desc || "";
    const sub = li.dataset.sub || "";
    const created = li.dataset.created || "";

    // map numeric priority -> label
    const priorityMap = {
      "1": "High",
      "2": "Medium",
      "3": "Low"
    };
    const priorityLabel = priorityMap[priority] || priority; // fallback if something else

    // render task details
    taskDetails.innerHTML = `
      <div class="task-details-box">

        <div id="header">
          <span class="prio">Priority Level: <strong>${escapeHtml(priorityLabel)}</strong></span>
          <span>Label: <strong>${escapeHtml(label)}</strong></span>
        </div>

        <h2 class="task-todo">${escapeHtml(taskName)}</h2>
        <hr>

        <div id="details">
          <span><strong>Deadline: </strong>${escapeHtml(formatDate(date))} | ${escapeHtml(formatTime(time))}</span>
          <br><br>
          <span><strong>Description:</strong><br>${escapeHtml(desc)}</span>
          <br><br><br>
          <span><strong>Sub-tasks:</strong> ${escapeHtml(sub)}</span>
          <br><br>
        </div>

        <div id="footer">
          <span><em>Created on: ${escapeHtml(formatCreatedDateTime(created))}</em></span>

          <div class="buttons" style="margin-top:12px;">
            <button id="edit-task-btn" type="button"  title="Edit Task"><span class="material-symbols-outlined">edit_square</span></button>
            <button id="delete-task-btn" type="button"  title="Delete Task"><span class="material-symbols-outlined">delete</span></button>
          </div>
        </div>
      </div>
    `;

    // ==================== EDIT BUTTON ====================
    const editBtn = document.getElementById("edit-task-btn");
    if (editBtn) {
      editBtn.addEventListener("click", () => {
        // Replace details with editable form
        taskDetails.innerHTML = `
          <form method="POST" action="/edit/${li.dataset.id}" class="task-details-box">
            <h2 class="edit-task">Edit Task</h2>

            <div id="task-header">

              <div id="edit-prio-select">
                <label><strong>Priority Level:</strong></label>
                <label><br>
                  <input type="radio" name="priority" value="1" ${priority === "1" ? "checked" : ""}> High Priority
                </label>
                <label>
                  <input type="radio" name="priority" value="2" ${priority === "2" ? "checked" : ""}> Medium Priority
                </label>
                <label>
                  <input type="radio" name="priority" value="3" ${priority === "3" ? "checked" : ""}> Low Priority
                </label>
              </div>

              <div id="label">
                <label><strong>Label</strong></label>
                <br>
                <input type="text" name="label" value="${escapeHtml(label)}" required><br>
              </div>

              <div id="to-do-title">
                <label><strong>Task Name</strong></label>
                <br>
                <input type="text" name="task_name" value="${escapeHtml(taskName)}" required><br>
              </div>
              
              <span class="dl-label"><strong>Deadline</strong></span>

              <div id="deadline">
                <label>Date:</label>
                <input type="date" name="date" value="${escapeHtml(date)}"><br>

                <label>Time:</label>
                <input type="time" name="time" value="${escapeHtml(time)}"><br>
              </div>
            </div>

            <div id="desc-label">
              <label><strong>Description</strong></label>
              <br>
              <textarea name="task_desc">${escapeHtml(desc)}</textarea><br>
            </div>

            <label class="switch-label">
                <strong> Add sub to-do(s) </strong>
                <label class="switch" title="Toggle sub to-dos">
                    <input type="checkbox" id="toggle-sub" ${sub ? "checked" : ""}>
                    <span class="slider"></span>
                </label>
            </label>

            <div id="sub-task-box" class="sub-box" style="display:${sub ? "block" : "none"}" aria-hidden="true">
              <label>Sub-Tasks:</label>
              <input type="text" name="sub_todo" value="${escapeHtml(sub)}"><br>
            </div>

            <div id="save-cancel-btns">
              <button type="button" id="cancel-edit"  title="Cancel Edit"><span class="material-symbols-outlined">close</span></button>
              <button type="submit" id="save-changes">SAVE CHANGES</button>
              
            </div>
          </form>
        `;

        // Sub-task toggle in edit form
        const toggle = document.getElementById("toggle-sub");
        const subBox = document.getElementById("sub-task-box");
        if (toggle && subBox) {
          toggle.addEventListener("change", () => {
            subBox.style.display = toggle.checked ? "block" : "none";
          });
        }

        // Save changes toast
        const editForm = taskDetails.querySelector("form");
        if (editForm) {
          editForm.addEventListener("submit", () => {
            localStorage.setItem("toastMessage", "Task Updated");
          });
        }

        // cancel button handler
        const cancelBtn = document.getElementById("cancel-edit");
        if (cancelBtn) {
          cancelBtn.addEventListener("click", () => {
            if (typeof li.click === "function") {
              li.click();
            } else {
              emptyView.classList.remove("hidden");
            }
          });
        }
      });
    }

    // ==================== DELETE BUTTON ====================
    const deleteBtn = document.getElementById("delete-task-btn");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", () => {
        if (confirm("Delete this task?")) {
          fetch("/delete/" + li.dataset.id).then(() => {
            localStorage.setItem("toastMessage", "Task Deleted");
            localStorage.setItem("undoUrl", "/undo_delete");
            window.location.reload();
          });
        }
      });
    }
  });

  // ====================  CLICK OUTSIDE RESET ====================
  document.addEventListener("click", () => {
    if (
      !emptyView.classList.contains("hidden") &&
      taskForm.classList.contains("hidden") &&
      taskDetails.classList.contains("hidden")
    ) {
      return;
    }
    taskForm.classList.add("hidden");
    taskDetails.classList.add("hidden");
    [...taskBox.querySelectorAll(".task")].forEach((t) => t.classList.remove("selected"));
    emptyView.classList.remove("hidden");
    viewBox.classList.remove("dim");

    viewBox.classList.remove("high", "medium", "low");
  });

  // show toast if stored in localStorage
  const savedMsg = localStorage.getItem("toastMessage");
  const savedUndo = localStorage.getItem("undoUrl");
  if (savedMsg) {
    showToast(savedMsg, savedUndo || "#");
    localStorage.removeItem("toastMessage");
    localStorage.removeItem("undoUrl");
  }
});

// ==================== SUB-TODO TOGGLE (GLOBAL) ====================
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("toggle-sub");
  const subBox = document.getElementById("sub-task-box");

  if (toggle && subBox) {
    toggle.addEventListener("change", () => {
      subBox.style.display = toggle.checked ? "block" : "none";
    });
  }
});

//  ==================== FORMAT HELPERS ====================
function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d)) return dateStr; // fallback if invalid
  return d.toLocaleDateString("en-US", {
    month: "long",   
    day: "numeric", 
    year: "numeric",
  });
}

function formatTime(timeStr) {
  if (!timeStr) return "";
  const [hourStr, minute] = timeStr.split(":");
  let hour = parseInt(hourStr, 10);
  const ampm = hour >= 12 ? "PM" : "AM";
  hour = hour % 12 || 12; // convert 0 → 12
  return `${hour}:${minute} ${ampm}`;
}

function formatCreatedDateTime(createdStr) {
  if (!createdStr) return "";
  const d = new Date(createdStr);
  if (isNaN(d)) return createdStr; // fallback if invalid

  // format MM-DD-YYYY
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const year = d.getFullYear();

  // format hh:mm AM/PM
  let hour = d.getHours();
  const minute = String(d.getMinutes()).padStart(2, "0");
  const ampm = hour >= 12 ? "PM" : "AM";
  hour = hour % 12 || 12; // 0 → 12

  return `${month}-${day}-${year} ${hour}:${minute} ${ampm}`;
}


document.addEventListener("DOMContentLoaded", () => {
    const accountIcon = document.getElementById("account-icon");
    const profileBox = document.getElementById("profile-box");

    // Toggle floating box when clicking the <a>
    accountIcon.addEventListener("click", (e) => {
        e.preventDefault(); // Prevent navigation
        e.stopPropagation(); // Prevent bubbling
        profileBox.classList.toggle("hidden");
    });

    // Hide when clicking outside
    document.addEventListener("click", (e) => {
        if (!profileBox.classList.contains("hidden") &&
            !profileBox.contains(e.target) &&
            !accountIcon.contains(e.target)) {
            profileBox.classList.add("hidden");
        }
    });
});