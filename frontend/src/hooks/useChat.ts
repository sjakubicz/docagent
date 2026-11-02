import { useState } from 'react'
import { useIntl } from 'react-intl'
import { chat, type ChatOptions } from '../client'
import { toHistory, type Turn } from '../lib/chat'

export const useChat = (options: ChatOptions | null) => {
    const intl = useIntl()
    const [turns, setTurns] = useState<Turn[]>([])
    const [pending, setPending] = useState<string | null>(null)
    const [error, setError] = useState<unknown>(null)

    const send = async (question: string): Promise<boolean> => {
        setError(null)
        setPending(question)
        const { data, error } = await chat({
            body: { message: question, history: toHistory(turns), options },
        })
        setPending(null)
        if (error || !data) {
            setError(error ?? intl.formatMessage({ id: 'chat.noResponse' }))
            return false
        }
        setTurns((prev) => [...prev, { question, response: data }])
        return true
    }

    const clear = () => {
        setTurns([])
        setError(null)
    }

    return { turns, pending, error, send, clear }
}
