const message = document.querySelector("#message");
const analyseBtn = document.querySelector("#analyseBtn");
const result = document.querySelector("#result");
const errorBox = document.querySelector("#error");

analyseBtn.addEventListener("click", async () => {
  errorBox.textContent = "";
  const text = message.value.trim();
  if (!text) {
    errorBox.textContent = "Paste a message or URL first.";
    message.focus();
    return;
  }
  analyseBtn.disabled = true;
  analyseBtn.textContent = "Checking…";
  try {
    const response = await fetch("/api/analyse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not analyse this input.");
    showResult(data);
    loadHistory();
  } catch (error) {
    errorBox.textContent = error.message || "Something went wrong. Please try again.";
  } finally {
    analyseBtn.disabled = false;
    analyseBtn.textContent = "Analyse warning signs";
  }
});

function showResult(data) {
  result.classList.remove("hidden");
  document.querySelector("#riskLevel").textContent = data.risk_level;
  document.querySelector("#score").textContent = data.risk_score;
  document.querySelector("#meterFill").style.width = `${data.risk_score}%`;
  const fill = document.querySelector("#meterFill");
  fill.style.background =
    data.risk_score >= 50 ? "#b42318" : data.risk_score >= 25 ? "#d97706" : "#067647";

  const signals = document.querySelector("#signals");
  signals.replaceChildren();
  if (!data.signals.length) {
    const li = document.createElement("li");
    li.textContent = "No configured warning patterns were detected.";
    signals.append(li);
  } else {
    data.signals.forEach((signal) => {
      const li = document.createElement("li");
      li.textContent = `${signal.explanation} (+${signal.points})`;
      signals.append(li);
    });
  }
  const recs = document.querySelector("#recommendations");
  recs.replaceChildren();
  data.recommendations.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    recs.append(li);
  });
  document.querySelector("#disclaimer").textContent = data.disclaimer;
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

document.querySelector("#clearBtn").addEventListener("click", () => {
  message.value = "";
  errorBox.textContent = "";
  result.classList.add("hidden");
  message.focus();
});

document.querySelectorAll("[data-sample]").forEach((button) => {
  button.addEventListener("click", () => {
    message.value = button.dataset.sample;
    message.focus();
  });
});

const tipContent = {
  en: [
    [
      "Never share OTPs",
      "Banks and legitimate support staff should not ask you to disclose your OTP, PIN, or password.",
    ],
    [
      "Verify independently",
      "Open the official app or type the known website address yourself. Do not trust a link just because it looks familiar.",
    ],
    [
      "Pause on urgency",
      "Threats, prizes, and urgent payment requests are common pressure tactics. Stop and verify before acting.",
    ],
  ],
  ta: [
    ["OTP-ஐ பகிர வேண்டாம்", "உங்கள் OTP, PIN அல்லது கடவுச்சொல்லை யாரிடமும் பகிர வேண்டாம்."],
    [
      "தனியாகச் சரிபார்க்கவும்",
      "செய்தியில் உள்ள இணைப்பை அழுத்துவதற்குப் பதிலாக அதிகாரப்பூர்வ செயலி அல்லது இணையதளத்தைத் திறக்கவும்.",
    ],
    [
      "அவசரப்பட வேண்டாம்",
      "பரிசு, மிரட்டல் அல்லது உடனடி பணம் கேட்பது போன்ற செய்திகளைச் சரிபார்த்த பிறகே செயல்படுங்கள்.",
    ],
  ],
};
function renderTips(language) {
  const container = document.querySelector("#tips");
  container.replaceChildren();
  tipContent[language].forEach(([title, body]) => {
    const article = document.createElement("article");
    article.className = "tip";
    const heading = document.createElement("strong");
    heading.textContent = title;
    const paragraph = document.createElement("p");
    paragraph.textContent = body;
    article.append(heading, paragraph);
    container.append(article);
  });
  document.querySelector("#englishBtn").classList.toggle("active", language === "en");
  document.querySelector("#tamilBtn").classList.toggle("active", language === "ta");
}
document.querySelector("#englishBtn").addEventListener("click", () => renderTips("en"));
document.querySelector("#tamilBtn").addEventListener("click", () => renderTips("ta"));

async function loadHistory() {
  const container = document.querySelector("#history");
  try {
    const response = await fetch("/api/history");
    const entries = await response.json();
    container.replaceChildren();
    if (!entries.length) {
      container.textContent = "No checks yet.";
      return;
    }
    entries.forEach((entry) => {
      const item = document.createElement("div");
      item.className = "history-item";
      const text = document.createElement("span");
      text.className = "history-text";
      text.textContent = entry.input_text;
      const label = document.createElement("span");
      label.className = "pill";
      label.textContent = `${entry.risk_level} · ${entry.risk_score}/100`;
      item.append(text, label);
      container.append(item);
    });
  } catch {
    container.textContent = "Could not load history.";
  }
}
document.querySelector("#historyBtn").addEventListener("click", loadHistory);
renderTips("en");
loadHistory();
