import { Field, SegmentGroup } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import { SEARCH_MODES, type SearchMode } from '../../lib/chatOptions'
import { Tip } from '../shared/Tip'

interface SearchModeSettingProps {
    value: SearchMode
    onChange: (mode: SearchMode) => void
}

const isSearchMode = (value: string | null): value is SearchMode =>
    SEARCH_MODES.some((mode) => mode.value === value)

export const SearchModeSetting: FC<SearchModeSettingProps> = ({ value, onChange }) => (
    <Field.Root>
        <Tip id="settings.mode.tip">
            <Field.Label>
                <FormattedMessage id="settings.mode.label" />
            </Field.Label>
        </Tip>
        <SegmentGroup.Root
            size="sm"
            value={value}
            onValueChange={(e) => isSearchMode(e.value) && onChange(e.value)}
        >
            <SegmentGroup.Indicator />
            {SEARCH_MODES.map((mode) => (
                <SegmentGroup.Item key={mode.value} value={mode.value}>
                    <Tip id={mode.tip}>
                        <SegmentGroup.ItemText>
                            <FormattedMessage id={mode.label} />
                        </SegmentGroup.ItemText>
                    </Tip>
                    <SegmentGroup.ItemHiddenInput />
                </SegmentGroup.Item>
            ))}
        </SegmentGroup.Root>
    </Field.Root>
)
