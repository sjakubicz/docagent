import { Badge, Card, HStack, Stack, Text } from '@chakra-ui/react'
import type { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import type { PageOut } from '../../client'
import { Tip } from '../shared/Tip'

interface PageListProps {
    pages: PageOut[]
}

export const PageList: FC<PageListProps> = ({ pages }) => (
    <Stack gap={3}>
        {pages.map((page) => (
            <Card.Root key={page.number} size="sm" variant="outline">
                <Card.Body gap={2}>
                    <HStack>
                        <Tip id="preview.page.tip" values={{ number: page.number }}>
                            <Text fontWeight="medium" fontSize="sm">
                                <FormattedMessage
                                    id="preview.page"
                                    values={{ number: page.number }}
                                />
                            </Text>
                        </Tip>
                        {page.ocr && (
                            <Tip id="preview.ocr.tip">
                                <Badge size="sm" colorPalette="purple">
                                    <FormattedMessage id="preview.ocr" />
                                </Badge>
                            </Tip>
                        )}
                    </HStack>
                    <Text fontSize="sm" whiteSpace="pre-wrap">
                        {page.text}
                    </Text>
                </Card.Body>
            </Card.Root>
        ))}
    </Stack>
)
