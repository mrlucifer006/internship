/**
 * SSBS Visitor & Logistics Management System
 * UI Controller, Authentication Guard & Global Component Helpers
 */

(function (window, document) {
  'use strict';

  function initApp() {
    const session = window.SSBS_DB ? window.SSBS_DB.getSession() : null;
    const isLoginPage = window.location.pathname.endsWith('login.html');

    // If unauthenticated and not on login page, authenticate as default developer or redirect
    if (!session && !isLoginPage) {
      if (window.SSBS_DB) {
        window.SSBS_DB.login('super', 'password123');
      }
    }

    renderUserHeader();
    highlightActiveNav();
    bindGlobalShortcuts();
    updateBadgeCounts();
  }

  function renderUserHeader() {
    if (!window.SSBS_DB) return;
    const user = window.SSBS_DB.getSession();
    if (!user) return;

    // Update avatar letter and names across sidebar
    const avatarEl = document.getElementById('user-avatar-initial');
    if (avatarEl) {
      avatarEl.textContent = (user.name || 'U').charAt(0).toUpperCase();
    }

    const nameEl = document.getElementById('user-display-name');
    if (nameEl) {
      nameEl.textContent = user.name || 'User';
    }

    const roleEl = document.getElementById('user-role-badge');
    if (roleEl) {
      roleEl.textContent = (user.role_name || window.SSBS_DB.getRoleName(user.auth_level)).toUpperCase();
    }

    // Role-based Admin navigation display
    const adminNavSection = document.getElementById('admin-nav-section');
    if (adminNavSection) {
      if (user.auth_level >= 4) {
        adminNavSection.classList.remove('hidden');
      } else {
        adminNavSection.classList.add('hidden');
      }
    }
  }

  function highlightActiveNav() {
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-link-item');

    navLinks.forEach(link => {
      const href = link.getAttribute('href') ? link.getAttribute('href').split('/').pop() : '';
      if (href === currentPath || (currentPath === '' && href === 'index.html')) {
        link.classList.remove('text-slate-400', 'hover:text-white', 'hover:bg-slate-800');
        link.classList.add('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-900/20');
        const icon = link.querySelector('.material-symbols-outlined');
        if (icon) icon.classList.remove('group-hover:text-indigo-400');
      }
    });
  }

  function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;

    const isClosed = sidebar.classList.contains('-translate-x-full');
    if (isClosed) {
      sidebar.classList.remove('-translate-x-full');
      sidebar.classList.add('translate-x-0');
      if (overlay) overlay.classList.remove('hidden');
    } else {
      sidebar.classList.add('-translate-x-full');
      sidebar.classList.remove('translate-x-0');
      if (overlay) overlay.classList.add('hidden');
    }
  }

  function toggleRecentSidebar() {
    const sidebar = document.getElementById('recent-sidebar');
    const overlay = document.getElementById('recent-sidebar-overlay');
    if (!sidebar) return;

    const isClosed = sidebar.classList.contains('translate-x-full');
    if (isClosed) {
      sidebar.classList.remove('translate-x-full');
      sidebar.classList.add('translate-x-0');
      if (overlay) overlay.classList.remove('hidden');
    } else {
      sidebar.classList.add('translate-x-full');
      sidebar.classList.remove('translate-x-0');
      if (overlay) overlay.classList.add('hidden');
    }
  }

  function updateBadgeCounts() {
    if (!window.SSBS_DB) return;
    const stats = window.SSBS_DB.getStats();
    const notifBadge = document.getElementById('nav-pending-notif-count');
    if (notifBadge) {
      if (stats.pendingApprovalsCount > 0) {
        notifBadge.textContent = stats.pendingApprovalsCount;
        notifBadge.classList.remove('hidden');
      } else {
        notifBadge.classList.add('hidden');
      }
    }
  }

  function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const isError = type === 'error';
    const isWarning = type === 'warning';

    const bgClass = isError ? 'bg-red-600 text-white' : (isWarning ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white');
    const iconName = isError ? 'error' : (isWarning ? 'warning' : 'check_circle');

    toast.className = `${bgClass} pointer-events-auto p-4 rounded-xl shadow-xl flex items-center gap-3 text-sm font-medium animate-fade-in transition-all duration-300`;
    toast.innerHTML = `
      <span class="material-symbols-outlined text-xl">${iconName}</span>
      <span class="flex-1">${message}</span>
      <button class="opacity-70 hover:opacity-100 transition-opacity" onclick="this.parentElement.remove()">
        <span class="material-symbols-outlined text-sm">close</span>
      </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }
  }

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  }

  function logout() {
    if (window.SSBS_DB) {
      window.SSBS_DB.clearSession();
    }
    showToast('Logged out successfully', 'info');
    setTimeout(() => {
      window.location.href = './login.html';
    }, 400);
  }

  // --- Visitor Pass Modal & Print Generator ---
  function showVisitorPassModal(visitor) {
    let modal = document.getElementById('visitor-pass-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'visitor-pass-modal';
      modal.className = 'fixed inset-0 z-50 bg-black/60 backdrop-blur-sm hidden items-center justify-center p-4';
      document.body.appendChild(modal);
    }

    const todayDate = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

    modal.innerHTML = `
      <div class="bg-white rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl border border-slate-200 animate-modal flex flex-col">
        <!-- Header -->
        <div class="bg-indigo-600 px-6 py-4 flex items-center justify-between text-white">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-2xl">badge</span>
            <h3 class="font-bold text-lg">Official Visitor Gate Pass</h3>
          </div>
          <button onclick="closeModal('visitor-pass-modal')" class="text-white/80 hover:text-white transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <!-- Printable Pass Card Area -->
        <div id="printable-gate-pass" class="p-6 bg-slate-50 border-b border-slate-200 flex flex-col gap-4 font-sans">
          <!-- Company & Badge Top -->
          <div class="flex items-center justify-between border-b pb-4 border-slate-200">
            <div>
              <span class="text-xs uppercase font-extrabold tracking-widest text-indigo-600">SSBS INDUSTRIAL PORTAL</span>
              <h2 class="text-xl font-black text-slate-800">VISITOR ENTRY PASS</h2>
              <p class="text-xs text-slate-500 font-mono">Date: ${todayDate}</p>
            </div>
            <div class="text-right">
              <span class="inline-block px-3 py-1 bg-indigo-100 text-indigo-700 font-mono font-bold text-sm rounded-lg border border-indigo-200">
                ${visitor.badge_number || 'V-2026-0000'}
              </span>
              <p class="text-[10px] text-slate-400 mt-0.5">Gate 1 - Main Terminal</p>
            </div>
          </div>

          <!-- Visitor Details Body -->
          <div class="flex gap-4 items-center">
            <img src="${visitor.photo || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80'}" 
                 class="w-24 h-24 rounded-xl object-cover border-2 border-indigo-200 shadow-sm" alt="Visitor Photo" />
            <div class="flex-1 space-y-1">
              <p class="text-xs font-bold text-slate-400 uppercase">Visitor Name</p>
              <p class="text-base font-bold text-slate-800 leading-tight">${visitor.name}</p>
              <p class="text-xs text-slate-600 font-mono">${visitor.phone}</p>
              <div class="flex items-center gap-2 mt-1">
                <span class="px-2 py-0.5 bg-slate-200 text-slate-700 text-[11px] rounded font-medium">ID: ${visitor.id_type || 'ID'}</span>
                <span class="text-xs font-mono text-slate-500">${visitor.id_number || 'Verified'}</span>
              </div>
            </div>
          </div>

          <!-- Meeting Host & Reason -->
          <div class="grid grid-cols-2 gap-3 bg-white p-3 rounded-xl border border-slate-200 text-xs">
            <div>
              <span class="text-slate-400 block font-semibold">PERSON TO VISIT</span>
              <span class="font-bold text-slate-800 text-sm">${visitor.person_to_visit || 'General Admin'}</span>
              <span class="text-slate-500 block text-[11px]">${visitor.department || 'Office Operations'}</span>
            </div>
            <div>
              <span class="text-slate-400 block font-semibold">ENTRY TIME</span>
              <span class="font-bold text-slate-800 text-sm">${visitor.entry_time}</span>
              <span class="text-slate-500 block text-[11px]">${visitor.vehicle_number ? `Veh: ${visitor.vehicle_number}` : 'Pedestrian Entry'}</span>
            </div>
          </div>

          <div class="bg-indigo-50/60 p-2.5 rounded-lg border border-indigo-100 text-xs">
            <span class="font-semibold text-indigo-900">Purpose:</span> 
            <span class="text-indigo-800">${visitor.reason || 'Official Company Business'}</span>
          </div>

          <!-- Barcode Graphic -->
          <div class="flex flex-col items-center justify-center pt-2">
            <div class="font-mono text-xs tracking-[8px] text-slate-800 font-bold">||| | |||| | ||| |||| | ||</div>
            <div class="text-[10px] text-slate-400 font-mono">${visitor.badge_number}</div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div class="p-4 bg-white flex items-center justify-end gap-3">
          <button onclick="closeModal('visitor-pass-modal')" class="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 text-sm font-medium hover:bg-slate-50">
            Close
          </button>
          <button onclick="window.print()" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold shadow-md shadow-indigo-100 flex items-center gap-2">
            <span class="material-symbols-outlined text-base">print</span>
            Print Gate Pass
          </button>
        </div>
      </div>
    `;

    openModal('visitor-pass-modal');
  }

  // --- Keyboard Shortcuts & Global listeners ---
  function bindGlobalShortcuts() {
    document.addEventListener('keydown', (e) => {
      // ESC closes any open modal
      if (e.key === 'Escape') {
        document.querySelectorAll('.fixed.inset-0.z-50').forEach(modal => {
          modal.classList.add('hidden');
          modal.classList.remove('flex');
        });
      }
    });

    // Listen for custom reactive storage update
    window.addEventListener('vms-db-updated', () => {
      updateBadgeCounts();
    });
  }

  // Expose to window
  window.toggleSidebar = toggleSidebar;
  window.toggleRecentSidebar = toggleRecentSidebar;
  window.showToast = showToast;
  window.openModal = openModal;
  window.closeModal = closeModal;
  window.logout = logout;
  window.showVisitorPassModal = showVisitorPassModal;

  document.addEventListener('DOMContentLoaded', initApp);

})(window, document);
