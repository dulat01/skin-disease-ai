import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Auth.css'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login, resetPassword } = useAuth()
  const navigate = useNavigate()

  const [forgotStep, setForgotStep] = useState(0)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotPassword, setForgotPassword] = useState('')
  const [forgotError, setForgotError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    if (!email.trim() || !password) {
      setError('Введите email и пароль')
      return
    }
    if (!login(email.trim(), password)) {
      setError('Неверный email или пароль')
      return
    }
    navigate('/', { replace: true })
  }

  const handleForgotReset = (e) => {
    e.preventDefault()
    setForgotError('')
    if (!forgotEmail.trim()) {
      setForgotError('Введите email')
      return
    }
    if (!forgotPassword || forgotPassword.length < 6) {
      setForgotError('Пароль должен быть не менее 6 символов')
      return
    }
    if (!resetPassword(forgotEmail.trim(), forgotPassword)) {
      setForgotError('Пользователь с таким email не найден')
      return
    }
    setForgotStep(0)
    setForgotEmail('')
    setForgotPassword('')
    setForgotError('')
    setError('Пароль успешно изменён. Войдите с новым паролем.')
  }

  const closeForgot = () => {
    setForgotStep(0)
    setForgotEmail('')
    setForgotPassword('')
    setForgotError('')
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-icon">✚</span>
          <h1>Вход в систему</h1>
          <p>Диагностика заболеваний кожи</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="auth-error">{error}</div>}
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@gmail.com"
              autoComplete="email"
            />
          </label>
          <label>
            Пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </label>
          <button type="submit" className="auth-submit">
            Войти
          </button>
          <button
            type="button"
            className="auth-forgot-link"
            onClick={() => setForgotStep(1)}
          >
            Забыли пароль?
          </button>
        </form>
        <p className="auth-footer">
          Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
        </p>
      </div>

      {forgotStep > 0 && (
        <div className="auth-overlay" onClick={closeForgot}>
          <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Сброс пароля</h3>
            <form className="auth-form" onSubmit={handleForgotReset}>
              <p className="auth-code-hint">
                Введите email и новый пароль. (Демо-режим без подтверждения по почте)
              </p>
              {forgotError && <div className="auth-error">{forgotError}</div>}
              <label>
                Email
                <input
                  type="email"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  placeholder="example@mail.ru"
                  autoFocus
                />
              </label>
              <label>
                Новый пароль
                <input
                  type="password"
                  value={forgotPassword}
                  onChange={(e) => setForgotPassword(e.target.value)}
                  placeholder="Не менее 6 символов"
                  autoComplete="new-password"
                />
              </label>
              <div className="auth-modal-actions">
                <button type="submit" className="auth-submit">
                  Сохранить пароль
                </button>
                <button type="button" className="auth-back" onClick={closeForgot}>
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
