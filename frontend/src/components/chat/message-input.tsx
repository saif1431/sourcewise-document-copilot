import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { SendIcon } from 'lucide-react'

import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupTextarea } from '@/components/ui/input-group'
import { Spinner } from '@/components/ui/spinner'

interface MessageInputProps {
  disabled: boolean
  onSend: (text: string) => void
}

export function MessageInput({ disabled, onSend }: MessageInputProps) {
  const [value, setValue] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto w-full max-w-2xl px-4 pb-4">
      <InputGroup>
        <InputGroupTextarea
          placeholder="Ask about a filing..."
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        <InputGroupAddon align="block-end">
          <InputGroupButton type="submit" size="icon-sm" disabled={disabled || !value.trim()}>
            {disabled ? <Spinner /> : <SendIcon />}
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
    </form>
  )
}
