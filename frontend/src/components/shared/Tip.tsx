import { Portal, Tooltip } from '@chakra-ui/react'
import type { FC, ReactElement } from 'react'
import { useIntl } from 'react-intl'
import type { MessageId } from '../../i18n'

interface TipProps {
    id: MessageId
    values?: Record<string, string | number>
    children: ReactElement
}

export const Tip: FC<TipProps> = ({ id, values, children }) => {
    const intl = useIntl()
    return (
        <Tooltip.Root openDelay={300} closeDelay={100} positioning={{ placement: 'top' }}>
            <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
            <Portal>
                <Tooltip.Positioner>
                    <Tooltip.Content maxW="xs">
                        {intl.formatMessage({ id }, values)}
                    </Tooltip.Content>
                </Tooltip.Positioner>
            </Portal>
        </Tooltip.Root>
    )
}
