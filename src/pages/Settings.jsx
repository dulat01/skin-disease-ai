import React from 'react'
import { useAuth } from '../context/AuthContext'
import './Settings.css'

export default function Settings() {
  const { user } = useAuth()

  return (
    <div className="settings-page">
      <h2 className="settings-title">Настройки</h2>
      <p className="settings-subtitle">Управление аккаунтом и приложением</p>

      <section className="settings-section">
        <h3 className="settings-section-title">Профиль</h3>
        <div className="settings-row">
          <span className="settings-label">Имя</span>
          <span className="settings-value">{user?.name || '—'}</span>
        </div>
        <div className="settings-row">
          <span className="settings-label">Email</span>
          <span className="settings-value">{user?.email || '—'}</span>
        </div>
      </section>

      <section className="settings-section">
        <h3 className="settings-section-title">Приложение</h3>
        <p className="settings-info">
          Диагностика заболеваний кожи — CAS Model. Модель ResNet18, точность 77.10%.
          Результаты носят справочный характер. Всегда консультируйтесь с врачом-дерматологом.
        </p>
      </section>
    </div>
  )
}
