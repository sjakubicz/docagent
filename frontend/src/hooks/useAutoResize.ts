import { useLayoutEffect, useRef } from 'react'

export const useAutoResize = (value: string) => {
    const ref = useRef<HTMLTextAreaElement>(null)

    useLayoutEffect(() => {
        const el = ref.current
        if (!el) return
        el.style.height = 'auto'
        const border = el.offsetHeight - el.clientHeight
        el.style.height = `${el.scrollHeight + border}px`
    }, [value])

    return ref
}
