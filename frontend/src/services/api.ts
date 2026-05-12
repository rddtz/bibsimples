import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await api.post('/auth/login', { username, password })
    return response.data
  },
  logout: async () => {
    const response = await api.post('/auth/logout')
    return response.data
  },
  me: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

export const searchApi = {
  search: async (query: string, options?: {
    database?: string
    material_type?: string
    page?: number
    per_page?: number
  }) => {
    const params = new URLSearchParams()
    params.set('query', query)
    if (options?.database) params.set('database', options.database)
    if (options?.material_type) params.set('material_type', options.material_type)
    if (options?.page) params.set('page', String(options.page))
    if (options?.per_page) params.set('per_page', String(options.per_page))

    const response = await api.get(`/search?${params}`)
    return response.data
  },
}

export const utilsApi = {
  generateCutter: async (author: string) => {
    const response = await api.post('/utils/cutter', { author })
    return response.data
  },
  formatAuthor: async (name: string) => {
    const response = await api.post('/utils/format-author', { name })
    return response.data
  },
  generateBookCode: async (data: {
    author: string
    title: string
    classification?: string
    volume?: string
  }) => {
    const response = await api.post('/utils/book-code', data)
    return response.data
  },
}

export interface SimilarRecord {
  id: number
  title: string
  author: string
  holdings_count: number
  holdings_available: number
}

export const catalogApi = {
  createBook: async (data: {
    author_name: string
    title: string
    cdd: string
    copies: number
    cutter_code?: string
    volume?: string
  }) => {
    const response = await api.post('/catalog/books', data)
    return response.data
  },
  findSimilar: async (title: string, author?: string): Promise<{ matches: SimilarRecord[] }> => {
    const params = new URLSearchParams({ title })
    if (author) params.set('author', author)
    const response = await api.get(`/catalog/books/similar?${params}`)
    return response.data
  },
  addCopies: async (recordId: number, copies: number) => {
    const response = await api.post(`/catalog/books/${recordId}/copies`, { copies })
    return response.data
  },
}

export default api
