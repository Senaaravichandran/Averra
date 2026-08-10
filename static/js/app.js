/* Averra client: small, dependency-free, and intentionally easy to extend. */

const state = {
  currentView: 'overview',
  students: [],
  overview: null,
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'Something went wrong.');
  return data;
}

function initials(name = '') {
  return name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase();
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' })[char]);
}

function showToast(message, type = 'success') {
  const toast = $('#toast');
  toast.querySelector('p').textContent = message;
  toast.querySelector('span').textContent = type === 'error' ? '!' : '✓';
  toast.classList.add('show');
  clearTimeout(showToast.timeout);
  showToast.timeout = setTimeout(() => toast.classList.remove('show'), 3200);
}

function setLoading(selector, message = 'Loading…') {
  const element = $(selector);
  if (element) element.innerHTML = `<div class="loading-row">${message}</div>`;
}

function navigate(viewName) {
  const view = $(`#view-${viewName}`);
  if (!view) return;
  state.currentView = viewName;
  $$('.view').forEach((item) => item.classList.toggle('active', item === view));
  $$('.nav-item[data-view]').forEach((item) => item.classList.toggle('active', item.dataset.view === viewName));
  $('#crumb-label').textContent = view.dataset.title || viewName;
  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (viewName === 'overview') loadOverview();
  if (viewName === 'attendance') loadAttendance($('#attendance-date-input').value || undefined);
  if (viewName === 'students') loadStudents();
  if (viewName === 'reports') loadReport();
}

function renderSchedule(items) {
  const container = $('#schedule-list');
  if (!items?.length) { container.innerHTML = '<div class="loading-row">No sessions scheduled today.</div>'; return; }
  container.innerHTML = items.map((item) => {
    const time = item.starts_at.split(' ')[1] || item.starts_at;
    return `<div class="schedule-item"><span class="schedule-time">${escapeHtml(time)}</span><i class="schedule-dot ${escapeHtml(item.accent)}"></i><div><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.room)}</small></div></div>`;
  }).join('');
}

function renderRecent(items) {
  const container = $('#recent-list');
  if (!items?.length) { container.innerHTML = '<div class="loading-row">No check-ins yet today.</div>'; return; }
  const variants = ['','coral','mint','blue'];
  container.innerHTML = items.map((item, index) => `<div class="activity-row"><span class="activity-avatar ${variants[index % variants.length]}">${escapeHtml(item.avatar || initials(item.name))}</span><div class="activity-copy"><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.program)}</span></div><span class="activity-time">${escapeHtml(item.check_in)}</span><span class="method-tag">${escapeHtml(item.method)}</span></div>`).join('');
}

async function loadOverview() {
  try {
    const data = await api('/api/overview');
    state.overview = data;
    $('#stat-present').textContent = data.stats.present;
    $('#stat-total').textContent = data.stats.total;
    $('#stat-rate').textContent = `${data.stats.rate}%`;
    $('#stat-late').textContent = data.stats.late;
    $('#unresolved-progress').style.width = `${data.stats.total ? Math.min(100, (data.stats.late / data.stats.total) * 100) : 0}%`;
    renderSchedule(data.schedule);
    renderRecent(data.recent);
    updateAttendanceHero(data);
  } catch (error) { showToast(error.message, 'error'); }
}

function updateAttendanceHero(data) {
  if (!data?.stats) return;
  const dateLabel = new Date(`${data.date}T12:00:00`).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' });
  const dateElement = $('#attendance-date');
  if (dateElement) dateElement.textContent = dateLabel;
  if ($('#attendance-present')) $('#attendance-present').textContent = data.stats.present;
  if ($('#attendance-rate')) $('#attendance-rate').textContent = `${data.stats.rate}%`;
  if ($('#attendance-progress')) $('#attendance-progress').style.width = `${data.stats.rate}%`;
}

function renderStudents(students) {
  const grid = $('#student-grid');
  if (!students.length) { grid.innerHTML = '<div class="loading-row">No students match that search.</div>'; return; }
  const colors = ['','coral','mint','blue'];
  grid.innerHTML = students.map((student, index) => `<article class="student-card"><div class="student-card-top"><div class="student-large-avatar ${colors[index % colors.length]}">${escapeHtml(student.avatar || initials(student.name))}</div><button class="student-menu" aria-label="Student options">•••</button></div><span class="student-status">${escapeHtml(student.status)}</span><h3>${escapeHtml(student.name)}</h3><p>${escapeHtml(student.email)}</p><div class="student-meta"><span>${escapeHtml(student.program)}</span><strong>${student.attendance_count} check-ins</strong></div></article>`).join('');
}

async function loadStudents(query = '') {
  try { state.students = await api(`/api/students${query ? `?q=${encodeURIComponent(query)}` : ''}`); renderStudents(state.students); } catch (error) { showToast(error.message, 'error'); }
}

function renderAttendance(records) {
  const table = $('#attendance-table');
  if (!records.length) { table.innerHTML = '<tr><td colspan="6" class="empty-cell">No attendance recorded for this day.</td></tr>'; return; }
  table.innerHTML = records.map((record) => `<tr><td><div class="student-cell"><span class="table-avatar">${escapeHtml(record.avatar || initials(record.name))}</span><div><strong>${escapeHtml(record.name)}</strong><small>${escapeHtml(record.roll_number)}</small></div></div></td><td>${escapeHtml(record.program)}</td><td><strong>${escapeHtml(record.check_in)}</strong></td><td><span class="method-tag">${escapeHtml(record.method)}</span></td><td><span class="confidence"><i></i>${record.confidence ? `${Math.round(record.confidence * 100)}%` : 'Manual'}</span></td><td>›</td></tr>`).join('');
}

async function loadAttendance(selectedDate) {
  const dateInput = $('#attendance-date-input');
  if (!dateInput.value) dateInput.value = selectedDate || new Date().toISOString().slice(0, 10);
  const date = dateInput.value;
  $('#attendance-date').textContent = new Date(`${date}T12:00:00`).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' });
  setLoading('#attendance-table', 'Loading attendance…');
  try { const data = await api(`/api/attendance?date=${date}`); renderAttendance(data.records); } catch (error) { showToast(error.message, 'error'); }
}

function renderReport(data) {
  const rows = data.rows || [];
  const totalPossible = rows.length * 7;
  const present = rows.reduce((sum, row) => sum + row.present_days, 0);
  const average = totalPossible ? Math.round((present / totalPossible) * 100) : 0;
  $('#report-average').textContent = `${average}%`;
  $('#report-count').textContent = `${rows.length} students`;
  $('#report-table').innerHTML = rows.length ? rows.map((row) => {
    const percent = Math.round((row.present_days / 7) * 100);
    return `<tr><td><div class="student-cell"><span class="table-avatar">${escapeHtml(initials(row.name))}</span><div><strong>${escapeHtml(row.name)}</strong><small>${escapeHtml(row.roll_number)}</small></div></div></td><td>${escapeHtml(row.program)}</td><td><strong>${row.present_days} / 7</strong></td><td><div class="consistency"><div class="progress-track"><span style="width:${percent}%"></span></div><small>${percent}%</small></div></td></tr>`;
  }).join('') : '<tr><td colspan="4" class="empty-cell">No report data in this period.</td></tr>';
}

async function loadReport() {
  const endInput = $('#report-end');
  const startInput = $('#report-start');
  const today = new Date();
  if (!endInput.value) endInput.value = today.toISOString().slice(0, 10);
  if (!startInput.value) { const start = new Date(today); start.setDate(start.getDate() - 6); startInput.value = start.toISOString().slice(0, 10); }
  try { renderReport(await api(`/api/reports?start=${startInput.value}&end=${endInput.value}`)); } catch (error) { showToast(error.message, 'error'); }
}

function openModal(mode = 'student') {
  const modal = $('.modal');
  $('#modal-backdrop').classList.add('open');
  $('#modal-backdrop').setAttribute('aria-hidden', 'false');
  modal.classList.toggle('attendance-mode', mode === 'attendance');
  if (mode === 'attendance') {
    $('#modal-title').textContent = 'Mark attendance';
    $('#modal-description').textContent = 'Choose a student to record a timestamped check-in.';
    populateAttendanceSelect();
  } else {
    $('#modal-title').textContent = 'Add a student';
    $('#modal-description').textContent = 'Create a profile that is ready for recognition and reporting.';
    $('#student-form').reset();
  }
  setTimeout(() => (mode === 'attendance' ? $('#attendance-student-select') : $('#student-form input')).focus(), 50);
}

function closeModal() {
  $('#modal-backdrop').classList.remove('open');
  $('#modal-backdrop').setAttribute('aria-hidden', 'true');
}

function populateAttendanceSelect() {
  const select = $('#attendance-student-select');
  const students = state.students.length ? state.students : [];
  select.innerHTML = '<option value="">Choose a student…</option>' + students.map((student) => `<option value="${student.id}">${escapeHtml(student.name)} · ${escapeHtml(student.student_id)}</option>`).join('');
  if (!students.length) loadStudents().then(() => populateAttendanceSelect());
}

async function submitStudent(event) {
  event.preventDefault();
  const button = $('#modal-submit');
  button.disabled = true;
  const formData = Object.fromEntries(new FormData(event.target));
  try { await api('/api/students', { method: 'POST', body: JSON.stringify(formData) }); closeModal(); showToast('Student added to your directory.'); loadStudents(); } catch (error) { showToast(error.message, 'error'); } finally { button.disabled = false; }
}

async function submitAttendance() {
  const select = $('#attendance-student-select');
  if (!select.value) { showToast('Choose a student first.', 'error'); return; }
  const button = $('#attendance-submit');
  button.disabled = true;
  try { await api('/api/attendance', { method: 'POST', body: JSON.stringify({ student_id: Number(select.value), method: 'manual' }) }); closeModal(); showToast('Attendance marked — nice and easy.'); await loadOverview(); await loadAttendance(); } catch (error) { showToast(error.message, 'error'); } finally { button.disabled = false; }
}

function bindEvents() {
  $$('[data-view]').forEach((element) => element.addEventListener('click', (event) => { event.preventDefault(); navigate(element.dataset.view); }));
  $$('[data-action="mark-attendance"]').forEach((element) => element.addEventListener('click', () => openModal('attendance')));
  $$('[data-action="add-student"]').forEach((element) => element.addEventListener('click', () => openModal('student')));
  $$('[data-action="start-camera"]').forEach((element) => element.addEventListener('click', startCamera));
  $$('[data-action="add-session"]').forEach((element) => element.addEventListener('click', () => showToast('Session creation is ready for your connected schedule.', 'success')));
  $('#student-form').addEventListener('submit', submitStudent);
  $('#attendance-submit').addEventListener('click', submitAttendance);
  $('#modal-close').addEventListener('click', closeModal); $('#modal-cancel').addEventListener('click', closeModal); $('#attendance-cancel').addEventListener('click', closeModal);
  $('#modal-backdrop').addEventListener('click', (event) => { if (event.target.id === 'modal-backdrop') closeModal(); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeModal(); });
  $('#student-search').addEventListener('input', (event) => loadStudents(event.target.value.trim()));
  $('#attendance-date-input').addEventListener('change', (event) => loadAttendance(event.target.value));
  $('#export-attendance').addEventListener('click', () => { window.location.href = `/api/reports/export?start=${$('#attendance-date-input').value}&end=${$('#attendance-date-input').value}`; });
  $('#refresh-report').addEventListener('click', loadReport);
  $('#theme-toggle').addEventListener('click', () => { document.body.classList.toggle('dark-mode'); showToast('Appearance preference updated.'); });
  $('#confidence-range').addEventListener('input', (event) => { $('#confidence-value').textContent = `${event.target.value}%`; });
}

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) { showToast('Camera access is not supported in this browser.', 'error'); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
    const video = $('#camera-video');
    video.srcObject = stream;
    video.classList.add('active');
    $('#camera-status').textContent = 'LIVE';
    $('.camera-action').innerHTML = 'Camera live <span>✓</span>';
    showToast('Camera is live. Recognition is ready for local mode.');
  } catch (error) { showToast('Camera permission was not granted.', 'error'); }
}

document.addEventListener('DOMContentLoaded', () => { bindEvents(); loadOverview(); });
