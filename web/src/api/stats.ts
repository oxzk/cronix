import { api } from './client'
import type { Stats } from './types'

export function getStats(): Promise<Stats> {
    return api.get<Stats>('/api/v1/stats')
}
