const state = {
  user: null,
  patients: [],
  doctors: [],
  appointments: [],
  visits: [],
  prescriptions: [],
  bills: [],
  overview: null,
  notifications: [],
  appointmentFilter: "all",
  billFilter: "all",
};

const api = async (path, options = {}) => {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "Request failed");
  return body;
};

let toastTimer;
const toast = (message, isError = false) => {
  const element = document.querySelector("#toast");
  const icon = isError
    ? '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>'
    : '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>';
  element.innerHTML = `${icon}<span>${escapeHtml(message)}</span>`;
  element.classList.toggle("error", isError);
  element.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => element.classList.remove("show"), 3200);
};

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[ch]));

const initials = (name) =>
  String(name || "?")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("") || "?";

const avatarTone = (seed) => {
  const value = String(seed || "");
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) % 5;
  }
  return hash === 0 ? "" : `av-${hash}`;
};

const money = (value) => `$${Number(value || 0).toFixed(2)}`;

const ICONS = {
  edit: '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
  calendarPlus: '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M12 14v4M10 16h4"/></svg>',
  clock: '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
  xCircle: '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/></svg>',
  clipboardPlus: '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M9 14h6M12 11v6"/></svg>',
  pill: '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/></svg>',
  receipt: '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8M12 17.5v-11"/></svg>',
  wallet: '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/></svg>',
  fileText: '<svg class="icon-stroke" viewBox="0 0 24 24" aria-hidden="true"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/></svg>',
};

/* ---------------- NAVIGATION ---------------- */
const sidebar = document.querySelector("#sidebar");
const sidebarBackdrop = document.querySelector("#sidebar-backdrop");

function closeSidebar() {
  sidebar.classList.remove("open");
  sidebarBackdrop.classList.remove("open");
}

document.querySelector("#mobile-menu-btn").addEventListener("click", () => {
  sidebar.classList.toggle("open");
  sidebarBackdrop.classList.toggle("open");
});
sidebarBackdrop.addEventListener("click", closeSidebar);

function openModule(moduleName) {
  const targetButton = document.querySelector(`.nav-button[data-module="${moduleName}"]`);
  const targetSection = document.querySelector(`#${moduleName}`);
  if (!targetButton || !targetSection) return;

  document.querySelectorAll(".nav-button").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".module").forEach((m) => m.classList.remove("active"));
  targetButton.classList.add("active");
  targetSection.classList.add("active");

  const label = targetButton.querySelector(".nav-label").textContent;
  document.querySelector("#page-title").textContent = label;
  document.querySelector("#breadcrumb").textContent =
    moduleName === "dashboard" ? "Overview" : "Clinic Management";
  closeSidebar();
}

document.querySelectorAll(".nav-button").forEach((button) => {
  button.addEventListener("click", () => openModule(button.dataset.module));
});

document.querySelectorAll("[data-open]").forEach((button) => {
  button.addEventListener("click", () => openModule(button.dataset.open));
});

document.querySelector("#quick-book-btn").addEventListener("click", () => {
  openModule("appointments");
  document.querySelector("#patient-select").focus();
});

/* ---------------- AUTH & HEADER ---------------- */
async function loadSession() {
  try {
    const user = await api("/api/session");
    state.user = user;
    document.querySelector("#user-name").textContent = user.name;
    document.querySelector("#user-role").textContent = user.role;
    document.querySelector("#user-avatar").textContent = initials(user.name);
    document.querySelector("#welcome-heading").textContent = `Welcome back, ${user.name}`;
  } catch (_) {
    window.location.href = "/login";
  }
}

document.querySelector("#logout-button").addEventListener("click", async () => {
  const response = await fetch("/logout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (response.ok) window.location.href = "/login";
});

const now = new Date();
const dateTextEl = document.querySelector("#current-date-text") || document.querySelector("#current-date");
dateTextEl.textContent = new Intl.DateTimeFormat("en", {
  weekday: "short",
  month: "short",
  day: "numeric",
}).format(now);

document.querySelector("#welcome-day").textContent = `${new Intl.DateTimeFormat("en", {
  weekday: "long",
}).format(now)}'s overview`;

/* ---------------- NOTIFICATIONS ---------------- */
const notifButton = document.querySelector("#notif-button");
const notifPopover = document.querySelector("#notif-popover");

notifButton.addEventListener("click", (event) => {
  event.stopPropagation();
  const isOpen = !notifPopover.classList.contains("hidden");
  notifPopover.classList.toggle("hidden", isOpen);
  notifButton.setAttribute("aria-expanded", String(!isOpen));
});

document.addEventListener("click", (event) => {
  if (!notifPopover.contains(event.target) && !notifButton.contains(event.target)) {
    notifPopover.classList.add("hidden");
    notifButton.setAttribute("aria-expanded", "false");
  }
});

document.querySelector("#clear-notifs-btn").addEventListener("click", async () => {
  await api("/api/notifications/clear", { method: "POST" });
  state.notifications = [];
  renderNotifications();
});

function renderNotifications() {
  const badge = document.querySelector("#notif-badge");
  const list = document.querySelector("#notif-list");
  if (state.notifications.length > 0) {
    badge.textContent = state.notifications.length;
    badge.classList.remove("hidden");
  } else {
    badge.classList.add("hidden");
  }
  list.innerHTML =
    state.notifications
      .map(
        (item) => `
      <div class="notif-item">
        <span class="notif-dot-cat ${escapeHtml(item.category)}"></span>
        <div>
          <p>${escapeHtml(item.message)}</p>
          <span>${escapeHtml(item.timestamp)}</span>
        </div>
      </div>`
      )
      .join("") || '<p class="empty-state-sm">No recent activity yet.</p>';
}

/* ---------------- MODAL SYSTEM ---------------- */
const modalBackdrop = document.querySelector("#modal-backdrop");
const modalBody = document.querySelector("#modal-body");

function openModal({ kicker = "Action", title, html }) {
  document.querySelector("#modal-kicker").textContent = kicker;
  document.querySelector("#modal-title").textContent = title;
  modalBody.innerHTML = html;
  modalBackdrop.classList.remove("hidden");
}

function closeModal() {
  modalBackdrop.classList.add("hidden");
  modalBody.innerHTML = "";
}

document.querySelector("#modal-close").addEventListener("click", closeModal);
modalBackdrop.addEventListener("click", (event) => {
  if (event.target === modalBackdrop) closeModal();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modalBackdrop.classList.contains("hidden")) {
    closeModal();
  }
});

/* ---------------- RENDERERS ---------------- */
function renderDashboard() {
  const counts = state.overview?.counts || {
    patients: state.patients.length,
    doctors: state.doctors.length,
    appointments: state.appointments.length,
    visits: state.visits.length,
    bills: state.bills.length,
  };

  const icons = {
    patients: '<svg class="icon-stroke" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    doctors: '<svg class="icon-stroke" viewBox="0 0 24 24"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/></svg>',
    appointments: '<svg class="icon-stroke" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M9 16l2 2 4-4"/></svg>',
    visits: '<svg class="icon-stroke" viewBox="0 0 24 24"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M9 14h6M12 11v6"/></svg>',
    bills: '<svg class="icon-stroke" viewBox="0 0 24 24"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8M12 17.5v-11"/></svg>',
  };

  document.querySelector("#dashboard-cards").innerHTML = Object.entries(counts)
    .map(
      ([key, value]) => `
      <article class="card" data-jump="${escapeHtml(key)}">
        <div class="card-label"><span>${escapeHtml(key)}</span><div class="card-icon">${icons[key] || ""}</div></div>
        <strong>${escapeHtml(value)}</strong>
      </article>`
    )
    .join("");

  document.querySelectorAll("#dashboard-cards [data-jump]").forEach((card) => {
    card.addEventListener("click", () => openModule(card.dataset.jump));
  });

  document.querySelector("#nav-count-patients").textContent = state.patients.length;
  document.querySelector("#nav-count-doctors").textContent = state.doctors.length;
  document.querySelector("#nav-count-appointments").textContent = state.appointments.filter(
    (a) => a.status === "scheduled"
  ).length;
  document.querySelector("#nav-count-visits").textContent = state.visits.length;
  document.querySelector("#nav-count-prescriptions").textContent = state.prescriptions.length;
  document.querySelector("#nav-count-bills").textContent = state.bills.filter(
    (b) => b.status === "pending"
  ).length;

  const upcoming = state.appointments.filter((row) => row.status === "scheduled").slice(0, 5);
  document.querySelector("#dashboard-appointments").innerHTML =
    upcoming
      .map(
        (row) => `
      <div class="compact-item">
        <div class="mini-avatar ${avatarTone(row.patient_name)}">${escapeHtml(initials(row.patient_name))}</div>
        <div>
          <strong>${escapeHtml(row.patient_name)}</strong>
          <p>${escapeHtml(row.doctor_name)} · ${escapeHtml(row.appointment_date)} at ${escapeHtml(row.appointment_time)}</p>
        </div>
        <div class="compact-actions">
          ${row.has_visit ? '<span class="badge info">Visited</span>' : '<span class="badge">Scheduled</span>'}
        </div>
      </div>`
      )
      .join("") || '<p class="empty-state">No upcoming appointments scheduled.</p>';

  const overview = state.overview;
  if (overview) {
    const totalPaid = overview.paid_revenue || 0;
    const totalPending = overview.pending_revenue || 0;
    const breakdown = overview.payment_breakdown || [];
    const maxPay = Math.max(...breakdown.map((b) => b.total), 1);

    document.querySelector("#dashboard-pulse").innerHTML = `
      <div class="pulse-kpis">
        <div class="pulse-stat">
          <span>Collected Revenue</span>
          <strong>${money(totalPaid)}</strong>
        </div>
        <div class="pulse-stat warn">
          <span>Pending Balance (${overview.pending_bills})</span>
          <strong>${money(totalPending)}</strong>
        </div>
      </div>
      <div class="pulse-bars">
        ${
          breakdown.length
            ? breakdown
                .map(
                  (b) => `
            <div class="pulse-bar-row">
              <div class="pulse-bar-top">
                <span>${escapeHtml(b.method)} (${b.count})</span>
                <strong>${money(b.total)}</strong>
              </div>
              <div class="pulse-track">
                <div class="pulse-fill" style="width: ${Math.max(8, Math.round((b.total / maxPay) * 100))}%"></div>
              </div>
            </div>`
                )
                .join("")
            : '<p class="empty-state-sm">No paid invoices yet to chart payment channels.</p>'
        }
      </div>
      <div class="pulse-meta">
        <span>Active appointments: <strong>${overview.scheduled_appointments}</strong></span>
        <span>Prescriptions issued: <strong>${overview.prescriptions}</strong></span>
      </div>`;
  }
}

function renderPatients() {
  const query = document.querySelector("#patient-search").value.trim().toLowerCase();
  const filtered = state.patients.filter(
    (row) =>
      !query ||
      row.name.toLowerCase().includes(query) ||
      row.phone.toLowerCase().includes(query) ||
      row.email.toLowerCase().includes(query)
  );

  document.querySelector("#patient-list").innerHTML =
    filtered
      .map(
        (row) => `
      <article class="item">
        <div class="item-main">
          <div class="mini-avatar ${avatarTone(row.name)}">${escapeHtml(initials(row.name))}</div>
          <div class="item-info">
            <h3>${escapeHtml(row.name)} <span class="badge neutral">#P-${row.id}</span></h3>
            <p>${escapeHtml(row.phone)} · ${escapeHtml(row.email)}</p>
          </div>
        </div>
        <div class="item-actions">
          <button class="action-button secondary" data-edit-patient="${row.id}">${ICONS.edit}<span>Edit</span></button>
          <button class="action-button" data-book-patient="${row.id}">${ICONS.calendarPlus}<span>Book visit</span></button>
        </div>
      </article>`
      )
      .join("") || '<p class="empty-state">No matching patients found.</p>';

  document.querySelector("#patient-select").innerHTML =
    '<option value="">Select patient</option>' +
    state.patients.map((row) => `<option value="${row.id}">${escapeHtml(row.name)}</option>`).join("");

  document.querySelectorAll("[data-book-patient]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openModule("appointments");
      document.querySelector("#patient-select").value = btn.dataset.bookPatient;
      document.querySelector("#doctor-select").focus();
    });
  });

  document.querySelectorAll("[data-edit-patient]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const patient = state.patients.find((p) => p.id === Number(btn.dataset.editPatient));
      if (!patient) return;
      openModal({
        kicker: "Patient Record",
        title: `Edit ${patient.name}`,
        html: `
          <form class="modal-form" id="edit-patient-modal-form">
            <label>Full name<input name="name" value="${escapeHtml(patient.name)}" required></label>
            <label>Phone<input name="phone" value="${escapeHtml(patient.phone)}" required></label>
            <label>Email<input type="email" name="email" value="${escapeHtml(patient.email)}" required></label>
            <div class="modal-actions">
              <button type="button" class="action-button secondary" id="cancel-modal-btn">Cancel</button>
              <button type="submit" class="btn-primary">Save changes</button>
            </div>
          </form>`,
      });
      document.querySelector("#cancel-modal-btn").addEventListener("click", closeModal);
      document.querySelector("#edit-patient-modal-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          const payload = Object.fromEntries(new FormData(e.target).entries());
          await api(`/api/patients/${patient.id}`, {
            method: "PUT",
            body: JSON.stringify(payload),
          });
          closeModal();
          await refreshAll();
          toast("Patient record updated");
        } catch (err) {
          toast(err.message, true);
        }
      });
    });
  });
}

function renderDoctors() {
  const query = document.querySelector("#doctor-search").value.trim().toLowerCase();
  const filtered = state.doctors.filter(
    (row) =>
      !query ||
      row.name.toLowerCase().includes(query) ||
      row.specialty.toLowerCase().includes(query) ||
      (row.schedule || "").toLowerCase().includes(query)
  );

  document.querySelector("#doctor-list").innerHTML =
    filtered
      .map(
        (row) => `
      <article class="doctor-card">
        <div class="doctor-card-top">
          <div class="mini-avatar ${avatarTone(row.name)}">${escapeHtml(initials(row.name.replace(/^Dr\.\s*/i, "")))}</div>
          <div>
            <h3>${escapeHtml(row.name)}</h3>
            <span class="badge">${escapeHtml(row.specialty)}</span>
          </div>
        </div>
        <p>${ICONS.clock}<span>${escapeHtml(row.schedule || "Mon-Fri, 9:00 AM-5:00 PM")}</span></p>
        <div class="doctor-card-footer">
          <button class="action-button secondary" data-edit-doctor="${row.id}">${ICONS.edit}<span>Edit</span></button>
          <button class="action-button" data-book-doctor="${row.id}">${ICONS.calendarPlus}<span>Book slot</span></button>
        </div>
      </article>`
      )
      .join("") || '<p class="empty-state">No matching doctors found.</p>';

  document.querySelector("#doctor-select").innerHTML =
    '<option value="">Select doctor</option>' +
    state.doctors
      .map((row) => `<option value="${row.id}">${escapeHtml(row.name)} (${escapeHtml(row.specialty)})</option>`)
      .join("");

  document.querySelectorAll("[data-book-doctor]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openModule("appointments");
      document.querySelector("#doctor-select").value = btn.dataset.bookDoctor;
      document.querySelector("#patient-select").focus();
    });
  });

  document.querySelectorAll("[data-edit-doctor]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const doctor = state.doctors.find((d) => d.id === Number(btn.dataset.editDoctor));
      if (!doctor) return;
      openModal({
        kicker: "Doctor Roster",
        title: `Edit ${doctor.name}`,
        html: `
          <form class="modal-form" id="edit-doctor-modal-form">
            <label>Doctor name<input name="name" value="${escapeHtml(doctor.name)}" required></label>
            <label>Specialty<input name="specialty" value="${escapeHtml(doctor.specialty)}" required></label>
            <label>Schedule<input name="schedule" value="${escapeHtml(doctor.schedule || "")}" required></label>
            <div class="modal-actions">
              <button type="button" class="action-button secondary" id="cancel-modal-btn">Cancel</button>
              <button type="submit" class="btn-primary">Save changes</button>
            </div>
          </form>`,
      });
      document.querySelector("#cancel-modal-btn").addEventListener("click", closeModal);
      document.querySelector("#edit-doctor-modal-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          const payload = Object.fromEntries(new FormData(e.target).entries());
          await api(`/api/doctors/${doctor.id}`, {
            method: "PUT",
            body: JSON.stringify(payload),
          });
          closeModal();
          await refreshAll();
          toast("Doctor profile updated");
        } catch (err) {
          toast(err.message, true);
        }
      });
    });
  });
}

function renderAppointments() {
  const query = document.querySelector("#appointment-search").value.trim().toLowerCase();
  const filtered = state.appointments.filter((row) => {
    const matchesStatus = state.appointmentFilter === "all" || row.status === state.appointmentFilter;
    const matchesQuery =
      !query ||
      row.patient_name.toLowerCase().includes(query) ||
      row.doctor_name.toLowerCase().includes(query) ||
      (row.reason || "").toLowerCase().includes(query);
    return matchesStatus && matchesQuery;
  });

  document.querySelector("#appointment-list").innerHTML =
    filtered
      .map((row) => {
        const statusClass = row.status === "cancelled" ? "cancelled" : "";
        return `
        <article class="item">
          <div class="item-main">
            <div class="mini-avatar ${avatarTone(row.patient_name)}">${escapeHtml(initials(row.patient_name))}</div>
            <div class="item-info">
              <h3>
                ${escapeHtml(row.patient_name)} with ${escapeHtml(row.doctor_name)}
                <span class="badge ${statusClass}">${escapeHtml(row.status)}</span>
                ${row.has_visit ? `<span class="badge info">Visit #${row.visit_id}</span>` : ""}
              </h3>
              <p>${escapeHtml(row.appointment_date)} at ${escapeHtml(row.appointment_time)} · ${escapeHtml(row.reason || "Standard consultation")}</p>
            </div>
          </div>
          ${
            row.status === "scheduled"
              ? `<div class="item-actions">
                  ${!row.has_visit ? `<button class="action-button" data-start-visit="${row.id}">${ICONS.clipboardPlus}<span>Record visit</span></button>` : ""}
                  <button class="action-button secondary" data-reschedule="${row.id}">${ICONS.clock}<span>Reschedule</span></button>
                  <button class="action-button danger" data-cancel="${row.id}">${ICONS.xCircle}<span>Cancel</span></button>
                </div>`
              : ""
          }
        </article>`;
      })
      .join("") || '<p class="empty-state">No appointments match your filter.</p>';

  const visitEligible = state.appointments.filter(
    (row) => row.status === "scheduled" && !row.has_visit
  );
  document.querySelector("#appointment-select").innerHTML =
    '<option value="">Select appointment</option>' +
    visitEligible
      .map(
        (row) =>
          `<option value="${row.id}">${escapeHtml(row.patient_name)} · ${escapeHtml(row.doctor_name)} (${escapeHtml(row.appointment_date)} ${escapeHtml(row.appointment_time)})</option>`
      )
      .join("");

  document.querySelectorAll("[data-start-visit]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openModule("visits");
      document.querySelector("#appointment-select").value = btn.dataset.startVisit;
      document.querySelector("#visit-form input[name='diagnosis']").focus();
    });
  });

  document.querySelectorAll("[data-cancel]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const appt = state.appointments.find((a) => a.id === Number(btn.dataset.cancel));
      if (!appt) return;
      openModal({
        kicker: "Confirm Cancellation",
        title: `Cancel appointment #${appt.id}?`,
        html: `
          <div class="modal-form">
            <p style="margin:0;color:var(--muted);font-size:14px;">
              This will cancel <strong>${escapeHtml(appt.patient_name)}</strong>'s slot with
              <strong>${escapeHtml(appt.doctor_name)}</strong> on ${escapeHtml(appt.appointment_date)} at ${escapeHtml(appt.appointment_time)}.
            </p>
            <div class="modal-actions">
              <button type="button" class="action-button secondary" id="cancel-modal-btn">Keep slot</button>
              <button type="button" class="action-button danger" id="confirm-cancel-btn">Confirm cancel</button>
            </div>
          </div>`,
      });
      document.querySelector("#cancel-modal-btn").addEventListener("click", closeModal);
      document.querySelector("#confirm-cancel-btn").addEventListener("click", async () => {
        try {
          await api(`/api/appointments/${appt.id}/cancel`, { method: "POST" });
          closeModal();
          await refreshAll();
          toast("Appointment cancelled");
        } catch (err) {
          toast(err.message, true);
        }
      });
    });
  });

  document.querySelectorAll("[data-reschedule]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const appt = state.appointments.find((a) => a.id === Number(btn.dataset.reschedule));
      if (!appt) return;
      openModal({
        kicker: "Reschedule Slot",
        title: `${appt.patient_name} · ${appt.doctor_name}`,
        html: `
          <form class="modal-form" id="reschedule-modal-form">
            <label>New appointment date
              <input type="date" name="appointment_date" value="${escapeHtml(appt.appointment_date)}" required>
            </label>
            <label>New appointment time
              <input type="time" name="appointment_time" value="${escapeHtml(appt.appointment_time)}" required>
            </label>
            <div class="modal-actions">
              <button type="button" class="action-button secondary" id="cancel-modal-btn">Cancel</button>
              <button type="submit" class="btn-primary">Update schedule</button>
            </div>
          </form>`,
      });
      document.querySelector("#cancel-modal-btn").addEventListener("click", closeModal);
      document.querySelector("#reschedule-modal-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          const payload = Object.fromEntries(new FormData(e.target).entries());
          await api(`/api/appointments/${appt.id}/reschedule`, {
            method: "POST",
            body: JSON.stringify(payload),
          });
          closeModal();
          await refreshAll();
          toast("Appointment rescheduled");
        } catch (err) {
          toast(err.message, true);
        }
      });
    });
  });
}

function renderVisits() {
  const query = document.querySelector("#visit-search").value.trim().toLowerCase();
  const filtered = state.visits.filter(
    (row) =>
      !query ||
      row.patient_name.toLowerCase().includes(query) ||
      row.doctor_name.toLowerCase().includes(query) ||
      (row.diagnosis || "").toLowerCase().includes(query)
  );

  document.querySelector("#visit-list").innerHTML =
    filtered
      .map(
        (row) => `
      <article class="item">
        <div class="item-main">
          <div class="mini-avatar ${avatarTone(row.patient_name)}">${escapeHtml(initials(row.patient_name))}</div>
          <div class="item-info">
            <h3>
              ${escapeHtml(row.patient_name)} · ${escapeHtml(row.doctor_name)}
              <span class="badge neutral">Visit #${row.id}</span>
            </h3>
            <p><strong>Diagnosis:</strong> ${escapeHtml(row.diagnosis || "Not recorded")} · <strong>Plan:</strong> ${escapeHtml(row.prescription || "None")}</p>
            ${row.notes ? `<p><strong>Notes:</strong> ${escapeHtml(row.notes)}</p>` : ""}
          </div>
        </div>
        <div class="item-actions">
          <button class="action-button secondary" data-add-rx="${row.id}">${ICONS.pill}<span>Issue Rx</span></button>
          <button class="action-button" data-add-bill="${row.id}">${ICONS.receipt}<span>Create bill</span></button>
        </div>
      </article>`
      )
      .join("") || '<p class="empty-state">No clinical visits recorded yet.</p>';

  const visitOptions =
    '<option value="">Select visit</option>' +
    state.visits
      .map((row) => `<option value="${row.id}">${escapeHtml(row.patient_name)} · Visit #${row.id} (${escapeHtml(row.appointment_date || "")})</option>`)
      .join("");
  document.querySelector("#visit-select").innerHTML = visitOptions;
  document.querySelector("#prescription-visit-select").innerHTML = visitOptions;

  document.querySelectorAll("[data-add-rx]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openModule("prescriptions");
      document.querySelector("#prescription-visit-select").value = btn.dataset.addRx;
      document.querySelector("#prescription-form input[name='medicine']").focus();
    });
  });

  document.querySelectorAll("[data-add-bill]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openModule("bills");
      document.querySelector("#visit-select").value = btn.dataset.addBill;
      document.querySelector("#bill-form input[name='amount']").focus();
    });
  });
}

function renderPrescriptions() {
  const query = document.querySelector("#prescription-search").value.trim().toLowerCase();
  const filtered = state.prescriptions.filter(
    (row) =>
      !query ||
      row.medicine.toLowerCase().includes(query) ||
      (row.patient_name || "").toLowerCase().includes(query) ||
      (row.doctor_name || "").toLowerCase().includes(query)
  );

  document.querySelector("#prescription-list").innerHTML =
    filtered
      .map(
        (row) => `
      <article class="item">
        <div class="item-main">
          <div class="mini-avatar av-2">${ICONS.pill}</div>
          <div class="item-info">
            <h3>
              ${escapeHtml(row.medicine)}
              <span class="badge">${escapeHtml(row.dosage)}</span>
              <span class="badge info">${escapeHtml(row.duration)}</span>
            </h3>
            <p>${escapeHtml(row.patient_name || "Patient")} · Prescribed by ${escapeHtml(row.doctor_name || "Clinician")} · ${escapeHtml(row.instructions || "Standard usage")}</p>
          </div>
        </div>
        <div class="item-actions">
          <button class="action-button secondary" data-view-rx="${row.id}">${ICONS.fileText}<span>View Rx</span></button>
        </div>
      </article>`
      )
      .join("") || '<p class="empty-state">No prescriptions issued yet.</p>';

  document.querySelectorAll("[data-view-rx]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const rx = state.prescriptions.find((p) => p.id === Number(btn.dataset.viewRx));
      if (!rx) return;
      openModal({
        kicker: "E-Prescription",
        title: `Rx #${rx.id} · ${rx.medicine}`,
        html: `
          <div class="rx-sheet">
            <div class="rx-sheet-head">
              <div><strong>${escapeHtml(rx.patient_name || "Patient")}</strong><br><span style="color:var(--muted);font-size:12px;">Visit #${rx.visit_id} (${escapeHtml(rx.appointment_date || "Today")})</span></div>
              <div style="text-align:right;"><strong>${escapeHtml(rx.doctor_name || "Clinician")}</strong><br><span style="color:var(--muted);font-size:12px;">Medicare Clinic</span></div>
            </div>
            <div class="rx-row"><span>Medication</span><strong>${escapeHtml(rx.medicine)}</strong></div>
            <div class="rx-row"><span>Dosage</span><strong>${escapeHtml(rx.dosage)}</strong></div>
            <div class="rx-row"><span>Duration</span><strong>${escapeHtml(rx.duration)}</strong></div>
            <div class="rx-row"><span>Instructions</span><strong>${escapeHtml(rx.instructions || "As directed")}</strong></div>
          </div>
          <div class="modal-actions" style="margin-top:16px;">
            <button type="button" class="action-button secondary" id="cancel-modal-btn">Close</button>
            <button type="button" class="btn-primary" id="print-rx-btn">Print Rx</button>
          </div>`,
      });
      document.querySelector("#cancel-modal-btn").addEventListener("click", closeModal);
      document.querySelector("#print-rx-btn").addEventListener("click", () => window.print());
    });
  });
}

function renderBills() {
  const paidTotal = state.bills
    .filter((b) => b.status === "paid")
    .reduce((sum, b) => sum + Number(b.amount || 0), 0);
  const pendingTotal = state.bills
    .filter((b) => b.status === "pending")
    .reduce((sum, b) => sum + Number(b.amount || 0), 0);

  document.querySelector("#billing-summary").innerHTML = `
    <div class="billing-stat paid"><span>Collected Revenue</span><strong>${money(paidTotal)}</strong></div>
    <div class="billing-stat pending"><span>Pending Collection</span><strong>${money(pendingTotal)}</strong></div>
    <div class="billing-stat"><span>Total Invoices</span><strong>${state.bills.length}</strong></div>`;

  const query = document.querySelector("#bill-search").value.trim().toLowerCase();
  const filtered = state.bills.filter((row) => {
    const matchesStatus = state.billFilter === "all" || row.status === state.billFilter;
    const matchesQuery =
      !query ||
      row.patient_name.toLowerCase().includes(query) ||
      String(row.id).includes(query);
    return matchesStatus && matchesQuery;
  });

  document.querySelector("#bill-list").innerHTML =
    filtered
      .map((row) => {
        const isPending = row.status === "pending";
        return `
        <article class="item">
          <div class="item-main">
            <div class="mini-avatar ${isPending ? "av-3" : ""}">${ICONS.receipt}</div>
            <div class="item-info">
              <h3>
                Invoice #${row.id} · ${escapeHtml(row.patient_name)} · ${money(row.amount)}
                <span class="badge ${isPending ? "pending" : ""}">${escapeHtml(row.status)}</span>
                ${row.payment_method ? `<span class="badge info">${escapeHtml(row.payment_method)}</span>` : ""}
              </h3>
              <p>${escapeHtml(row.doctor_name || "Clinic Visit")} · Visit #${row.visit_id}${row.diagnosis ? ` · ${escapeHtml(row.diagnosis)}` : ""}</p>
            </div>
          </div>
          <div class="item-actions">
            ${isPending ? `<button class="action-button" data-pay="${row.id}">${ICONS.wallet}<span>Collect payment</span></button>` : ""}
            <button class="action-button secondary" data-receipt="${row.id}">${ICONS.fileText}<span>Receipt</span></button>
          </div>
        </article>`;
      })
      .join("") || '<p class="empty-state">No invoices match your filter.</p>';

  document.querySelectorAll("[data-pay]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const bill = state.bills.find((b) => b.id === Number(btn.dataset.pay));
      if (!bill) return;
      openModal({
        kicker: "Payment Strategy",
        title: `Pay Invoice #${bill.id} (${money(bill.amount)})`,
        html: `
          <form class="modal-form" id="pay-bill-modal-form">
            <p style="margin:0;color:var(--muted);font-size:13.5px;">Select a payment channel for <strong>${escapeHtml(bill.patient_name)}</strong>:</p>
            <div class="pay-methods">
              <label class="pay-method-option">
                <input type="radio" name="payment_method" value="cash" checked>
                <svg class="icon-stroke" viewBox="0 0 24 24"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/></svg>
                <strong>Cash</strong><span>Front desk</span>
              </label>
              <label class="pay-method-option">
                <input type="radio" name="payment_method" value="card">
                <svg class="icon-stroke" viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/></svg>
                <strong>Card</strong><span>POS / Debit</span>
              </label>
              <label class="pay-method-option">
                <input type="radio" name="payment_method" value="bkash">
                <svg class="icon-stroke" viewBox="0 0 24 24"><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/></svg>
                <strong>bKash</strong><span>Mobile wallet</span>
              </label>
            </div>
            <div class="modal-actions">
              <button type="button" class="action-button secondary" id="cancel-modal-btn">Cancel</button>
              <button type="submit" class="btn-primary">Confirm payment</button>
            </div>
          </form>`,
      });
      document.querySelector("#cancel-modal-btn").addEventListener("click", closeModal);
      document.querySelector("#pay-bill-modal-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          const method = new FormData(e.target).get("payment_method");
          await api(`/api/bills/${bill.id}/pay`, {
            method: "POST",
            body: JSON.stringify({ payment_method: method }),
          });
          closeModal();
          await refreshAll();
          toast(`Invoice #${bill.id} marked paid via ${method}`);
        } catch (err) {
          toast(err.message, true);
        }
      });
    });
  });

  document.querySelectorAll("[data-receipt]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const bill = state.bills.find((b) => b.id === Number(btn.dataset.receipt));
      if (!bill) return;
      openModal({
        kicker: "Clinic Invoice",
        title: `Invoice #${bill.id}`,
        html: `
          <div class="rx-sheet">
            <div class="rx-sheet-head">
              <div><strong>${escapeHtml(bill.patient_name)}</strong><br><span style="color:var(--muted);font-size:12px;">Visit #${bill.visit_id}</span></div>
              <div style="text-align:right;"><span class="badge ${bill.status === "pending" ? "pending" : ""}">${escapeHtml(bill.status)}</span></div>
            </div>
            <div class="rx-row"><span>Attending Clinician</span><strong>${escapeHtml(bill.doctor_name || "Medicare Staff")}</strong></div>
            <div class="rx-row"><span>Diagnosis</span><strong>${escapeHtml(bill.diagnosis || "Consultation")}</strong></div>
            <div class="rx-row"><span>Payment Channel</span><strong>${escapeHtml(bill.payment_method || "Awaiting payment")}</strong></div>
            <div class="rx-row"><span>Total Amount</span><strong>${money(bill.amount)}</strong></div>
          </div>
          <div class="modal-actions" style="margin-top:16px;">
            <button type="button" class="action-button secondary" id="cancel-modal-btn">Close</button>
            <button type="button" class="btn-primary" id="print-bill-btn">Print receipt</button>
          </div>`,
      });
      document.querySelector("#cancel-modal-btn").addEventListener("click", closeModal);
      document.querySelector("#print-bill-btn").addEventListener("click", () => window.print());
    });
  });
}

/* ---------------- DATA FETCHING & FORM BINDING ---------------- */
async function refreshAll() {
  const [patients, doctors, appointments, visits, prescriptions, bills, overview, notifications] =
    await Promise.all([
      api("/api/patients"),
      api("/api/doctors"),
      api("/api/appointments"),
      api("/api/visits"),
      api("/api/prescriptions"),
      api("/api/bills"),
      api("/api/overview"),
      api("/api/notifications"),
    ]);

  state.patients = patients;
  state.doctors = doctors;
  state.appointments = appointments;
  state.visits = visits;
  state.prescriptions = prescriptions;
  state.bills = bills;
  state.overview = overview;
  state.notifications = notifications;

  renderPatients();
  renderDoctors();
  renderAppointments();
  renderVisits();
  renderPrescriptions();
  renderBills();
  renderDashboard();
  renderNotifications();
}

function bindCreateForm(formId, endpoint, successMessage) {
  const form = document.querySelector(formId);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      await api(endpoint, { method: "POST", body: JSON.stringify(data) });
      form.reset();
      await refreshAll();
      toast(successMessage);
    } catch (error) {
      toast(error.message, true);
    }
  });
}

document.querySelector("#patient-search").addEventListener("input", renderPatients);
document.querySelector("#doctor-search").addEventListener("input", renderDoctors);
document.querySelector("#appointment-search").addEventListener("input", renderAppointments);
document.querySelector("#visit-search").addEventListener("input", renderVisits);
document.querySelector("#prescription-search").addEventListener("input", renderPrescriptions);
document.querySelector("#bill-search").addEventListener("input", renderBills);

document.querySelectorAll("#appointment-filters .filter-pill").forEach((pill) => {
  pill.addEventListener("click", () => {
    document.querySelectorAll("#appointment-filters .filter-pill").forEach((p) => p.classList.remove("active"));
    pill.classList.add("active");
    state.appointmentFilter = pill.dataset.filter;
    renderAppointments();
  });
});

document.querySelectorAll("#bill-filters .filter-pill").forEach((pill) => {
  pill.addEventListener("click", () => {
    document.querySelectorAll("#bill-filters .filter-pill").forEach((p) => p.classList.remove("active"));
    pill.classList.add("active");
    state.billFilter = pill.dataset.filter;
    renderBills();
  });
});

const dateInput = document.querySelector("#appointment-date-input");
if (dateInput && !dateInput.value) {
  dateInput.value = new Date().toISOString().split("T")[0];
}

bindCreateForm("#patient-form", "/api/patients", "Patient registered");
bindCreateForm("#doctor-form", "/api/doctors", "Doctor added to roster");
bindCreateForm("#appointment-form", "/api/appointments", "Appointment scheduled");
bindCreateForm("#visit-form", "/api/visits", "Clinical visit recorded");
bindCreateForm("#prescription-form", "/api/prescriptions", "Prescription issued");
bindCreateForm("#bill-form", "/api/bills", "Invoice created");

loadSession();
refreshAll();
