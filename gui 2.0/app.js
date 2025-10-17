// Smart Attendance System - Modern SPA Application

class SmartAttendanceApp {
  constructor() {
    this.currentPage = "home";
    this.navigationHistory = ["home"];
    this.theme = "dark";
    this.cameraStream = null;
    this.capturedPhoto = null;
    this.selectedStatus = null;
    this.selectedStudent = null;

    // Live data (fetched from backend)
    this.students = [];
    this.studentLookup = {};
    this.attendanceRows = [];
    
    // Training state
    this.trainingStream = null;
    this.capturedImages = [];
    this.trainingInProgress = false;
    this.isAdmin = false;
    this.adminToken = null;

    this.init();
  }

  navigateBack() {
    if (this.navigationHistory.length > 1) {
      // Remove current page from history
      this.navigationHistory.pop();

      // Get previous page
      const previousPage =
        this.navigationHistory[this.navigationHistory.length - 1];

      // Navigate without adding to history
      this.navigateToPageWithoutHistory(previousPage);
    }
  }

  navigateToPageWithoutHistory(page) {
    // Hide all pages
    document.querySelectorAll(".page").forEach((p) => {
      p.classList.remove("active");
    });

    // Show target page
    const targetPage = document.getElementById(`${page}-page`);
    if (targetPage) {
      targetPage.classList.add("active");
    }

    // Update navigation state
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.classList.remove("active");
    });

    // Update home button state
    const homeBtn = document.querySelector(".nav-home-btn");
    if (homeBtn) {
      if (page === "home") {
        homeBtn.classList.add("active");
      } else {
        homeBtn.classList.remove("active");
      }
    }

    // Update regular nav links
    const activeNavLink = document.querySelector(`[data-page="${page}"]`);
    if (activeNavLink && activeNavLink.classList.contains("nav-link")) {
      activeNavLink.classList.add("active");
    }

    this.currentPage = page;

    // Update back button state
    this.updateBackButton();

    // Page-specific initialization
    if (page === "check") {
      this.renderAttendanceTable();
      this.updateStats();
    }
  }

  updateBackButton() {
    const backBtn = document.getElementById("backBtn");
    if (backBtn) {
      // Disable back button if we're on home or if there's no history
      const canGoBack =
        this.navigationHistory.length > 1 && this.currentPage !== "home";
      backBtn.disabled = !canGoBack;

      if (canGoBack) {
        const previousPage =
          this.navigationHistory[this.navigationHistory.length - 2];
        const pageNames = {
          home: "Home",
          register: "Register",
          mark: "Mark",
          check: "Records",
        };

        const backText = pageNames[previousPage] || "Back";
        const span = backBtn.querySelector("span");
        if (span) {
          span.textContent = `Back`; // Keep it simple for consistent UI
        }
      }
    }
  }

  init() {
    this.setupTheme();
    this.setupEventListeners();
    this.setupCurrentTime();
    this.refreshData();
    this.updateBackButton();

    // Show loading animation briefly for better UX
    this.showLoading();
    setTimeout(() => {
      this.hideLoading();
    }, 1000);
  }

  get apiBase() {
    return "/web";
  }

  async apiGet(path) {
    const res = await fetch(`${this.apiBase}${path}`, {
      credentials: "same-origin",
    });
    if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
    return res.json();
  }

  async apiPost(path, body) {
    const res = await fetch(`${this.apiBase}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      let msg = "Request failed";
      try {
        const j = await res.json();
        msg = j.detail || msg;
      } catch {}
      throw new Error(msg);
    }
    return res.json();
  }

  async refreshData() {
    try {
      const [students, records, stats] = await Promise.all([
        this.apiGet("/students"),
        this.apiGet("/records"),
        this.apiGet("/stats"),
      ]);
      this.students = (students || []).map((s) => ({
        id: s.roll_no,
        name: s.name,
      }));
      this.studentLookup = {};
      this.students.forEach((s) => {
        this.studentLookup[s.id] = s;
      });
      this.attendanceRows = records && records.rows ? records.rows : [];
      this.updateHomeStats(stats);
      this.updateStudentDropdown();

      // Update hero stats on Home
      const elTotal = document.getElementById("heroTotalStudents");
      const elRate = document.getElementById("heroAttendanceRate");
      const elPresent = document.getElementById("heroPresentToday");
      if (elTotal) elTotal.textContent = String(stats?.total_students ?? 0);
      if (elRate) elRate.textContent = `${String(stats?.attendance_rate ?? 0)}%`;
      if (elPresent) elPresent.textContent = String(stats?.present_today ?? 0);
      this.renderAttendanceTable();
      this.updateStats();
    } catch (e) {
      console.error(e);
      this.showToast("Failed to load data from server", "error");
    }
  }

  updateHomeStats(stats) {
    try {
      const totalEl = document.querySelector(
        ".hero-stats .stat-card:nth-child(1) .stat-number"
      );
      const rateEl = document.querySelector(
        ".hero-stats .stat-card:nth-child(2) .stat-number"
      );
      const presentEl = document.querySelector(
        ".hero-stats .stat-card:nth-child(3) .stat-number"
      );
      if (totalEl && typeof stats?.total_students === "number")
        totalEl.textContent = String(stats.total_students);
      if (rateEl && typeof stats?.attendance_rate === "number")
        rateEl.textContent = `${stats.attendance_rate}%`;
      if (presentEl && typeof stats?.present_today === "number")
        presentEl.textContent = String(stats.present_today);
    } catch {}
  }

  setupTheme() {
    document.body.setAttribute("data-theme", this.theme);
    const themeIcon = document.querySelector("#themeToggle i");
    if (themeIcon) {
      themeIcon.className =
        this.theme === "dark" ? "fas fa-moon" : "fas fa-sun";
    }
  }

  setupEventListeners() {
    // Navigation
    document.querySelectorAll("[data-page]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const page = e.currentTarget.getAttribute("data-page");
        this.navigateToPage(page);
      });
    });

    // Back button
    const backBtn = document.getElementById("backBtn");
    if (backBtn) {
      backBtn.addEventListener("click", () => {
        this.navigateBack();
      });
    }

    // Theme toggle
    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
      themeToggle.addEventListener("click", () => {
        this.toggleTheme();
      });
    }

    // Register form
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
      registerForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleRegisterStudent();
      });
    }

    // Admin login
    const adminLoginForm = document.getElementById("adminLoginForm");
    if (adminLoginForm) {
      adminLoginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        await this.handleAdminLogin();
      });
    }
    const adminLogoutBtn = document.getElementById("adminLogoutBtn");
    if (adminLogoutBtn) {
      adminLogoutBtn.addEventListener("click", () => this.handleAdminLogout());
    }

    // Photo capture for register
    const capturePhotoBtn = document.getElementById("capturePhotoBtn");
    if (capturePhotoBtn) {
      capturePhotoBtn.addEventListener("click", () => {
        this.openCameraModal("register");
      });
    }

    // Camera controls for attendance
    const startCameraBtn = document.getElementById("startCameraBtn");
    if (startCameraBtn) {
      startCameraBtn.addEventListener("click", () => {
        this.startCamera();
      });
    }

    const captureBtn = document.getElementById("captureBtn");
    if (captureBtn) {
      captureBtn.addEventListener("click", () => {
        this.capturePhoto();
      });
    }

    const retakeBtn = document.getElementById("retakeBtn");
    if (retakeBtn) {
      retakeBtn.addEventListener("click", () => {
        this.retakePhoto();
      });
    }

    // Status selection
    document.querySelectorAll(".status-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        this.selectStatus(e.currentTarget.getAttribute("data-status"));
      });
    });

    // Mark attendance
    const markAttendanceBtn = document.getElementById("markAttendanceBtn");
    if (markAttendanceBtn) {
      markAttendanceBtn.addEventListener("click", () => {
        this.markAttendance();
      });
    }

    // Student selection
    const attendanceStudent = document.getElementById("attendanceStudent");
    if (attendanceStudent) {
      attendanceStudent.addEventListener("change", (e) => {
        this.selectedStudent = e.target.value;
        this.validateMarkAttendance();
      });
    }

    // Training controls
    const startTrainingBtn = document.getElementById("startTrainingBtn");
    if (startTrainingBtn) {
      startTrainingBtn.addEventListener("click", () => {
        this.startTraining();
      });
    }

    const manualCaptureBtn = document.getElementById("manualCaptureBtn");
    if (manualCaptureBtn) {
      manualCaptureBtn.addEventListener("click", () => {
        this.manualCapture();
      });
    }

    const stopTrainingBtn = document.getElementById("stopTrainingBtn");
    if (stopTrainingBtn) {
      stopTrainingBtn.addEventListener("click", () => {
        this.stopTraining();
      });
    }

    // Admin danger zone buttons
    const resetDatabaseBtn = document.getElementById("resetDatabaseBtn");
    if (resetDatabaseBtn) {
      resetDatabaseBtn.addEventListener("click", () => {
        this.resetDatabase();
      });
    }

    const deleteFacesBtn = document.getElementById("deleteFacesBtn");
    if (deleteFacesBtn) {
      deleteFacesBtn.addEventListener("click", () => {
        this.deleteAllFaces();
      });
    }

    const deleteAttendanceBtn = document.getElementById("deleteAttendanceBtn");
    if (deleteAttendanceBtn) {
      deleteAttendanceBtn.addEventListener("click", () => {
        this.deleteAttendanceRecords();
      });
    }

    // Search and filters
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.filterAttendanceTable(e.target.value);
      });
    }

    const classFilter = document.getElementById("classFilter");
    if (classFilter) {
      classFilter.addEventListener("change", () => {
        this.filterAttendanceTable();
      });
    }

    const statusFilter = document.getElementById("statusFilter");
    if (statusFilter) {
      statusFilter.addEventListener("change", () => {
        this.filterAttendanceTable();
      });
    }

    // Export functionality
    const exportBtn = document.getElementById("exportBtn");
    if (exportBtn) {
      exportBtn.addEventListener("click", () => {
        this.exportData();
      });
    }

    // Camera modal
    const closeCameraModal = document.getElementById("closeCameraModal");
    if (closeCameraModal) {
      closeCameraModal.addEventListener("click", () => {
        this.closeCameraModal();
      });
    }

    const modalCaptureBtn = document.getElementById("modalCaptureBtn");
    if (modalCaptureBtn) {
      modalCaptureBtn.addEventListener("click", () => {
        this.captureModalPhoto();
      });
    }

    const modalCancelBtn = document.getElementById("modalCancelBtn");
    if (modalCancelBtn) {
      modalCancelBtn.addEventListener("click", () => {
        this.closeCameraModal();
      });
    }
  }

  async handleAdminLogin() {
    const email = document.getElementById("adminEmail")?.value?.trim();
    const password = document.getElementById("adminPassword")?.value || "";
    const statusEl = document.getElementById("adminStatus");
    
    if (!email || !password) {
      this.showToast("Enter email and password", "error");
      return;
    }
    
    const success = await this.adminLogin(email, password);
    if (success && statusEl) {
      statusEl.textContent = `Logged in as ${email}`;
    }
  }

  handleAdminLogout() {
    this.adminLogout();
  }

  setupCurrentTime() {
    const updateTime = () => {
      const now = new Date();
      const timeString = now.toLocaleString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });

      const currentTimeElement = document.getElementById("currentTime");
      if (currentTimeElement) {
        currentTimeElement.innerHTML = `<i class="fas fa-clock"></i> ${timeString}`;
      }
    };

    updateTime();
    setInterval(updateTime, 1000);
  }

  navigateToPage(page) {
    // Add to navigation history if it's a new page
    if (this.currentPage !== page) {
      // Remove any forward history if we're navigating to a new page
      const currentIndex = this.navigationHistory.indexOf(this.currentPage);
      if (
        currentIndex !== -1 &&
        currentIndex < this.navigationHistory.length - 1
      ) {
        this.navigationHistory = this.navigationHistory.slice(
          0,
          currentIndex + 1
        );
      }

      // Add new page to history
      this.navigationHistory.push(page);

      // Limit history to prevent memory issues
      if (this.navigationHistory.length > 10) {
        this.navigationHistory = this.navigationHistory.slice(-10);
      }
    }

    // Hide all pages
    document.querySelectorAll(".page").forEach((p) => {
      p.classList.remove("active");
    });

    // Show target page
    const targetPage = document.getElementById(`${page}-page`);
    if (targetPage) {
      targetPage.classList.add("active");
    }

    // Update navigation state
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.classList.remove("active");
    });

    // Update home button state
    const homeBtn = document.querySelector(".nav-home-btn");
    if (homeBtn) {
      if (page === "home") {
        homeBtn.classList.add("active");
      } else {
        homeBtn.classList.remove("active");
      }
    }

    // Update regular nav links
    const activeNavLink = document.querySelector(`[data-page="${page}"]`);
    if (activeNavLink && activeNavLink.classList.contains("nav-link")) {
      activeNavLink.classList.add("active");
    }

    this.currentPage = page;

    // Update back button state
    this.updateBackButton();

    // Page-specific initialization
    if (page === "check") {
      this.renderAttendanceTable();
      this.updateStats();
    }
  }

  toggleTheme() {
    this.theme = this.theme === "dark" ? "light" : "dark";
    // Theme is stored in memory only
    this.setupTheme();
  }

  showLoading() {
    const loadingOverlay = document.getElementById("loadingOverlay");
    if (loadingOverlay) {
      loadingOverlay.classList.add("active");
    }
  }

  hideLoading() {
    const loadingOverlay = document.getElementById("loadingOverlay");
    if (loadingOverlay) {
      loadingOverlay.classList.remove("active");
    }
  }

  showToast(message, type = "success", duration = 3000) {
    const toastContainer = document.getElementById("toastContainer");
    if (!toastContainer) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icon =
      type === "success"
        ? "fa-check-circle"
        : type === "error"
        ? "fa-exclamation-circle"
        : type === "warning"
        ? "fa-exclamation-triangle"
        : "fa-info-circle";

    toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = "toastSlideOut 0.3s ease";
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }, duration);
  }

  async handleRegisterStudent() {
    const form = document.getElementById("registerForm");
    const formData = new FormData(form);

    const studentData = {
      id: formData.get("id"),
      name: formData.get("name"),
      class: formData.get("class"),
      email: formData.get("email"),
      photo: this.capturedPhoto,
    };

    // Validate required fields
    if (
      !studentData.id ||
      !studentData.name ||
      !studentData.class ||
      !studentData.email
    ) {
      this.showToast("Please fill in all required fields", "error");
      return;
    }

    try {
      await this.apiPost("/register_student", {
        id: studentData.id,
        name: studentData.name,
        email: studentData.email,
        class_name: studentData.class,
        photo_base64: studentData.photo || null,
      });
      this.showToast("Student registered successfully!", "success");
      await this.refreshData();
      form.reset();
      this.resetPhotoCapture();
      setTimeout(() => {
        this.navigateToPage("mark");
      }, 800);
    } catch (e) {
      this.showToast(e.message || "Registration failed", "error");
    }
  }

  updateStudentDropdown() {
    const dropdown = document.getElementById("attendanceStudent");
    if (!dropdown) return;

    // Clear existing options except the first empty one
    dropdown.innerHTML = '<option value=""></option>';

    // Add all students
    this.students.forEach((student) => {
      const option = document.createElement("option");
      option.value = student.id;
      option.textContent = `${student.name} (${student.id})`;
      dropdown.appendChild(option);
    });
  }

  async openCameraModal(context) {
    const modal = document.getElementById("cameraModal");
    if (!modal) return;

    modal.classList.add("active");

    try {
      this.cameraStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
      });

      const video = document.getElementById("modalCamera");
      if (video) {
        video.srcObject = this.cameraStream;
      }
    } catch (error) {
      console.error("Error accessing camera:", error);
      this.showToast(
        "Unable to access camera. Please check permissions.",
        "error"
      );
      this.closeCameraModal();
    }
  }

  captureModalPhoto() {
    const video = document.getElementById("modalCamera");
    const canvas = document.getElementById("modalCanvas");

    if (!video || !canvas) return;

    const context = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to base64
    this.capturedPhoto = canvas.toDataURL("image/jpeg", 0.8);

    // Update photo preview
    const photoPreview = document.getElementById("photoPreview");
    if (photoPreview) {
      photoPreview.innerHTML = `<img src="${this.capturedPhoto}" alt="Captured photo" />`;
    }

    // Show retake button
    const retakePhotoBtn = document.getElementById("retakePhotoBtn");
    if (retakePhotoBtn) {
      retakePhotoBtn.style.display = "inline-flex";
    }

    this.closeCameraModal();
    this.showToast("Photo captured successfully!", "success");
  }

  closeCameraModal() {
    const modal = document.getElementById("cameraModal");
    if (modal) {
      modal.classList.remove("active");
    }

    if (this.cameraStream) {
      this.cameraStream.getTracks().forEach((track) => track.stop());
      this.cameraStream = null;
    }
  }

  resetPhotoCapture() {
    this.capturedPhoto = null;

    const photoPreview = document.getElementById("photoPreview");
    if (photoPreview) {
      photoPreview.innerHTML = `
                <div class="photo-placeholder">
                    <i class="fas fa-camera"></i>
                    <p>Click to capture photo</p>
                </div>
            `;
    }

    const retakePhotoBtn = document.getElementById("retakePhotoBtn");
    if (retakePhotoBtn) {
      retakePhotoBtn.style.display = "none";
    }
  }

  async startCamera() {
    try {
      this.cameraStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
      });

      const video = document.getElementById("cameraVideo");
      const placeholder = document.querySelector(".camera-placeholder");

      if (video && placeholder) {
        video.srcObject = this.cameraStream;
        video.style.display = "block";
        placeholder.style.display = "none";

        const captureBtn = document.getElementById("captureBtn");
        if (captureBtn) {
          captureBtn.disabled = false;
        }
      }

      this.showToast("Camera started successfully!", "success");
    } catch (error) {
      console.error("Error accessing camera:", error);
      this.showToast(
        "Unable to access camera. Please check permissions.",
        "error"
      );
    }
  }

  capturePhoto() {
    const video = document.getElementById("cameraVideo");
    const canvas = document.getElementById("cameraCanvas");

    if (!video || !canvas) return;

    const context = canvas.getContext("2d");
    
    // Set canvas size to match video dimensions
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Set canvas display size to fit the container while maintaining aspect ratio
    const container = canvas.parentElement;
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;
    
    const aspectRatio = video.videoWidth / video.videoHeight;
    let displayWidth = containerWidth;
    let displayHeight = containerWidth / aspectRatio;
    
    if (displayHeight > containerHeight) {
      displayHeight = containerHeight;
      displayWidth = containerHeight * aspectRatio;
    }
    
    canvas.style.width = displayWidth + 'px';
    canvas.style.height = displayHeight + 'px';
    canvas.style.maxWidth = '100%';
    canvas.style.maxHeight = '100%';
    canvas.style.objectFit = 'contain';

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to base64
    this.capturedPhoto = canvas.toDataURL("image/jpeg", 0.8);

    // Hide video and show captured image
    video.style.display = "none";
    canvas.style.display = "block";

    // Show retake button
    const retakeBtn = document.getElementById("retakeBtn");
    if (retakeBtn) {
      retakeBtn.style.display = "inline-flex";
    }

    // Hide capture button
    const captureBtn = document.getElementById("captureBtn");
    if (captureBtn) {
      captureBtn.style.display = "none";
    }

    this.validateMarkAttendance();
    this.showToast("Photo captured successfully!", "success");
  }

  retakePhoto() {
    const video = document.getElementById("cameraVideo");
    const canvas = document.getElementById("cameraCanvas");
    const retakeBtn = document.getElementById("retakeBtn");
    const captureBtn = document.getElementById("captureBtn");

    if (video) video.style.display = "block";
    if (canvas) canvas.style.display = "none";
    if (retakeBtn) retakeBtn.style.display = "none";
    if (captureBtn) {
      captureBtn.style.display = "inline-flex";
      captureBtn.disabled = false;
    }

    this.capturedPhoto = null;
    this.validateMarkAttendance();
  }

  selectStatus(status) {
    // Remove previous selection
    document.querySelectorAll(".status-btn").forEach((btn) => {
      btn.classList.remove("selected");
    });

    // Select current status
    const selectedBtn = document.querySelector(`[data-status="${status}"]`);
    if (selectedBtn) {
      selectedBtn.classList.add("selected");
    }

    this.selectedStatus = status;
    this.validateMarkAttendance();
  }

  validateMarkAttendance() {
    const markBtn = document.getElementById("markAttendanceBtn");
    if (!markBtn) return;

    const isValid =
      this.selectedStudent && this.capturedPhoto && this.selectedStatus;
    markBtn.disabled = !isValid;
  }

  async markAttendance() {
    if (!this.selectedStudent || !this.capturedPhoto || !this.selectedStatus) {
      this.showToast(
        "Please complete all steps before marking attendance",
        "error"
      );
      return;
    }
    try {
      const res = await this.apiPost("/mark", {
        photo_base64: this.capturedPhoto,
      });
      if (res.status === "Present" || res.status === "Debounced") {
        const label = res.student_id || "Unknown";
        this.showToast(`Marked ${res.status} for ${label}`, "success");
      } else {
        this.showToast(res.status || "Uncertain", "warning");
      }
      await this.refreshData();
      this.resetAttendanceForm();
      setTimeout(() => {
        this.navigateToPage("check");
      }, 800);
    } catch (e) {
      this.showToast(e.message || "Mark failed", "error");
    }
  }

  resetAttendanceForm() {
    // Reset selections
    this.selectedStudent = null;
    this.selectedStatus = null;
    this.capturedPhoto = null;

    // Reset UI elements
    const studentSelect = document.getElementById("attendanceStudent");
    if (studentSelect) studentSelect.value = "";

    document.querySelectorAll(".status-btn").forEach((btn) => {
      btn.classList.remove("selected");
    });

    // Stop camera
    if (this.cameraStream) {
      this.cameraStream.getTracks().forEach((track) => track.stop());
      this.cameraStream = null;
    }

    // Reset camera UI
    const video = document.getElementById("cameraVideo");
    const canvas = document.getElementById("cameraCanvas");
    const placeholder = document.querySelector(".camera-placeholder");
    const captureBtn = document.getElementById("captureBtn");
    const retakeBtn = document.getElementById("retakeBtn");

    if (video) {
      video.style.display = "none";
      video.srcObject = null;
    }
    if (canvas) canvas.style.display = "none";
    if (placeholder) placeholder.style.display = "flex";
    if (captureBtn) {
      captureBtn.style.display = "inline-flex";
      captureBtn.disabled = true;
    }
    if (retakeBtn) retakeBtn.style.display = "none";

    this.validateMarkAttendance();
  }

  renderAttendanceTable() {
    const tbody = document.getElementById("attendanceTableBody");
    if (!tbody) return;

    const filtered = this.getFilteredRecords();

    tbody.innerHTML = filtered
      .map((row, idx) => {
        const sid = row.person_id || "";
        const ts = row.timestamp || "";
        const dt = ts ? new Date(ts) : null;
        const dateStr = dt ? dt.toISOString().split("T")[0] : "";
        const timeStr = dt
          ? dt.toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            })
          : "";
        const stu = this.studentLookup[sid];
        const name = stu ? stu.name : sid || "Unknown";
        const cls = "";
        const status = row.status || "Present";
        return `
                <tr>
                    <td>
                        <div style="font-weight: 500;">${name}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">${sid}</div>
                    </td>
                    <td>${cls}</td>
                    <td>${dateStr}</td>
                    <td>${timeStr}</td>
                    <td>
                        <span class="status-badge ${status.toLowerCase()}">
                            <i class="fas ${this.getStatusIcon(status)}"></i>
                            ${status}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" disabled>
                            <i class="fas fa-edit"></i>
                        </button>
                    </td>
                </tr>
            `;
      })
      .join("");
  }

  getStatusIcon(status) {
    switch (status.toLowerCase()) {
      case "present":
        return "fa-check-circle";
      case "late":
        return "fa-clock";
      case "absent":
        return "fa-times-circle";
      default:
        return "fa-question-circle";
    }
  }

  getFilteredRecords() {
    let filtered = [...this.attendanceRows];
    const searchTerm =
      document.getElementById("searchInput")?.value.toLowerCase() || "";
    const classFilter = document.getElementById("classFilter")?.value || "";
    const statusFilter = document.getElementById("statusFilter")?.value || "";
    if (searchTerm) {
      filtered = filtered.filter((record) => {
        const sid = (record.person_id || "").toLowerCase();
        const name = (
          this.studentLookup[record.person_id]?.name || ""
        ).toLowerCase();
        return sid.includes(searchTerm) || name.includes(searchTerm);
      });
    }
    if (classFilter) {
      filtered = filtered.filter(() => true);
    }
    if (statusFilter) {
      filtered = filtered.filter(
        (record) =>
          (record.status || "").toLowerCase() === statusFilter.toLowerCase()
      );
    }
    return filtered;
  }

  filterAttendanceTable(searchTerm = "") {
    this.renderAttendanceTable();
  }

  updateStats() {
    const today = new Date().toISOString().split("T")[0];
    const todayRecords = this.attendanceRows.filter((row) =>
      (row.timestamp || "").startsWith(today)
    );
    const presentCount = todayRecords.filter(
      (r) => (r.status || "").toLowerCase() === "present"
    ).length;
    const lateCount = todayRecords.filter(
      (r) => (r.status || "").toLowerCase() === "late"
    ).length;
    const absentCount = todayRecords.filter(
      (r) => (r.status || "").toLowerCase() === "absent"
    ).length;
    const presentEl = document.getElementById("presentCount");
    const lateEl = document.getElementById("lateCount");
    const absentEl = document.getElementById("absentCount");
    if (presentEl) presentEl.textContent = presentCount;
    if (lateEl) lateEl.textContent = lateCount;
    if (absentEl) absentEl.textContent = absentCount;
  }

  editRecord(recordId) {
    const record = this.attendanceRecords.find((r) => r.id === recordId);
    if (!record) return;

    this.showToast(
      `Editing record for ${record.student_name} (Feature coming soon)`,
      "info"
    );
  }

  exportData() {
    const filteredRecords = this.getFilteredRecords();
    const csvContent = this.convertToCSV(filteredRecords);

    // Simulate download
    this.showToast(
      `Exporting ${filteredRecords.length} records (Demo mode)`,
      "success"
    );

    // In a real application, you would create a downloadable file
    console.log("CSV Data:", csvContent);
  }

  convertToCSV(records) {
    const headers = [
      "Student Name",
      "Student ID",
      "Class",
      "Date",
      "Time",
      "Status",
      "Marked By",
    ];
    const rows = records.map((record) => [
      record.student_name,
      record.student_id,
      record.class,
      record.date,
      record.time,
      record.status,
      record.marked_by,
    ]);

    return [headers, ...rows]
      .map((row) => row.map((field) => `"${field}"`).join(","))
      .join("\n");
  }

  // Training functionality
  async startTraining() {
    try {
      this.trainingStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
      });

      const video = document.getElementById("trainingVideo");
      const placeholder = document.querySelector("#photoPreview .photo-placeholder");
      if (video) {
        video.srcObject = this.trainingStream;
        video.style.display = "block";
        if (placeholder) placeholder.style.display = "none";

        // Wait for video to be ready
        await new Promise((resolve) => {
          if (video.readyState >= 2) return resolve();
          const onCanPlay = () => {
            video.removeEventListener("canplay", onCanPlay);
            resolve();
          };
          video.addEventListener("canplay", onCanPlay);
        });
      }

      const startBtn = document.getElementById("startTrainingBtn");
      const manualBtn = document.getElementById("manualCaptureBtn");
      const stopBtn = document.getElementById("stopTrainingBtn");

      if (startBtn) startBtn.style.display = "none";
      if (manualBtn) manualBtn.disabled = false;
      if (stopBtn) stopBtn.style.display = "inline-flex";

      this.trainingInProgress = true;
      this.showToast("Training camera started! Click 'Manual Capture' 50 times.", "success");
    } catch (error) {
      console.error("Error starting training camera:", error);
      this.showToast("Unable to access camera. Please check permissions.", "error");
    }
  }

  async manualCapture() {
    if (!this.trainingStream || this.capturedImages.length >= 50) {
      return;
    }

    try {
      const video = document.getElementById("trainingVideo");
      if (!video || video.readyState < 2 || video.videoWidth === 0 || video.videoHeight === 0) {
        this.showToast("Camera not ready. Please wait a moment and try again.", "error");
        return;
      }
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const imageData = canvas.toDataURL("image/jpeg", 0.8);
      this.capturedImages.push(imageData);

      this.updateTrainingProgress();

      if (this.capturedImages.length >= 50) {
        await this.completeTraining();
      } else {
        this.showToast(`Captured ${this.capturedImages.length}/50 images`, "success");
      }
    } catch (error) {
      console.error("Error capturing image:", error);
      this.showToast("Error capturing image. Please try again.", "error");
    }
  }

  updateTrainingProgress() {
    const progress = (this.capturedImages.length / 50) * 100;
    const progressBar = document.getElementById("trainingProgress");
    const countDisplay = document.getElementById("capturedCount");

    if (progressBar) {
      progressBar.style.width = `${progress}%`;
    }
    if (countDisplay) {
      countDisplay.textContent = this.capturedImages.length;
    }
  }

  async completeTraining() {
    this.trainingInProgress = false;
    
    const startBtn = document.getElementById("startTrainingBtn");
    const manualBtn = document.getElementById("manualCaptureBtn");
    const stopBtn = document.getElementById("stopTrainingBtn");

    if (startBtn) startBtn.style.display = "inline-flex";
    if (manualBtn) manualBtn.disabled = true;
    if (stopBtn) stopBtn.style.display = "none";

    this.showToast("Training completed! 50 images captured.", "success");
    
    // If studentId present, send images to backend for saving/training
    try {
      const studentIdInput = document.getElementById("studentId");
      const studentId = studentIdInput ? (studentIdInput.value || "").trim() : "";
      if (studentId && this.capturedImages.length >= 50) {
        await fetch("/web/capture_50_images", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ student_id: studentId, photos_base64: this.capturedImages.slice(0, 50) }),
        });
        this.showToast("Uploaded 50 images and retrained model.", "success");
      }
    } catch (e) {
      console.error("Upload training images error:", e);
    }
    
    // Stop the camera
    if (this.trainingStream) {
      this.trainingStream.getTracks().forEach(track => track.stop());
      this.trainingStream = null;
    }

    // Hide video
    const video = document.getElementById("trainingVideo");
    const placeholder = document.querySelector("#photoPreview .photo-placeholder");
    if (video) video.style.display = "none";
    if (placeholder) placeholder.style.display = "";
  }

  stopTraining() {
    this.trainingInProgress = false;
    this.capturedImages = [];

    const startBtn = document.getElementById("startTrainingBtn");
    const manualBtn = document.getElementById("manualCaptureBtn");
    const stopBtn = document.getElementById("stopTrainingBtn");

    if (startBtn) startBtn.style.display = "inline-flex";
    if (manualBtn) manualBtn.disabled = true;
    if (stopBtn) stopBtn.style.display = "none";

    if (this.trainingStream) {
      this.trainingStream.getTracks().forEach(track => track.stop());
      this.trainingStream = null;
    }

    const video = document.getElementById("trainingVideo");
    const placeholder = document.querySelector("#photoPreview .photo-placeholder");
    if (video) video.style.display = "none";
    if (placeholder) placeholder.style.display = "";

    this.updateTrainingProgress();
    this.showToast("Training stopped.", "info");
  }

  // Admin functionality
  async adminLogin(email, password) {
    try {
      const response = await fetch("/web/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();
      if (data.ok) {
        this.isAdmin = true;
        this.adminToken = data.token;
        this.showAdminDashboard();
        this.showToast("Admin login successful!", "success");
        return true;
      } else {
        this.showToast("Invalid admin credentials", "error");
        return false;
      }
    } catch (error) {
      console.error("Admin login error:", error);
      this.showToast("Login failed. Please try again.", "error");
      return false;
    }
  }

  showAdminDashboard() {
    const loginSection = document.getElementById("adminLoginSection");
    const dashboardSection = document.getElementById("adminDashboardSection");

    if (loginSection) loginSection.style.display = "none";
    if (dashboardSection) dashboardSection.style.display = "block";
  }

  adminLogout() {
    this.isAdmin = false;
    this.adminToken = null;

    const loginSection = document.getElementById("adminLoginSection");
    const dashboardSection = document.getElementById("adminDashboardSection");

    if (loginSection) loginSection.style.display = "block";
    if (dashboardSection) dashboardSection.style.display = "none";

    this.showToast("Logged out successfully", "info");
  }

  async resetDatabase() {
    if (!confirm("Are you sure you want to reset the entire database? This action cannot be undone!")) {
      return;
    }

    try {
      const response = await fetch("/web/reset_database", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${this.adminToken}`,
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();
      if (data.ok) {
        this.showToast("Database reset successfully!", "success");
        this.loadStudents();
        this.loadAttendanceRecords();
      } else {
        this.showToast("Failed to reset database", "error");
      }
    } catch (error) {
      console.error("Reset database error:", error);
      this.showToast("Error resetting database", "error");
    }
  }

  async deleteAllFaces() {
    if (!confirm("Are you sure you want to delete all enrolled faces? This will require retraining the model.")) {
      return;
    }

    try {
      const response = await fetch("/web/delete_faces", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${this.adminToken}`,
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();
      if (data.ok) {
        this.showToast("All faces deleted successfully!", "success");
      } else {
        this.showToast("Failed to delete faces", "error");
      }
    } catch (error) {
      console.error("Delete faces error:", error);
      this.showToast("Error deleting faces", "error");
    }
  }

  async deleteAttendanceRecords() {
    if (!confirm("Are you sure you want to delete all attendance records?")) {
      return;
    }

    try {
      const response = await fetch("/web/delete_attendance", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${this.adminToken}`,
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();
      if (data.ok) {
        this.showToast("Attendance records deleted successfully!", "success");
        this.loadAttendanceRecords();
      } else {
        this.showToast("Failed to delete attendance records", "error");
      }
    } catch (error) {
      console.error("Delete attendance error:", error);
      this.showToast("Error deleting attendance records", "error");
    }
  }
}

// Initialize the application
const app = new SmartAttendanceApp();

// Add some nice hover effects and animations
document.addEventListener("DOMContentLoaded", () => {
  // Add floating animation to hero elements
  const heroElements = document.querySelectorAll(".hero-content > *");
  heroElements.forEach((el, index) => {
    el.style.animationDelay = `${index * 0.2}s`;
    el.classList.add("fade-in-up");
  });

  // Add stagger animation to navigation cards
  const navCards = document.querySelectorAll(".nav-card");
  navCards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
    card.classList.add("fade-in-up");
  });
});

// CSS animations
const style = document.createElement("style");
style.textContent = `
    @keyframes fade-in-up {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in-up {
        animation: fade-in-up 0.6s ease forwards;
    }
    
    @keyframes toastSlideOut {
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);
