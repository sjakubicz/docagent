import type { AgentResult, ChatMessage } from '../client'

export type Turn = { question: string; response: AgentResult }

export const toHistory = (turns: Turn[]): ChatMessage[] =>
    turns.flatMap((turn) => [
        { role: 'user', content: turn.question },
        { role: 'assistant', content: turn.response.answer },
    ])
