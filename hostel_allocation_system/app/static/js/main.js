/**
 * Hostel Allocation and Management System
 * Core UI interactions, toasts, modals, charts and sidebar behaviors.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Sidebar Toggle
  const toggleBtn = document.querySelector('.sidebar-toggle-btn');
  const sidebar = document.querySelector('.app-sidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (window.innerWidth < 992 && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('show');
      }
    });
  }

  // Auto-dismiss Bootstrap flash alerts after 5 seconds
  setTimeout(() => {
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
      if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
        new bootstrap.Alert(alert).close();
      }
    });
  }, 5000);
});

// Toast notification trigger
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `custom-toast ${type === 'danger' ? 'toast-danger' : type === 'success' ? 'toast-success' : ''}`;
  
  const icon = type === 'danger' ? 'bi-exclamation-circle' : type === 'success' ? 'bi-check2-circle' : 'bi-info-circle';
  toast.innerHTML = `<i class="bi ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Global Chart.js Initialization Palette & Options
window.createHostelChart = function(canvasId, type, data, customOptions = {}) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === 'undefined') return null;

  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: { family: 'Inter', size: 12 },
          color: '#777A73',
          boxWidth: 12,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: '#202725',
        titleFont: { family: 'Inter', size: 12 },
        bodyFont: { family: 'Inter', size: 12 },
        padding: 10,
        cornerRadius: 6
      }
    }
  };

  if (type === 'bar') {
    defaultOptions.scales = {
      x: {
        grid: { display: false },
        ticks: { color: '#777A73', font: { family: 'Inter', size: 11 } }
      },
      y: {
        grid: { color: '#E5E1D8' },
        ticks: { color: '#777A73', font: { family: 'Inter', size: 11 }, precision: 0 }
      }
    };
  }

  const mergedOptions = Object.assign(defaultOptions, customOptions);
  return new Chart(canvas, { type, data, options: mergedOptions });
};

