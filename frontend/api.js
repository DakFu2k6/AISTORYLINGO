"use strict";

const API_BASE = (() => {
  try {
    return localStorage.getItem("storylingo_api") || "http://localhost:8000";
  } catch (err) {
    return "http://localhost:8000";
  }
})();

const REQUEST_TIMEOUT_MS = 90000;

async function request(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response;
  try {
    response = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json", ...(sessionStorage.getItem("storylingo_token") ? { Authorization: `Bearer ${sessionStorage.getItem("storylingo_token")}` } : {}) },
      signal: controller.signal,
      ...options,
    });
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error("The server took too long to answer. Please try again.");
    }
    throw new Error(`Cannot reach the backend at ${API_BASE}. Is the server running?`);
  } finally {
    clearTimeout(timer);
  }

  let data = null;
  try {
    data = await response.json();
  } catch (err) {
    // Ignore JSON parse errors
  }

  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/auth/")) window.dispatchEvent(new Event("session-expired"));
    const detail = data && data.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg).join(", ")
          : `Server error (${response.status})`;
    throw new Error(message);
  }
  return data;
}

const post = (path, body) => request(path, { method: "POST", body: JSON.stringify(body) });
const api = {
  register: (name, email, password) => post("/auth/register", { name, email, password, accepted_terms: document.querySelector("#accept-terms").checked }),
  login: (email, password) => post("/auth/login", { email, password }),

  // Stories 
  generateStory: (payload) => post("/stories/generate", payload),
  nextChapter: (storyId, chapterId, choice, userId) =>
    post(`/stories/${storyId}/next-chapter`, { user_id: userId, chapter_id: chapterId, choice }),
  getStory: (storyId, userId) => request(`/stories/${storyId}?user_id=${encodeURIComponent(userId)}`),

  // Vocabulary
  saveWord: (userId, vocabularyId) =>
    post("/vocabulary/save", { user_id: userId, vocabulary_id: vocabularyId }),
  getSavedWords: (userId) => request(`/vocabulary/user/${userId}`),

  // Quiz
  getQuiz: (storyId) => request(`/quiz/story/${storyId}`),
  submitAnswer: (userId, vocabularyId, answer, kind = "meaning") =>
    post("/quiz/submit", { user_id: userId, vocabulary_id: vocabularyId, answer, kind }),

  // Progress
  getDashboard: (userId, wordsPage = 1, storiesPage = 1) => request(`/dashboard/${userId}?words_page=${wordsPage}&stories_page=${storiesPage}&page_size=6`),
};
