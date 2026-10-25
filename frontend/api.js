"use strict";

const API_BASE = "http://localhost:8000";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (err) {
    throw new Error(`Cannot reach the backend at ${API_BASE}. Is the server running?`);
  }

  let data = null;
  try {
    data = await response.json();
  } catch (err) {
  }

  if (!response.ok) {
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
  // Auth
  register: (name, email, password) => post("/auth/register", { name, email, password }),
  login: (email, password) => post("/auth/login", { email, password }),

  // Stories
  generateStory: (payload) => post("/stories/generate", payload),
  nextChapter: (storyId, chapterId, choice) =>
    post(`/stories/${storyId}/next-chapter`, { chapter_id: chapterId, choice }),
  getStory: (storyId) => request(`/stories/${storyId}`),

  // Vocabulary
  saveWord: (userId, vocabularyId) =>
    post("/vocabulary/save", { user_id: userId, vocabulary_id: vocabularyId }),
  getSavedWords: (userId) => request(`/vocabulary/user/${userId}`),

  // Quiz
  getQuiz: (storyId) => request(`/quiz/story/${storyId}`),
  submitAnswer: (userId, vocabularyId, answer) =>
    post("/quiz/submit", { user_id: userId, vocabulary_id: vocabularyId, answer }),

  // Progress
  getDashboard: (userId) => request(`/dashboard/${userId}`),
};
