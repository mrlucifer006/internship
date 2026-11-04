/**
 * SSBS Visitor & Logistics Management System
 * Client-side Reactive State & Mock Storage Engine
 */

(function (window) {
  'use strict';

  const STORAGE_KEY = 'ssbs_vms_database_v2';
  const SESSION_KEY = 'ssbs_vms_session_v2';

  const DEFAULT_EMPLOYEES = [
    { id: 1, name: 'Sanjai M S (Developer)', login_id: 'super', phone: '9876543210', auth_level: 5, status: 1, department: 'R&D / Systems', role_name: 'Developer' },
    { id: 2, name: 'Rajesh Sharma', login_id: 'admin', phone: '9845123456', auth_level: 4, status: 1, department: 'Administration', role_name: 'Admin' },
    { id: 3, name: 'Vikram Singh', login_id: 'supervisor1', phone: '9811223344', auth_level: 2, status: 1, department: 'Security & Gate', role_name: 'Supervisor' },
    { id: 4, name: 'Ramesh Patel', login_id: 'foreman1', phone: '9722334455', auth_level: 1, status: 1, department: 'Warehouse & Yard', role_name: 'Foreman' },
    { id: 5, name: 'Dr. Anita Desai', login_id: 'emp1', phone: '9633445566', auth_level: 3, status: 1, department: 'Human Resources', role_name: 'Employee' },
    { id: 6, name: 'Karthik Raman', login_id: 'emp2', phone: '9544556677', auth_level: 3, status: 0, department: 'Procurement & Logistics', role_name: 'Employee' },
    { id: 7, name: 'Pooja Verma', login_id: 'emp3', phone: '9455667788', auth_level: 3, status: 1, department: 'Quality Assurance', role_name: 'Employee' },
    { id: 8, name: 'Manoj Kumar', login_id: 'emp4', phone: '9366778899', auth_level: 3, status: 0, department: 'IT Infrastructure', role_name: 'Employee' }
  ];

  const now = new Date();
  const formatTime = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
  const formatDate = (d) => d.toISOString().split('T')[0];

  const todayStr = formatDate(now);

  const DEFAULT_VISITORS = [
    {
      id: 101,
      name: 'Amitabh Joshi',
      phone: '9820011223',
      person_to_visit: 'Dr. Anita Desai',
      reason: 'Quarterly Vendor Audit & Review',
      has_vehicle: true,
      vehicle_number: 'KA-01-MJ-4521',
      entry_time: `${todayStr} 09:30 AM`,
      exit_time: null,
      status: 1, // 0: Pending, 1: Approved/Checked-in, 2: Checked-out, 3: Denied
      id_type: 'Aadhar',
      id_number: '4589 1234 9876',
      added_by: 'supervisor1',
      department: 'Human Resources',
      badge_number: 'V-2026-0101',
      photo: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'
    },
    {
      id: 102,
      name: 'Sneha Kulkarni',
      phone: '9845099887',
      person_to_visit: 'Rajesh Sharma',
      reason: 'Campus Recruitment Drive Interview',
      has_vehicle: false,
      vehicle_number: '',
      entry_time: `${todayStr} 10:15 AM`,
      exit_time: null,
      status: 1,
      id_type: 'PAN',
      id_number: 'ABCDE1234F',
      added_by: 'supervisor1',
      department: 'Administration',
      badge_number: 'V-2026-0102',
      photo: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80'
    },
    {
      id: 103,
      name: 'Mohammed Arshad',
      phone: '9731234567',
      person_to_visit: 'Karthik Raman',
      reason: 'HVAC Air Filter Maintenance & Inspection',
      has_vehicle: true,
      vehicle_number: 'KA-03-EX-9988',
      entry_time: `${todayStr} 08:45 AM`,
      exit_time: `${todayStr} 11:30 AM`,
      status: 2,
      id_type: 'Driving License',
      id_number: 'DL-KA-2019-004321',
      added_by: 'foreman1',
      department: 'Facilities',
      badge_number: 'V-2026-0099',
      photo: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80'
    },
    {
      id: 104,
      name: 'Neha Roy',
      phone: '9900112244',
      person_to_visit: 'Pooja Verma',
      reason: 'ISO 9001 Documentation Verification',
      has_vehicle: false,
      vehicle_number: '',
      entry_time: `${todayStr} 11:45 AM`,
      exit_time: null,
      status: 1,
      id_type: 'Aadhar',
      id_number: '8877 6655 4433',
      added_by: 'super',
      department: 'Quality Assurance',
      badge_number: 'V-2026-0104',
      photo: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80'
    },
    {
      id: 105,
      name: 'Gaurav Sen',
      phone: '9123456780',
      person_to_visit: 'Sanjai M S (Developer)',
      reason: 'Cloud Integration Discussion',
      has_vehicle: true,
      vehicle_number: 'TN-09-CB-1102',
      entry_time: `${todayStr} 12:20 PM`,
      exit_time: null,
      status: 0, // Pending Host approval
      id_type: 'PAN',
      id_number: 'XYZPK9876Q',
      added_by: 'supervisor1',
      department: 'R&D / Systems',
      badge_number: 'V-2026-0105',
      photo: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80'
    }
  ];

  const DEFAULT_VEHICLES = [
    {
      id: 201,
      driver_name: 'Gurpreet Singh',
      driver_phone: '9872134560',
      driver_id_type: 'Driving License',
      driver_id_number: 'DL-04-2015-8899',
      veh_reg_no: 'HR-55-AN-8910',
      vehicle_img: 'https://images.unsplash.com/photo-1586191582056-a15d2a6a8274?w=200&auto=format&fit=crop&q=80',
      origin: 'Delhi Steel Depot',
      destination: 'Raw Material Bay 3',
      purchase_no: 'PO-2026-8812',
      entry_type: 'Entry',
      tare_weight: 12450,
      gross_weight: 24800,
      material_type: 'Cold Rolled Steel Sheets',
      is_returnable: 0,
      return_reason: '',
      vehicle_length: 'Heavy 10-Wheeler',
      time: `${todayStr} 08:15 AM`,
      exit_time: null,
      status: 'Inside'
    },
    {
      id: 202,
      driver_name: 'Ramu Gowda',
      driver_phone: '9448123890',
      driver_id_type: 'Aadhar',
      driver_id_number: '7744 1122 3344',
      veh_reg_no: 'KA-04-B-3341',
      vehicle_img: 'https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=200&auto=format&fit=crop&q=80',
      origin: 'Apex Industrial Packaging',
      destination: 'Logistics Warehouse A',
      purchase_no: 'DC-99214',
      entry_type: 'Entry',
      tare_weight: 4800,
      gross_weight: 8900,
      material_type: 'Corrugated Heavy Packing Boxes',
      is_returnable: 1,
      return_reason: 'Wooden Delivery Pallets (Qty: 40)',
      vehicle_length: 'Medium Truck',
      time: `${todayStr} 09:40 AM`,
      exit_time: `${todayStr} 11:15 AM`,
      status: 'Exited'
    },
    {
      id: 203,
      driver_name: 'Satish Patil',
      driver_phone: '9822339911',
      driver_id_type: 'Driving License',
      driver_id_number: 'MH-12-2018-0912',
      veh_reg_no: 'MH-14-GH-6721',
      vehicle_img: 'https://images.unsplash.com/photo-1519003722824-194d4455a60c?w=200&auto=format&fit=crop&q=80',
      origin: 'Pune Precision Tools Ltd',
      destination: 'Assembly Line 2',
      purchase_no: 'PO-2026-9045',
      entry_type: 'Entry',
      tare_weight: 5200,
      gross_weight: 11400,
      material_type: 'Machined Components & Bearings',
      is_returnable: 0,
      return_reason: '',
      vehicle_length: 'Container Truck',
      time: `${todayStr} 11:00 AM`,
      exit_time: null,
      status: 'Inside'
    }
  ];

  const DEFAULT_WHATSAPP_QUEUE = [
    {
      id: 301,
      phone: '+919633445566',
      recipient: 'Dr. Anita Desai',
      message: '🚨 SSBS Visitor Arrival: Amitabh Joshi from Vendor Audit has arrived at Gate 1 to meet you.',
      message_type: 'visitor_arrival',
      status: 'sent',
      time: `${todayStr} 09:31 AM`
    },
    {
      id: 302,
      phone: '+919455667788',
      recipient: 'Pooja Verma',
      message: '🚨 SSBS Visitor Arrival: Neha Roy (ISO Verification) has arrived at Gate 1.',
      message_type: 'visitor_arrival',
      status: 'sent',
      time: `${todayStr} 11:46 AM`
    }
  ];

  class VMSDatabase {
    constructor() {
      this.init();
    }

    init() {
      if (!localStorage.getItem(STORAGE_KEY)) {
        this.reset();
      }
      if (!sessionStorage.getItem(SESSION_KEY) && !localStorage.getItem(SESSION_KEY)) {
        // Default login session as Super Admin / Developer
        const defaultUser = {
          name: 'Sanjai M S (Developer)',
          login_id: 'super',
          auth_level: 5,
          role_name: 'Developer'
        };
        this.setSession(defaultUser);
      }
    }

    reset() {
      const initialData = {
        employees: DEFAULT_EMPLOYEES,
        visitors: DEFAULT_VISITORS,
        vehicles: DEFAULT_VEHICLES,
        whatsapp_queue: DEFAULT_WHATSAPP_QUEUE
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(initialData));
      return initialData;
    }

    getData() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : this.reset();
      } catch (e) {
        console.error('Failed to parse localStorage data:', e);
        return this.reset();
      }
    }

    saveData(data) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      window.dispatchEvent(new CustomEvent('vms-db-updated', { detail: data }));
    }

    // --- Authentication & Session ---
    getSession() {
      const raw = sessionStorage.getItem(SESSION_KEY) || localStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    }

    setSession(user, remember = true) {
      const val = JSON.stringify(user);
      if (remember) {
        localStorage.setItem(SESSION_KEY, val);
      }
      sessionStorage.setItem(SESSION_KEY, val);
    }

    clearSession() {
      sessionStorage.removeItem(SESSION_KEY);
      localStorage.removeItem(SESSION_KEY);
    }

    login(username, password) {
      const data = this.getData();
      // Super user check
      if (username === 'super' && (password === 'password123' || password === 'admin' || password === 'super')) {
        const user = {
          name: 'Sanjai M S (Developer)',
          login_id: 'super',
          auth_level: 5,
          role_name: 'Developer'
        };
        this.setSession(user);
        return { success: true, user };
      }

      // Check DB employees
      const emp = data.employees.find(e => e.login_id.toLowerCase() === username.toLowerCase());
      if (emp && (password === 'password123' || password === '123456' || password === emp.login_id)) {
        const user = {
          name: emp.name,
          login_id: emp.login_id,
          auth_level: emp.auth_level,
          role_name: emp.role_name
        };
        // Mark employee online
        emp.status = 1;
        this.saveData(data);
        this.setSession(user);
        return { success: true, user };
      }

      return { success: false, message: 'Invalid username or password. (Hint: Try username "super" with password "password123")' };
    }

    getRoleName(level) {
      const map = {
        1: 'Foreman',
        2: 'Supervisor',
        3: 'Employee',
        4: 'Admin',
        5: 'Developer'
      };
      return map[parseInt(level)] || 'User';
    }

    // --- Employee Operations ---
    getEmployees(query = '', role = '', status = '') {
      const data = this.getData();
      return data.employees.filter(emp => {
        const matchQuery = !query || 
          emp.name.toLowerCase().includes(query.toLowerCase()) || 
          emp.login_id.toLowerCase().includes(query.toLowerCase()) || 
          (emp.phone && emp.phone.includes(query));
        const matchRole = !role || String(emp.auth_level) === String(role);
        const matchStatus = status === '' || String(emp.status) === String(status);
        return matchQuery && matchRole && matchStatus;
      });
    }

    addEmployee(empData) {
      const data = this.getData();
      if (data.employees.some(e => e.login_id.toLowerCase() === empData.login_id.toLowerCase())) {
        throw new Error(`Login ID "${empData.login_id}" already exists.`);
      }
      const newEmp = {
        id: Date.now(),
        name: empData.name,
        login_id: empData.login_id,
        phone: empData.phone,
        auth_level: parseInt(empData.auth_level) || 3,
        role_name: this.getRoleName(empData.auth_level),
        department: empData.department || 'Operations',
        status: 0,
        created_at: new Date().toISOString()
      };
      data.employees.push(newEmp);
      this.saveData(data);
      return newEmp;
    }

    deleteEmployee(loginId) {
      const data = this.getData();
      data.employees = data.employees.filter(e => e.login_id !== loginId);
      this.saveData(data);
    }

    toggleEmployeeStatus(loginId) {
      const data = this.getData();
      const emp = data.employees.find(e => e.login_id === loginId);
      if (emp) {
        emp.status = emp.status === 1 ? 0 : 1;
        this.saveData(data);
      }
      return emp;
    }

    // --- Visitor Operations ---
    getVisitors(filter = {}) {
      const data = this.getData();
      let list = [...data.visitors].reverse(); // newest first
      if (filter.search) {
        const q = filter.search.toLowerCase();
        list = list.filter(v => 
          (v.name && v.name.toLowerCase().includes(q)) ||
          (v.phone && v.phone.includes(q)) ||
          (v.badge_number && v.badge_number.toLowerCase().includes(q)) ||
          (v.person_to_visit && v.person_to_visit.toLowerCase().includes(q)) ||
          (v.vehicle_number && v.vehicle_number.toLowerCase().includes(q))
        );
      }
      if (filter.status !== undefined && filter.status !== '') {
        list = list.filter(v => String(v.status) === String(filter.status));
      }
      return list;
    }

    getActiveVisitors() {
      return this.getData().visitors.filter(v => v.status === 1);
    }

    getPendingVisitors() {
      return this.getData().visitors.filter(v => v.status === 0);
    }

    addVisitor(formData) {
      const data = this.getData();
      const id = Date.now();
      const entryTime = `${formatDate(now)} ${formatTime(now)}`;
      const badgeNumber = `V-${now.getFullYear()}-${String(data.visitors.length + 101).padStart(4, '0')}`;

      const newVisitor = {
        id,
        name: formData.name,
        phone: formData.phone,
        person_to_visit: formData.person_to_visit,
        reason: formData.reason,
        has_vehicle: !!formData.has_vehicle,
        vehicle_number: formData.vehicle_number || '',
        entry_time: entryTime,
        exit_time: null,
        status: 1, // Auto-checked in or pending based on system
        id_type: formData.id_type || 'Aadhar',
        id_number: formData.id_number || '',
        added_by: this.getSession() ? this.getSession().name : 'Security Gate',
        department: formData.department || 'General',
        badge_number: badgeNumber,
        photo: formData.photo || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80'
      };

      data.visitors.push(newVisitor);

      // Queue WhatsApp notification to host
      data.whatsapp_queue.push({
        id: Date.now() + 1,
        phone: '+919988776655',
        recipient: formData.person_to_visit,
        message: `🚨 SSBS Visitor Arrival: ${formData.name} has arrived at Main Gate to meet you. Reason: ${formData.reason}`,
        message_type: 'visitor_arrival',
        status: 'sent',
        time: entryTime
      });

      this.saveData(data);
      return newVisitor;
    }

    checkOutVisitor(id) {
      const data = this.getData();
      const visitor = data.visitors.find(v => v.id === Number(id));
      if (!visitor) throw new Error('Visitor not found');
      visitor.status = 2; // Checked out
      visitor.exit_time = `${formatDate(new Date())} ${formatTime(new Date())}`;
      this.saveData(data);
      return visitor;
    }

    updateVisitorApproval(id, status, reason = '') {
      const data = this.getData();
      const visitor = data.visitors.find(v => v.id === Number(id));
      if (!visitor) throw new Error('Visitor not found');
      visitor.status = Number(status);
      if (reason) visitor.denial_reason = reason;
      this.saveData(data);
      return visitor;
    }

    // --- Logistics Operations ---
    getVehicles(filter = {}) {
      const data = this.getData();
      let list = [...data.vehicles].reverse();
      if (filter.search) {
        const q = filter.search.toLowerCase();
        list = list.filter(v =>
          (v.driver_name && v.driver_name.toLowerCase().includes(q)) ||
          (v.veh_reg_no && v.veh_reg_no.toLowerCase().includes(q)) ||
          (v.origin && v.origin.toLowerCase().includes(q)) ||
          (v.destination && v.destination.toLowerCase().includes(q)) ||
          (v.purchase_no && v.purchase_no.toLowerCase().includes(q)) ||
          (v.material_type && v.material_type.toLowerCase().includes(q))
        );
      }
      if (filter.status) {
        list = list.filter(v => v.status.toLowerCase() === filter.status.toLowerCase());
      }
      return list;
    }

    addLogisticsEntry(formData) {
      const data = this.getData();
      const timeStr = `${formatDate(now)} ${formatTime(now)}`;
      const newVehicle = {
        id: Date.now(),
        driver_name: formData.driver_name,
        driver_phone: formData.driver_phone,
        driver_id_type: formData.id_type || 'Driving License',
        driver_id_number: formData.id_number || '',
        veh_reg_no: formData.veh_reg_no.toUpperCase(),
        vehicle_img: formData.vehicle_img || 'https://images.unsplash.com/photo-1586191582056-a15d2a6a8274?w=200&auto=format&fit=crop&q=80',
        origin: formData.origin,
        destination: formData.destination,
        purchase_no: formData.purchase_no,
        entry_type: 'Entry',
        gross_weight: parseFloat(formData.gross_weight) || 0,
        tare_weight: null,
        material_type: formData.material_type,
        is_returnable: formData.is_returnable ? 1 : 0,
        return_reason: formData.return_reason || '',
        vehicle_length: formData.vehicle_length || 'Heavy Vehicle',
        time: timeStr,
        exit_time: null,
        status: 'Inside'
      };

      data.vehicles.push(newVehicle);
      this.saveData(data);
      return newVehicle;
    }

    processLogisticsExit(id, tareWeight, challanNo = '') {
      const data = this.getData();
      const vehicle = data.vehicles.find(v => v.id === Number(id));
      if (!vehicle) throw new Error('Vehicle record not found');
      vehicle.tare_weight = parseFloat(tareWeight) || 0;
      vehicle.net_weight = Math.max(0, (vehicle.gross_weight || 0) - vehicle.tare_weight);
      vehicle.exit_challan_no = challanNo || `OUT-${Date.now().toString().slice(-6)}`;
      vehicle.exit_time = `${formatDate(new Date())} ${formatTime(new Date())}`;
      vehicle.status = 'Exited';
      this.saveData(data);
      return vehicle;
    }

    // --- Statistics ---
    getStats() {
      const data = this.getData();
      const today = formatDate(new Date());
      const visitorsToday = data.visitors.filter(v => v.entry_time && v.entry_time.startsWith(today));
      const activeVisitors = data.visitors.filter(v => v.status === 1);
      const vehiclesInside = data.vehicles.filter(v => v.status === 'Inside');
      const employeesOnline = data.employees.filter(e => e.status === 1);

      return {
        totalVisitorsToday: visitorsToday.length,
        activeVisitorsCount: activeVisitors.length,
        vehiclesInsideCount: vehiclesInside.length,
        employeesOnlineCount: employeesOnline.length,
        pendingApprovalsCount: data.visitors.filter(v => v.status === 0).length
      };
    }
  }

  // Expose singleton instance to window
  window.SSBS_DB = new VMSDatabase();

})(window);
