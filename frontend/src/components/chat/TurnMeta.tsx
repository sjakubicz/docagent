import { Badge, HStack } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage, FormattedNumber } from 'react-intl'
import type { AgentResult } from '../../client'
import { SEARCH_MODES } from '../../lib/chatOptions'
import { Tip } from '../shared/Tip'

interface TurnMetaProps {
    result: AgentResult
}

export const TurnMeta: FC<TurnMetaProps> = ({ result }) => {
    const mode = SEARCH_MODES.find((m) => m.value === result.options.search_mode)
    return (
        <HStack gap={1} wrap="wrap">
            <Tip id="turn.mode.tip">
                <Badge variant="subtle">{mode && <FormattedMessage id={mode.label} />}</Badge>
            </Tip>
            <Tip id="turn.topK.tip">
                <Badge variant="subtle">
                    <FormattedMessage id="turn.topK" values={{ count: result.options.top_k }} />
                </Badge>
            </Tip>
            <Tip id="turn.steps.tip">
                <Badge variant="subtle">
                    <FormattedMessage id="turn.steps" values={{ count: result.steps.length }} />
                </Badge>
            </Tip>
            <Tip id="turn.duration.tip">
                <Badge variant="subtle">
                    <FormattedMessage
                        id="turn.duration"
                        values={{
                            seconds: (
                                <FormattedNumber
                                    value={result.duration_ms / 1000}
                                    maximumFractionDigits={1}
                                />
                            ),
                        }}
                    />
                </Badge>
            </Tip>
        </HStack>
    )
}
