import { Stack, Text } from '@chakra-ui/react'
import type { FC } from 'react'
import type { Turn } from '../../lib/chat'
import { Tip } from '../shared/Tip'
import { AgentTrace } from './AgentTrace'
import { TurnMeta } from './TurnMeta'
import { UserBubble } from './UserBubble'

interface TurnViewProps {
    turn: Turn
}

export const TurnView: FC<TurnViewProps> = ({ turn }) => (
    <Stack gap={2}>
        <UserBubble text={turn.question} />
        <Tip id="chat.answer.tip">
            <Text whiteSpace="pre-wrap" alignSelf="start">
                {turn.response.answer}
            </Text>
        </Tip>
        <TurnMeta result={turn.response} />
        <AgentTrace steps={turn.response.steps} />
    </Stack>
)
