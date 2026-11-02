import { Badge, Card, HStack, Text } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage, FormattedNumber } from 'react-intl'
import type { SearchHit } from '../../client'
import { Tip } from './Tip'

interface HitCardProps {
    hit: SearchHit
    showScore?: boolean
}

export const HitCard: FC<HitCardProps> = ({ hit, showScore = false }) => (
    <Card.Root size="sm" variant="outline">
        <Card.Body gap={2}>
            <HStack justify="space-between">
                <Tip id="hit.tip" values={{ filename: hit.filename, page: hit.page }}>
                    <Text fontWeight="medium" fontSize="sm">
                        <FormattedMessage
                            id="hit.location"
                            values={{ filename: hit.filename, page: hit.page }}
                        />
                    </Text>
                </Tip>
                {showScore && (
                    <Tip id="hit.score.tip">
                        <Badge variant="subtle">
                            <FormattedNumber value={hit.score} maximumFractionDigits={3} />
                        </Badge>
                    </Tip>
                )}
            </HStack>
            <Text fontSize="sm" color="fg.muted" lineClamp={4}>
                {hit.text}
            </Text>
        </Card.Body>
    </Card.Root>
)
