import { useEffect, useState } from 'react'
import { getDocument, type DocumentDetail } from '../client'

export const useDocument = (id: number) => {
    const [doc, setDoc] = useState<DocumentDetail | null>(null)
    const [error, setError] = useState<unknown>(null)

    useEffect(() => {
        let active = true
        void getDocument({ path: { document_id: id } }).then(({ data, error }) => {
            if (!active) return
            setDoc(data ?? null)
            setError(error ?? null)
        })
        return () => {
            active = false
        }
    }, [id])

    return { doc, error }
}
