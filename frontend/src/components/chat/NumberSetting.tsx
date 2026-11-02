import { Field, NumberInput } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import type { MessageId } from '../../i18n'
import { Tip } from '../shared/Tip'

interface NumberSettingProps {
    label: MessageId
    tip: MessageId
    value: number
    max: number
    onChange: (value: number) => void
}

export const NumberSetting: FC<NumberSettingProps> = ({ label, tip, value, max, onChange }) => (
    <Field.Root>
        <Field.Label>
            <FormattedMessage id={label} />
        </Field.Label>
        <Tip id={tip} values={{ max }}>
            <NumberInput.Root
                size="sm"
                width="24"
                min={1}
                max={max}
                value={String(value)}
                onValueChange={(e) => Number.isFinite(e.valueAsNumber) && onChange(e.valueAsNumber)}
            >
                <NumberInput.Control />
                <NumberInput.Input />
            </NumberInput.Root>
        </Tip>
    </Field.Root>
)
