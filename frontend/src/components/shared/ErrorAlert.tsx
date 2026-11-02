import { Alert } from '@chakra-ui/react'
import type { FC } from 'react'
import { errorMessage } from '../../lib/errors'

interface ErrorAlertProps {
    error: unknown
}

export const ErrorAlert: FC<ErrorAlertProps> = ({ error }) => {
    if (!error) return null
    return (
        <Alert.Root status="error">
            <Alert.Indicator />
            <Alert.Title>{errorMessage(error)}</Alert.Title>
        </Alert.Root>
    )
}
