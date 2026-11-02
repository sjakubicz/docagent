import { Badge, Code, HStack, Stack, Text, Timeline } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import type { ToolStep } from '../../client'
import { stepTip } from '../../lib/steps'
import { HitCard } from '../shared/HitCard'
import { Tip } from '../shared/Tip'

interface StepViewProps {
    step: ToolStep
}

export const StepView: FC<StepViewProps> = ({ step }) => (
    <Timeline.Item>
        <Timeline.Connector>
            <Timeline.Separator />
            <Timeline.Indicator bg={step.error ? 'red.solid' : undefined} />
        </Timeline.Connector>
        <Timeline.Content>
            <HStack gap={1} wrap="wrap">
                <Tip id={stepTip(step.name)}>
                    <Badge colorPalette={step.error ? 'red' : 'purple'}>{step.name}</Badge>
                </Tip>
                {step.automatic && (
                    <Tip id="step.auto.tip">
                        <Badge variant="outline">
                            <FormattedMessage id="step.auto" />
                        </Badge>
                    </Tip>
                )}
                {step.error && (
                    <Tip id="step.error.tip">
                        <Badge colorPalette="red" variant="outline">
                            <FormattedMessage id="step.error" />
                        </Badge>
                    </Tip>
                )}
            </HStack>
            <Tip id="step.args.tip">
                <Code alignSelf="start" whiteSpace="pre-wrap">
                    {JSON.stringify(step.args)}
                </Code>
            </Tip>
            <StepResult step={step} />
        </Timeline.Content>
    </Timeline.Item>
)

const StepResult: FC<StepViewProps> = ({ step }) => {
    if (step.hits.length > 0) {
        return (
            <Stack gap={2}>
                {step.hits.map((hit, i) => (
                    <HitCard key={i} hit={hit} showScore={step.name === 'search_documents'} />
                ))}
            </Stack>
        )
    }
    if (step.name === 'search_documents' && !step.error) {
        return (
            <Tip id="step.noHits.tip">
                <Text fontSize="sm" color="fg.muted" alignSelf="start">
                    <FormattedMessage id="step.noHits" />
                </Text>
            </Tip>
        )
    }
    return (
        <Tip id="step.output.tip">
            <Text fontSize="sm" color="fg.muted" whiteSpace="pre-wrap" alignSelf="start">
                {step.output}
            </Text>
        </Tip>
    )
}
