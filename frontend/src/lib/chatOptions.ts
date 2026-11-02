import type { ChatOptions } from '../client'
import type { MessageId } from '../i18n'

export type SearchMode = ChatOptions['search_mode']

export const MAX_TOP_K = 20
export const MAX_STEPS = 10

export const SEARCH_MODES: { value: SearchMode; label: MessageId; tip: MessageId }[] = [
    { value: 'hybrid', label: 'settings.mode.hybrid', tip: 'settings.mode.hybrid.tip' },
    { value: 'bm25', label: 'settings.mode.bm25', tip: 'settings.mode.bm25.tip' },
    { value: 'vector', label: 'settings.mode.vector', tip: 'settings.mode.vector.tip' },
]

const STORAGE_KEY = 'docagent.chatOptions'

export const loadStoredOptions = (): ChatOptions | null => {
    try {
        const raw = localStorage.getItem(STORAGE_KEY)
        return raw ? (JSON.parse(raw) as ChatOptions) : null
    } catch {
        return null
    }
}

export const storeOptions = (options: ChatOptions | null) => {
    try {
        if (options) localStorage.setItem(STORAGE_KEY, JSON.stringify(options))
        else localStorage.removeItem(STORAGE_KEY)
    } catch {
        return
    }
}
