import { HStack, IconButton } from '@chakra-ui/react'
import { MessageSquarePlus } from 'lucide-react'
import type { FC } from 'react'
import { useIntl } from 'react-intl'
import type { ChatOptions } from '../../client'
import { Tip } from '../shared/Tip'
import { ChatSettings } from './ChatSettings'

interface ChatToolbarProps {
    options: ChatOptions | null
    onChange: (patch: Partial<ChatOptions>) => void
    onReset: () => void
    onClear: () => void
    canClear: boolean
}

export const ChatToolbar: FC<ChatToolbarProps> = ({
    options,
    onChange,
    onReset,
    onClear,
    canClear,
}) => {
    const intl = useIntl()
    return (
        <HStack justify="end" gap={1}>
            <Tip id="chat.clear.tip">
                <IconButton
                    aria-label={intl.formatMessage({ id: 'chat.clear' })}
                    variant="ghost"
                    size="sm"
                    onClick={onClear}
                    disabled={!canClear}
                >
                    <MessageSquarePlus />
                </IconButton>
            </Tip>
            <ChatSettings options={options} onChange={onChange} onReset={onReset} />
        </HStack>
    )
}
