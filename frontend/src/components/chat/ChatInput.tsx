import { Button, HStack, Textarea } from '@chakra-ui/react'
import { useState, type FC, type KeyboardEvent } from 'react'
import { FormattedMessage, useIntl } from 'react-intl'
import { useAutoResize } from '../../hooks/useAutoResize'
import { Tip } from '../shared/Tip'

interface ChatInputProps {
    onSend: (question: string) => Promise<boolean>
    busy: boolean
}

export const ChatInput: FC<ChatInputProps> = ({ onSend, busy }) => {
    const intl = useIntl()
    const [input, setInput] = useState('')
    const textarea = useAutoResize(input)

    const submit = async () => {
        const question = input.trim()
        if (!question || busy) return
        setInput('')
        if (!(await onSend(question))) setInput(question)
    }

    const onKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            void submit()
        }
    }

    return (
        <HStack align="stretch">
            <Tip id="chat.input.tip">
                <Textarea
                    ref={textarea}
                    rows={1}
                    resize="none"
                    maxH="2xs"
                    overflowY="auto"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={onKeyDown}
                    placeholder={intl.formatMessage({ id: 'chat.input.placeholder' })}
                />
            </Tip>
            <Tip id="chat.send.tip">
                <Button
                    h="auto"
                    variant="outline"
                    outlineColor="gray.800"
                    onClick={submit}
                    loading={busy}
                    disabled={!input.trim()}
                >
                    <FormattedMessage id="chat.send" />
                </Button>
            </Tip>
        </HStack>
    )
}
