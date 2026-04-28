import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

const STORAGE_KEY = 'skin_diagnosis_user'
const USERS_KEY = 'skin_diagnosis_users'
const ADMIN_EMAILS_KEY = 'skin_diagnosis_admin_emails'

function normalizeEmail(email) {
  return String(email || '').trim().toLowerCase()
}

function getAdminEmails() {
  // 1) Жёсткий дефолт для диплома (можно поменять под себя)
  const defaults = ['nail@gmail.com']
  // 2) Переопределение через localStorage (если когда-то понадобится)
  try {
    const stored = JSON.parse(localStorage.getItem(ADMIN_EMAILS_KEY) || '[]')
    const list = Array.isArray(stored) ? stored : []
    return Array.from(new Set([...defaults, ...list].map(normalizeEmail))).filter(Boolean)
  } catch {
    return defaults.map(normalizeEmail)
  }
}

function isAdminEmail(email) {
  const e = normalizeEmail(email)
  return getAdminEmails().includes(e)
}

function getUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY) || '[]')
  } catch {
    return []
  }
}

function setUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        setUser(JSON.parse(saved))
      } catch (_) {}
    }
    setLoading(false)
  }, [])

  const login = (email, password) => {
    const e = normalizeEmail(email)
    const users = getUsers()
    const found = users.find(u => normalizeEmail(u.email) === e && u.password === password)
    if (!found) return false
    const sessionUser = {
      email: normalizeEmail(found.email),
      name: found.name,
      isAdmin: Boolean(found.isAdmin) || isAdminEmail(found.email),
    }
    setUser(sessionUser)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionUser))
    return true
  }

  const register = (email, password, name) => {
    const e = normalizeEmail(email)
    const users = getUsers()
    if (users.some(u => normalizeEmail(u.email) === e)) return false
    // Первый зарегистрированный пользователь становится админом (удобно для диплома/демо)
    const isAdmin = users.length === 0 || isAdminEmail(e)
    users.push({ email: e, password, name, isAdmin })
    setUsers(users)
    const sessionUser = { email: e, name, isAdmin }
    setUser(sessionUser)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionUser))
    return true
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem(STORAGE_KEY)
  }

  const resetPassword = (email, newPassword) => {
    const e = normalizeEmail(email)
    const users = getUsers()
    const idx = users.findIndex(u => normalizeEmail(u.email) === e)
    if (idx === -1) return false
    users[idx].password = newPassword
    setUsers(users)
    return true
  }

  // Admin helpers
  const listUsers = () => getUsers().map(u => ({
    email: normalizeEmail(u.email),
    name: u.name,
    isAdmin: Boolean(u.isAdmin) || isAdminEmail(u.email),
  }))

  const deleteUser = (email) => {
    const e = normalizeEmail(email)
    const users = getUsers().filter(u => normalizeEmail(u.email) !== e)
    setUsers(users)
    // если удалили текущего пользователя — разлогиним
    if (normalizeEmail(user?.email) === e) logout()
    return true
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, resetPassword, listUsers, deleteUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
