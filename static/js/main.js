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
    clockEl.innerHTML = `<i class="bi bi-clock me-1"></i> ${dateStr} | ${timeStr}`;
  }
  update();
  setInterval(update, 1000);
}

// 2. Photo Capture Simulation / Upload Preview
let webStream = null;
function startCamera() {
  const box = document.getElementById("camera-box");
  const video = document.getElementById("camera-stream");
  const imgInput = document.getElementById("photo-data-input");

  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(function (stream) {
        webStream = stream;
        video.srcObject = stream;
        video.style.display = "block";
        document.getElementById("camera-placeholder").style.display = "none";
      })
      .catch(function (err) {
        alert("Camera access unavailable or denied. Using static photo upload preview.");
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
    // Generate sample avatar preview
    const sampleCanvas = document.createElement("canvas");
    sampleCanvas.width = 120;
    sampleCanvas.height = 120;
    const ctx = sampleCanvas.getContext("2d");
    ctx.fillStyle = "#0F172A";
    ctx.fillRect(0, 0, 120, 120);
    ctx.fillStyle = "#EAB308";
    ctx.font = "bold 40px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("CCL", 60, 70);
    const dataUrl = sampleCanvas.toDataURL();
    imgInput.value = dataUrl;
    if (preview) {
      preview.src = dataUrl;
      preview.style.display = "block";
    }
    alert("Visitor Photo Captured Successfully!");
  }
}

// 3. Emergency Evacuation Roll Call Fetcher
function triggerEmergencyRollCall() {
  fetch("/api/emergency-rollcall")
    .then((res) => res.json())
    .then((data) => {
      const countBadge = document.getElementById("evac-count-badge");
      const listContainer = document.getElementById("evac-list-container");

      if (countBadge) countBadge.innerText = data.count + " Persons";
      if (listContainer) {
        if (data.visitors.length === 0) {
          listContainer.innerHTML = `<div class="text-center p-4 text-muted"><i class="bi bi-shield-check fs-1 text-success"></i><p class="mt-2">No visitors currently inside CCL premises. Premises clear!</p></div>`;
        } else {
          let html = `<div class="table-responsive"><table class="table table-bordered align-middle">
            <thead class="table-dark">
              <tr>
                <th>Pass Code</th>
                <th>Visitor Name</th>
                <th>Mobile</th>
                <th>Host Employee</th>
                <th>Host Phone</th>
                <th>Gate</th>
                <th>Entry Time</th>
              </tr>
            </thead><tbody>`;

          data.visitors.forEach((v) => {
            html += `<tr>
              <td><span class="badge bg-dark">${v.pass_code}</span></td>
              <td class="fw-bold">${v.visitor_name}</td>
              <td>${v.mobile}</td>
              <td>${v.host_name} (${v.department})</td>
              <td><a href="tel:${v.host_phone}" class="btn btn-sm btn-outline-danger"><i class="bi bi-telephone-fill"></i> ${v.host_phone}</a></td>
              <td><span class="badge bg-warning text-dark">${v.gate}</span></td>
              <td><i class="bi bi-clock me-1"></i>${v.entry_time}</td>
            </tr>`;
          });
          html += `</tbody></table></div>`;
          listContainer.innerHTML = html;
        }
      }
      const evacModal = new bootstrap.Modal(document.getElementById("emergencyModal"));
      evacModal.show();
    });
}

// 4. Admin Dashboard Chart.js Initializer
function initCharts() {
  const chartCanvas = document.getElementById("visitorTrendChart");
  if (!chartCanvas) return;

  const ctx = chartCanvas.getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: {
      labels: ["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM"],
      datasets: [
        {
          label: "Hourly Visitor Gate Traffic",
          data: [5, 18, 42, 35, 20, 15, 28, 19, 10],
          borderColor: "#0F172A",
          backgroundColor: "rgba(15, 23, 42, 0.08)",
          fill: true,
          tension: 0.35,
          borderWidth: 3
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true }
      }
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
            backgroundColor: ["#0F172A", "#EAB308", "#059669", "#0284C7", "#64748B"]
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" }
        }
      }
    });
  }
}
