import { HStack, Spinner, Stack } from '@chakra-ui/react'
import type { FC } from 'react'
import { useChat } from '../../hooks/useChat'
import { useChatOptions } from '../../hooks/useChatOptions'
import { ErrorAlert } from '../shared/ErrorAlert'
import { Tip } from '../shared/Tip'
import { ChatInput } from './ChatInput'
import { ChatToolbar } from './ChatToolbar'
import { TurnView } from './TurnView'
import { UserBubble } from './UserBubble'

export const ChatPanel: FC = () => {
    const { options, update, reset } = useChatOptions()
    const { turns, pending, error, send, clear } = useChat(options)
    return (
        <Stack gap={4} pt={4}>
            <ChatToolbar
                options={options}
                onChange={update}
                onReset={reset}
                onClear={clear}
                canClear={turns.length > 0}
            />
            {turns.map((turn, i) => (
                <TurnView key={i} turn={turn} />
            ))}
            {pending && (
                <Stack gap={2}>
                    <UserBubble text={pending} />
                    <HStack>
                        <Tip id="chat.thinking.tip">
                            <Spinner size="sm" />
                        </Tip>
                    </HStack>
                </Stack>
            )}
            <ErrorAlert error={error} />
            <ChatInput onSend={send} busy={!!pending} />
        </Stack>
    )
}
