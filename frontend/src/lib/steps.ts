import type { MessageId } from '../i18n'

const TOOL_TIPS: Record<string, MessageId> = {
    search_documents: 'step.search_documents.tip',
    list_documents: 'step.list_documents.tip',
    read_page: 'step.read_page.tip',
}

export const stepTip = (name: string): MessageId => TOOL_TIPS[name] ?? 'step.unknown.tip'
