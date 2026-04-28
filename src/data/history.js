const STORAGE_KEY = 'skin_diagnosis_history'
const MAX_ITEMS_PER_USER = 50

function getStorage() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

function setStorage(data) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

export function getHistory(email) {
  if (!email) return []
  const data = getStorage()
  const list = data[email] || []
  return [...list].reverse()
}

export function getAllHistory() {
  return getStorage()
}

export function addToHistory(email, { result, image }) {
  if (!email || !result) return
  const data = getStorage()
  const list = data[email] || []
  const item = {
    id: Date.now(),
    date: new Date().toISOString(),
    image: image || null,
    result: {
      main: result.main,
      top3: result.top3,
    },
  }
  const next = [item, ...list].slice(0, MAX_ITEMS_PER_USER)
  data[email] = next
  setStorage(data)
}

export function removeFromHistory(email, id) {
  if (!email) return
  const data = getStorage()
  const list = (data[email] || []).filter((item) => item.id !== id)
  data[email] = list
  setStorage(data)
}

export function clearHistory(email) {
  if (!email) return
  const data = getStorage()
  delete data[email]
  setStorage(data)
}
