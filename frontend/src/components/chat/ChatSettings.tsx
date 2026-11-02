import { Button, IconButton, Popover, Portal, Stack } from '@chakra-ui/react'
import { Settings2 } from 'lucide-react'
import type { FC } from 'react'
import { FormattedMessage, useIntl } from 'react-intl'
import type { ChatOptions } from '../../client'
import { MAX_STEPS, MAX_TOP_K } from '../../lib/chatOptions'
import { Tip } from '../shared/Tip'
import { NumberSetting } from './NumberSetting'
import { SearchModeSetting } from './SearchModeSetting'

interface ChatSettingsProps {
    options: ChatOptions | null
    onChange: (patch: Partial<ChatOptions>) => void
    onReset: () => void
}

export const ChatSettings: FC<ChatSettingsProps> = ({ options, onChange, onReset }) => {
    const intl = useIntl()
    return (
        <Popover.Root positioning={{ placement: 'bottom-end' }}>
            <Tip id="settings.open.tip">
                <Popover.Trigger asChild>
                    <IconButton
                        aria-label={intl.formatMessage({ id: 'settings.title' })}
                        variant="ghost"
                        size="sm"
                        disabled={!options}
                    >
                        <Settings2 />
                    </IconButton>
                </Popover.Trigger>
            </Tip>
            <Portal>
                <Popover.Positioner>
                    <Popover.Content>
                        <Popover.Arrow />
                        <Popover.Body>
                            <Popover.Title fontWeight="medium" mb={4}>
                                <FormattedMessage id="settings.title" />
                            </Popover.Title>
                            {options && (
                                <Stack gap={4}>
                                    <SearchModeSetting
                                        value={options.search_mode}
                                        onChange={(search_mode) => onChange({ search_mode })}
                                    />
                                    <NumberSetting
                                        label="settings.topK.label"
                                        tip="settings.topK.tip"
                                        value={options.top_k}
                                        max={MAX_TOP_K}
                                        onChange={(top_k) => onChange({ top_k })}
                                    />
                                    <NumberSetting
                                        label="settings.maxSteps.label"
                                        tip="settings.maxSteps.tip"
                                        value={options.max_steps}
                                        max={MAX_STEPS}
                                        onChange={(max_steps) => onChange({ max_steps })}
                                    />
                                    <Tip id="settings.reset.tip">
                                        <Button size="xs" variant="outline" onClick={onReset}>
                                            <FormattedMessage id="settings.reset" />
                                        </Button>
                                    </Tip>
                                </Stack>
                            )}
                        </Popover.Body>
                    </Popover.Content>
                </Popover.Positioner>
            </Portal>
        </Popover.Root>
    )
}
