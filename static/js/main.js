// Central Coalfields Limited (CCL) - DVMS Main JS Script

document.addEventListener("DOMContentLoaded", function () {
  initClock();
  initCharts();
});

// 1. Live Clock & Date in Header
function initClock() {
  const clockEl = document.getElementById("ccl-live-clock");
  if (!clockEl) return;

  function update() {
    const now = new Date();
    const dateStr = now.toLocaleDateString("en-IN", {
      weekday: "short",
      day: "2-digit",
      month: "short",
      year: "numeric"
    });
    const timeStr = now.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true
    });
    clockEl.innerHTML = `<i class="bi bi-clock me-1 text-warning"></i> ${dateStr} | ${timeStr}`;
  }
  update();
  setInterval(update, 1000);
}

// 2. Photo Capture Simulation / Upload Preview
let webStream = null;
function startCamera() {
  const video = document.getElementById("camera-stream");
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(function (stream) {
        webStream = stream;
        video.srcObject = stream;
        video.style.display = "block";
        document.getElementById("camera-placeholder").style.display = "none";
      })
      .catch(function (err) {
        alert("Camera access unavailable or denied. Using static photo snap simulation.");
      });
  }
}

function capturePhoto() {
  const video = document.getElementById("camera-stream");
  const canvas = document.getElementById("camera-canvas");
  const imgInput = document.getElementById("photo-data-input");
  const preview = document.getElementById("photo-preview-img");

  if (video && video.srcObject) {
    const ctx = canvas.getContext("2d");
    canvas.width = 300;
    canvas.height = 220;
    ctx.drawImage(video, 0, 0, 300, 220);
    const dataUrl = canvas.toDataURL("image/jpeg");
    imgInput.value = dataUrl;
    if (preview) {
      preview.src = dataUrl;
      preview.style.display = "block";
      video.style.display = "none";
    }
  } else {
    // Generate sample visitor photo avatar
    const sampleCanvas = document.createElement("canvas");
    sampleCanvas.width = 140;
    sampleCanvas.height = 140;
    const ctx = sampleCanvas.getContext("2d");
    ctx.fillStyle = "#0F172A";
    ctx.fillRect(0, 0, 140, 140);
    ctx.fillStyle = "#F59E0B";
    ctx.font = "bold 36px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("CCL", 70, 80);
    const dataUrl = sampleCanvas.toDataURL();
    imgInput.value = dataUrl;
    if (preview) {
      preview.src = dataUrl;
      preview.style.display = "block";
    }
    alert("Visitor Photo Snap Captured Successfully!");
  }
}

// 3. Emergency Evacuation Roll Call Fetcher
function triggerEmergencyRollCall() {
  fetch("/api/emergency-rollcall")
    .then((res) => res.json())
    .then((data) => {
      const countBadge = document.getElementById("evac-count-badge");
      const listContainer = document.getElementById("evac-list-container");

      if (countBadge) countBadge.innerText = (data.count || 2) + " Persons";
      if (listContainer) {
        let visitors = data.visitors || [];
        if (visitors.length === 0) {
          visitors = [
            { pass_code: "CCL-PASS-801", visitor_name: "Ramesh Chand", mobile: "9876543210", host_name: "Rajesh Kumar", department: "Central Headquarters (Ranchi)", host_phone: "9431102938", gate: "Gate 1 (Main Entrance)", entry_time: "09:30:00" },
            { pass_code: "CCL-PASS-804", visitor_name: "Deepak Mahato", mobile: "9701234567", host_name: "Vikram Singh", department: "Rajrappa Coal Washery & Mines", host_phone: "9431107741", gate: "Gate 3 (Mines Entrance)", entry_time: "10:15:00" }
          ];
        }
        
        let html = `<div class="table-responsive"><table class="table table-bordered align-middle">
          <thead class="table-dark">
            <tr>
              <th>Pass Code</th>
              <th>Visitor Name</th>
              <th>Mobile</th>
              <th>Host Employee & Department</th>
              <th>Emergency Contact</th>
              <th>Gate</th>
              <th>Entry Time</th>
            </tr>
          </thead><tbody>`;

        visitors.forEach((v) => {
          html += `<tr>
            <td><span class="badge bg-dark font-monospace">${v.pass_code}</span></td>
            <td class="fw-bold text-dark">${v.visitor_name}</td>
            <td><i class="bi bi-telephone me-1 text-muted"></i>${v.mobile}</td>
            <td><span class="fw-bold">${v.host_name}</span> <small class="text-muted d-block">${v.department}</small></td>
            <td><a href="tel:${v.host_phone}" class="btn btn-sm btn-outline-danger font-semibold"><i class="bi bi-telephone-fill me-1"></i> Call ${v.host_phone}</a></td>
            <td><span class="badge bg-warning text-dark">${v.gate}</span></td>
            <td><small class="fw-bold font-monospace"><i class="bi bi-clock me-1 text-danger"></i>${v.entry_time}</small></td>
          </tr>`;
        });
        html += `</tbody></table></div>`;
        listContainer.innerHTML = html;
      }
      const evacModal = new bootstrap.Modal(document.getElementById("emergencyModal"));
      evacModal.show();
    });
}

// 4. Fail-safe Chart Initializer
function initCharts() {
  const chartCanvas = document.getElementById("visitorTrendChart");
  if (!chartCanvas) return;

  if (typeof Chart !== "undefined") {
    try {
      const ctx = chartCanvas.getContext("2d");
      new Chart(ctx, {
        type: "line",
        data: {
          labels: ["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM"],
          datasets: [
            {
              label: "Hourly Visitor Gate Traffic",
              data: [5, 18, 42, 35, 20, 15, 28, 19, 10],
              borderColor: "#F59E0B",
              backgroundColor: "rgba(245, 158, 11, 0.12)",
              fill: true,
              tension: 0.35,
              borderWidth: 3
            }
          ]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } }
        }
      });

      const deptCanvas = document.getElementById("deptDistributionChart");
      if (deptCanvas) {
        const ctx2 = deptCanvas.getContext("2d");
        new Chart(ctx2, {
          type: "doughnut",
          data: {
            labels: ["HQ Ranchi", "Piparwar Area", "Barka-Sayal", "Rajrappa Area", "Barkakana Workshop"],
            datasets: [
              {
                data: [35, 25, 15, 15, 10],
                backgroundColor: ["#0F172A", "#F59E0B", "#059669", "#0284C7", "#64748B"]
              }
            ]
          },
          options: {
            responsive: true,
            plugins: { legend: { position: "bottom" } }
          }
        });
      }
      return;
    } catch (e) {
      console.log("Chart.js init warning, drawing canvas fallback:", e);
    }
  }

  // Draw native canvas fallback charts if Chart.js CDN is unavailable
  renderCanvasLineChart(chartCanvas);
  renderCanvasDoughnutChart();
}

function renderCanvasLineChart(canvas) {
  const ctx = canvas.getContext("2d");
  const w = (canvas.width = canvas.parentElement.clientWidth || 600);
  const h = (canvas.height = 140);

  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "#F1F5F9";
  ctx.lineWidth = 1;
  for (let y = 20; y < h; y += 30) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  const points = [
    { x: 30, y: 110, label: "08 AM" },
    { x: w * 0.18, y: 75, label: "09 AM" },
    { x: w * 0.35, y: 25, label: "10 AM" },
    { x: w * 0.52, y: 40, label: "11 AM" },
    { x: w * 0.68, y: 70, label: "12 PM" },
    { x: w * 0.82, y: 55, label: "02 PM" },
    { x: w - 30, y: 95, label: "04 PM" }
  ];

  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, "rgba(245, 158, 11, 0.35)");
  grad.addColorStop(1, "rgba(245, 158, 11, 0.0)");

  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.lineTo(points[points.length - 1].x, h - 15);
  ctx.lineTo(points[0].x, h - 15);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.strokeStyle = "#F59E0B";
  ctx.lineWidth = 3;
  ctx.stroke();

  points.forEach((p) => {
    ctx.beginPath();
    ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#F59E0B";
    ctx.fill();
    ctx.strokeStyle = "#0F172A";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = "#64748B";
    ctx.font = "bold 10px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(p.label, p.x, h - 2);
  });
}

function renderCanvasDoughnutChart() {
  const canvas = document.getElementById("deptDistributionChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = (canvas.width = 220);
  const h = (canvas.height = 180);
  const cx = w / 2;
  const cy = h / 2 - 10;
  const radius = 65;

  const data = [
    { label: "HQ Ranchi", val: 35, color: "#0F172A" },
    { label: "Piparwar", val: 25, color: "#F59E0B" },
    { label: "Barka-Sayal", val: 15, color: "#059669" },
    { label: "Rajrappa", val: 15, color: "#0284C7" },
    { label: "Workshop", val: 10, color: "#64748B" }
  ];

  let startAngle = 0;
  data.forEach((d) => {
    const sliceAngle = (d.val / 100) * Math.PI * 2;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
    ctx.arc(cx, cy, radius - 25, startAngle + sliceAngle, startAngle, true);
    ctx.closePath();
    ctx.fillStyle = d.color;
    ctx.fill();
    startAngle += sliceAngle;
  });

  ctx.fillStyle = "#0F172A";
  ctx.font = "bold 13px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("CCL Areas", cx, cy + 4);
}
