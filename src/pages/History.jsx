import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getHistory, removeFromHistory } from '../data/history'
import { DIAGNOSES } from '../data/diagnoses'
import './History.css'

function formatDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function History() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [expandedId, setExpandedId] = useState(null)

  useEffect(() => {
    if (user?.email) {
      setItems(getHistory(user.email))
    }
  }, [user?.email])

  const refresh = () => {
    if (user?.email) setItems(getHistory(user.email))
  }

  const handleRemove = (e, id) => {
    e.preventDefault()
    e.stopPropagation()
    if (!user?.email) return
    if (window.confirm('Удалить запись из истории?')) {
      removeFromHistory(user.email, id)
      refresh()
      if (expandedId === id) setExpandedId(null)
    }
  }

  if (!items.length) {
    return (
      <div className="history-page">
        <div className="history-empty">
          <p className="history-empty-title">История результатов пуста</p>
          <p className="history-empty-text">
            После каждой диагностики результат будет сохраняться здесь. Загрузите изображение на главной странице.
          </p>
          <Link to="/" className="history-empty-link">
            Перейти к диагностике
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="history-page">
      <h2 className="history-title">История результатов</h2>
      <p className="history-subtitle">Ваши прошлые анализы (последние сначала)</p>

      <ul className="history-list">
        {items.map((item) => {
          const main = item.result?.main
          const info = main ? DIAGNOSES[main.key] : null
          const isExpanded = expandedId === item.id

          return (
            <li key={item.id} className="history-item">
              <button
                type="button"
                className="history-item-head"
                onClick={() => setExpandedId(isExpanded ? null : item.id)}
              >
                <div className="history-item-preview">
                  {item.image ? (
                    <img src={item.image} alt="" className="history-thumb" />
                  ) : (
                    <div className="history-thumb-placeholder">Нет фото</div>
                  )}
                </div>
                <div className="history-item-info">
                  <span className="history-item-date">{formatDate(item.date)}</span>
                  {info && (
                    <>
                      <span className="history-item-diagnosis">{info.name}</span>
                      <span className={`history-item-badge ${info.malignant ? 'history-item-badge-malignant' : 'history-item-badge-benign'}`}>
                        {info.malignant ? 'Злокачественная' : 'Доброкачественная'}
                      </span>
                      <span className="history-item-confidence">{main.value}%</span>
                    </>
                  )}
                </div>
                <span className="history-item-expand">{isExpanded ? '▼' : '▶'}</span>
                <button
                  type="button"
                  className="history-item-remove"
                  onClick={(e) => handleRemove(e, item.id)}
                  title="Удалить"
                  aria-label="Удалить запись"
                >
                  ✕
                </button>
              </button>

              {isExpanded && item.result && (
                <div className="history-item-detail">
                  {item.image && (
                    <div className="history-detail-image">
                      <img src={item.image} alt="Изображение анализа" />
                    </div>
                  )}
                  <div className="history-detail-result">
                    <h4>ОСНОВНОЙ ДИАГНОЗ</h4>
                    {info && (
                      <div className="history-detail-main">
                        <strong>{info.name}</strong>
                        <span className={`history-badge ${info.malignant ? 'history-badge-malignant' : 'history-badge-benign'}`}>
                          {info.malignant ? 'ЗЛОКАЧЕСТВЕННАЯ' : 'ДОБРОКАЧЕСТВЕННАЯ'}
                        </span>
                        <span>Уверенность: {main.value}%</span>
                        <p>{info.description}</p>
                      </div>
                    )}
                    <h4>ТОП-3 ВЕРОЯТНОСТИ</h4>
                    <ul className="history-detail-top3">
                      {item.result.top3?.map((p, i) => {
                        const diag = DIAGNOSES[p.key]
                        if (!diag) return null
                        return (
                          <li key={p.key}>
                            {diag.name}: {p.value}%
                            <div className="history-detail-bar-wrap">
                              <div className="history-detail-bar" style={{ width: `${p.value}%` }} />
                            </div>
                          </li>
                        )
                      })}
                    </ul>
                  </div>
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
