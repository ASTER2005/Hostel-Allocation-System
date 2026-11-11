/**
 * Hostel Allocation and Management System
 * Interactive Live Database Spreadsheet Component
 * Supports real-time inline cell updates, table switching, search/filter, and CSV export.
 */

class LiveSheetManager {
  constructor(config = {}) {
    this.role = config.role || 'admin';
    this.containerId = config.containerId || 'live-sheet-root';
    this.csrfToken = config.csrfToken || '';
    this.dataUrl = config.dataUrl || (this.role === 'admin' ? '/admin/api/sheet/data' : '/warden/api/sheet/data');
    this.updateUrl = config.updateUrl || (this.role === 'admin' ? '/admin/api/sheet/update' : '/warden/api/sheet/update');

    this.activeTab = config.initialTab || (this.role === 'admin' ? 'students' : 'rooms');
    this.sheetData = {};
    this.searchQuery = '';
    this.container = document.getElementById(this.containerId);

    if (this.container) {
      this.init();
    }
  }

  async init() {
    this.renderSkeleton();
    await this.fetchData();
    this.render();
  }

  renderSkeleton() {
    this.container.innerHTML = `
      <div class="sheet-container">
        <div class="sheet-toolbar">
          <span style="font-size: 13px; color: var(--text-muted);"><i class="bi bi-arrow-repeat spin"></i> Loading live database records...</span>
        </div>
      </div>
    `;
  }

  async fetchData() {
    try {
      const resp = await fetch(this.dataUrl);
      if (!resp.ok) throw new Error('Network response failed');
      this.sheetData = await resp.json();
    } catch (err) {
      console.error('Failed to load live sheet data:', err);
      this.container.innerHTML = `
        <div class="p-4 text-center text-danger">
          <i class="bi bi-exclamation-triangle fs-3"></i>
          <p class="mt-2">Error connecting to live database: ${err.message}</p>
          <button class="btn btn-sm btn-outline-custom" onclick="window.liveSheet.fetchData().then(()=>window.liveSheet.render())">Retry</button>
        </div>
      `;
    }
  }

  render() {
    const tabs = this.role === 'admin'
      ? [
          { key: 'students', label: 'Students' },
          { key: 'hostels', label: 'Hostels' },
          { key: 'rooms', label: 'Rooms' },
          { key: 'applications', label: 'Applications' },
          { key: 'allocations', label: 'Allocations' },
          { key: 'complaints', label: 'Complaints' }
        ]
      : [
          { key: 'rooms', label: 'My Hostel Rooms' },
          { key: 'allocations', label: 'Residents & Allocations' },
          { key: 'complaints', label: 'Hostel Complaints' }
        ];

    const currentRecords = this.sheetData[this.activeTab] || [];
    const filteredRecords = this.filterRecords(currentRecords);

    this.container.innerHTML = `
      <div class="sheet-container">
        <!-- Toolbar -->
        <div class="sheet-toolbar">
          <div class="sheet-tabs">
            ${tabs.map(t => `
              <button class="sheet-tab-btn ${this.activeTab === t.key ? 'active' : ''}" 
                      onclick="window.liveSheet.switchTab('${t.key}')">
                ${t.label} (${(this.sheetData[t.key] || []).length})
              </button>
            `).join('')}
          </div>

          <div class="d-flex align-items-center gap-2">
            <div class="sheet-status-indicator" id="sheet-sync-status">
              <span class="status-dot"></span>
              <span id="sync-text">Live Sync Active</span>
            </div>
            
            <input type="text" class="form-control-custom form-control-sm" style="width: 220px;" 
                   placeholder="Search in sheet..." 
                   value="${this.searchQuery}" 
                   oninput="window.liveSheet.handleSearch(this.value)">

            <button class="btn-custom btn-outline-custom btn-sm-custom" onclick="window.liveSheet.exportActiveToCSV()">
              <i class="bi bi-download"></i> Export CSV
            </button>
          </div>
        </div>

        <!-- Spreadsheet Grid -->
        <div class="sheet-table-wrapper">
          ${this.renderActiveTable(filteredRecords)}
        </div>
      </div>
    `;
  }

  filterRecords(records) {
    if (!this.searchQuery) return records;
    const q = this.searchQuery.toLowerCase();
    return records.filter(row => {
      return Object.values(row).some(val => 
        val !== null && val !== undefined && String(val).toLowerCase().includes(q)
      );
    });
  }

  switchTab(tabKey) {
    this.activeTab = tabKey;
    this.render();
  }

  handleSearch(query) {
    this.searchQuery = query;
    const records = this.sheetData[this.activeTab] || [];
    const filtered = this.filterRecords(records);
    const wrapper = this.container.querySelector('.sheet-table-wrapper');
    if (wrapper) {
      wrapper.innerHTML = this.renderActiveTable(filtered);
    }
  }

  renderActiveTable(records) {
    if (!records || records.length === 0) {
      return `<div class="p-4 text-center text-muted">No records match your search criteria.</div>`;
    }

    switch (this.activeTab) {
      case 'students':
        return this.renderStudentsTable(records);
      case 'hostels':
        return this.renderHostelsTable(records);
      case 'rooms':
        return this.renderRoomsTable(records);
      case 'applications':
        return this.renderApplicationsTable(records);
      case 'allocations':
        return this.renderAllocationsTable(records);
      case 'complaints':
        return this.renderComplaintsTable(records);
      default:
        return `<div class="p-3">Select a valid sheet tab.</div>`;
    }
  }

  // --- 1. Students Sheet ---
  renderStudentsTable(rows) {
    const isWarden = this.role === 'warden';
    return `
      <table class="sheet-table">
        <thead>
          <tr>
            <th>#ID</th>
            <th>Reg. Number</th>
            <th>Full Name</th>
            <th>College Email</th>
            <th>Phone</th>
            <th>Department</th>
            <th>Year</th>
            <th>Gender</th>
            <th>Allocated Room</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(s => `
            <tr>
              <td class="sheet-cell-readonly">${s.id}</td>
              <td>${this.cell('students', s.id, 'registration_number', s.registration_number, isWarden)}</td>
              <td>${this.cell('students', s.id, 'name', s.name, isWarden)}</td>
              <td class="sheet-cell-readonly">${s.email}</td>
              <td>${this.cell('students', s.id, 'phone', s.phone, isWarden)}</td>
              <td>${this.cell('students', s.id, 'department', s.department, isWarden)}</td>
              <td>${this.cell('students', s.id, 'academic_year', s.academic_year, isWarden, 'number')}</td>
              <td>${this.cellSelect('students', s.id, 'gender', s.gender, ['Male', 'Female', 'Other'], isWarden)}</td>
              <td class="sheet-cell-readonly">${s.active_allocation || 'None'}</td>
              <td class="sheet-cell-readonly"><span class="custom-badge badge-neutral">${s.allocation_status}</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  // --- 2. Hostels Sheet ---
  renderHostelsTable(rows) {
    return `
      <table class="sheet-table">
        <thead>
          <tr>
            <th>#ID</th>
            <th>Hostel Name</th>
            <th>Type</th>
            <th>Campus Address</th>
            <th>Rooms</th>
            <th>Total Beds</th>
            <th>Occupied</th>
            <th>Free Beds</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(h => `
            <tr>
              <td class="sheet-cell-readonly">${h.id}</td>
              <td>${this.cell('hostels', h.id, 'hostel_name', h.hostel_name)}</td>
              <td>${this.cellSelect('hostels', h.id, 'hostel_type', h.hostel_type, ['Boys', 'Girls', 'Co-ed'])}</td>
              <td>${this.cell('hostels', h.id, 'address', h.address)}</td>
              <td class="sheet-cell-readonly">${h.total_rooms}</td>
              <td class="sheet-cell-readonly">${h.total_capacity}</td>
              <td class="sheet-cell-readonly">${h.total_occupied}</td>
              <td class="sheet-cell-readonly"><span class="custom-badge badge-available">${h.free_beds}</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  // --- 3. Rooms Sheet ---
  renderRoomsTable(rows) {
    const isWarden = this.role === 'warden';
    return `
      <table class="sheet-table">
        <thead>
          <tr>
            <th>#ID</th>
            <th>Hostel</th>
            <th>Room Number</th>
            <th>Room Type</th>
            <th>Capacity</th>
            <th>Occupied</th>
            <th>Free Beds</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(r => `
            <tr>
              <td class="sheet-cell-readonly">${r.id}</td>
              <td class="sheet-cell-readonly">${r.hostel_name}</td>
              <td>${this.cell('rooms', r.id, 'room_number', r.room_number, isWarden)}</td>
              <td>${this.cellSelect('rooms', r.id, 'room_type', r.room_type, ['Single', 'Double', 'Triple', 'Dormitory'], isWarden)}</td>
              <td>${this.cell('rooms', r.id, 'capacity', r.capacity, false, 'number')}</td>
              <td class="sheet-cell-readonly">${r.occupied_count}</td>
              <td class="sheet-cell-readonly">${r.free_beds}</td>
              <td>${this.cellSelect('rooms', r.id, 'status', r.status, ['Available', 'Full', 'Maintenance'])}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  // --- 4. Applications Sheet ---
  renderApplicationsTable(rows) {
    return `
      <table class="sheet-table">
        <thead>
          <tr>
            <th>#ID</th>
            <th>Student Name</th>
            <th>Reg No</th>
            <th>Preferred Hostel</th>
            <th>Room Type</th>
            <th>Date</th>
            <th>Status</th>
            <th>Admin Remarks</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(a => `
            <tr>
              <td class="sheet-cell-readonly">${a.id}</td>
              <td class="sheet-cell-readonly">${a.student_name}</td>
              <td class="sheet-cell-readonly">${a.reg_no}</td>
              <td class="sheet-cell-readonly">${a.preferred_hostel_name}</td>
              <td class="sheet-cell-readonly">${a.preferred_room_type}</td>
              <td class="sheet-cell-readonly">${a.application_date}</td>
              <td>${this.cellSelect('applications', a.id, 'status', a.status, ['Pending', 'Approved', 'Rejected', 'Allocated', 'Cancelled'])}</td>
              <td>${this.cell('applications', a.id, 'admin_remarks', a.admin_remarks)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  // --- 5. Allocations Sheet ---
  renderAllocationsTable(rows) {
    return `
      <table class="sheet-table">
        <thead>
          <tr>
            <th>#ID</th>
            <th>Student Name</th>
            <th>Reg No</th>
            <th>Hostel</th>
            <th>Room No</th>
            <th>Allocated Date</th>
            <th>Check-in Date</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(al => `
            <tr>
              <td class="sheet-cell-readonly">${al.id}</td>
              <td class="sheet-cell-readonly">${al.student_name}</td>
              <td class="sheet-cell-readonly">${al.reg_no}</td>
              <td class="sheet-cell-readonly">${al.hostel_name}</td>
              <td class="sheet-cell-readonly">${al.room_number}</td>
              <td class="sheet-cell-readonly">${al.allocation_date}</td>
              <td class="sheet-cell-readonly">${al.check_in_date || '-'}</td>
              <td>${this.cellSelect('allocations', al.id, 'status', al.status, ['Allocated', 'Checked-In', 'Checked-Out', 'Cancelled'])}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  // --- 6. Complaints Sheet ---
  renderComplaintsTable(rows) {
    return `
      <table class="sheet-table">
        <thead>
          <tr>
            <th>#ID</th>
            <th>Student</th>
            <th>Hostel</th>
            <th>Subject</th>
            <th>Date</th>
            <th>Status</th>
            <th>Remarks</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(c => `
            <tr>
              <td class="sheet-cell-readonly">${c.id}</td>
              <td class="sheet-cell-readonly">${c.student_name}</td>
              <td class="sheet-cell-readonly">${c.hostel_name}</td>
              <td class="sheet-cell-readonly">${c.complaint_title}</td>
              <td class="sheet-cell-readonly">${c.complaint_date}</td>
              <td>${this.cellSelect('complaints', c.id, 'status', c.status, ['Open', 'In Progress', 'Resolved', 'Closed'])}</td>
              <td>${this.cell('complaints', c.id, 'warden_remarks', c.warden_remarks)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  // Cell helper: text input
  cell(table, id, field, value, readonly = false, type = 'text') {
    if (readonly) {
      return `<div class="sheet-cell-readonly">${value ?? ''}</div>`;
    }
    const safeVal = String(value ?? '').replace(/"/g, '&quot;');
    return `
      <input type="${type}" class="sheet-cell-input" value="${safeVal}" 
             data-table="${table}" data-id="${id}" data-field="${field}" 
             onchange="window.liveSheet.handleCellChange(this)"
             onkeydown="if(event.key==='Enter')this.blur()">
    `;
  }

  // Cell helper: dropdown selector
  cellSelect(table, id, field, currentVal, options, readonly = false) {
    if (readonly) {
      return `<div class="sheet-cell-readonly">${currentVal}</div>`;
    }
    return `
      <select class="sheet-cell-input" data-table="${table}" data-id="${id}" data-field="${field}" 
              onchange="window.liveSheet.handleCellChange(this)">
        ${options.map(o => `
          <option value="${o}" ${o === currentVal ? 'selected' : ''}>${o}</option>
        `).join('')}
      </select>
    `;
  }

  // Live Inline Update via Fetch API
  async handleCellChange(element) {
    const table = element.getAttribute('data-table');
    const id = element.getAttribute('data-id');
    const field = element.getAttribute('data-field');
    const value = element.value;

    const statusEl = document.getElementById('sheet-sync-status');
    const syncText = document.getElementById('sync-text');
    const dot = statusEl ? statusEl.querySelector('.status-dot') : null;

    if (dot) dot.classList.add('saving');
    if (syncText) syncText.textContent = 'Saving changes...';

    try {
      const response = await fetch(this.updateUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken
        },
        body: JSON.stringify({ table, id: parseInt(id), field, value })
      });

      const result = await response.json();
      if (result.success) {
        if (syncText) syncText.textContent = 'All changes saved live';
        if (dot) {
          dot.classList.remove('saving');
          dot.style.backgroundColor = '#3b755d';
        }
        // Update local state cache
        const row = (this.sheetData[table] || []).find(r => r.id == id);
        if (row) row[field] = value;
      } else {
        throw new Error(result.error || 'Update failed');
      }
    } catch (err) {
      console.error('Cell update failed:', err);
      if (syncText) syncText.textContent = `Error: ${err.message}`;
      if (dot) {
        dot.classList.remove('saving');
        dot.style.backgroundColor = '#B4574B';
      }
      alert(`Save error: ${err.message}`);
    }
  }

  // CSV Export for active sheet
  exportActiveToCSV() {
    const records = this.sheetData[this.activeTab] || [];
    if (records.length === 0) {
      alert('No data to export.');
      return;
    }

    const headers = Object.keys(records[0]);
    const csvRows = [
      headers.join(','),
      ...records.map(r => headers.map(h => `"${String(r[h] ?? '').replace(/"/g, '""')}"`).join(','))
    ];

    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${this.activeTab}_sheet_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// Global initialization helper
window.initLiveSheet = function(config) {
  window.liveSheet = new LiveSheetManager(config);
  return window.liveSheet;
};

