import React, { useMemo, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { clearHistory, getAllHistory } from '../data/history'
import './Admin.css'

function countHistoryForEmail(allHistory, email) {
  const list = allHistory?.[email] || []
  return Array.isArray(list) ? list.length : 0
}

export default function Admin() {
  const { user, listUsers, deleteUser } = useAuth()
  const [query, setQuery] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  const allUsers = useMemo(() => listUsers(), [listUsers, refreshKey])
  const allHistory = useMemo(() => getAllHistory(), [refreshKey])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return allUsers
    return allUsers.filter(u =>
      String(u.email).toLowerCase().includes(q) ||
      String(u.name || '').toLowerCase().includes(q),
    )
  }, [allUsers, query])

  const totalUsers = allUsers.length
  const totalAdmins = allUsers.filter(u => u.isAdmin).length
  const totalHistory = Object.values(allHistory || {}).reduce((sum, arr) => sum + (Array.isArray(arr) ? arr.length : 0), 0)

  const doRefresh = () => setRefreshKey(k => k + 1)

  const handleClearHistory = (email) => {
    if (!window.confirm(`Очистить историю для ${email}?`)) return
    clearHistory(email)
    doRefresh()
  }

  const handleDeleteUser = (email) => {
    if (!window.confirm(`Удалить пользователя ${email}?\nИстория останется (можно очистить отдельно).`)) return
    deleteUser(email)
    doRefresh()
  }

  if (!user?.isAdmin) {
    return (
      <div className="admin-page">
        <div className="admin-denied">
          Нет доступа. Требуются права администратора.
        </div>
      </div>
    )
  }

  return (
    <div className="admin-page">
      <div className="admin-head">
        <div>
          <h2 className="admin-title">Админ‑панель</h2>
          <p className="admin-subtitle">Управление пользователями и историей результатов</p>
        </div>
        <button type="button" className="admin-refresh" onClick={doRefresh}>
          Обновить
        </button>
      </div>

      <div className="admin-stats">
        <div className="admin-stat">
          <span className="admin-stat-label">Пользователей</span>
          <span className="admin-stat-value">{totalUsers}</span>
        </div>
        <div className="admin-stat">
          <span className="admin-stat-label">Админов</span>
          <span className="admin-stat-value">{totalAdmins}</span>
        </div>
        <div className="admin-stat">
          <span className="admin-stat-label">Записей истории</span>
          <span className="admin-stat-value">{totalHistory}</span>
        </div>
      </div>

      <div className="admin-toolbar">
        <label className="admin-search">
          Поиск
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="email или имя…"
          />
        </label>
      </div>

      <div className="admin-table">
        <div className="admin-table-head">
          <span>Email</span>
          <span>Имя</span>
          <span>Роль</span>
          <span>История</span>
          <span>Действия</span>
        </div>

        {filtered.map(u => (
          <div className="admin-row" key={u.email}>
            <span className="admin-cell-email">{u.email}</span>
            <span className="admin-cell-name">{u.name || '—'}</span>
            <span>
              <span className={`admin-badge ${u.isAdmin ? 'admin-badge-admin' : 'admin-badge-user'}`}>
                {u.isAdmin ? 'ADMIN' : 'USER'}
              </span>
            </span>
            <span>{countHistoryForEmail(allHistory, u.email)}</span>
            <span className="admin-actions">
              <button type="button" className="admin-btn" onClick={() => handleClearHistory(u.email)}>
                Очистить историю
              </button>
              <button
                type="button"
                className="admin-btn admin-btn-danger"
                onClick={() => handleDeleteUser(u.email)}
                disabled={u.email === user.email}
                title={u.email === user.email ? 'Нельзя удалить себя' : 'Удалить пользователя'}
              >
                Удалить
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

