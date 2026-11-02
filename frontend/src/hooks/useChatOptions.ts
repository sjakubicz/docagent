import { useEffect, useState } from 'react'
import { defaultChatOptions, type ChatOptions } from '../client'
import { loadStoredOptions, storeOptions } from '../lib/chatOptions'

export const useChatOptions = () => {
    const [defaults, setDefaults] = useState<ChatOptions | null>(null)
    const [custom, setCustom] = useState<ChatOptions | null>(loadStoredOptions)

    useEffect(() => {
        void defaultChatOptions().then(({ data }) => setDefaults(data ?? null))
    }, [])

    const update = (patch: Partial<ChatOptions>) => {
        const base = custom ?? defaults
        if (!base) return
        const next = { ...base, ...patch }
        setCustom(next)
        storeOptions(next)
    }

    const reset = () => {
        setCustom(null)
        storeOptions(null)
    }

    return { options: custom ?? defaults, update, reset }
}
