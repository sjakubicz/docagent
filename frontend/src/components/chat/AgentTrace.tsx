import { Button, Collapsible, Timeline } from '@chakra-ui/react'
import { ChevronDown } from 'lucide-react'
import type { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import type { ToolStep } from '../../client'
import { Tip } from '../shared/Tip'
import { StepView } from './StepView'

interface AgentTraceProps {
    steps: ToolStep[]
}

export const AgentTrace: FC<AgentTraceProps> = ({ steps }) => (
    <Collapsible.Root>
        <Tip id="turn.details.tip">
            <Collapsible.Trigger asChild>
                <Button variant="ghost" size="xs" alignSelf="start">
                    <FormattedMessage id="turn.details" />
                    <ChevronDown />
                </Button>
            </Collapsible.Trigger>
        </Tip>
        <Collapsible.Content>
            <Timeline.Root size="sm" pt={2}>
                {steps.map((step, i) => (
                    <StepView key={i} step={step} />
                ))}
            </Timeline.Root>
        </Collapsible.Content>
    </Collapsible.Root>
)
