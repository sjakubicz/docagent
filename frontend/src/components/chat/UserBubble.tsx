import { Box, Text } from '@chakra-ui/react'
import type { FC } from 'react'
import { Tip } from '../shared/Tip'

interface UserBubbleProps {
    text: string
}

export const UserBubble: FC<UserBubbleProps> = ({ text }) => (
    <Tip id="chat.question.tip">
        <Box alignSelf="end" bg="bg.muted" px={4} py={2} borderRadius="lg" maxW="80%">
            <Text whiteSpace="pre-wrap">{text}</Text>
        </Box>
    </Tip>
)
