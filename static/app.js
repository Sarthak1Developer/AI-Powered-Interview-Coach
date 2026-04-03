const state = {
  username: null,
  questions: [],
  reports: [],
  posture: { status: "Not analyzed", feedback: "No posture analysis yet" },
  stream: null,
  speechRecognizer: null,
  confidenceChart: null,
  toneChart: null,
  speechTimers: {},
  rlSessionStarted: false
};

function isRlModeEnabled() {
  const el = document.getElementById("useRlMode");
  return Boolean(el && el.checked);
}

function setRlStatus(text) {
  const status = document.getElementById("rlStatus");
  if (status) status.textContent = text;
}

function resetRlSummary() {
  const summary = document.getElementById("rlSummary");
  if (summary) summary.classList.add("hidden");
  document.getElementById("rlAttempt").textContent = "-";
  document.getElementById("rlReward").textContent = "-";
  document.getElementById("rlAvgGrade").textContent = "-";
  document.getElementById("rlStrategy").textContent = "-";
  document.getElementById("rlSessionState").textContent = "No active RL session.";
}

function updateRlSummary(result) {
  const summary = document.getElementById("rlSummary");
  if (summary) summary.classList.remove("hidden");

  const attempt = result?.session_progress?.attempt;
  const totalReward = result?.session_progress?.total_reward;
  const avgGrade = result?.session_progress?.avg_grade;
  const strategy = result?.rl_strategy;

  document.getElementById("rlAttempt").textContent = attempt ?? "-";
  document.getElementById("rlReward").textContent =
    typeof totalReward === "number" ? totalReward.toFixed(2) : "-";
  document.getElementById("rlAvgGrade").textContent =
    typeof avgGrade === "number" ? avgGrade.toFixed(2) : "-";
  document.getElementById("rlStrategy").textContent = strategy || "-";
  document.getElementById("rlSessionState").textContent = result?.episode_done
    ? "Episode completed. Next submit starts a new episode."
    : `Episode running${attempt ? ` (attempt ${attempt})` : ""}.`;
}

function setupPasswordVisibility() {
  document.querySelectorAll(".password-toggle").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute("data-toggle-password");
      const input = document.getElementById(targetId);
      if (!input) return;
      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
    });
  });
}

function updatePostureUi(status, feedback) {
  const safeStatus = status || "Not analyzed";
  const safeFeedback = feedback || "No posture analysis yet";

  const statusEl = document.getElementById("postureStatus");
  const feedbackEl = document.getElementById("postureFeedback");
  if (statusEl) statusEl.textContent = `Posture: ${safeStatus}`;
  if (feedbackEl) feedbackEl.textContent = `Feedback: ${safeFeedback}`;

  const overlay = document.getElementById("postureOverlay");
  const overlayStatus = document.getElementById("postureOverlayStatus");
  const overlayFeedback = document.getElementById("postureOverlayFeedback");
  if (!overlay || !overlayStatus || !overlayFeedback) return;

  overlayStatus.textContent = `Posture: ${safeStatus}`;
  overlayFeedback.textContent = safeFeedback;

  overlay.classList.remove("posture-overlay-good", "posture-overlay-warning", "posture-overlay-neutral");
  if (safeStatus === "Good") {
    overlay.classList.add("posture-overlay-good");
  } else if (safeStatus === "Needs Improvement" || safeStatus === "Not Visible") {
    overlay.classList.add("posture-overlay-warning");
  } else {
    overlay.classList.add("posture-overlay-neutral");
  }
}

async function ensureRlSession() {
  if (!isRlModeEnabled()) return;
  if (state.rlSessionStarted) return;

  const difficulty = document.getElementById("rlDifficulty")?.value || "medium";
  await api("/api/rl/new-session", { method: "POST", body: { difficulty } });
  state.rlSessionStarted = true;
  setRlStatus(`RL session active (${difficulty})`);
}

function buildRlFeedback(result) {
  const attempt = result?.session_progress?.attempt ?? "-";
  const reward = typeof result?.reward === "number" ? result.reward.toFixed(2) : "-";
  const strategy = result?.rl_strategy || "none";
  const rlFeedback = result?.rl_feedback || "";
  return `${result.feedback}\n\nRL Strategy: ${strategy}\nRL Feedback: ${rlFeedback}\nAttempt: ${attempt}\nReward: ${reward}`;
}

function formatSecondsToClock(totalSeconds) {
  const mins = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const secs = String(totalSeconds % 60).padStart(2, "0");
  return `${mins}:${secs}`;
}

function startSpeechTimer(timerElementId) {
  if (!timerElementId) return;
  const timerEl = document.getElementById(timerElementId);
  if (!timerEl) return;

  stopSpeechTimer(timerElementId);
  const startedAt = Date.now();
  timerEl.textContent = "Recording Time: 00:00";

  state.speechTimers[timerElementId] = setInterval(() => {
    const elapsedSeconds = Math.floor((Date.now() - startedAt) / 1000);
    timerEl.textContent = `Recording Time: ${formatSecondsToClock(elapsedSeconds)}`;
  }, 1000);
}

function stopSpeechTimer(timerElementId) {
  const timerId = state.speechTimers[timerElementId];
  if (timerId) {
    clearInterval(timerId);
    delete state.speechTimers[timerElementId];
  }
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function setMessage(id, text) {
  document.getElementById(id).textContent = text || "";
}

function showToast(text, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = text;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 2800);
}

function setLoading(active, text = "Processing...") {
  const overlay = document.getElementById("loadingOverlay");
  const loadingText = document.getElementById("loadingText");
  if (!overlay || !loadingText) return;

  loadingText.textContent = text;
  overlay.classList.toggle("hidden", !active);
}

function animateCounter(elementId, targetValue, decimals = 0, durationMs = 700) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const rawCurrent = Number.parseFloat(el.textContent);
  const startValue = Number.isFinite(rawCurrent) ? rawCurrent : 0;
  const startTime = performance.now();

  const tick = (now) => {
    const progress = Math.min((now - startTime) / durationMs, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = startValue + (targetValue - startValue) * eased;
    el.textContent = value.toFixed(decimals);
    if (progress < 1) requestAnimationFrame(tick);
  };

  requestAnimationFrame(tick);
}

function initParallaxBackground() {
  const a = document.querySelector(".bg-shape-a");
  const b = document.querySelector(".bg-shape-b");
  if (!a || !b) return;

  window.addEventListener("mousemove", (event) => {
    const x = (event.clientX / window.innerWidth - 0.5) * 16;
    const y = (event.clientY / window.innerHeight - 0.5) * 16;
    a.style.transform = `translate(${x}px, ${y}px)`;
    b.style.transform = `translate(${-x}px, ${-y}px)`;
  });
}

function initCardTilt() {
  const cards = document.querySelectorAll(".about-card");
  cards.forEach((card) => {
    card.addEventListener("mousemove", (event) => {
      const rect = card.getBoundingClientRect();
      const px = (event.clientX - rect.left) / rect.width;
      const py = (event.clientY - rect.top) / rect.height;
      const rx = (0.5 - py) * 5;
      const ry = (px - 0.5) * 5;
      card.style.transform = `perspective(700px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-2px)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "translateY(0)";
    });
  });
}

function switchAuthMode(mode) {
  const loginPanel = document.getElementById("loginPanel");
  const signupPanel = document.getElementById("signupPanel");
  const loginBtn = document.getElementById("showLoginBtn");
  const signupBtn = document.getElementById("showSignupBtn");

  const showLogin = mode === "login";
  loginPanel.classList.toggle("hidden", !showLogin);
  signupPanel.classList.toggle("hidden", showLogin);
  loginBtn.classList.toggle("active", showLogin);
  signupBtn.classList.toggle("active", !showLogin);
  setMessage("authMessage", "");
}

function currentQuestion() {
  const select = document.getElementById("questionSelect");
  const custom = document.getElementById("customQuestion");
  if (select.value === "Add custom question...") {
    return custom.value.trim();
  }
  return select.value;
}

function initTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(tab.dataset.tab).classList.add("active");
      if (tab.dataset.tab === "progress") loadProgress();
      if (tab.dataset.tab === "reports") loadReports();
      if (tab.dataset.tab === "practice") {
        document.getElementById("analysisResult").textContent = "";
      }
    });
  });
}

function togglePracticeMode() {
  const mode = document.getElementById("practiceMode").value;
  document.getElementById("audioPractice").classList.toggle("hidden", mode !== "Record Audio Response");
  document.getElementById("textPractice").classList.toggle("hidden", mode !== "Text Input Response");
  document.getElementById("videoPractice").classList.toggle("hidden", mode !== "Video Practice");
}

function initSpeech(targetElementId, timerElementId) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    alert("Speech recognition is not supported in this browser.");
    return null;
  }

  const recognizer = new SR();
  recognizer.continuous = true;
  recognizer.interimResults = true;
  recognizer.lang = "en-US";

  let finalizedTranscript = "";

  recognizer.onstart = () => {
    startSpeechTimer(timerElementId);
  };

  recognizer.onresult = (event) => {
    let interimTranscript = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const chunk = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalizedTranscript += `${chunk} `;
      } else {
        interimTranscript += chunk;
      }
    }

    const textBox = document.getElementById(targetElementId);
    textBox.value = `${finalizedTranscript}${interimTranscript}`.trim();
  };

  recognizer.onend = () => {
    stopSpeechTimer(timerElementId);
  };

  recognizer.onerror = () => {
    stopSpeechTimer(timerElementId);
    showToast("Speech recognition error occurred.", "error");
  };

  return recognizer;
}

function safeStartRecognition(recognizer) {
  if (!recognizer) return;
  try {
    recognizer.start();
  } catch (_err) {
    // Ignore duplicate start calls.
  }
}

async function doLogin() {
  try {
    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;
    setLoading(true, "Logging in...");
    await api("/api/login", { method: "POST", body: { username, password } });
    setMessage("authMessage", "Logged in successfully");
    setLoading(false);
    await loginFlow();
  } catch (e) {
    setLoading(false);
    setMessage("authMessage", e.message);
    showToast(e.message, "error");
  }
}

async function doSignup() {
  try {
    const username = document.getElementById("signupUsername").value.trim();
    const password = document.getElementById("signupPassword").value;
    const confirm_password = document.getElementById("signupConfirmPassword").value;
    setLoading(true, "Creating account...");
    await api("/api/signup", { method: "POST", body: { username, password, confirm_password } });
    setLoading(false);
    setMessage("authMessage", "Account created. Please login.");
    switchAuthMode("login");
    showToast("Account created. Please login.", "success");
  } catch (e) {
    setLoading(false);
    setMessage("authMessage", e.message);
    showToast(e.message, "error");
  }
}

async function loginFlow() {
  // Always lock the app view first, then unlock only for authenticated users.
  document.getElementById("authSection").classList.remove("hidden");
  document.getElementById("appSection").classList.add("hidden");
  document.getElementById("logoutBtn").classList.add("hidden");

  const me = await api("/api/me");
  if (!me.logged_in) {
    return;
  }

  state.username = me.username;
  document.getElementById("authSection").classList.add("hidden");
  document.getElementById("appSection").classList.remove("hidden");
  document.getElementById("logoutBtn").classList.remove("hidden");
  document.getElementById("accountUsername").textContent = `Username: ${state.username}`;

  await loadMeta();
  await loadReports();
  await loadProgress();
  showToast(`Welcome, ${state.username}`);
}

async function loadMeta() {
  const meta = await api("/api/meta");
  state.questions = [...meta.questions, "Add custom question..."];

  const select = document.getElementById("questionSelect");
  select.innerHTML = "";
  state.questions.forEach((q) => {
    const option = document.createElement("option");
    option.value = q;
    option.textContent = q;
    select.appendChild(option);
  });
}

async function loadReports() {
  const data = await api("/api/reports");
  state.reports = data.reports || [];

  const reportsList = document.getElementById("reportsList");
  reportsList.innerHTML = "";
  if (!state.reports.length) {
    reportsList.textContent = "No reports yet.";
  } else {
    state.reports.forEach((r, idx) => {
      const div = document.createElement("div");
      div.className = "card";
      div.innerHTML = `<strong>Report ${idx + 1}</strong><br>${r.timestamp}<br><em>${r.question}</em><br>Confidence: ${r.analysis.confidence.confidence_score.toFixed(1)} / 10`;
      reportsList.appendChild(div);
    });
  }

  const sessions = state.reports.length;
  const avgConfidence = sessions
    ? state.reports.reduce((acc, r) => acc + r.analysis.confidence.confidence_score, 0) / sessions
    : 0;
  animateCounter("totalSessions", sessions, 0);
  animateCounter("avgConfidence", avgConfidence, 1);
  document.getElementById("userStatus").textContent = sessions ? "Active" : "New";
  document.getElementById("accountSessions").textContent = `Total Sessions: ${sessions}`;
}

async function loadProgress() {
  const data = await api("/api/progress");
  const timeline = data.timeline || [];
  const labels = timeline.map((_, idx) => `Session ${idx + 1}`);
  const confidence = timeline.map((r) => r.confidence);
  const tone = timeline.map((r) => r.tone);

  const sessions = timeline.length;
  const avgConfidence = sessions
    ? confidence.reduce((a, b) => a + b, 0) / sessions
    : 0;
  const avgTone = sessions ? tone.reduce((a, b) => a + b, 0) / sessions : 0;
  const bestConfidence = sessions ? Math.max(...confidence) : 0;

  document.getElementById("progressSessions").textContent = String(sessions);
  document.getElementById("progressAvgConfidence").textContent = avgConfidence.toFixed(1);
  document.getElementById("progressAvgTone").textContent = avgTone.toFixed(2);
  document.getElementById("progressBestConfidence").textContent = bestConfidence.toFixed(1);

  const insight = document.getElementById("progressInsight");
  if (!sessions) {
    insight.textContent = "No sessions yet. Complete a practice round to unlock charts and trend insights.";
  } else {
    const trend = confidence[sessions - 1] - confidence[0];
    if (trend > 0.3) {
      insight.textContent = `Confidence trend is improving (+${trend.toFixed(1)}). Keep up the practice momentum.`;
    } else if (trend < -0.3) {
      insight.textContent = `Confidence trend dipped (${trend.toFixed(1)}). Revisit recent feedback and practice again.`;
    } else {
      insight.textContent = "Confidence trend is stable. Try varying questions to continue improving.";
    }
  }

  if (state.confidenceChart) state.confidenceChart.destroy();
  if (state.toneChart) state.toneChart.destroy();

  state.confidenceChart = new Chart(document.getElementById("confidenceChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Confidence",
        data: confidence,
        borderColor: "#6f7dff",
        backgroundColor: "rgba(111, 125, 255, 0.2)",
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointHoverRadius: 5
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#ddd6ff" } } },
      scales: {
        x: { ticks: { color: "#b9b2df" }, grid: { color: "rgba(133, 118, 198, 0.2)" } },
        y: { min: 0, max: 10, ticks: { color: "#b9b2df" }, grid: { color: "rgba(133, 118, 198, 0.2)" } }
      }
    }
  });

  state.toneChart = new Chart(document.getElementById("toneChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Tone",
        data: tone,
        borderColor: "#ff4fd8",
        backgroundColor: "rgba(255, 79, 216, 0.18)",
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointHoverRadius: 5
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#ddd6ff" } } },
      scales: {
        x: { ticks: { color: "#b9b2df" }, grid: { color: "rgba(133, 118, 198, 0.2)" } },
        y: { min: -1, max: 1, ticks: { color: "#b9b2df" }, grid: { color: "rgba(133, 118, 198, 0.2)" } }
      }
    }
  });
}

async function submitTextPractice() {
  const question = currentQuestion();
  const answer = document.getElementById("textAnswer").value.trim();
  if (!question || !answer) {
    showToast("Question and answer are required", "error");
    return;
  }

  setLoading(true, "Analyzing text response...");
  let result;
  if (isRlModeEnabled()) {
    await ensureRlSession();
    result = await api("/api/rl/practice/text", {
      method: "POST",
      body: {
        question,
        answer,
        task_difficulty: document.getElementById("rlDifficulty")?.value || "medium",
        use_agent_feedback: true
      }
    });
    if (result.episode_done) {
      state.rlSessionStarted = false;
      setRlStatus("RL episode completed. Next submit starts a new episode.");
    } else {
      setRlStatus(`RL active: attempt ${result?.session_progress?.attempt || 1}`);
    }
    updateRlSummary(result);
  } else {
    result = await api("/api/practice/text", {
      method: "POST",
      body: { question, answer }
    });
  }
  setLoading(false);

  document.getElementById("analysisResult").textContent = isRlModeEnabled()
    ? buildRlFeedback(result)
    : result.feedback;
  showToast("Text response analyzed", "success");
  await loadReports();
  await loadProgress();
}

async function submitAudioPractice() {
  const question = currentQuestion();
  const transcription = document.getElementById("audioTranscript").value.trim();
  if (!question || !transcription) {
    showToast("Question and transcription are required", "error");
    return;
  }

  setLoading(true, "Analyzing audio response...");
  let result;
  if (isRlModeEnabled()) {
    await ensureRlSession();
    result = await api("/api/rl/practice/text", {
      method: "POST",
      body: {
        question,
        answer: transcription,
        task_difficulty: document.getElementById("rlDifficulty")?.value || "medium",
        use_agent_feedback: true
      }
    });
    if (result.episode_done) {
      state.rlSessionStarted = false;
      setRlStatus("RL episode completed. Next submit starts a new episode.");
    } else {
      setRlStatus(`RL active: attempt ${result?.session_progress?.attempt || 1}`);
    }
    updateRlSummary(result);
  } else {
    result = await api("/api/practice/audio", {
      method: "POST",
      body: { question, transcription }
    });
  }
  setLoading(false);

  document.getElementById("analysisResult").textContent = isRlModeEnabled()
    ? buildRlFeedback(result)
    : result.feedback;
  showToast("Audio response analyzed", "success");
  await loadReports();
  await loadProgress();
}

function frameFromVideo(video) {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.8);
}

async function startCamera() {
  state.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  const video = document.getElementById("videoPreview");
  video.srcObject = state.stream;
  updatePostureUi(state.posture.status, state.posture.feedback);
  showToast("Camera started", "success");

  const loop = async () => {
    if (!state.stream) return;
    try {
      const image = frameFromVideo(video);
      const result = await api("/api/posture/frame", {
        method: "POST",
        body: { image }
      });
      state.posture = { status: result.status, feedback: result.feedback };
      updatePostureUi(result.status, result.feedback);
    } catch (_e) {
      // Ignore transient frame errors.
    }
    setTimeout(loop, 2000);
  };

  loop();
}

function stopCamera() {
  if (!state.stream) return;
  state.stream.getTracks().forEach((t) => t.stop());
  state.stream = null;
  const video = document.getElementById("videoPreview");
  video.srcObject = null;
  state.posture = { status: "Not analyzed", feedback: "No posture analysis yet" };
  updatePostureUi(state.posture.status, state.posture.feedback);
  showToast("Camera stopped");
}

async function submitVideoPractice() {
  const question = currentQuestion();
  const transcription = document.getElementById("videoTranscript").value.trim();
  if (!question || !transcription) {
    showToast("Question and transcription are required", "error");
    return;
  }

  setLoading(true, "Submitting video practice...");
  let result;
  if (isRlModeEnabled()) {
    await ensureRlSession();
    result = await api("/api/rl/practice/text", {
      method: "POST",
      body: {
        question,
        answer: transcription,
        task_difficulty: document.getElementById("rlDifficulty")?.value || "medium",
        use_agent_feedback: true
      }
    });
    if (result.episode_done) {
      state.rlSessionStarted = false;
      setRlStatus("RL episode completed. Next submit starts a new episode.");
    } else {
      setRlStatus(`RL active: attempt ${result?.session_progress?.attempt || 1}`);
    }
    updateRlSummary(result);
  } else {
    result = await api("/api/practice/video", {
      method: "POST",
      body: {
        question,
        transcription,
        posture: state.posture
      }
    });
  }
  setLoading(false);

  document.getElementById("analysisResult").textContent = isRlModeEnabled()
    ? buildRlFeedback(result)
    : result.feedback;
  showToast("Video practice submitted", "success");
  await loadReports();
  await loadProgress();
}

async function generateMockInterview() {
  setMessage("mockMessage", "Generating mock interview video. This can take 1-2 minutes...");
  setLoading(true, "Generating mock interview video...");

  try {
    const result = await api("/api/mock-interview", {
      method: "POST",
      body: {
        role: document.getElementById("mockRole").value.trim(),
        experience: document.getElementById("mockExperience").value,
        interview_type: document.getElementById("mockType").value,
        additional_details: document.getElementById("mockDetails").value.trim()
      }
    });

    document.getElementById("mockTranscript").textContent = result.transcript || "";
    const link = document.getElementById("downloadMockLink");
    const player = document.getElementById("mockVideoPlayer");

    if (result.video_available && result.video_id) {
      setMessage("mockMessage", "Video generated. Use the link below to download.");
      link.href = `/api/mock-interview/${result.video_id}`;
      link.textContent = "Download Generated Video";
      link.classList.remove("hidden");
      player.src = `/api/mock-interview/${result.video_id}`;
      player.classList.remove("hidden");
      showToast("Mock interview video generated", "success");
    } else {
      setMessage(
        "mockMessage",
        result.warning || "Transcript generated, but video is unavailable on this machine."
      );
      link.classList.add("hidden");
      player.removeAttribute("src");
      player.classList.add("hidden");
      showToast("Transcript generated (video unavailable)", "error");
    }

    if (result.warning) {
      showToast(result.warning, "error");
    }
  } catch (e) {
    setMessage("mockMessage", e.message || "Failed to generate mock interview");
    showToast(e.message || "Failed to generate mock interview", "error");
  } finally {
    setLoading(false);
  }
}

function setupEvents() {
  initTabs();

  document.getElementById("loginBtn").addEventListener("click", doLogin);
  document.getElementById("signupBtn").addEventListener("click", doSignup);

  ["loginUsername", "loginPassword"].forEach((id) => {
    document.getElementById(id).addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        doLogin();
      }
    });
  });

  ["signupUsername", "signupPassword", "signupConfirmPassword"].forEach((id) => {
    document.getElementById(id).addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        doSignup();
      }
    });
  });

  document.getElementById("showLoginBtn").addEventListener("click", () => switchAuthMode("login"));
  document.getElementById("showSignupBtn").addEventListener("click", () => switchAuthMode("signup"));
  document.getElementById("toSignupLink").addEventListener("click", () => switchAuthMode("signup"));
  document.getElementById("toLoginLink").addEventListener("click", () => switchAuthMode("login"));

  document.getElementById("logoutBtn").addEventListener("click", async () => {
    await api("/api/logout", { method: "POST" });
    stopCamera();
    await loginFlow();
    showToast("Logged out");
  });

  document.getElementById("practiceMode").addEventListener("change", togglePracticeMode);
  document.getElementById("useRlMode").addEventListener("change", async (event) => {
    if (event.target.checked) {
      state.rlSessionStarted = false;
      setRlStatus("RL mode enabled. Session starts on your next submit.");
      resetRlSummary();
      return;
    }
    state.rlSessionStarted = false;
    setRlStatus("RL mode is off.");
    resetRlSummary();
  });

  document.getElementById("rlDifficulty").addEventListener("change", () => {
    state.rlSessionStarted = false;
    if (isRlModeEnabled()) {
      setRlStatus("Difficulty changed. Next submit starts a new RL session.");
      resetRlSummary();
    }
  });

  document.getElementById("questionSelect").addEventListener("change", (e) => {
    document.getElementById("customQuestion").classList.toggle("hidden", e.target.value !== "Add custom question...");
  });

  document.getElementById("analyzeTextBtn").addEventListener("click", () => {
    submitTextPractice().catch((e) => {
      setLoading(false);
      showToast(e.message, "error");
    });
  });

  document.getElementById("analyzeAudioBtn").addEventListener("click", () => {
    submitAudioPractice().catch((e) => {
      setLoading(false);
      showToast(e.message, "error");
    });
  });

  const audioRecognizer = initSpeech("audioTranscript", "audioSpeechTimer");
  document.getElementById("startSpeechBtn").addEventListener("click", () => safeStartRecognition(audioRecognizer));
  document.getElementById("stopSpeechBtn").addEventListener("click", () => {
    if (audioRecognizer) audioRecognizer.stop();
    stopSpeechTimer("audioSpeechTimer");
  });

  const videoRecognizer = initSpeech("videoTranscript", "videoSpeechTimer");
  document.getElementById("startVideoSpeechBtn").addEventListener("click", () => safeStartRecognition(videoRecognizer));
  document.getElementById("stopVideoSpeechBtn").addEventListener("click", () => {
    if (videoRecognizer) videoRecognizer.stop();
    stopSpeechTimer("videoSpeechTimer");
  });

  document.getElementById("startCameraBtn").addEventListener("click", () => {
    startCamera().catch((e) => showToast(e.message, "error"));
  });

  document.getElementById("stopCameraBtn").addEventListener("click", stopCamera);
  document.getElementById("submitVideoBtn").addEventListener("click", () => {
    submitVideoPractice().catch((e) => {
      setLoading(false);
      showToast(e.message, "error");
    });
  });

  document.getElementById("generateMockBtn").addEventListener("click", () => {
    generateMockInterview().catch((e) => {
      setLoading(false);
      setMessage("mockMessage", e.message);
      showToast(e.message, "error");
    });
  });

  document.getElementById("downloadPdfBtn").addEventListener("click", () => {
    const startDate = document.getElementById("startDate").value;
    const endDate = document.getElementById("endDate").value;
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    window.open(`/api/reports/pdf?${params.toString()}`, "_blank");
    showToast("Downloading PDF report", "success");
  });

  ["startDate", "endDate"].forEach((id) => {
    const dateInput = document.getElementById(id);
    if (!dateInput) return;
    ["focus", "click"].forEach((evt) => {
      dateInput.addEventListener(evt, () => {
        if (typeof dateInput.showPicker === "function") {
          dateInput.showPicker();
        }
      });
    });
  });
}

setupEvents();
setupPasswordVisibility();
initParallaxBackground();
initCardTilt();
resetRlSummary();
updatePostureUi(state.posture.status, state.posture.feedback);
switchAuthMode("login");
loginFlow().catch(() => {
  setMessage("authMessage", "Unable to initialize app.");
});
