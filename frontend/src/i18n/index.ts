import en from './messages/en.json'

export const DEFAULT_LOCALE = 'en'

export const MESSAGES = { en } satisfies Record<string, Record<MessageId, string>>

export type Locale = keyof typeof MESSAGES
export type MessageId = keyof typeof en

const isLocale = (value: string): value is Locale => value in MESSAGES

export const detectLocale = (): Locale => {
    const preferred = navigator.languages.map((tag) => tag.split('-')[0])
    return preferred.find(isLocale) ?? DEFAULT_LOCALE
}

declare global {
    namespace FormatjsIntl {
        interface Message {
            ids: MessageId
        }
    }
}
