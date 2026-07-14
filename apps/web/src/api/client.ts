import axios from 'axios'

const client = axios.create({
  // In local dev / docker-compose, '/api' is proxied to the backend (Vite proxy or nginx).
  // For a split deploy (static frontend + separate backend host), set VITE_API_BASE_URL
  // at build time to the backend's full URL, e.g. https://cashflow-sahayak-api.onrender.com/api
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('cf_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default client
