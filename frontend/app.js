"use strict";
/* 1. STATE & HELPERS */
const KEY_USER = "storylingo_user";
const KEY_STORY = "storylingo_story_id";
const LANG_CODES = { English: "en-US", Japanese: "ja-JP", Korean: "ko-KR" };
const LOADING_STEPS = [
  "Creating characters…",
  "Building the plot…",
  "Choosing vocabulary…",
  "Writing chapter 1…",
];
const VIEWS = ["auth", "recovery", "create", "story", "quiz", "progress", "admin"];
const state = {
  user: null,
  story: null,
  savedIds: new Set(),
  quiz: null,
  busy: false,
  currentWordId: null,
};
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function toast(message, type = "info", ms = 3800) {
  const el = $("#toast");
  el.textContent = message;
  el.className = `toast show ${type}`;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (el.className = "toast"), ms);
}

const loadingHTML = (text) =>
  `<div class="loading"><span class="spinner"></span><span>${esc(text)}</span></div>`;
const errorHTML = (message) =>
  `<div class="card empty"><h2>Something went wrong</h2><p class="error">${esc(message)}</p>
   <button class="btn" data-goto="create">Back to Create</button></div>`;
const emptyHTML = (title, text) =>
  `<div class="card empty"><h2>${esc(title)}</h2><p class="muted">${esc(text)}</p>
   <button class="btn primary" data-goto="create">Create a story</button></div>`;

function speak(text, language) {
  if (!("speechSynthesis" in window)) {
    toast("Your browser does not support speech.", "error");
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = LANG_CODES[language] || "en-US";
  utterance.rate = 0.9;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

/* 2. LOGIN / REGISTER */
let authMode = "login";

function setAuthMode(mode) {
  authMode = mode;
  $("#tab-login").classList.toggle("active", mode === "login");
  $("#tab-register").classList.toggle("active", mode === "register");
  $("#auth-name-group").hidden = mode !== "register";
  $("#auth-username-group").hidden = mode !== "register";
  $("#auth-identifier-label").textContent = mode === "register" ? "Email" : "Email or username";
  $("#auth-email").placeholder = mode === "register" ? "you@example.com" : "Email or username";
  $("#auth-email").autocomplete = mode === "register" ? "email" : "username";
  $("#auth-confirm-group").hidden = mode !== "register";
  $("#terms-group").hidden = mode !== "register";
  $("#auth-submit").textContent = mode === "register" ? "Create account" : "Log in";
  $("#auth-password").autocomplete = mode === "register" ? "new-password" : "current-password";
  $("#auth-error").textContent = "";
}

async function onAuthSubmit(event) {
  event.preventDefault();
  const name = $("#auth-name").value.trim();
  const username = $("#auth-username").value.trim().toLowerCase();
  const email = $("#auth-email").value.trim();
  const password = $("#auth-password").value;
  const errorEl = $("#auth-error");
  errorEl.textContent = "";

  if (authMode === "register" && !name) return (errorEl.textContent = "Please enter your name.");
  if (authMode === "register" && !/^[a-z0-9_]{3,30}$/.test(username)) return (errorEl.textContent = "Username must have 3–30 letters, numbers or underscores.");
  if (authMode === "register" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return (errorEl.textContent = "Please enter a valid email.");
  if (authMode === "login" && !email) return (errorEl.textContent = "Enter your email or username.");
  if (authMode === "register" && !$("#accept-terms").checked) return (errorEl.textContent = "Please accept the terms of use.");
  if (authMode === "register" && (password.length < 8 || !/[A-Za-z]/.test(password) || !/[0-9]/.test(password))) return (errorEl.textContent = "Use 8+ characters, including a letter and a number.");
  if (!password) return (errorEl.textContent = "Please enter your password.");

  if (authMode === "register" && password !== $("#auth-confirm").value) return (errorEl.textContent = "Passwords do not match.");
  const button = $("#auth-submit");
  button.disabled = true;
  try {
    const data =
      authMode === "register"
        ? await api.register(name, username, email, password)
        : await api.login(email, password);
    sessionStorage.setItem("storylingo_token", data.access_token);
    setUser(data.user);
    $("#auth-password").value = "";
    $("#auth-confirm").value = "";
    goTo("create");
    toast(`Welcome, ${data.user.name}!`, "success");
  } catch (err) {
    errorEl.textContent = err.message;
  } finally {
    button.disabled = false;
  }
}

function setUser(user) {
  state.user = user;
  localStorage.setItem(KEY_USER, JSON.stringify(user));
  $("#nav").hidden = false;
  $("#menu-toggle").hidden = false;
  $("#admin-nav").hidden = user.role !== "admin";
  $("#user-name").textContent = user.name;
}

function logout() {
  if (sessionStorage.getItem("storylingo_token")) post("/auth/logout", {}).catch(() => { });
  sessionStorage.removeItem("storylingo_token");
  $("#menu-toggle").hidden = true;
  $("#nav").classList.remove("open");
  state.user = null;
  state.story = null;
  state.quiz = null;
  wordsPage = storiesPage = adminPage = 1;
  state.savedIds = new Set();
  localStorage.removeItem(KEY_USER);
  localStorage.removeItem(KEY_STORY);
  $("#nav").hidden = true;
  goTo("auth");
}

/* 3. CREATE A STORY */
async function onCreateSubmit(event) {
  event.preventDefault();
  if (state.busy) return;

  const form = Object.fromEntries(new FormData(event.target));
  const errorEl = $("#create-error");
  errorEl.textContent = "";

  const topic = (form.topic || "").trim();
  const words = Number(form.target_words);
  if (topic.length < 2) return (errorEl.textContent = "Please enter a topic (at least 2 characters).");
  if (!Number.isInteger(words) || words < 1 || words > 10)
    return (errorEl.textContent = "Vocabulary words must be between 1 and 10.");

  const button = $("#create-btn");
  const status = $("#create-status");
  state.busy = true;
  button.disabled = true;
  let step = 0;
  status.textContent = LOADING_STEPS[0];
  const timer = setInterval(() => {
    step = Math.min(step + 1, LOADING_STEPS.length - 1);
    status.textContent = LOADING_STEPS[step];
  }, 1500);

  try {
    const data = await api.generateStory({
      user_id: state.user.id,
      language: form.language,
      level: form.level,
      genre: form.genre,
      topic,
      target_words: words,
      total_chapters: Number(form.total_chapters),
    });
    state.story = { story: data.story, chapters: [data.chapter], vocabulary: data.vocabulary };
    state.quiz = null;
    localStorage.setItem(KEY_STORY, String(data.story.id));
    await refreshSavedWords();
    goTo("story");
    if (data.story.source === "demo" && data.fallback_reason) {
      toast(`Demo story used. Reason: ${data.fallback_reason}`, "error", 9000);
    }
  } catch (err) {
    errorEl.textContent = err.message;
    if (/log in again/i.test(err.message)) logout();
  } finally {
    clearInterval(timer);
    status.textContent = "";
    button.disabled = false;
    state.busy = false;
  }
}

/* 4. STORY READER */
async function loadStory(storyId) {
  state.story = await api.getStory(storyId, state.user.id);
  state.quiz = null;
  localStorage.setItem(KEY_STORY, String(storyId));
  await refreshSavedWords();
}

async function refreshSavedWords() {
  try {
    const res = await api.getSavedWords(state.user.id);
    state.savedIds = new Set(res.data.map((w) => w.vocabulary_id));
  } catch (err) {
  }
}

function highlightWords(text, vocabulary) {
  const safeText = esc(text);
  if (!vocabulary.length) return safeText;

  const byWord = new Map(vocabulary.map((v) => [esc(v.word).toLowerCase(), v]));
  const escapeRegex = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const isLatin = (w) => /^[\p{Script=Latin}'’\- ]+$/u.test(w);
  const keys = [...byWord.keys()].sort((a, b) => b.length - a.length);
  const parts = [];
  const latin = keys.filter(isLatin).map(escapeRegex);
  const other = keys.filter((k) => !isLatin(k)).map(escapeRegex);

  if (latin.length) parts.push(`(?<![\\p{L}\\p{N}])(?:${latin.join("|")})(?![\\p{L}\\p{N}])`);
  if (other.length) parts.push(other.join("|"));

  const regex = new RegExp(parts.join("|"), "giu");
  return safeText.replace(regex, (match) => {
    const vocab = byWord.get(match.toLowerCase());
    return vocab ? `<button type="button" class="vocab-word" data-word-id="${vocab.id}">${match}</button>` : match;
  });
}

function lastChapter() {
  const chapters = state.story.chapters;
  return chapters[chapters.length - 1];
}

function choiceAreaHTML() {
  const { story } = state.story;
  const last = lastChapter();

  if (story.status === "completed" || last.choices.length === 0) {
    return `<div class="the-end card">
      <h3>The End ✦</h3>
      <p class="muted">You finished the story. Now test the words you met.</p>
      <button class="btn primary big" data-action="start-quiz">Take the quiz</button>
    </div>`;
  }

  const letters = ["A", "B", "C", "D"];
  return `<h3>What will you do?</h3>` + last.choices
    .map(
      (choice, i) => `<button class="choice-btn" data-choice="${i}">
        <span class="choice-letter">${letters[i]}</span><span>${esc(choice)}</span></button>`
    )
    .join("");
}

function renderStoryView() {
  const root = $("#view-story");
  if (!state.story) {
    root.innerHTML = emptyHTML("No story yet", "Create your first story to start reading.");
    return;
  }

  const { story, chapters, vocabulary } = state.story;
  const demoBadge =
    story.source === "demo"
      ? `<span class="badge warn" title="No Gemini API key found, so a built-in demo story is used.">Demo story</span>`
      : "";

  root.innerHTML = `
    <article class="card">
      <div class="reader-head">
        <h2>${esc(story.title)}</h2>
        <div class="badges">
          <span class="badge">${esc(story.language)}</span>
          <span class="badge">Level ${esc(story.level)}</span>
          <span class="badge">${esc(story.genre)}</span>
          <span class="badge">Topic: ${esc(story.topic)}</span>
          <span class="badge">Chapter ${chapters.length} / ${story.total_chapters}</span>
          ${demoBadge}
        </div>
      </div>

      ${chapters
      .map(
        (ch) => `<section class="chapter" id="chapter-${ch.chapter_number}">
            <h3>Chapter ${ch.chapter_number}</h3>
            <p class="story-text">${highlightWords(ch.content, vocabulary)}</p>
            ${ch.chosen_choice ? `<p class="you-chose">You chose: ${esc(ch.chosen_choice)}</p>` : ""}
          </section>`
      )
      .join("")}

      <section class="words-box">
        <h3>Words in this story (click to learn)</h3>
        <div class="chips">
          ${vocabulary
      .map(
        (v) => `<button class="chip ${state.savedIds.has(v.id) ? "saved" : ""}" data-word-id="${v.id}">${esc(v.word)}</button>`
      )
      .join("")}
        </div>
      </section>

      <section class="choice-area" id="choice-area">${choiceAreaHTML()}</section>
    </article>`;
}

async function chooseOption(index) {
  if (state.busy) return;
  const { story, chapters } = state.story;
  const last = lastChapter();
  const choice = last.choices[index];
  if (!choice) return;

  state.busy = true;
  $("#choice-area").innerHTML = loadingHTML("Writing the next chapter…");
  try {
    const data = await api.nextChapter(story.id, last.id, choice, state.user.id);
    last.chosen_choice = choice;
    chapters.push(data.chapter);
    state.story.story = data.story;
    state.quiz = null;
    if (data.source === "demo" && story.source !== "demo") {
      const why = data.fallback_reason ? ` Reason: ${data.fallback_reason}` : "";
      toast(`The AI was unavailable, so demo text was used for this chapter.${why}`, "error", 9000);
    }
    renderStoryView();
    const el = document.getElementById(`chapter-${data.chapter.chapter_number}`);
    if (el && el.scrollIntoView) el.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    toast(err.message, "error");
    $("#choice-area").innerHTML = choiceAreaHTML();
  } finally {
    state.busy = false;
  }
}

/* Vocabulary popup */
function openWord(wordId) {
  const vocab = state.story && state.story.vocabulary.find((v) => v.id === Number(wordId));
  if (!vocab) return;
  state.currentWordId = vocab.id;
  const saved = state.savedIds.has(vocab.id);

  $("#popup-body").innerHTML = `
    <h2 id="popup-title">${esc(vocab.word)}</h2>
    <p class="pron">${esc(vocab.pronunciation)}</p>
    ${vocab.part_of_speech ? `<span class="pos">${esc(vocab.part_of_speech)}</span>` : ""}
    <p class="meaning">${esc(vocab.meaning)}</p>
    ${vocab.meaning_vi ? `<p class="meaning-vi">🇻🇳 ${esc(vocab.meaning_vi)}</p>` : ""}
    ${vocab.example ? `<p class="example">${esc(vocab.example)}</p>` : ""}
    <div class="popup-actions">
      <button class="btn" data-action="speak">🔊 Listen</button>
      <button class="btn primary" data-action="save-word" ${saved ? "disabled" : ""}>
        ${saved ? "✓ Saved" : "+ Save word"}
      </button>
    </div>`;
  $("#word-popup").hidden = false;
}

function closePopup() {
  $("#word-popup").hidden = true;
  state.currentWordId = null;
}

async function saveCurrentWord() {
  const id = state.currentWordId;
  if (id === null) return;
  const button = $('[data-action="save-word"]');
  button.disabled = true;
  try {
    await api.saveWord(state.user.id, id);
    state.savedIds.add(id);
    button.textContent = "✓ Saved";
    $$(`.chip[data-word-id="${id}"]`).forEach((chip) => chip.classList.add("saved"));
    toast("Word saved to your notebook!", "success");
  } catch (err) {
    button.disabled = false;
    toast(err.message, "error");
  }
}

function speakCurrentWord() {
  const vocab = state.story.vocabulary.find((v) => v.id === state.currentWordId);
  if (vocab) speak(vocab.word, state.story.story.language);
}

/* 5. QUIZ */
async function openQuiz() {
  const root = $("#view-quiz");
  if (!state.story) {
    root.innerHTML = emptyHTML("No quiz yet", "Read a story first, then test its words here.");
    return;
  }

  const storyId = state.story.story.id;
  if (state.quiz && state.quiz.storyId === storyId && !state.quiz.finished) {
    renderQuestion();
    return;
  }

  root.innerHTML = loadingHTML("Preparing your quiz…");
  try {
    const data = await api.getQuiz(storyId);
    state.quiz = { storyId, questions: data.questions, index: 0, score: 0, locked: false, finished: false };
    renderQuestion();
  } catch (err) {
    root.innerHTML = errorHTML(err.message);
  }
}

function renderQuestion() {
  const quiz = state.quiz;
  const root = $("#view-quiz");
  if (quiz.index >= quiz.questions.length) return renderQuizResult();

  const item = quiz.questions[quiz.index];
  const percent = (quiz.index / quiz.questions.length) * 100;
  quiz.locked = false;

  root.innerHTML = `
    <div class="card quiz-card">
      <div class="quiz-progress">
        Question ${quiz.index + 1} of ${quiz.questions.length}
        <div class="bar"><span style="width:${percent}%"></span></div>
      </div>
      <h2>${esc(item.question)}</h2>
      <div class="options">
        ${item.options
      .map((option, i) => `<button class="option-btn" data-option="${i}">${esc(option)}</button>`)
      .join("")}
      </div>
      <div id="quiz-feedback"></div>
    </div>`;
}

async function answerQuestion(optionIndex) {
  const quiz = state.quiz;
  if (!quiz || quiz.locked) return;
  quiz.locked = true;

  const item = quiz.questions[quiz.index];
  const answer = item.options[optionIndex];
  try {
    const res = await api.submitAnswer(state.user.id, item.vocabulary_id, answer, item.kind);
    if (res.is_correct) quiz.score += 1;

    $$(".option-btn").forEach((btn, i) => {
      btn.disabled = true;
      if (item.options[i] === res.correct_answer) btn.classList.add("correct");
      else if (i === optionIndex) btn.classList.add("wrong");
    });

    const isLast = quiz.index + 1 >= quiz.questions.length;
    $("#quiz-feedback").innerHTML = `
      <div class="feedback ${res.is_correct ? "good" : "bad"}">
        <strong>${res.is_correct ? "Correct! 🎉" : "Not quite."}</strong>
        <div><b>${esc(res.word)}</b> = ${esc(res.meaning)}</div>
        ${res.meaning_vi ? `<div class="muted">🇻🇳 ${esc(res.meaning_vi)}</div>` : ""}
        <div class="muted">Mastery of this word: ${res.mastery_level}%</div>
        <div class="muted">+${res.xp_gained} XP · Level ${res.level} · 🔥 ${res.streak_days}-day streak</div>
        <button class="btn primary" data-action="next-question">${isLast ? "See results" : "Next question"}</button>
      </div>`;
  } catch (err) {
    quiz.locked = false;
    toast(err.message, "error");
  }
}

function renderQuizResult() {
  const quiz = state.quiz;
  quiz.finished = true;
  const total = quiz.questions.length;
  const percent = Math.round((quiz.score / total) * 100);
  const message =
    percent >= 80 ? "Excellent! You really know these words." :
      percent >= 50 ? "Good job! A little more practice and you will master them." :
        "Keep going! Re-read the story and try again.";

  $("#view-quiz").innerHTML = `
    <div class="card">
      <h2 class="center">Quiz complete</h2>
      <p class="score">${quiz.score} / ${total}</p>
      <p class="center muted">${percent}% correct. ${esc(message)}</p>
      <div class="result-actions">
        <button class="btn" data-action="retry-quiz">Try again</button>
        <button class="btn primary" data-goto="progress">View my progress</button>
        <button class="btn" data-goto="create">New story</button>
      </div>
    </div>`;
}

/* 6. PROGRESS */
let wordsPage = 1, storiesPage = 1, adminPage = 1;
async function loadProgress() {
  const root = $("#view-progress");
  root.innerHTML = loadingHTML("Loading your progress…");
  try {
    const data = await api.getDashboard(state.user.id, wordsPage, storiesPage);
    renderProgress(data);
  } catch (err) {
    root.innerHTML = errorHTML(err.message);
    if (/log in again/i.test(err.message)) logout();
  }
}

function renderProgress({ statistics: s, words, stories, recommendation, pagination }) {
  const statCards = [
    [`🔥 ${s.streak_days}`, "Day streak"],
    [s.xp, `XP · Level ${s.level}`],
    [s.total_stories, "Stories created"],
    [s.completed_stories, "Stories finished"],
    [s.words_saved, "Words in notebook"],
    [s.words_mastered, "Words mastered"],
    [`${s.quiz_accuracy}%`, `Quiz accuracy (${s.quiz_total} answers)`],
  ];

  const wordRows = words.length
    ? words
      .map(
        (w) => `<div class="row">
            <div class="grow"><div class="name">${esc(w.word)}</div><div class="sub">${esc(w.meaning)}</div></div>
            <div class="mastery">Mastery ${w.mastery_level}%
              <div class="bar"><span style="width:${w.mastery_level}%"></span></div></div>
          </div>`
      )
      .join("")
    : `<p class="muted">No saved words yet. Click a word in a story, or take a quiz.</p>`;

  const storyRows = stories.length
    ? stories
      .map(
        (st) => `<div class="row">
            <div class="grow">
              <div class="name">${esc(st.title)}</div>
              <div class="sub">${esc(st.language)} · ${esc(st.level)} · ${esc(st.genre)} ·
                chapter ${st.chapters_done}/${st.total_chapters} ·
                ${st.status === "completed" ? "finished" : "in progress"} ·
                ${new Date(st.created_at).toLocaleDateString()}</div>
            </div>
            <button class="btn" data-read="${st.id}">${st.status === "completed" ? "Read again" : "Continue"}</button>
          </div>`
      )
      .join("")
    : `<p class="muted">No stories yet.</p>`;

  $("#view-progress").innerHTML = `
    <h1 class="title">Your progress</h1>
    ${recommendation ? `<p class="reco ${recommendation.suggested_level !== recommendation.current_level ? "change" : ""}">💡 ${esc(recommendation.message)}</p>` : ""}
    <div class="stats">
      ${statCards
      .map(([num, label]) => `<div class="card stat"><div class="num">${esc(num)}</div><div class="label">${esc(label)}</div></div>`)
      .join("")}
    </div>
    <h2 class="section-title">My words</h2>
    <div class="rows">${wordRows}</div>${pager("words", wordsPage, pagination.words_total, pagination.page_size)}
    <h2 class="section-title">My stories</h2>
    <div class="rows">${storyRows}</div>${pager("stories", storiesPage, pagination.stories_total, pagination.page_size)}`;
}

async function readStoryAgain(storyId) {
  try {
    await loadStory(storyId);
    goTo("story");
  } catch (err) {
    toast(err.message, "error");
  }
}

/* 7. NAVIGATION & START */
function goTo(view) {
  if (!VIEWS.includes(view)) return;
  if (!["auth", "recovery"].includes(view) && !state.user) view = "auth";
  if (view === "admin" && state.user?.role !== "admin") return;
  $("#nav").classList.remove("open");
  $("#menu-toggle").setAttribute("aria-expanded", "false");
  VIEWS.forEach((v) => ($(`#view-${v}`).hidden = v !== view));
  $$(".nav-btn[data-view]").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
  window.scrollTo({ top: 0 });

  if (view === "admin") loadAdmin();
  if (view === "story") renderStoryView();
  if (view === "quiz") openQuiz();
  if (view === "progress") loadProgress();
}

function onPageClick(event) {
  const target = event.target;

  const authTab = target.closest("[data-auth-mode]");
  if (authTab) return setAuthMode(authTab.dataset.authMode);

  const gotoBtn = target.closest("[data-goto]");
  if (gotoBtn) return goTo(gotoBtn.dataset.goto);

  const navBtn = target.closest("[data-view]");
  if (navBtn) return goTo(navBtn.dataset.view);

  const wordBtn = target.closest("[data-word-id]");
  if (wordBtn) return openWord(wordBtn.dataset.wordId);

  const choiceBtn = target.closest("[data-choice]");
  if (choiceBtn) return chooseOption(Number(choiceBtn.dataset.choice));

  const optionBtn = target.closest("[data-option]");
  if (optionBtn) return answerQuestion(Number(optionBtn.dataset.option));

  const readBtn = target.closest("[data-read]");
  if (readBtn) return readStoryAgain(Number(readBtn.dataset.read));

  if (target.id === "word-popup") return closePopup(); // click on the dark background

  const actionBtn = target.closest("[data-action]");
  if (!actionBtn) return;
  switch (actionBtn.dataset.action) {
    case "logout": return logout();
    case "close-popup": return closePopup();
    case "speak": return speakCurrentWord();
    case "save-word": return saveCurrentWord();
    case "start-quiz": return goTo("quiz");
    case "next-question":
      state.quiz.index += 1;
      return renderQuestion();
    case "retry-quiz":
      state.quiz = null;
      return openQuiz();
  }
}

async function init() {
  initAccountFeatures();
  $("#auth-form").addEventListener("submit", onAuthSubmit);
  $("#create-form").addEventListener("submit", onCreateSubmit);
  document.addEventListener("click", onPageClick);
  document.addEventListener("keydown", (e) => e.key === "Escape" && closePopup());

  let savedUser = null;
  try {
    savedUser = JSON.parse(localStorage.getItem(KEY_USER));
  } catch (err) {
    savedUser = null;
  }

  if (resetToken) { setupRecovery(); goTo("recovery"); return; }
  if (savedUser && savedUser.id && sessionStorage.getItem("storylingo_token")) {
    try { savedUser = (await request("/auth/me")).user; } catch { logout(); return; }
    setUser(savedUser);
    goTo("create");
    const lastStoryId = localStorage.getItem(KEY_STORY);
    if (lastStoryId) {
      loadStory(lastStoryId).catch(() => localStorage.removeItem(KEY_STORY));
    }
  } else {
    goTo("auth");
  }
}

document.addEventListener("DOMContentLoaded", init);

function pager(kind, page, total, size) {
  const pages = Math.max(1, Math.ceil(total / size));
  return `<div class="pagination" aria-label="${kind} pagination"><span>${total} items · Page ${page} of ${pages}</span><button class="btn" data-page-kind="${kind}" data-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>Previous</button><button class="btn" data-page-kind="${kind}" data-page="${page + 1}" ${page >= pages ? "disabled" : ""}>Next</button></div>`;
}

async function loadAdmin() {
  const root = $("#view-admin");
  root.innerHTML = loadingHTML("Loading administration…");
  try {
    const [s, users] = await Promise.all([request("/admin/overview"), request(`/admin/users?page=${adminPage}&page_size=10`)]);
    root.innerHTML = `<p class="eyebrow">WORKSPACE OVERVIEW</p><h1 class="title">Admin dashboard</h1><p class="muted">Monitor your learning community.</p><div class="stats">${Object.entries(s).map(([k, v]) => `<div class="card stat"><div class="num">${v}</div><div class="label">${esc(k)}</div></div>`).join("")}</div><h2 class="section-title">Registered learners</h2><div class="table-wrap"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead><tbody>${users.data.map(u => `<tr><td>${esc(u.name)}</td><td>${esc(u.email)}</td><td><span class="badge">${esc(u.role)}</span></td></tr>`).join("")}</tbody></table></div>${pager("admin", adminPage, users.total, users.page_size)}`;
  } catch (err) { root.innerHTML = errorHTML(err.message); }
}

let resetToken = new URLSearchParams(location.search).get("reset_token");
if (resetToken) history.replaceState(null, "", location.pathname);
function setupRecovery() {
  const reset = Boolean(resetToken);
  $("#recovery-title").textContent = reset ? "Choose a new password" : "Forgot password?";
  $("#recovery-help").textContent = reset ? "Your reset link is valid for 15 minutes and can be used once." : "We will email you a secure reset link.";
  $("#recovery-email-group").hidden = reset;
  $("#recovery-email").required = !reset;
  $("#recovery-password-group").hidden = !reset;
  $("#recovery-confirm-group").hidden = !reset;
  $("#recovery-password").required = reset;
  $("#recovery-confirm").required = reset;
  $("#recovery-submit").textContent = reset ? "Update password" : "Send reset link";
  $("#recovery-message").textContent = "";
}
async function recoverySubmit(event) {
  event.preventDefault();
  const btn = $("#recovery-submit"); btn.disabled = true;
  try {
    const password = $("#recovery-password").value;
    if (resetToken && password !== $("#recovery-confirm").value) throw new Error("Passwords do not match.");
    const result = resetToken ? await post("/auth/reset-password", { token: resetToken, password }) : await post("/auth/forgot-password", { email: $("#recovery-email").value.trim() });
    $("#recovery-message").textContent = result.message;
    if (resetToken) { resetToken = null; sessionStorage.removeItem("storylingo_token"); toast(result.message, "success"); logout(); }
  } catch (err) { $("#recovery-message").textContent = err.message; }
  finally { btn.disabled = false; }
}
async function setupGoogle() {
  try {
    const cfg = await request("/auth/config");
    if (!cfg.google_client_id) { $("#google-status").textContent = "Google sign-in is not configured. Add GOOGLE_CLIENT_ID to .env and restart the backend."; $("#google-retry").hidden = false; return; }
    if (!window.google?.accounts) await new Promise((resolve, reject) => {
      const script = document.createElement("script"); script.src = "https://accounts.google.com/gsi/client";
      script.onload = resolve; script.onerror = () => reject(new Error("Cannot load Google sign-in. Check your connection.")); document.head.append(script);
    });
    const challenge = await request("/auth/google/nonce");
    google.accounts.id.initialize({
      client_id: cfg.google_client_id, nonce: challenge.nonce, callback: async response => {
        try {
          const result = await post("/auth/google", { credential: response.credential, nonce: challenge.nonce, accepted_terms: true });
          sessionStorage.setItem("storylingo_token", result.access_token); setUser(result.user); goTo("create"); toast("Welcome to StoryLingo!", "success");
        } catch (err) { $("#auth-error").textContent = err.message; }
        finally { $("#google-button").innerHTML = ""; setupGoogle(); }
      }
    });
    google.accounts.id.renderButton($("#google-button"), { theme: "outline", size: "large", width: Math.max(200, Math.min(280, $("#google-button").clientWidth || 280)) });
    $("#google-status").textContent = "";
    $("#google-retry").hidden = true;
  } catch (err) { $("#google-status").textContent = err.message; $("#google-retry").hidden = false; }
}
function initAccountFeatures() {
  setupGoogle();
  $("#google-retry").addEventListener("click", () => { $("#google-retry").hidden = true; setupGoogle(); });
  $("#menu-toggle").addEventListener("click", () => {
    const open = $("#nav").classList.toggle("open"); $("#menu-toggle").setAttribute("aria-expanded", String(open));
  });
  $("#forgot-password").addEventListener("click", () => { resetToken = null; setupRecovery(); goTo("recovery"); });
  $("#recovery-form").addEventListener("submit", recoverySubmit);
  window.addEventListener("session-expired", () => { sessionStorage.removeItem("storylingo_token"); logout(); toast("Session expired. Please log in again.", "error"); });
  document.addEventListener("keydown", event => { if (event.key === "Escape") { $("#nav").classList.remove("open"); $("#menu-toggle").setAttribute("aria-expanded", "false"); } });
  document.addEventListener("click", event => {
    const button = event.target.closest("[data-page-kind]"); if (!button || button.disabled) return;
    const page = Number(button.dataset.page);
    if (button.dataset.pageKind === "admin") { adminPage = page; loadAdmin(); }
    else { if (button.dataset.pageKind === "words") wordsPage = page; else storiesPage = page; loadProgress(); }
  });
}

function initThemeToggle() {
  const button = document.getElementById("theme-toggle");
  const icon = document.getElementById("theme-icon");
  if (!button || !icon) return;
  const systemTheme = window.matchMedia(
    "(prefers-color-scheme: dark)"
  );
  function getSavedTheme() {
    try {
      return localStorage.getItem("storylingo_theme");
    } catch {
      return null;
    }
  }
  function applyTheme(theme) {
    const isDark = theme === "dark";
    document.documentElement.dataset.theme = theme;
    const label = isDark
      ? "Chuyển sang giao diện sáng"
      : "Chuyển sang giao diện tối";
    button.setAttribute("aria-label", label);
    button.setAttribute("aria-pressed", String(isDark));
    button.title = label;
    icon.textContent = "💡";
    icon.style.opacity = isDark ? "0.65" : "1";
  }
  const savedTheme = getSavedTheme();
  applyTheme(
    savedTheme === "light" || savedTheme === "dark"
      ? savedTheme
      : systemTheme.matches
        ? "dark"
        : "light"
  );
  button.addEventListener("click", () => {
    const nextTheme =
      document.documentElement.dataset.theme === "dark"
        ? "light"
        : "dark";
    applyTheme(nextTheme);
    try {
      localStorage.setItem("storylingo_theme", nextTheme);
    } catch {
    }
  });
  systemTheme.addEventListener("change", (event) => {
    const preference = getSavedTheme();

    if (preference !== "light" && preference !== "dark") {
      applyTheme(event.matches ? "dark" : "light");
    }
  });
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initThemeToggle);
} else {
  initThemeToggle();
}